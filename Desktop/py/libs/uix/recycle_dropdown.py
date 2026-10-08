from typing import Any, Callable, Dict, List, Optional, Tuple

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import BooleanProperty, NumericProperty, ObjectProperty
from kivy.uix.widget import Widget

from libs.uix.behaviors.modal import ModalBehavior
from libs.uix.recycle_restricted_scrollview import RecycleRestrictedScrollView
from libs.uix.scroll_layout import ScrollLayout

Builder.load_string("""
<RecycleDropdown>:  # ScrollLayout
    size_hint: None, None

    scrollview: scrollview
    canvas.before:
        Color:
            rgba: uix_cs.general.menu_bg
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: uix_cs.general.border_color
        Line:
            rectangle: (self.x, self.y, self.width, self.height)
    RecycleRestrictedScrollView:
        id: scrollview
        viewclass: root.viewclass
        scroll_by_content: True
        do_scroll_x: False
        RecycleBoxLayout:
            size_hint: (1, None)
            orientation: "vertical"
            default_size_hint: (1, None)
            width: self.minimum_width
            height: self.minimum_height
            default_size: (None, root.cls_height)
"""
)


class RecycleDropdown(ModalBehavior, ScrollLayout):
    max_height: float = NumericProperty("400dp")
    min_height: float = NumericProperty("120dp")
    auto_width: bool = BooleanProperty(True)
    force_width: float = NumericProperty("300dp")
    auto_height: bool = BooleanProperty(True)
    force_height: float = NumericProperty("300dp")
    cls_height: float = NumericProperty("30dp")
    values: List[Any] = ObjectProperty()
    selected: Any = ObjectProperty()
    scrollview: RecycleRestrictedScrollView

    __events__ = ("on_select",)

    def update_values(self):
        if self.scrollview:
            self.scrollview.data = [self.value_to_dict(
                self, v) for v in self.values_getter(self)]
            self._reposition()

    def default_values_getter(self) -> List[Any]:
        return self.values
    values_getter: Callable[[Any], List[Any]] = ObjectProperty(default_values_getter)

    def default_value_to_dict(self, value: Any) -> Dict[str, Any]:
        return {
            "text": str(self.value_to_host(value)),
            "stored_value": value,
            "on_release": lambda x=value: self.select(x)
        }
    value_to_dict: Callable[[Any, Any], Dict[str, Any]] = ObjectProperty(default_value_to_dict)

    @staticmethod
    def default_value_to_host(value: str) -> str:
        return value
    value_to_host: Callable[[Any], Any] = ObjectProperty(default_value_to_host)

    def open(self, widget: Optional[Widget]=None, pos:Optional[Tuple[float, float]]=None):
        self.update_values()
        super().open(widget)

    def on_values(self, *_):
        self.update_values()

    def on_cls_height(self, _, value: float):
        self.scrollview.layout_manager.default_size = (None, value)

    def select(self, data: Any):
        self.selected = data
        self.dispatch("on_select", data)
        self.dismiss()

    def on_select(self, data: Any):
        pass

    def _reposition(self, *_):
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
            self.top = wtop + self.height
