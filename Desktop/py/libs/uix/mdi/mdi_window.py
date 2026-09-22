from kivy.uix.boxlayout import BoxLayout
from kivy.properties import (
    BooleanProperty, ObjectProperty, NumericProperty, StringProperty,
    ReferenceListProperty, DictProperty, AliasProperty
)
from libs.kivy_utils import ViewContextSaverMixin
from libs.sdl2_keyboard import KeyboardBehavior
from libs.animation import AnimationBehavior
from typing import Optional, Tuple
from misc import colorscheme as cs
from libs.kivy_utils import AutoUnbindBehavior
from libs.animation import StatefulColorProperty
from kivy.lang import Builder

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
    title = StringProperty("")
    focus = BooleanProperty(False)
    hidden = BooleanProperty(False)
    state = DictProperty()
    window_minimum_width = NumericProperty("250dp")
    window_minimum_height = NumericProperty("250dp")
    window_minimum_size = ReferenceListProperty(window_minimum_width, window_minimum_height)
    focus_selected = BooleanProperty(False)  # Для UI border: наведение, перемещение...

    animation_time = 0.0
    border_color = StatefulColorProperty(
        normal=cs.MDIWindow.border_normal,
        states={
            "focus_selected": cs.MDIWindow.border_selected,
            "focus": cs.MDIWindow.border_focused,
        }
    )

    mdi_container = ObjectProperty(allownone=True)
    title_bar = ObjectProperty()
    title_bar_label = ObjectProperty()

    def __init__(self, view_context=None, layout_state=None, *args, **kwargs):
        state = {}
        if layout_state is not None:
            state["layout_state"] = layout_state
        super().__init__(*args, state=state, **kwargs)
        self.load_view_context(view_context)

    def on_window_minimum_width(self, _, value):
        if self.width < value:
            self.width = value

    def on_window_minimum_height(self, _, value):
        if self.height < value:
            self.height = value

    def on_kv_post(self, _):
        super().on_kv_post(_)
        w, h = self.size
        w_min, h_min = self.window_minimum_size
        self.size = [max(w, w_min), max(h, h_min)]

    def get_layout_state(self, key, default):
        return self.state.get("layout_state", {}).get(key, default)

    def set_layout_state(self, **kwargs):
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

    def get_view_context(self):
        return self.state.get("view_context", {})

    def set_view_context(self, view_context):
        state = self.state.copy()
        state["view_context"] = dict(view_context)
        self.state = state
        return True

    view_context = AliasProperty(
        get_view_context,
        set_view_context,
    )

    def on_hidden(self, _, hidden: bool):
        if hidden and self._view_context_loaded:
            self._save_vc()

    def on_focus(self, _, focus: bool):
        if focus:
            self.register_keyboard_context()
        else:
            self.unregister_keyboard_context()

    def create_hotkeys(self) -> Optional[dict]:
        return {}
