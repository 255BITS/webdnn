from typing import Optional

from webdnn.graph.operators.attributes.scalar_operation import ScalarOperation
from webdnn.graph.operators.elementwise import Elementwise


class ScalarAdd(Elementwise):
    def __init__(self, name: Optional[str], value: float):
        super().__init__(name)
        self.attributes.add(ScalarOperation(self))
        self.parameters["value"] = value

    @property
    def value(self) -> float:
        return self.parameters["value"]
