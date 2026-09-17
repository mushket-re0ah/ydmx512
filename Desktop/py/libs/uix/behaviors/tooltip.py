from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import StringProperty
from kivy.lang import Builder
from kivy.animation import Animation
from libs.uix.label import RestrictedLabel
from libs.mouse_manager.hover import HoverBehavior


Builder.load_string("""
<TooltipLabel>:  # RestrictedLabel
    padding: ["5dp"]
    font_size: "14sp"
    text_size: self.width, None
    size_hint: (None, None)
    size_hint_y: None
    size: ["125dp", self.texture_size[1]]
    halign: "center"
    valign: "middle"
    canvas.before:
        Color:
            rgba: (0.4, 0.4, 0.4, 1)
        Rectangle:
            pos: self.pos
            size: self.size
"""
)


class TooltipLabel(RestrictedLabel):
    window_hover_ignore = True


class TooltipBehavior(HoverBehavior):
    tooltip_text = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tooltip = None
        self._scheduled_show = None

    def on_enter(self):
        if self.tooltip_text:
            self._scheduled_show = Clock.schedule_once(self._show_tooltip, 0.5)

    def on_leave(self):
        if self._scheduled_show:
            self._scheduled_show.cancel()
            self._scheduled_show = None

        if self._tooltip:
            self._hide_tooltip()

    def _show_tooltip(self, *_):
        self._tooltip = TooltipLabel(text=self.tooltip_text,
                                     pos=Window.mouse_pos)
        Window.add_widget(self._tooltip)

        anim = Animation(opacity=1, duration=0.2)
        anim.start(self._tooltip)

    def _hide_tooltip(self):
        anim = Animation(opacity=0, duration=0.2)
        anim.bind(on_complete=self._remove_tooltip)
        anim.start(self._tooltip)

    def _remove_tooltip(self, *_):
        if self._tooltip:
            Window.remove_widget(self._tooltip)
            self._tooltip = None
