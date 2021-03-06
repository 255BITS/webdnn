import chainer.computational_graph

from webdnn.frontend.chainer.converter import ChainerConverter
from webdnn.graph.operators.concat import Concat
from webdnn.graph.operators.reshape import Reshape
from webdnn.graph.order import OrderC, OrderNC, OrderNCHW
from webdnn.util import console
from webdnn.util.misc import mul


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("Broadcast")
def _convert_broadcast(converter: ChainerConverter, c_op: chainer.functions.Broadcast):
    # TODO
    raise NotImplementedError("[ChainerConverter] Broadcast is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("BroadcastTo")
def _convert_broadcast_to(converter: ChainerConverter, c_op: chainer.functions.BroadcastTo):
    # TODO
    raise NotImplementedError("[ChainerConverter] BroadcastTo is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("Cast")
def _convert_cast(converter: ChainerConverter, c_op: chainer.functions.Cast):
    # TODO
    raise NotImplementedError("[ChainerConverter] Cast is not supported")


@ChainerConverter.register_handler("Concat")
def _convert_concat(converter: ChainerConverter, c_op: chainer.functions.Concat):
    xs = [converter.get_variable(x) for x in c_op.inputs]
    y, = Concat(None, axis=xs[0].order.axes[c_op.axis])(*xs)
    converter.set_variable(c_op.outputs[0](), y)


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("Copy")
def _convert_copy(converter: ChainerConverter, c_op: chainer.functions.Copy):
    # TODO
    raise NotImplementedError("[ChainerConverter] Copy is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("Depth2Space")
def _convert_depth2space(converter: ChainerConverter, c_op: chainer.functions.Depth2Space):
    # TODO
    raise NotImplementedError("[ChainerConverter] Depth2Space is not supported")


# noinspection PyUnusedLocal,PyUnresolvedReferences
@ChainerConverter.register_handler("Dstack")
def _convert_dstack(converter: ChainerConverter, c_op: chainer.functions.array.dstack.Dstack):
    # TODO
    raise NotImplementedError("[ChainerConverter] Dstack is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("ExpandDims")
def _convert_expand_dims(converter: ChainerConverter, c_op: chainer.functions.ExpandDims):
    # TODO
    raise NotImplementedError("[ChainerConverter] ExpandDims is not supported")


@ChainerConverter.register_handler("Flatten")
def _convert_flatten(converter: ChainerConverter, c_op: chainer.functions.Flatten):
    x = converter.get_variable(c_op.inputs[0])
    y, = Reshape(None, in_order=x.order, out_shape=[x.size], out_order=OrderC)
    converter.set_variable(c_op.outputs[0](), y)

    console.warning("[ChainerConverter] In chainer.functions.Flatten, output data order is parsed as OrderC. To "
                    "customize this, please overwrite chainer.functions.Flatten converter handler.")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("FlipLR")
def _convert_flip_lr(converter: ChainerConverter, c_op: chainer.functions.FlipLR):
    # TODO
    raise NotImplementedError("[ChainerConverter] FlipLR is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("FlipUD")
def _convert_flip_ud(converter: ChainerConverter, c_op: chainer.functions.FlipUD):
    # TODO
    raise NotImplementedError("[ChainerConverter] FlipUD is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("GetItem")
def _convert_get_item(converter: ChainerConverter, c_op: chainer.functions.GetItem):
    # TODO
    raise NotImplementedError("[ChainerConverter] GetItem is not supported")


# noinspection PyUnusedLocal,PyUnresolvedReferences
@ChainerConverter.register_handler("Hstack")
def _convert_hstack(converter: ChainerConverter, c_op: chainer.functions.array.hstack.Hstack):
    # TODO
    raise NotImplementedError("[ChainerConverter] Hstack is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("Im2Col")
def _convert_im2col(converter: ChainerConverter, c_op: chainer.functions.Im2Col):
    # TODO
    raise NotImplementedError("[ChainerConverter] Im2Col is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("Pad")
def _convert_pad(converter: ChainerConverter, c_op: chainer.functions.Pad):
    # TODO
    raise NotImplementedError("[ChainerConverter] Pad is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("PadSequence")
def _convert_pad_sequence(converter: ChainerConverter, c_op: chainer.functions.PadSequence):
    # TODO
    raise NotImplementedError("[ChainerConverter] PadSequence is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("Permutate")
def _convert_permutate(converter: ChainerConverter, c_op: chainer.functions.Permutate):
    # TODO
    raise NotImplementedError("[ChainerConverter] Permutate is not supported")


@ChainerConverter.register_handler("Reshape")
def _convert_reshape(converter: ChainerConverter, c_op: chainer.functions.Reshape):
    assert len(c_op.inputs) == 1, \
        f"For 'Reshape' operator in chainer, expected number of inputs is 1, but actual is {len(c_op.inputs)}"

    x = converter.get_variable(c_op.inputs[0])

    out_shape = list(c_op.shape)  # c_op.shape is tuple
    if len(out_shape) == 1:
        out_order = OrderC
    elif len(out_shape) == 2:
        out_order = OrderNC
    elif len(out_shape) == 4:
        out_order = OrderNCHW
    else:
        raise NotImplementedError("Reshaping into dimensions none of 1, 2, 4 is not supported.")
    assert mul(out_shape) == x.size

    y, = Reshape(None, in_order=x.order, out_order=out_order, out_shape=out_shape)(x)

    converter.set_variable(c_op.outputs[0](), y)


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("ResizeImages")
def _convert_resize_images(converter: ChainerConverter, c_op: chainer.functions.ResizeImages):
    # TODO
    raise NotImplementedError("[ChainerConverter] ResizeImages is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("Rollaxis")
def _convert_rollaxis(converter: ChainerConverter, c_op: chainer.functions.Rollaxis):
    # TODO
    raise NotImplementedError("[ChainerConverter] Rollaxis is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("SelectItem")
def _convert_selected_item(converter: ChainerConverter, c_op: chainer.functions.SelectItem):
    # TODO
    raise NotImplementedError("[ChainerConverter] SelectItem is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("Space2Depth")
def _convert_space2depth(converter: ChainerConverter, c_op: chainer.functions.Space2Depth):
    # TODO
    raise NotImplementedError("[ChainerConverter] Space2Depth is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("SpatialTransformerGrid")
def _convert_spatial_transformer_grid(converter: ChainerConverter, c_op: chainer.functions.SpatialTransformerGrid):
    # TODO
    raise NotImplementedError("[ChainerConverter] SpatialTransformerGrid is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("SpatialTransformerSampler")
def _convert_spatial_transformer_sampler(converter: ChainerConverter,
                                         c_op: chainer.functions.SpatialTransformerSampler):
    # TODO
    raise NotImplementedError("[ChainerConverter] SpatialTransformerSampler is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("SplitAxis")
def _convert_split_axis(converter: ChainerConverter, c_op: chainer.functions.SplitAxis):
    # TODO
    raise NotImplementedError("[ChainerConverter] SplitAxis is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("Squeeze")
def _convert_squeeze(converter: ChainerConverter, c_op: chainer.functions.Squeeze):
    # TODO
    raise NotImplementedError("[ChainerConverter] Squeeze is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("Swapaxes")
def _convert_swapaxes(converter: ChainerConverter, c_op: chainer.functions.Swapaxes):
    # TODO
    raise NotImplementedError("[ChainerConverter] Swapaxes is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("Tile")
def _convert_tile(converter: ChainerConverter, c_op: chainer.functions.Tile):
    # TODO
    raise NotImplementedError("[ChainerConverter] Tile is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("Transpose")
def _convert_transpose(converter: ChainerConverter, c_op: chainer.functions.Transpose):
    # TODO
    raise NotImplementedError("[ChainerConverter] Transpose is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("TransposeSequence")
def _convert_transpose_sequence(converter: ChainerConverter, c_op: chainer.functions.TransposeSequence):
    # TODO
    raise NotImplementedError("[ChainerConverter] TransposeSequence is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("Where")
def _convert_where(converter: ChainerConverter, c_op: chainer.functions.Where):
    # TODO
    raise NotImplementedError("[ChainerConverter] Where is not supported")
