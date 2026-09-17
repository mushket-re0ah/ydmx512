from kivy.clock import Clock
from kivy.properties import ObjectProperty, NumericProperty
from kivy.core.window import Window
from kivy.animation import Animation
from typing import Optional
from libs.sdl2_keyboard import KeyboardBehavior
from libs.kivy_utils import AutoUnbindBehavior


class ModalBehavior(AutoUnbindBehavior, KeyboardBehavior):
    attach_to = ObjectProperty(None, allownone=True)
    opacity_animation_duration = NumericProperty(0.2)
    dismiss_on_attach_click = True
    pos_fix = None
    is_blocked_keyboard = True

    __events__ = ("on_open", "on_dismiss")

    def __init__(self, **kwargs):
        self._trigger_reposition = Clock.create_trigger(self._reposition, -1)
        self.bind(size=self._trigger_reposition, pos=self._trigger_reposition)
        super().__init__(**kwargs)

    def create_hotkeys(self) -> Optional[dict]:
        return {
            frozenset({"esc"}): self.dismiss,
        }

    def open(self, widget=None, pos=None):
        self.register_keyboard_context()
        if self.attach_to:
            self.dismiss()
        if pos and widget:
            pos = widget.to_window(*pos)
        self.pos_fix = pos
        self.attach_to = widget
        self.bind_to(Window, size=self._trigger_reposition)
        Window.add_widget(self)
        if widget:
            self.bind_to(widget,
                         pos=self._trigger_reposition,
                         size=self._trigger_reposition)
        self._trigger_reposition()
        self.opacity = 0.0
        anim = Animation(opacity=1.0, duration=self.opacity_animation_duration)
        anim.start(self)
        self.dispatch("on_open")

    def dismiss(self):
        if self.parent:
            self.parent.remove_widget(self)
        self.unbind_from(self.attach_to)
        self.attach_to = None
        self.dispatch("on_dismiss")
        self.unregister_keyboard_context()

    def on_open(self):
        pass

    def on_dismiss(self):
        pass

    def _clamp_to_window(self, x, y):
        win = Window
        x = max(0, min(x, win.width - self.width))
        y = max(0, min(y, win.height - self.height))
        return x, y

    def _reposition(self, *largs):
        win = Window
        if self.pos_fix is not None:
            wx, wy = self.pos_fix
            wy -= self.height
            self.pos = self._clamp_to_window(wx, wy)
            return

        widget = self.attach_to
        if not widget or not widget.get_parent_window():
            return

        wx, wy = widget.to_window(*widget.pos)
        self.pos = self._clamp_to_window(wx, wy)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            super().on_touch_down(touch)
            return True
        if (self.attach_to
                and self.attach_to.collide_point(*touch.pos)
                and not self.dismiss_on_attach_click):
            return False
        self.dismiss()
        return True
