from typing import Type

from kivy.clock import Clock
from kivy.input.motionevent import MotionEvent
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.behaviors import FocusBehavior

from libs.uix.behaviors.recycle_dropdown import RecycleDropdownBehavior
from libs.uix.button import HoverButton
from libs.uix.input import HoverInput
from libs.uix.recycle_dropdown import RecycleDropdown
from libs.uix.recycle_spinner import SpinnerHoverButton


class SnippetDropdown(RecycleDropdown):
    is_blocked_keyboard: bool = False
    allow_hover_outside: bool = True
    dismiss_on_attach_click: bool = False

    def on_touch_down(self, touch: MotionEvent) -> bool:
        if self.collide_point(*touch.pos):
            FocusBehavior.ignored_touch.append(touch)
        return super().on_touch_down(touch)


class Snippet(RecycleDropdownBehavior, HoverInput):
    host_attr: str = StringProperty("text")
    viewclass: Type[HoverButton] = ObjectProperty(SpinnerHoverButton)
    dropdown_cls: Type[RecycleDropdown] = ObjectProperty(SnippetDropdown)

    def on_focus(self, _, focus: bool):
        super().on_focus(_, focus)
        if focus:
            self._open_dropdown()
        elif self.opened:
            # Клик по элементу dropdown уводит фокус с Input,
            # и ранний dismiss ломает grab-фазу в post_dispatch_input
            # (кнопка вылетает из дерева до того, как Kivy применит
            # к touch её transform). Откладываем закрытие на кадр.
            Clock.schedule_once(self._close_dropdown_if_unfocused, 0)

    def _close_dropdown_if_unfocused(self, dt: float):
        if self.opened and not self.focus:
            self.opened = False

    def on_text(self, _, text: str):
        self._update_filtered_values()
