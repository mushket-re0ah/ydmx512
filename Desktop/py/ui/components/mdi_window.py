from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import (
    BooleanProperty, ObjectProperty, NumericProperty, AliasProperty,
    StringProperty, ColorProperty
)
from libs.uix.context_menu import ContextMenu, ContextMenuTemplates
from libs.sdl2_keyboard import KeyboardBehavior
from libs.animation import AnimationBehavior
from database.mdi_manager import WindowManager, FlexManager
from typing import Optional
from kivy.lang import Builder
from misc import colorscheme as cs
from libs.kivy_utils import AutoUnbindBehavior
from libs.animation import StatefulColorProperty
from database.mdi_window import ViewContextSaverMixin

Builder.load_file("ui/components/mdi_window.kv")


class MDIWindow(ViewContextSaverMixin, KeyboardBehavior, AutoUnbindBehavior, AnimationBehavior, BoxLayout):
    # constants
    SIZE_HINT_MINIMUM = 0.1

    _db_title_id = "DB_TITLE_ID"
    title_id = StringProperty(_db_title_id)  # Должно быть переназначено в наследнике
    title = StringProperty("")
    mdi_db_row = ObjectProperty()
    focus = BooleanProperty(False)
    hidden = BooleanProperty(True)

    _mdi_container = ObjectProperty(allownone=True)

    # widgets
    title_bar = ObjectProperty()
    title_bar_label = ObjectProperty()
    toggle_lock = ObjectProperty()
    toggle_expand = ObjectProperty()
    btn_close = ObjectProperty()

    real_minimum_width = NumericProperty(200)
    real_minimum_height = NumericProperty(200)

    focus_selected = BooleanProperty(False)  # Для UI border: наведение, перемещение...

    animation_time = 0.0
    border_color = StatefulColorProperty(
        normal=cs.MDIWindow.border_normal,
        states={
            "focus_selected": cs.MDIWindow.border_selected,
            "focus": cs.MDIWindow.border_focused,
        }
    )

    __events__ = ("on_close", "on_open", "on_expand")

    def _set_attr(self, attr: str, value: any) -> bool:
        if value != getattr(self.mdi_db_row, attr):
            self.mdi_db_row.edit(**{attr: value})
            return True
        return False

    locked = AliasProperty(
        lambda self: self.mdi_db_row.locked,
        lambda self, value:  self._set_attr("locked", value),
    )
    expanded = AliasProperty(
        lambda self: self.mdi_db_row.expanded,
        lambda self, value: self._set_attr("expanded", value),
    )
    view_context = AliasProperty(
        lambda self: self.mdi_db_row.view_context,
        lambda self, value: self._set_attr("view_context", value),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_view_context()

    def _save_attr(self, attr: str, value: any):
        self.mdi_db_row.edit(**{attr: value})

    def on_expanded(self, _, expanded: bool):
        self.dispatch("on_expand", expanded)

    def on_focus(self, _, focus: bool):
        if focus:
            self.register_keyboard_context()
        else:
            self.unregister_keyboard_context()

    def on_hidden(self, _, hidden: bool):
        if hidden:
            self.close()
        else:
            self.open()

    def set_mdi_container(self, mdi_container):
        if self._mdi_container:
            self.unbind_from(self._mdi_container.db_row)
        if mdi_container:
            self.bind_to(mdi_container.db_row, window_manager=self.on_set_window_manager)
            self.on_set_window_manager(mdi_container, mdi_container.db_row.window_manager)
        self._mdi_container = mdi_container

    def on_set_window_manager(self, mdi_container_or_db_row, window_manager: WindowManager):
        container = mdi_container_or_db_row if hasattr(mdi_container_or_db_row, "layout_mode") else self.mdi_container
        if container is None:
            return
        layout_mode = container.layout_mode
        if layout_mode is None:
            return

        title_bar = self.title_bar
        title_bar.remove_widget(self.toggle_lock)
        title_bar.remove_widget(self.toggle_expand)
        title_bar.remove_widget(self.btn_close)

        buttons = layout_mode.get_title_buttons()
        if "lock" in buttons:
            title_bar.add_widget(self.toggle_lock)
        if "expand" in buttons:
            title_bar.add_widget(self.toggle_expand)
        if "close" in buttons:
            title_bar.add_widget(self.btn_close)

    mdi_container = AliasProperty(
        lambda self: self._mdi_container, set_mdi_container
    )

    def create_hotkeys(self) -> Optional[dict]:
        return {
            frozenset({"ctrl", "shift", "l"}): self.invert_locked,
            frozenset({"ctrl", "shift", "e"}): self.close,
            frozenset({"ctrl", "shift", "u"}): self.invert_expanded,
            frozenset({"ctrl", "shift", "up"}): self.do_expand,
            frozenset({"ctrl", "shift", "down"}): self.do_unexpand,
        }

    def open_context_menu(self, pos):
        items = []
        buttons = self.mdi_container.layout_mode.get_title_buttons()
        if "lock" in buttons:
            items.append(self.create_context_menu_lock_btn())
        if "expand" in buttons:
            items.append(self.create_context_menu_expand_btn())
        if "close" in buttons:
            items.append(self.create_context_menu_close_btn())
        ctx_menu = ContextMenu(items=items)
        ctx_menu.open(self, pos=pos)

    def create_context_menu_lock_btn(self):
        return ContextMenuTemplates.button(
            text="Разблокировать" if self.locked else "Заблокировать",
            on_release=self.invert_locked,
            hotkey=frozenset({"ctrl", "shift", "l"}),
        )

    def create_context_menu_expand_btn(self):
        return ContextMenuTemplates.button(
            text="Свернуть" if self.expanded else "Развернуть",
            on_release=self.invert_expanded,
            hotkey=frozenset({"ctrl", "shift", "u"}),
            disabled=self.locked or self.toggle_expand.disabled
        )

    def create_context_menu_close_btn(self):
        return ContextMenuTemplates.button(
            text="Закрыть",
            on_release=self.close,
            hotkey=frozenset({"ctrl", "shift", "e"}),
        )

    def invert_locked(self, _=None):
        self.locked = not self.locked

    def invert_expanded(self, _=None):
        if self.locked:
            return
        self.expanded = not self.expanded

    def invert_hidden(self):
        self.hidden = not self.hidden

    def do_expand(self):
        if self.locked:
            return
        self.expanded = True

    def do_unexpand(self):
        if self.locked:
            return
        self.expanded = False

    def close(self, _=None):
        if self.mdi_container:
            self.mdi_container.hide_mdi(self)
            self.hidden = True
            self.dispatch("on_close")

    def open(self, _=None, workspace_index: Optional[int]=None):
        if not self.mdi_container:
            App.get_running_app().root.mdi_container_manager.show_mdi(self, workspace_index)
            self.hidden = False
            self.dispatch("on_open")

    def on_close(self):
        pass

    def on_open(self):
        pass

    def on_expand(self, expanded: bool):
        pass
