from typing import Optional

from webdnn.graph.axis import Axis
from webdnn.graph.operator import Operator
from webdnn.graph.operators.attributes.axiswise import Axiswise
from webdnn.graph.operators.attributes.post_axiswise import PostAxiswise
from webdnn.graph.operators.util import IntOrTuple, to_tuple
from webdnn.graph.order import OrderNHWC
from webdnn.graph.variable import Variable


class ZeroPadding2D(Operator):
    """Zero padding 2D operator

    Supposed to be merged into convolution in optimization

    Args:
        name (str): Operator name.
        padding (int or tuple of int): Padding size. [top, left]
    """

    def __init__(self, name: Optional[str], padding: IntOrTuple):
        super().__init__(name)
        self.parameters["padding"] = to_tuple(padding)
        self.attributes = {PostAxiswise(self, Axis.C),
                           Axiswise(self, Axis.C)}

    def __call__(self, x: Variable):
        """
        Args:
            x (:class:`~webdnn.graph.variable.Variable`): Input

        Returns:
            tuple of :class:`~webdnn.graph.variable.Variable`: Output
        """
        x_shape_dict = x.shape_dict
        N = x_shape_dict[Axis.N]
        H2 = x_shape_dict[Axis.H] + 2 * self.parameters["padding"][0]
        W2 = x_shape_dict[Axis.W] + 2 * self.parameters["padding"][1]
        C2 = x_shape_dict[Axis.C]

        y = Variable([N, H2, W2, C2], OrderNHWC)

        self.append_input("x", x)
        self.append_output("y", y)
        return y,
