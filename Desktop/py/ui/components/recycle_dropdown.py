from kivy.properties import (
    ObjectProperty, NumericProperty, BooleanProperty
)
from kivy.core.window import Window
from ui.components.scroll_layout import ScrollLayout
from libs.uix.behaviors.modal import ModalBehavior
from kivy.lang import Builder

Builder.load_file("ui/components/recycle_dropdown.kv")


class RecycleDropdown(ModalBehavior, ScrollLayout):
    max_height = NumericProperty("400dp")
    min_height = NumericProperty("120dp")
    auto_width = BooleanProperty(True)
    force_width = NumericProperty("300dp")
    auto_height = BooleanProperty(True)
    force_height = NumericProperty("300dp")
    cls_height = NumericProperty("30dp")
    values = ObjectProperty()
    selected = ObjectProperty()

    __events__ = ("on_select",)

    def update_values(self):
        if self.scrollview:
            self.scrollview.data = [self.value_to_dict(
                self, v) for v in self.values_getter(self)]
            self._reposition()

    def _default_values_getter(self) -> any:
        return self.values
    values_getter = ObjectProperty(_default_values_getter)

    def _default_value_to_dict(self, value) -> dict:
        return {
            "text": str(self.value_to_host(value)),
            "stored_value": value,
            "on_release": lambda x=value: self.select(x)
        }
    value_to_dict = ObjectProperty(_default_value_to_dict)

    @staticmethod
    def _default_value_to_host(value: str) -> str:
        return value
    value_to_host = ObjectProperty(_default_value_to_host)

    def open(self, widget):
        self.update_values()
        super().open(widget)

    def on_values(self, *args):
        self.update_values()

    def on_cls_height(self, _, value: float):
        self.scrollview.layout_manager.default_size = (None, value)

    def select(self, data: any):
        self.selected = data
        self.dispatch("on_select", data)
        self.dismiss()

    def on_select(self, data: any):
        pass

    def _reposition(self, *args):
        win = Window
        widget = self.attach_to
        if not widget or not widget.get_parent_window():
            return

        wx, wy = widget.to_window(*widget.pos)
        wright, wtop = widget.to_window(widget.right, widget.top)

        if self.auto_width:
            self.width = wright - wx
            self.width = min(self.width, win.width - wx)  # Не шире экрана
            x = wx
        else:
            self.width = self.force_width
            x = widget.to_window(*widget.center)[0] - self.width / 2
        # Позиция по X
        if x + self.width > win.width:
            x = win.width - self.width
        self.x = max(x, 0)

        space_below = wy
        space_above = win.height - wtop

        if space_below >= space_above:
            max_possible = min(self.max_height, space_below)
            place_below = True
        else:
            max_possible = min(self.max_height, space_above)
            place_below = False

        if self.auto_height:
            self.height = min(
                max(max_possible, self.min_height),
                self.scrollview.layout_manager.minimum_height
            )
        else:
            self.height = min(self.force_height, max_possible)

        if place_below:
            self.top = wy
        else:
            self.top = win.height if False else wtop + self.height
