from typing import Callable

from webdnn.backend.code_generator.injector import Injector, Tag
from webdnn.backend.webgpu.attributes.inline_inject import PostInlineInplace
from webdnn.graph import traverse
from webdnn.graph.operator import Operator

_noop = lambda exp: exp


class InlineInjector(Injector):
    def __init__(self, op: Operator):
        self.delegate = lambda exp: exp  # type: Callable[[str], str]
        self.has_inline = traverse.check_attribute_match(op, PostInlineInplace)

        if self.has_inline:
            post_inline_inplace = op.get_attribute(PostInlineInplace)[0]  # type: PostInlineInplace
            if post_inline_inplace.injected is not None:
                self.delegate = post_inline_inplace.injected.injector

    def inject_tag(self, tag: Tag):
        if tag.name == "INLINE":
            return self.delegate(tag.args[0])

        else:
            return tag.original
