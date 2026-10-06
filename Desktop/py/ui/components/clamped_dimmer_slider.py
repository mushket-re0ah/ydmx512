from typing import Tuple

from kivy.lang import Builder
from kivy.properties import AliasProperty

from libs.properties import ClampedNumericProperty, ContextualNumericProperty
from libs.uix.slider import HoverSlider

Builder.load_string(
"""
<ClampedDimmerSlider>:  # HoverSlider
    canvas.after:
        Color:
            rgba: cs.ClampedDimmerSlider.global_dimmer_mask
        Rectangle:
            pos: self.dimmer_mask_pos
            size: self.dimmer_mask_size
"""
)


class ClampedDimmerSlider(HoverSlider):
    visual_maximum: int = ClampedNumericProperty(255, 0, 255)

    value: int = ContextualNumericProperty(
        default=0,
        min_getter=lambda self: self.minimum,
        max_getter=lambda self: min(self.maximum, self.visual_maximum),
        decimals_getter=lambda self: self.decimals,
        dependencies=("minimum", "maximum", "visual_maximum", "decimals")
    )

    def _get_dimmer_mask_pos(self) -> Tuple[float, float]:
        if self.orientation == "vertical":
            return (self.x, self.y + self.height * self.visual_maximum / 255)
        else:
            return (self.x + self.width * self.visual_maximum / 255, self.y)

    dimmer_mask_pos: Tuple[float, float] = AliasProperty(
        _get_dimmer_mask_pos,
        bind=("visual_maximum", "pos", "size", "orientation"),
        cache=True
    )

    def _get_dimmer_mask_size(self) -> Tuple[float, float]:
        if self.orientation == "vertical":
            return (self.width, self.height - self.height * self.visual_maximum / 255)
        else:
            return (self.width - self.width * self.visual_maximum / 255, self.height)

    dimmer_mask_size: Tuple[float, float] = AliasProperty(
        _get_dimmer_mask_size,
        bind=("visual_maximum", "pos", "size", "orientation"),
        cache=True
    )
