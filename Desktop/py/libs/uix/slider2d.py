from kivy.input.motionevent import MotionEvent
from kivy.lang import Builder
from kivy.properties import AliasProperty, BooleanProperty, NumericProperty
from kivy.uix.widget import Widget

from libs.animation import AnimationBehavior, StatefulColorProperty
from libs.mouse_manager import cursor_manager
from libs.properties import ContextualNumericProperty
from libs.typecheck import RGBA, Number
from libs.uix import colorscheme as uix_cs
from libs.uix.behaviors.mouse import TouchMouseBehavior
from libs.uix.behaviors.tooltip import TooltipBehavior

Builder.load_string("""
<Slider2D>:
    padding: 6
    size_hint: (1, 1)
    canvas:
        Color:
            rgba: (1, 1, 1, 1)
        Rectangle:
            size: self.size
            pos: self.pos
            source: imgs_path.slider_2d_bg
        Color:
            rgba: self.dot_color
        SmoothEllipse:
            pos: (self.dot_x, self.dot_y)
            size: (self.dot_radius, self.dot_radius)
        Color:
            rgba: self.line_color
        Line:
            width: dp(1)
            rectangle: (\
                self.x + self.padding,\
                self.y + self.padding,\
                self.width - self.padding * 2,\
                self.height - self.padding * 2\
            )
        Line:
            width: dp(1)
            points: [\
                self.x + self.padding, self.dot_y + self.dot_radius / 2,\
                self.dot_x + self.dot_radius / 2, self.dot_y + self.dot_radius / 2,\
                self.dot_x + self.dot_radius / 2, self.y + self.padding\
            ]
"""
)


class Slider2D(TouchMouseBehavior, TooltipBehavior, AnimationBehavior, Widget):
    dot_color: RGBA = StatefulColorProperty(
        normal=uix_cs.Slider2D.dot_color_normal,
        states={
            "disabled": uix_cs.Slider2D.dot_color_disabled,
            "focus": uix_cs.Slider2D.dot_color_focused,
            "hover": uix_cs.Slider2D.dot_color_hover,
        }
    )
    line_color: RGBA = StatefulColorProperty(
        normal=uix_cs.Slider2D.line_color_normal,
        states={
            "disabled": uix_cs.Slider2D.line_color_disabled,
            "focus": uix_cs.Slider2D.line_color_focused,
            "hover": uix_cs.Slider2D.line_color_hover,
        }
    )

    focus: bool = BooleanProperty(False)

    value_x_minimum: Number = NumericProperty(0)
    value_x_maximum: Number = NumericProperty(255)
    value_x: Number = ContextualNumericProperty(
        default=0,
        min_getter=lambda self: self.value_x_minimum,
        max_getter=lambda self: self.value_x_maximum,
        dependencies=("value_x_minimum", "value_x_maximum")
    )

    value_y_minimum: Number = NumericProperty(0)
    value_y_maximum: Number = NumericProperty(255)
    value_y: Number = ContextualNumericProperty(
        default=0,
        min_getter=lambda self: self.value_y_minimum,
        max_getter=lambda self: self.value_y_maximum,
        dependencies=("value_y_minimum", "value_y_maximum")
    )

    padding: float = NumericProperty(0)

    dot_radius: float = NumericProperty("10dp")

    def on_mouse_move(self, _):
        if self.hover and not self.disabled:
            cursor_manager.set_cursor("crosshair")

    drag_enabled: bool = BooleanProperty(True)

    def on_drag_start(self, touch: MotionEvent) -> bool:
        self.focus = True
        self._set_from_touch(touch)
        return True

    def on_drag(self, touch: MotionEvent, delta_x: float, delta_y: float) -> bool:
        self._set_from_touch(touch)
        return True

    def on_drag_end(self, touch: MotionEvent) -> bool:
        self.focus = False
        return True

    def _set_from_touch(self, touch: MotionEvent):
        minmax_x = max(self.value_x_maximum - self.value_x_minimum, 1)
        px_to_val_x = (self.width - 2 * self.padding) / minmax_x
        xdiff = (touch.x - (self.x + self.padding)) - self.dot_radius / 4
        self.value_x = self.value_x_minimum + xdiff / px_to_val_x

        minmax_y = max(self.value_y_maximum - self.value_y_minimum, 1)
        px_to_val_y = (self.height - 2 * self.padding) / minmax_y
        ydiff = (touch.y - (self.y + self.padding)) - self.dot_radius / 4
        self.value_y = self.value_y_minimum + ydiff / px_to_val_y

    def _get_dot_x(self) -> float:
        diff = max(self.value_x_maximum - self.value_x_minimum, 1)
        xdiff = (self.value_x - self.value_x_minimum) / diff
        x = self.x + self.padding
        width = self.width - (2 * self.padding)
        return x + width * xdiff - self.dot_radius / 2
    dot_x: float = AliasProperty(
        _get_dot_x,
        bind=(
            "pos", "size", "padding", "dot_radius", "value_x", "value_x_minimum",
            "value_x_maximum"
        ),
        cache=True
    )

    def _get_dot_y(self) -> float:
        diff = max(self.value_y_maximum - self.value_y_minimum, 1)
        ydiff = (self.value_y - self.value_y_minimum) / diff
        y = self.y + self.padding
        height = self.height - (2 * self.padding)
        return y + height * ydiff - self.dot_radius / 2
    dot_y: float = AliasProperty(
        _get_dot_y,
        bind=(
            "pos", "size", "padding", "dot_radius", "value_y", "value_y_minimum",
            "value_y_maximum"
        ),
        cache=True
    )
