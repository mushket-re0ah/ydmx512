from kivy.properties import NumericProperty, BooleanProperty, ColorProperty, AliasProperty
from libs.animation import AnimationBehavior
from libs.uix.behaviors.tooltip import TooltipBehavior
from kivy.clock import Clock
from kivy.utils import boundary
from kivy.uix.widget import Widget
from kivy.lang import Builder
from libs.mouse_manager import cursor_manager
from misc import colorscheme as cs
from libs.animation import StatefulColorProperty
from libs.uix.behaviors.mouse import TouchMouseBehavior
from libs.properties import ContextualNumericProperty


Builder.load_file("ui/components/slider2d.kv")


class Slider2D(TouchMouseBehavior, TooltipBehavior, AnimationBehavior, Widget):
    dot_color = StatefulColorProperty(
        normal=cs.Slider2D.dot_color_normal,
        states={
            "disabled": cs.Slider2D.dot_color_disabled,
            "focus": cs.Slider2D.dot_color_focused,
            "hover": cs.Slider2D.dot_color_hover,
        }
    )
    line_color = StatefulColorProperty(
        normal=cs.Slider2D.line_color_normal,
        states={
            "disabled": cs.Slider2D.line_color_disabled,
            "focus": cs.Slider2D.line_color_focused,
            "hover": cs.Slider2D.line_color_hover,
        }
    )

    focus = BooleanProperty(False)

    value_x_minimum = NumericProperty(0)
    value_x_maximum = NumericProperty(255)
    value_x = ContextualNumericProperty(
        default=0,
        min_getter=lambda self: self.value_x_minimum,
        max_getter=lambda self: self.value_x_maximum,
        dependencies=("value_x_minimum", "value_x_maximum")
    )

    value_y_minimum = NumericProperty(0)
    value_y_maximum = NumericProperty(255)
    value_y = ContextualNumericProperty(
        default=0,
        min_getter=lambda self: self.value_y_minimum,
        max_getter=lambda self: self.value_y_maximum,
        dependencies=("value_y_minimum", "value_y_maximum")
    )

    padding = NumericProperty(0)

    dot_radius = NumericProperty("10dp")

    def on_mouse_move(self, _):
        if self.hover and not self.disabled:
            cursor_manager.set_cursor("crosshair")

    drag_enabled = BooleanProperty(True)

    def on_drag_start(self, touch):
        self.focus = True
        self._set_from_touch(touch)

    def on_drag(self, touch, delta_x, delta_y):
        self._set_from_touch(touch)

    def on_drag_end(self, touch):
        self.focus = False

    def _set_from_touch(self, touch):
        minmax_x = max(self.value_x_maximum - self.value_x_minimum, 1)
        px_to_val_x = (self.width - 2 * self.padding) / minmax_x
        xdiff = (touch.x - (self.x + self.padding)) - self.dot_radius / 4
        self.value_x = self.value_x_minimum + xdiff / px_to_val_x

        minmax_y = max(self.value_y_maximum - self.value_y_minimum, 1)
        px_to_val_y = (self.height - 2 * self.padding) / minmax_y
        ydiff = (touch.y - (self.y + self.padding)) - self.dot_radius / 4
        self.value_y = self.value_y_minimum + ydiff / px_to_val_y

    def _get_dot_x(self):
        diff = max(self.value_x_maximum - self.value_x_minimum, 1)
        xdiff = (self.value_x - self.value_x_minimum) / diff
        return (self.x + self.padding) + (self.width - 2 * self.padding) * xdiff - self.dot_radius / 2
    dot_x = AliasProperty(_get_dot_x,
                          bind=['pos', 'size', 'padding', 'dot_radius',
                                'value_x', 'value_x_minimum', 'value_x_maximum'],
                          cache=True)

    def _get_dot_y(self):
        diff = max(self.value_y_maximum - self.value_y_minimum, 1)
        ydiff = (self.value_y - self.value_y_minimum) / diff
        return (self.y + self.padding) + (self.height - 2 * self.padding) * ydiff - self.dot_radius / 2
    dot_y = AliasProperty(_get_dot_y,
                          bind=['pos', 'size', 'padding', 'dot_radius',
                                'value_y', 'value_y_minimum', 'value_y_maximum'],
                          cache=True)
