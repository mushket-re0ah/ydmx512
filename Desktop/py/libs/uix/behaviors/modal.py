from typing import Any, Callable, Dict, FrozenSet, Optional, Tuple

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.input.motionevent import MotionEvent
from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.widget import Widget

from libs.kivy_mixins import AutoUnbindBehavior
from libs.sdl2_keyboard import KeyboardBehavior


class ModalBehavior(AutoUnbindBehavior, KeyboardBehavior):
    attach_to: Optional[Widget] = ObjectProperty(None, allownone=True)
    opacity_animation_duration: float = NumericProperty(0.2)
    dismiss_on_attach_click: bool = True
    pos_fix: Optional[Tuple[float, float]] = None
    is_blocked_keyboard: bool = True

    __events__ = ("on_open", "on_dismiss")
    def __init__(self, **kwargs: Any):
        self._trigger_reposition = Clock.create_trigger(self._reposition, -1)
        self.bind(size=self._trigger_reposition, pos=self._trigger_reposition)
        super().__init__(**kwargs)

    def create_hotkeys(self) -> Dict[FrozenSet[str], Callable[[], None]]:
        return {
            frozenset({"esc"}): self.dismiss,
        }

    def open(self, widget: Optional[Widget]=None, pos:Optional[Tuple[float, float]]=None):
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

    def _clamp_to_window(self, x: float, y: float) -> Tuple[float, float]:
        win = Window
        x = max(0, min(x, win.width - self.width))
        y = max(0, min(y, win.height - self.height))
        return (x, y)

    def _reposition(self, *_:Any):
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

    def on_touch_down(self, touch: MotionEvent) -> bool:
        if self.collide_point(*touch.pos):
            super().on_touch_down(touch)
            return True
        if (self.attach_to
                and self.attach_to.collide_point(*touch.pos)
                and not self.dismiss_on_attach_click):
            return False
        self.dismiss()
        return True
