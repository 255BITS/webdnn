from enum import auto, Enum
from typing import Dict, List, Set, Tuple, Union, Optional

import numpy as np

from webdnn.graph import traverse
from webdnn.graph.graph import Graph
from webdnn.graph.operator import Operator
from webdnn.graph.operators.attributes.inplace import Inplace
from webdnn.graph.placeholder import Placeholder
from webdnn.graph.variable import Variable
from webdnn.graph.variables.constant_variable import ConstantVariable
from webdnn.util import json, flags


class BufferType(Enum):
    Static = auto()
    Dynamic = auto()


class Allocation(json.SerializableMixin):
    variable: Variable
    offset: Union[int, Placeholder]
    buffer_type: BufferType

    def __init__(self,
                 variable: Variable,
                 offset: Union[int, Placeholder],
                 buffer_type: BufferType):
        self.variable = variable
        self.offset = offset
        self.buffer_type = buffer_type

    @property
    def size(self) -> Union[int, Placeholder]:
        return self.variable.size

    def _to_serializable_(self):
        return {
            "name": self.variable.name,
            "offset": self.offset,
            "size": self.size
        }


class MemoryLayout(json.SerializableMixin):
    data: np.array

    def __init__(self):
        self.allocations = {}  # type: Dict[str, Allocation]

    def _to_serializable_(self):
        return {
            "static": {
                "size": self.static_size,
                "allocations": {a.variable.name: a for a in self.allocations.values() if
                                a.buffer_type == BufferType.Static}
            },
            "dynamic": {
                "size": self.dynamic_size,
                "allocations": {a.variable.name: a for a in self.allocations.values() if
                                a.buffer_type == BufferType.Dynamic}
            }
        }

    def __len__(self):
        return len(self.allocations)

    def __getitem__(self, var: Variable):
        return self.allocations[var.name]

    def __contains__(self, var: Variable):
        return var.name in self.allocations

    def append(self, var: Variable, offset: Union[int, Placeholder] = -1, buffer_type: Optional[BufferType] = None):
        if buffer_type is None:
            if Placeholder.check_resolved(offset) and Placeholder.check_resolved(var.size):
                buffer_type = BufferType.Static
            else:
                buffer_type = BufferType.Dynamic

        if offset == -1:
            if buffer_type is BufferType.Static:
                offset = self.static_size
            else:
                offset = self.dynamic_size

        self.allocations[var.name] = Allocation(var, offset, buffer_type)

    @property
    def total_size(self) -> Union[int, Placeholder]:
        return self.static_size + self.dynamic_size

    @property
    def static_size(self) -> int:
        size = 0
        for a in self.allocations.values():
            if a.buffer_type == BufferType.Static:
                size = max(a.offset + a.size, size)

        return size

    @property
    def dynamic_size(self) -> Union[int, Placeholder]:
        size = 0
        for a in self.allocations.values():
            if a.buffer_type == BufferType.Dynamic:
                size += a.size

        return size


class Allocator:
    layout: MemoryLayout

    @classmethod
    def allocate(cls, graph: Graph) -> MemoryLayout:
        variables = set(traverse.listup_variables(graph))
        for i, v in enumerate(variables):
            v.name = f"v{i}"

        return cls.allocate_variables(graph, list(variables))

    @classmethod
    def allocate_variables(cls, graph: Graph, variables: List[Variable]):
        # check if constant variable with shape with unresolved placeholder.
        dynamic_constants = traverse.filter_nodes([v for v in variables if not Placeholder.check_resolved(v.size)],
                                                  ConstantVariable)
        assert len(
            dynamic_constants) == 0, f"ConstantVariable with unresolved placeholder shape is detected: f{dynamic_constants}"

        ops = traverse.listup_operators(graph)
        layout = MemoryLayout()

        lifetime = get_lifetime(graph, ops, variables)  # type: Dict[Variable, Tuple[int, int]]
        offsets = generate_allocation_info(variables, lifetime)  # type: Dict[Variable, Union[int, Placeholder]]
        for variable, offset in offsets.items():
            layout.append(variable, offset)

        layout.data = np.zeros(layout.static_size, dtype=np.float32)
        for var in variables:
            if not isinstance(var, ConstantVariable):
                continue

            allocation = layout[var]
            layout.data[allocation.offset:allocation.offset + allocation.size] = var.data.flatten()

        if flags.VISUALIZE_MEMORY_ALLOCATION:
            _visualize_allocation(ops, variables, layout, lifetime, offsets)

        return layout


def get_lifetime(graph: Graph, ops: List[Operator], variables: List[Variable]):
    LIFETIME_FOREVER = len(ops) + 1

    lifetime = {}  # type: Dict[Variable, Tuple[int, int]]
    retain_count = {v: 0 for v in variables}  # type: Dict[Variable, int]
    allocated = set()  # type: Set[Variable]

    for var in variables:
        if isinstance(var, ConstantVariable):
            lifetime[var] = (0, LIFETIME_FOREVER)
            allocated.add(var)

    for var in graph.inputs:
        lifetime[var] = (0, LIFETIME_FOREVER)
        allocated.add(var)

    for t, op in enumerate(ops):
        for var in op.outputs.values():
            if isinstance(var, ConstantVariable):
                continue

            if var not in allocated:
                flag_allocated = False

                if flags.optimize.OPTIMIZE and flags.optimize.OPTIMIZE_INPLACE_OPERATION \
                    and not flag_allocated \
                    and traverse.check_attribute_match(op, Inplace):

                    # Inplace optimization
                    inplace = op.get_attribute(Inplace)[0]  # type: Inplace
                    v_in = inplace.get_input()  # Use memory allocated for input variable
                    v_out = inplace.get_output()

                    if len(v_in.input_to) == 1 and \
                            v_in.order == v_out.order and \
                            v_in.output_from is not None and \
                            len(v_out.input_to) != 0:
                        while "inplace_src" in v_in.parameters:
                            v_in = v_in.parameters["inplace_src"]

                        var.parameters["inplace_src"] = v_in
                        retain_count[v_in] += len(var.input_to)

                        allocated.add(var)
                        flag_allocated = True

                if not flag_allocated:
                    lifetime[var] = (t, LIFETIME_FOREVER)
                    retain_count[var] = len(var.input_to)

                    allocated.add(var)
                    flag_allocated = True

                if not flag_allocated:
                    raise ValueError("[Allocator] Memory Allocation Failed.")

        for var in op.inputs.values():
            if isinstance(var, ConstantVariable) or var in graph.inputs:
                continue

            while "inplace_src" in var.parameters:
                var = var.parameters["inplace_src"]

            if retain_count[var] == 0:
                # var is temporally workspace memory
                lifetime[var] = (t, t + 1)

            else:
                retain_count[var] -= 1

                if retain_count[var] == 0:
                    # `t + 1` means that `var` will be released AFTER `op` will be finished.
                    lifetime[var] = (lifetime[var][0], t + 1)

    return lifetime


def generate_allocation_info(variables: List[Variable],
                             lifetime: Dict[Variable, Tuple[int, int]]) -> Dict[Variable, int]:
    """
    heuristic-based optimization

        1. allocate constant variables first
        2. allocate unresolved shape variables last
        3. allocate variables which lives longer first
        4. allocate variables which released earlier first
        5. allocate larger variables first
    """

    static_variables = [v for v in variables if Placeholder.check_resolved(v.size)]
    dynamic_variables = [v for v in variables if not Placeholder.check_resolved(v.size)]

    queue = filter(lambda x: x in lifetime, static_variables)
    queue = sorted(queue, key=lambda x: x.size, reverse=True)
    queue = sorted(queue, key=lambda x: lifetime[x][1])
    queue = sorted(queue, key=lambda x: lifetime[x][1] - lifetime[x][0], reverse=True)
    queue = sorted(queue, key=lambda x: isinstance(x, ConstantVariable), reverse=True)
    queue = list(queue)

    allocated_range = {}  # type: Dict[int, List[Tuple[Union[int, Placeholder], Union[int, Placeholder]]]]
    workspace = {v: [0, lifetime[v][0], lifetime[v][1]] for v in queue}
    result = {}  # type: Dict[Variable, int]

    while len(queue) > 0:
        min_offset = +float("inf")
        min_offset_v = None

        # find space
        for v1 in queue:
            info1 = workspace[v1]
            offset1, start1, end1 = info1

            flag_retry = True
            while flag_retry:
                flag_retry = False

                for t in range(start1, end1):
                    if t not in allocated_range:
                        continue

                    for offset2, size2 in allocated_range[t]:
                        if offset2 + size2 <= offset1 or offset1 + v1.size <= offset2:
                            continue

                        else:
                            # align for 16byte
                            offset1 = ((offset2 + size2 + 4 - 1) // 4) * 4
                            flag_retry = True
                            break

                    if flag_retry:
                        break

            info1[0] = offset1
            if offset1 < min_offset:
                min_offset = offset1
                min_offset_v = v1

        queue.remove(min_offset_v)
        _, start1, end1 = workspace[min_offset_v]

        result[min_offset_v] = min_offset
        for t in range(start1, end1):
            if t not in allocated_range:
                allocated_range[t] = []

            allocated_range[t].append((min_offset, min_offset_v.size))

        min_offset += min_offset_v.size

    for v in dynamic_variables:
        result[v] = -1  # FIXME: optimize dynamic allocation

    for v1 in variables:
        v2 = v1
        while "inplace_src" in v2.parameters:
            v2 = v2.parameters["inplace_src"]

        result[v1] = result[v2]

    return result


def _visualize_allocation(ops: List[Operator],
                          variables: List[Variable],
                          layout: MemoryLayout,
                          lifetime: Dict[Variable, Tuple[int, int]],
                          offsets: Dict[Variable, Union[int, Placeholder]]):
    UNIT_HEIGHT = 14
    total_size = layout.total_size
    rendering_dict = {}  # type: Dict[Variable, RenderingInfo]

    class RenderingInfo:
        names: List[str]
        v1: Variable
        offset: int
        lifetime: Tuple[int, int]

        # noinspection PyShadowingNames
        def __init__(self, variable: Variable, offset: int, lifetime: Tuple[int, int]):
            self.names = []
            self.variable = variable
            self.offset = offset
            self.lifetime = lifetime

        @property
        def size(self):
            return self.variable.size

        @property
        def top(self):
            return f"{self.lifetime[0] * UNIT_HEIGHT}px"

        @property
        def height(self):
            return f"{(self.lifetime[1] - self.lifetime[0]) * UNIT_HEIGHT + 1}px"

        @property
        def left(self):
            return f"{self.offset * 100 / total_size}%"

        @property
        def width(self):
            return f"calc({self.size * 100 / total_size}% + 1px)"

        # noinspection PyMethodMayBeStatic
        def generate_html(self):
            return f"""<div class="Allocation {"Constant" if isinstance(self.variable, ConstantVariable) else ""}"
style="top: {self.top}; height: {self.height}; left: {self.left}; width: {self.width}" title="{", ".join(self.names)}
size: {self.size}
offset: {self.offset}
lifetime: {self.lifetime[0]} - {self.lifetime[1]} 
">
    <p>{", ".join(self.names)}</p>
</div>"""

    html = """<html>
<head>
    <style>
        html, body {
            margin: 0;
        }

        body {
            padding: 32px;
            box-sizing: border-box;
        }

        .MemoryLayout {
            position: relative;
            background: #888;
            font-size: 8px;
        }

        .Allocation {
            position: absolute;
            border: 1px solid #000;
            display: block;
            padding: 0;
            box-sizing: border-box;
            overflow: hidden;
            background: #0f0;
        }
        .Constant {
            background: #ff0;
        }
        p {
            margin: 0;
            white-space: nowrap;
        }
    </style>
</head>
<body>
<header style="margin-bottom: 32px;">
    <h1>Memory Allocation Visualization</h1>
    <div style="margin: 32px 0">
        <p>Total allocation size: """ + str(total_size * 4) + """[byte]</p>
        <p># of allocated variables: """ + str(len(layout)) + """</p>
    </div>
    <div style="margin: 32px 0">
        <p>縦軸：時間経過（上から下へ）</p>
        <p>横軸：メモリアドレス</p>
        <p>各要素はカーソルホバーで詳細が見られます。</p>
    </div>
</header>
    <div class="MemoryLayout" style="height: """ + str(UNIT_HEIGHT * (len(ops) + 1) + 1) + """px;">
"""

    for v1 in variables:
        v2 = v1
        while "inplace_src" in v2.parameters:
            v2 = v2.parameters["inplace_src"]

        if v2 not in rendering_dict:
            rendering_dict[v2] = RenderingInfo(v2, offsets[v2], lifetime[v2])

        rendering_dict[v2].names.append(v1.name)

    for item in rendering_dict.values():
        html += item.generate_html()

    html += """
    </div>
</body>
</html>
"""

    with open('memory_visualize.html', "w+") as f:
        f.write(html)
