from kivy.properties import (
    ObjectProperty, NumericProperty, ListProperty, BooleanProperty
)
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Rectangle
from kivy.core.text import Label as CoreLabel
from libs.uix.button import HoverButton
from ui.components.recycle_spinner import RecycleSpinner
from libs.uix.label import RestrictedLabel
from kivy.uix.widget import Widget
from kivy.metrics import dp
from libs.uix.layouts import ModalBoxLayout
from libs.sdl2_keyboard import hotkey_to_str
from dataclasses import dataclass, field
from typing import Optional
from kivy.lang import Builder
from libs.utils import merge_kwargs

Builder.load_file("ui/components/context_menu.kv")


@dataclass
class ContextMenuItem:
    widget_class: Widget
    kwargs: dict = field(default_factory=dict)


class ContextMenuSeparator(Widget):
    pass


class ContextMenuBehavior:
    focus = BooleanProperty(False)


class ContextMenuButton(ContextMenuBehavior, HoverButton):
    hotkey = ObjectProperty(frozenset())
    hotkey_font_size = NumericProperty("12sp")
    hotkey_label: CoreLabel = ObjectProperty()
    hotkey_texture = ObjectProperty()
    hotkey_texture_x = NumericProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.hotkey:
            self._update_trigger = Clock.create_trigger(
                self._update_canvas, -1)
            self.bind(
                size=self._update_trigger,
                pos=self._update_trigger,
                hotkey=self._update_trigger,
                hotkey_font_size=self._update_trigger
            )
            self._create_hotkey_label()
            self._update_trigger()

    def _create_hotkey_label(self):
        self.hotkey_label = CoreLabel(
            text=hotkey_to_str(self.hotkey).lower(),
            font_size=self.hotkey_font_size,
            color=self.color
        )
        self.hotkey_label.refresh()
        self.hotkey_texture = self.hotkey_label.texture

    def _update_canvas(self, *args):
        self.canvas.after.clear()

        with self.canvas.after:
            Rectangle(
                texture=self.hotkey_texture,
                pos=(
                    self.right - self.hotkey_texture_x - dp(10),
                    self.center_y - self.hotkey_texture.height / 2
                ),
                size=self.hotkey_texture.size
            )


class ContextMenuSpinner(ContextMenuBehavior, RecycleSpinner):
    pass


class SubMenu(ContextMenuBehavior, RestrictedLabel):
    menu = ObjectProperty()

    def __init__(self, items: tuple, **kwargs):
        super().__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouse_pos)
        self._open_submenu_trigger = Clock.create_trigger(
            self.open_submenu, 1.0)
        self.items = items

    def on_mouse_pos(self, window, mouse_pos: tuple):
        if self.collide_point(*mouse_pos):
            self._open_submenu_trigger()
        elif self._open_submenu_trigger.is_triggered:
            self._open_submenu_trigger.cancel()

    def open_submenu(self, _):
        self.menu = ContextMenu(self.items)
        self.menu.open(self, pos=(self.right, self.top))


class ContextMenuTemplates:
    @staticmethod
    def button(**kwargs) -> ContextMenuItem:
        return ContextMenuTemplates._apply_kwargs({
            "widget_class": ContextMenuButton,
        }, kwargs)

    @staticmethod
    def separator(**kwargs) -> ContextMenuItem:
        return ContextMenuTemplates._apply_kwargs({
            "widget_class": ContextMenuSeparator,
        }, kwargs)

    @staticmethod
    def spinner(**kwargs) -> ContextMenuItem:
        return ContextMenuTemplates._apply_kwargs({
            "widget_class": ContextMenuSpinner,
        }, kwargs)

    @staticmethod
    def _apply_kwargs(default_kwargs: dict, kwargs: dict) -> ContextMenuItem:
        data = merge_kwargs(default_kwargs, kwargs)
        widget_class = data.pop("widget_class")
        return ContextMenuItem(widget_class=widget_class, kwargs=data)


class ContextMenu(ModalBoxLayout):
    content = ObjectProperty()
    items = ListProperty()

    hotkeys = None
    was_inited = False
    def on_kv_post(self, _):
        self.was_inited = True
        self.hotkeys = {}
        self.property("items").dispatch(self)

    def on_items(self, _, items: list):
        if self.was_inited:
            self.parse_items(items)

    def parse_items(self, items: tuple):
        self.hotkey_button_list = []
        self.button_list = []
        for item in items:
            widget_cls = item.widget_class
            widget_kwargs = item.kwargs
            widget = widget_cls(**widget_kwargs)
            self.add_widget(widget)
            if isinstance(widget, ContextMenuButton):
                widget.bind(on_release=lambda _: self.dismiss())
                if "hotkey" in widget_kwargs:
                    self.hotkey_button_list.append(widget)
                else:
                    self.button_list.append(widget)
        Clock.schedule_once(self.processing_hotkey_button_list, -1)

    def processing_hotkey_button_list(self, _):
        hotkey_buttons = self.hotkey_button_list
        normal_buttons = self.button_list
        all_buttons = hotkey_buttons + normal_buttons

        if not all_buttons:
            return

        max_btn_text_width = max(btn.texture_size[0] for btn in all_buttons)

        if hotkey_buttons:
            max_hotkey_width = max(
                btn.hotkey_texture.width for btn in hotkey_buttons
            )

            hotkey_btn_width = (
                max(btn.texture_size[0] for btn in hotkey_buttons)
                + max_hotkey_width
                + dp(10)
            )

            self.width = max(max_btn_text_width, hotkey_btn_width)

            for btn in hotkey_buttons:
                btn.hotkey_texture_x = max_hotkey_width

                if not btn.disabled:
                    self.hotkeys[btn.hotkey] = (
                        lambda x=btn: x.dispatch("on_release")
                    )
        else:
            self.width = max_btn_text_width

        for btn in all_buttons:
            btn.text_size = (self.width, btn.height)

        if hotkey_buttons:
            self.update_keyboard_context()

    is_blocked_keyboard = True
    def create_hotkeys(self) -> Optional[dict]:
        return {
            **super().create_hotkeys(),
            **self.hotkeys
        }
