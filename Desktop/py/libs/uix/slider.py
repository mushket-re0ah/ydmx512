from kivy.properties import (NumericProperty, BooleanProperty, OptionProperty,
                             ColorProperty, StringProperty, AliasProperty)
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from libs.animation import AnimationBehavior
from libs.uix.behaviors.tooltip import TooltipBehavior
from typing import Union
from ui.components.context_menu import (
    ContextMenu, ContextMenuTemplates
)
from kivy.utils import boundary
from libs.mouse_manager import cursor_manager
from libs.animation import StatefulColorProperty
from libs.properties import ContextualNumericProperty
from libs.uix.behaviors.mouse import TouchMouseBehavior
from libs.uix.restricted_scrollview import RestrictedScrollView
from libs.uix import colorscheme as cs
from kivy.lang import Builder


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
            pos: (self.x + self.padding, self.center_y - self.background_width / 2) if self.orientation == 'horizontal' else (self.center_x - self.background_width / 2, self.y + self.padding)
            size: (self.width - self.padding * 2, self.background_width) if self.orientation == 'horizontal' else (self.background_width, self.height - self.padding * 2)
            source: self.background_image
        Color:
            rgba: root.value_track_color
        Line:
            width: self.value_track_width
            points: (self.x + self.padding, self.center_y, self.value_pos[0], self.center_y) if self.orientation == 'horizontal' else (self.center_x, self.y + self.padding, self.center_x, self.value_pos[1])
    ImageButton:
        pos: (root.value_pos[0] - root.cursor_width / 2, root.center_y - root.cursor_height / 2) if root.orientation == 'horizontal' else (root.center_x - root.cursor_width / 2, root.value_pos[1] - root.cursor_height / 2)
        size: (root.cursor_width, root.cursor_height)
        -background_normal: root.cursor_image
        on_hover: root.hover = self.hover


<TitleNumericHoverSlider>:  # BoxLayout
    numeric: numeric
    slider: slider

    size_hint: (None, None)
    orientation: "vertical"
    RestrictedLabel:
        size_hint: (1, None)
        height: "20dp"
        text: root.index
        font_size: "12sp"
        canvas.before:
            Color:
                rgba: uix_cs.TitleNumericSlider.title_bg
            Rectangle:
                pos: self.pos
                size: self.size
    HoverSlider:
        id: slider
        size_hint: (1, 1)
        minimum: root.minimum
        maximum: root.maximum
        value: root.value
        on_value: root.value = self.value
        on_hover: numeric.hover = self.hover
        on_focus: numeric.visible_focus = self.focus
    NumericInput:
        size_hint: (1, None)
        id: numeric
        minimum: root.minimum
        maximum: root.maximum
        value: root.value
        on_value: root.value = self.value
        on_hover: slider.hover = self.hover
        on_visible_focus: slider.focus = self.visible_focus
"""
)


class HoverSlider(TouchMouseBehavior, AnimationBehavior, TooltipBehavior, Widget):
    value_track_color = StatefulColorProperty(
        normal=cs.HoverSlider.value_track_color_normal,
        states={
            "focus": cs.HoverSlider.value_track_color_focused,
            "disabled": cs.HoverSlider.value_track_color_disabled,
            "hover": cs.HoverSlider.value_track_color_hover,
        }
    )
    background_color = StatefulColorProperty(
        normal=cs.HoverSlider.background_color_normal,
        states={
            "focus": cs.HoverSlider.background_color_focused,
            "disabled": cs.HoverSlider.background_color_disabled,
            "hover": cs.HoverSlider.background_color_hover,
        }
    )

    minimum = NumericProperty(0)
    maximum = NumericProperty(100)
    decimals = NumericProperty(0)
    value = ContextualNumericProperty(
        default=0,
        min_getter=lambda self: self.minimum,
        max_getter=lambda self: self.maximum,
        decimals_getter=lambda self: self.decimals,
        dependencies=("minimum", "maximum", "decimals")
    )

    default_value = NumericProperty(0)
    step_mouse_scroll = NumericProperty(1)

    focus = BooleanProperty(False)

    padding = NumericProperty("16sp")
    orientation = OptionProperty("horizontal", options=(
        "vertical", "horizontal"))

    background_image = StringProperty()
    background_width = NumericProperty("36sp")

    cursor_image = StringProperty()
    cursor_width = NumericProperty("32sp")
    cursor_height = NumericProperty("32sp")

    value_track_width = NumericProperty("3dp")

    drag_enabled = BooleanProperty(True)

    def on_kv_post(self, _):
        self.default_value = self.value

    def on_drag_start(self, touch):
        self.focus = True
        self._set_value_from_pos(*touch.pos)
        return True

    def on_drag(self, touch, delta_x, delta_y):
        # дельты не используем, берём абсолютную позицию касания
        self._set_value_from_pos(*touch.pos)

    def on_drag_end(self, touch):
        self.focus = False

    def _set_value_from_pos(self, x, y):
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

    def on_scroll_up(self, touch):
        self.value -= self.step_mouse_scroll
        return True

    def on_scroll_down(self, touch):
        self.value += self.step_mouse_scroll
        return True

    def on_right_click(self, touch):
        self.open_context_menu(touch.pos)
        return True

    # --- позиция курсора (только для визуального отображения) ---
    def get_value_pos(self):
        nval = (self.value - self.minimum) / max(self.maximum - self.minimum, 1)
        if self.orientation == 'horizontal':
            x = self.x + self.padding + nval * (self.width - 2 * self.padding)
            return (x, self.y + self.height / 2)
        else:
            y = self.y + self.padding + nval * (self.height - 2 * self.padding)
            return (self.x + self.width / 2, y)

    value_pos = AliasProperty(get_value_pos,
                              bind=['pos', 'size', 'minimum', 'maximum',
                                    'padding', 'value', 'orientation'],
                              cache=True)

    def open_context_menu(self, pos):
        if self.disabled:
            return
        self._create_context_menu().open(self, pos=pos)

    def _create_context_menu(self):
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


class TitleNumericHoverSlider(BoxLayout):
    index = StringProperty()
    minimum = NumericProperty(0)
    maximum = NumericProperty(100)
    value = NumericProperty()

RestrictedScrollView.register_scrollable_widget_class(HoverSlider)
