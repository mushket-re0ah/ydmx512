from ui.components.input import HoverInput
from libs.uix.behaviors.recycle_dropdown import RecycleDropdownBehavior
from kivy.properties import (
    ObjectProperty, StringProperty, BooleanProperty, NumericProperty
)
from libs.uix.recycle_spinner import SpinnerHoverButton
from libs.uix.recycle_dropdown import RecycleDropdown
from kivy.uix.widget import Widget
from libs.uix.behaviors.modal import ModalBehavior
from kivy.uix.behaviors import FocusBehavior
from kivy.clock import Clock


class SnippetDropdown(RecycleDropdown):
    is_blocked_keyboard = False
    allow_hover_outside = True
    dismiss_on_attach_click = False

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            FocusBehavior.ignored_touch.append(touch)
        return super().on_touch_down(touch)


class Snippet(RecycleDropdownBehavior, HoverInput):
    host_attr = StringProperty("text")
    viewclass = ObjectProperty(SpinnerHoverButton)
    dropdown_cls = ObjectProperty(SnippetDropdown)

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

    def _close_dropdown_if_unfocused(self, _dt):
        if self.opened and not self.focus:
            self.opened = False

    def on_text(self, _, text: str):
        self._update_filtered_values()
