from typing import Any, Callable, Dict, FrozenSet, Optional, Tuple

from kivy.lang import Builder
from kivy.properties import (
    AliasProperty,
    BooleanProperty,
    DictProperty,
    NumericProperty,
    ObjectProperty,
    ReferenceListProperty,
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from libs.animation import AnimationBehavior, StatefulColorProperty
from libs.kivy_mixins import AutoUnbindBehavior, ViewContextSaverMixin
from libs.sdl2_keyboard import KeyboardBehavior
from libs.typecheck import RGBA, Number
from libs.uix import colorscheme as uix_cs
from libs.uix.label import RestrictedLabel

Builder.load_string("""
#:import uix_cs libs.uix.colorscheme
#:import imgs_path misc.imgs_path


<MDIWindow>:  # BoxLayout
    title_bar: title_bar
    title_bar_label: title_bar_label

    size_hint: (None, None)
    size: ("600dp", "400dp")
    window_minimum_size: ("250dp", "250dp")
    padding: "3dp"
    orientation: 'vertical'

    canvas.before:
        Color:
            rgba: uix_cs.general.menu_wrap_bg
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: self.border_color
        Line:
            width: dp(1)
            rectangle: (self.x, self.y, self.width, self.height)
    BoxLayout:
        id: title_bar
        size_hint: (1, None)
        height: "20dp"
        spacing: "4dp"
        RestrictedLabel:
            id: title_bar_label
            text: root.title
            size_hint_x: 1
            halign: 'left'
            valign: 'center'
            padding: ("6dp", 0)
            font_size: "12sp"
            text_size: self.size
            canvas.before:
                Color:
                    rgba: uix_cs.general.menu_bg
                Rectangle:
                    pos: self.pos
                    size: self.size
"""
)


class MDIWindow(ViewContextSaverMixin, KeyboardBehavior, AutoUnbindBehavior, AnimationBehavior, BoxLayout):
    title: str = StringProperty("")
    focus: bool = BooleanProperty(False)
    hidden: bool = BooleanProperty(False)
    state: Dict[str, Any] = DictProperty()
    window_minimum_width: Number = NumericProperty("250dp")
    window_minimum_height: Number = NumericProperty("250dp")
    window_minimum_size: Tuple[Number, Number] = ReferenceListProperty(window_minimum_width, window_minimum_height)
    focus_selected: bool = BooleanProperty(False)  # Для UI border: наведение, перемещение...

    animation_time: float = 0.0
    border_color: RGBA = StatefulColorProperty(
        normal=uix_cs.MDIWindow.border_normal,
        states={
            "focus_selected": uix_cs.MDIWindow.border_selected,
            "focus": uix_cs.MDIWindow.border_focused,
        }
    )

    mdi_container: Optional["MDIContainer"] = ObjectProperty(allownone=True)
    title_bar: BoxLayout = ObjectProperty()
    title_bar_label: RestrictedLabel = ObjectProperty()

    def __init__(
            self,
            view_context: Optional[Dict[str, Any]]=None,
            layout_state: Optional[Dict[str, Any]]=None,
            *args: Any,
            **kwargs: Any):
        state = {}
        if layout_state is not None:
            state["layout_state"] = layout_state
        super().__init__(*args, state=state, **kwargs)
        self.load_view_context(view_context)

    def on_window_minimum_width(self, _, value: float):
        self.width = max(self.width, value)

    def on_window_minimum_height(self, _, value: float):
        self.height = max(self.height, value)

    def on_kv_post(self, base_widget: Widget):
        super().on_kv_post(base_widget)
        w, h = self.size
        w_min, h_min = self.window_minimum_size
        self.size = [max(w, w_min), max(h, h_min)]

    def get_layout_state(self, key: str, default: Any) -> Any:
        return self.state.get("layout_state", {}).get(key, default)

    def set_layout_state(self, **kwargs: Any):
        layout_state = self.state.get("layout_state", {}).copy()
        changed = False
        for key, value in kwargs.items():
            if layout_state.get(key) != value:
                layout_state[key] = value
                changed = True
        if changed:
            fullstate = self.state.copy()
            fullstate["layout_state"] = layout_state
            self.state = fullstate

    def clear_layout_state(self):
        if self.state.get("layout_state"):
            state = self.state.copy()
            state["layout_state"] = {}
            self.state = state

    def get_view_context(self) -> Dict[str, Any]:
        return self.state.get("view_context", {})

    def set_view_context(self, view_context: Dict[str, Any]) -> bool:
        state = self.state.copy()
        state["view_context"] = dict(view_context)
        self.state = state
        return True

    view_context: Dict[str, Any] = AliasProperty(
        get_view_context,
        set_view_context,
    )

    def on_hidden(self, _: Widget, hidden: bool):
        if hidden and self._view_context_loaded:
            self._save_vc()

    def on_focus(self, _: Widget, focus: bool):
        if focus:
            self.register_keyboard_context()
        else:
            self.unregister_keyboard_context()

    def create_hotkeys(self) -> Dict[FrozenSet[str], Callable[[], None]]:
        return {}
