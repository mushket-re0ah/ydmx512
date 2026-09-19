from libs.uix.button import ArrowToggleButton, HoverButton
from libs.uix.behaviors.recycle_dropdown import RecycleDropdownBehavior
from libs.uix.restricted_scrollview import RestrictedScrollView
from kivy.properties import ObjectProperty, StringProperty
from kivy.lang import Builder

Builder.load_file("ui/components/recycle_spinner.kv")


class SpinnerHoverButton(HoverButton):
    pass

class RecycleSpinner(RecycleDropdownBehavior, ArrowToggleButton):
    host_attr = StringProperty("text")
    viewclass = ObjectProperty(SpinnerHoverButton)

    def on_press(self):
        self._open_dropdown()

    def _close_dropdown(self, *largs):
        super()._close_dropdown(*largs)
        self.is_down = False

RestrictedScrollView.register_scrollable_widget_class(RecycleSpinner)
