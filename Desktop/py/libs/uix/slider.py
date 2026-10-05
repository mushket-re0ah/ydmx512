from typing import Literal, Tuple

from kivy.input.motionevent import MotionEvent
from kivy.lang import Builder
from kivy.properties import (
    AliasProperty,
    BooleanProperty,
    NumericProperty,
    OptionProperty,
    StringProperty,
)
from kivy.uix.widget import Widget

from libs.animation import AnimationBehavior, StatefulColorProperty
from libs.mouse_manager import cursor_manager
from libs.properties import ContextualNumericProperty
from libs.typecheck import RGBA, Number
from libs.uix import colorscheme as uix_cs
from libs.uix.behaviors.mouse import TouchMouseBehavior
from libs.uix.behaviors.tooltip import TooltipBehavior
from libs.uix.context_menu import ContextMenu, ContextMenuTemplates
from libs.uix.restricted_scrollview import RestrictedScrollView

Builder.load_string("""
#:import uix_cs libs.uix.colorscheme
#:import imgs_path misc.imgs_path

<HoverSlider>:
    orientation: "vertical"
    value_track_width: "1dp"
    background_image: imgs_path.hover_slider_bg_vertical\
                    if self.orientation == "vertical" else\
                    imgs_path.hover_slider_bg_horizontal
    cursor_width: "25dp" if self.orientation == "vertical" else "32dp"
    cursor_height: "32dp" if self.orientation == "vertical" else "25dp"
    cursor_image: imgs_path.hover_slider_cursor_image_vertical\
                    if self.orientation == "vertical" else\
                    imgs_path.hover_slider_cursor_image_horizontal
    value_track_color: uix_cs.HoverSlider.value_track_color_normal
    padding: "16dp"
    minimum: 0
    maximum: 255
    canvas:
        Color:
            rgba: self.background_color
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgb: (1, 1, 1)
        Rectangle:
            pos: self.track_pos
            size: self.track_size
            source: self.background_image
        Color:
            rgba: self.value_track_color
        SmoothLine:
            width: self.value_track_width
            points: self.track_start + self.track_end
    ImageButton:
        pos: (root.cursor_pos[0] - root.cursor_width / 2,\
            root.cursor_pos[1] - root.cursor_height / 2)
        size: (root.cursor_width, root.cursor_height)
        -background_normal: root.cursor_image
        on_hover: root.hover = self.hover
"""
)


class HoverSlider(TouchMouseBehavior, AnimationBehavior, TooltipBehavior, Widget):
    value_track_color: RGBA = StatefulColorProperty(
        normal=uix_cs.HoverSlider.value_track_color_normal,
        states={
            "focus": uix_cs.HoverSlider.value_track_color_focused,
            "disabled": uix_cs.HoverSlider.value_track_color_disabled,
            "hover": uix_cs.HoverSlider.value_track_color_hover,
        }
    )
    background_color: RGBA = StatefulColorProperty(
        normal=uix_cs.HoverSlider.background_color_normal,
        states={
            "focus": uix_cs.HoverSlider.background_color_focused,
            "disabled": uix_cs.HoverSlider.background_color_disabled,
            "hover": uix_cs.HoverSlider.background_color_hover,
        }
    )

    minimum: Number = NumericProperty(0)
    maximum: Number = NumericProperty(100)
    decimals: int = NumericProperty(0)
    value: Number = ContextualNumericProperty(
        default=0,
        min_getter=lambda self: self.minimum,
        max_getter=lambda self: self.maximum,
        decimals_getter=lambda self: self.decimals,
        dependencies=("minimum", "maximum", "decimals")
    )

    default_value: Number = NumericProperty(0)
    step_mouse_scroll: Number = NumericProperty(1)

    focus: bool = BooleanProperty(False)

    padding: float = NumericProperty("16sp")
    orientation: Literal["vertical", "horizontal"] = OptionProperty("horizontal",
                options=("vertical", "horizontal"))

    background_image: str = StringProperty()

    cursor_image: str = StringProperty()
    cursor_width: float = NumericProperty("32sp")
    cursor_height: float = NumericProperty("32sp")

    value_track_width: float = NumericProperty("3dp")

    drag_enabled: bool = BooleanProperty(True)

    def on_drag_start(self, touch: MotionEvent) -> bool:
        self.focus = True
        self._set_value_from_pos(*touch.pos)
        return True

    def on_drag(self, touch: MotionEvent, delta_x: float, delta_y: float) -> bool:
        # дельты не используем, берём абсолютную позицию касания
        self._set_value_from_pos(*touch.pos)
        return True

    def on_drag_end(self, touch: MotionEvent) -> bool:
        self.focus = False
        return True

    def on_scroll_up(self, touch: MotionEvent) -> bool:
        self.value -= self.step_mouse_scroll
        return True

    def on_scroll_down(self, touch: MotionEvent) -> bool:
        self.value += self.step_mouse_scroll
        return True

    def on_right_click(self, touch: MotionEvent) -> bool:
        self.open_context_menu(touch.pos)
        return True

    def _axis_bounds(self) -> Tuple[float, float]:
        """Границы хода курсора по главной оси (start, end)."""
        p = self.padding
        if self.orientation == "horizontal":
            return (self.x + p, self.right - p)
        return (self.y + p, self.top - p)

    def _cross_center(self) -> float:
        """Центр по поперечной оси."""
        return self.center_y if self.orientation == "horizontal" else self.center_x

    def _set_value_from_pos(self, x: float, y: float):
        a, b = self._axis_bounds()
        pos = x if self.orientation == "horizontal" else y
        if b - a <= 0:
            self.value = self.minimum
            return
        normalized = min(1.0, max(0.0, (pos - a) / (b - a)))
        self.value = self.minimum + normalized * (self.maximum - self.minimum)

    def _get_value_pos(self) -> Tuple[float, float]:
        a, b = self._axis_bounds()
        nval = (self.value - self.minimum) / max(self.maximum - self.minimum, 1)
        along = a + nval * (b - a)
        cross = self._cross_center()
        if self.orientation == "horizontal":
            return (along, cross)
        return (cross, along)

    value_pos: Tuple[float, float] = AliasProperty(
        _get_value_pos,
        bind=("pos", "size", "minimum", "maximum", "padding", "value", "orientation"),
        cache=True
    )

    def _get_track_pos(self) -> Tuple[float, float]:
        p = self.padding
        if self.orientation == "horizontal":
            return (self.x + p, self.y)
        return (self.x, self.y + p)

    track_pos: Tuple[float, float] = AliasProperty(
        _get_track_pos,
        bind=("pos", "padding", "orientation"),
        cache=True
    )

    def _get_track_size(self) -> Tuple[float, float]:
        p = self.padding
        if self.orientation == "horizontal":
            return (self.width - p * 2, self.height)
        return (self.width, self.height - p * 2)

    track_size: Tuple[float, float] = AliasProperty(
        _get_track_size,
        bind=("size", "padding", "orientation"),
        cache=True
    )

    def _get_track_start(self) -> Tuple[float, float]:
        p = self.padding
        if self.orientation == "horizontal":
            return (self.x + p, self.center_y)
        return (self.center_x, self.y + p)

    track_start: Tuple[float, float] = AliasProperty(
        _get_track_start,
        bind=("pos", "size", "padding", "orientation"),
        cache=True
    )

    track_end: Tuple[float, float] = AliasProperty(
        lambda self: self.cursor_pos,
        bind=("cursor_pos",),
        cache=True
    )

    def _get_cursor_pos(self) -> Tuple[float, float]:
        vx, vy = self.value_pos
        if self.orientation == "horizontal":
            return (vx, self.center_y)
        return (self.center_x, vy)

    cursor_pos: Tuple[float, float] = AliasProperty(
        _get_cursor_pos,
        bind=("value_pos", "pos", "size", "orientation"),
        cache=True
    )

    def open_context_menu(self, pos: Tuple[float, float]):
        if self.disabled:
            return
        self._create_context_menu().open(self, pos=pos)

    def _create_context_menu(self) -> ContextMenu:
        return ContextMenu(items=[
            ContextMenuTemplates.button(
                text="Установить по-умолчанию",
                on_release=lambda _: setattr(self, "value", self.default_value),
            ),
            ContextMenuTemplates.button(
                text="Установить минимум",
                on_release=lambda _: setattr(self, "value", self.minimum),
            ),
            ContextMenuTemplates.button(
                text="Установить максимум",
                on_release=lambda _: setattr(self, "value", self.maximum),
            ),
        ])

    def on_mouse_move(self, _):
        if self.hover and not self.disabled:
            cursor_manager.set_cursor("hand")


RestrictedScrollView.register_scrollable_widget_class(HoverSlider)
