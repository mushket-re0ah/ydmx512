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

<HoverSlider>:
    orientation: "vertical"
    value_track_width: "1dp"
    background_image: "./data/imgs/fader_scale.png"
    cursor_width: "25dp"
    cursor_height: "32dp"
    cursor_image: "./data/imgs/fader_cursor.png"
    value_track_color: uix_cs.HoverSlider.value_track_color_normal
    padding: 16
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
            pos: (\
                        self.x + self.padding,\
                        self.center_y - self.background_width / 2.0\
                    )\
                    if self.orientation == 'horizontal' else\
                    (\
                        self.center_x - self.background_width / 2.0,\
                        self.y + self.padding\
                    )
            size: (\
                        self.width - self.padding * 2,\
                        self.height\
                    )\
                    if self.orientation == 'horizontal' else\
                    (\
                        self.background_width,\
                        self.height - self.padding * 2\
                    )
            source: self.background_image
        Color:
            rgba: root.value_track_color
        Line:
            width: self.value_track_width
            points: (\
                        self.x + self.padding, self.center_y,\
                        self.value_pos[0], self.center_y\
                    )\
                    if self.orientation == 'horizontal' else\
                    (\
                        self.center_x, self.y + self.padding,\
                        self.center_x, self.value_pos[1]\
                    )
    ImageButton:
        pos: (\
                root.value_pos[0] - root.cursor_width / 2,\
                root.center_y - root.cursor_height / 2\
            )\
            if root.orientation == 'horizontal' else\
            (\
                root.center_x - root.cursor_width / 2,\
                root.value_pos[1] - root.cursor_height / 2\
            )
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
    background_width: float = NumericProperty("36sp")

    cursor_image: str = StringProperty()
    cursor_width: float = NumericProperty("32sp")
    cursor_height: float = NumericProperty("32sp")

    value_track_width: float = NumericProperty("3dp")

    drag_enabled: bool = BooleanProperty(True)

    def on_kv_post(self, base_widget: Widget):
        self.default_value = self.value

    def on_drag_start(self, touch: MotionEvent) -> bool:
        self.focus = True
        self._set_value_from_pos(*touch.pos)
        return True

    def on_drag(self, touch: MotionEvent, delta_x: float, delta_y: float) -> bool:
        # дельты не используем, берём абсолютную позицию касания
        self._set_value_from_pos(*touch.pos)
        return False

    def on_drag_end(self, touch: MotionEvent) -> bool:
        self.focus = False
        return False

    def _set_value_from_pos(self, x: float, y: float):
        padding = self.padding
        if self.orientation == 'horizontal':
            x = min(self.right - padding, max(x, self.x + padding))
            if self.width - 2 * padding > 0:
                normalized = (x - self.x - padding) / (self.width - 2 * padding)
            else:
                normalized = 0
        else:
            y = min(self.top - padding, max(y, self.y + padding))
            if self.height - 2 * padding > 0:
                normalized = (y - self.y - padding) / (self.height - 2 * padding)
            else:
                normalized = 0
        self.value = self.minimum + normalized * (self.maximum - self.minimum)

    def on_scroll_up(self, touch: MotionEvent) -> bool:
        self.value -= self.step_mouse_scroll
        return True

    def on_scroll_down(self, touch: MotionEvent) -> bool:
        self.value += self.step_mouse_scroll
        return True

    def on_right_click(self, touch: MotionEvent) -> bool:
        self.open_context_menu(touch.pos)
        return True

    def get_value_pos(self) -> Tuple[float, float]:
        """позиция курсора (только для визуального отображения)"""
        nval = (self.value - self.minimum) / max(self.maximum - self.minimum, 1)
        if self.orientation == 'horizontal':
            x = self.x + self.padding + nval * (self.width - 2 * self.padding)
            return (x, self.y + self.height / 2)
        y = self.y + self.padding + nval * (self.height - 2 * self.padding)
        return (self.x + self.width / 2, y)

    value_pos: Tuple[float, float] = AliasProperty(
        get_value_pos,
        bind=('pos', 'size', 'minimum', 'maximum', 'padding', 'value', 'orientation'),
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
