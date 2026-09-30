from typing import Any, Type

from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty

from libs.uix.behaviors.recycle_dropdown import RecycleDropdownBehavior
from libs.uix.button import ArrowToggleButton, HoverButton
from libs.uix.restricted_scrollview import RestrictedScrollView

Builder.load_string("""
<SpinnerHoverButton>:  # HoverButton
    font_size: "13sp"


<RecycleSpinner>:  # ArrowToggleButton
    reverse_arrow: self.is_down
"""
)


class SpinnerHoverButton(HoverButton):
    pass

class RecycleSpinner(RecycleDropdownBehavior, ArrowToggleButton):
    host_attr: str = StringProperty("text")
    viewclass: Type[HoverButton] = ObjectProperty(SpinnerHoverButton)

    def on_press(self):
        self._open_dropdown()

    def _close_dropdown(self, *largs: Any):
        super()._close_dropdown(*largs)
        self.is_down = False

RestrictedScrollView.register_scrollable_widget_class(RecycleSpinner)
