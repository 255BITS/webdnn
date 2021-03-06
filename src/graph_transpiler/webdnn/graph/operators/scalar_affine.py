from typing import Optional

from webdnn.graph.operators.attributes.scalar_operation import ScalarOperation
from webdnn.graph.operators.elementwise import Elementwise


class ScalarAffine(Elementwise):
    def __init__(self, name: Optional[str], scale: float, bias: float):
        super().__init__(name)
        self.attributes.add(ScalarOperation(self))
        self.scale = scale
        self.bias = bias

    @property
    def scale(self) -> float:
        return self.parameters["scale"]

    @scale.setter
    def scale(self, value: float):
        self.parameters["scale"] = value

    @property
    def bias(self) -> float:
        return self.parameters["bias"]

    @bias.setter
    def bias(self, value: float):
        self.parameters["bias"] = value
