from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.stencilview import StencilView
from kivy.clock import Clock
from kivy.properties import (
    ObjectProperty, OptionProperty, BooleanProperty, ListProperty
)
from ui.components.mdi_window import MDIWindow
from libs.uix.context_menu import ContextMenu, ContextMenuTemplates
from typing import Optional, List
from ui.mdi.window_manager import (
    IWindowManager, TilingWindowManager, FloatingWindowManager
)
from libs.uix.workspace_manager import WorkspaceBehavior
from database.mdi_manager import WindowManager, RowMDIManager
from libs.kivy_utils import AutoUnbindBehavior


class MDIContainer(WorkspaceBehavior, AutoUnbindBehavior, FloatLayout, StencilView):
    mdi_focused: Optional[MDIWindow] = ObjectProperty(None, allownone=True)
    mdi_list_showed: List[MDIWindow] = ListProperty()
    window_manager = OptionProperty(None, options=[FloatingWindowManager, TilingWindowManager])
    layout_mode: Optional[IWindowManager] = ObjectProperty()
    db_row: RowMDIManager = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.db_row.window_manager is WindowManager.FLOATING:
            self.window_manager = FloatingWindowManager
        elif self.db_row.window_manager is WindowManager.TILING:
            self.window_manager = TilingWindowManager
        Clock.schedule_once(self._restore_state, -1)

    def _restore_state(self, _):
        mdi_focused = self.db_row.mdi_focused
        self.layout_mode.db_sync()
        if self.db_row.layout is None:
            self.db_row.layout = []
            self.db_row.save()
        if mdi_focused:
            mdi = App.get_running_app().get_mdi_by_title_id(mdi_focused)
            self.set_focus(mdi)

    def on_showed(self, _, showed: bool):
        if showed:
            if self.layout_mode:
                self.layout_mode.register_keyboard_context()
        else:
            if self.layout_mode:
                self.layout_mode.unregister_keyboard_context()

    def on_mdi_focused(self, _, mdi_focused):
        self.db_row.edit(mdi_focused=mdi_focused._db_title_id if mdi_focused else None)

    def on_mdi_list_showed(self, _, mdi_list_showed):
        self.layout_mode.sync_mdi_list_showed()

    def show_mdi(self, mdi):
        mdi.mdi_container = self
        self.layout_mode.show_mdi(mdi)
        self.mdi_list_showed.append(mdi)
        self.set_focus(mdi)

    def hide_mdi(self, mdi):
        mdi.mdi_container = None
        if mdi in self.mdi_list_showed:
            self.layout_mode.hide_mdi(mdi)
            self.mdi_list_showed.remove(mdi)
        if not self.mdi_list_showed:
            self.set_focus(None)

    def switch_focus(self):
        if not self.mdi_list_showed:
            return
        current_idx = self.mdi_list_showed.index(self.mdi_focused) if self.mdi_focused else -1
        new_idx = (current_idx + 1) % len(self.mdi_list_showed)
        self.set_focus(self.mdi_list_showed[new_idx])

    def on_window_manager(self, _, window_manager_cls):
        if self.layout_mode:
            self.layout_mode.unregister_keyboard_context()
        self.layout_mode = window_manager_cls(self, self.layout_mode)
        self.layout_mode.register_keyboard_context()
        if window_manager_cls is FloatingWindowManager:
            self.db_row.edit(window_manager=WindowManager.FLOATING)
        elif window_manager_cls is TilingWindowManager:
            self.db_row.edit(window_manager=WindowManager.TILING)

    def expand_focused_mdi(self):
        mdi = self.mdi_focused
        if mdi and not mdi.toggle_expand.disabled:
            mdi.expanded = True

    def unexpand_focused_mdi(self):
        mdi = self.mdi_focused
        if mdi and not mdi.toggle_expand.disabled:
            mdi.expanded = False

    def hide_focused_mdi(self):
        self.mdi_focused.close()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and not self.layout_mode.find_mdi_at_pos(touch.pos):
            if touch.button == "right":
                self.open_context_menu(touch.pos)
                return True
        return self.layout_mode.handle_touch_down(touch)

    def on_touch_move(self, touch):
        return self.layout_mode.handle_touch_move(touch)

    def on_touch_up(self, touch):
        return self.layout_mode.handle_touch_up(touch)

    def on_mouse_move(self, pos):
        self.layout_mode.handle_mouse_move(pos)

    def set_focus(self, mdi_window):
        self.__discard_focus()
        if mdi_window is None:
            return
        mdi_window.focus = True
        self.mdi_focused = mdi_window
        self.layout_mode.on_mdi_focus(mdi_window)
        if mdi_window in self.mdi_list_showed:
            self.mdi_list_showed.remove(mdi_window)
            self.mdi_list_showed.append(mdi_window)
        for mdi in [mdi for mdi in self.mdi_list_showed if mdi.locked]:
            self.mdi_list_showed.remove(mdi)
            self.mdi_list_showed.append(mdi)

    def __discard_focus(self):
        if self.mdi_focused:
            self.mdi_focused.focus = False
        self.mdi_focused = None

    def open_context_menu(self, pos):
        ctx_menu = ContextMenu(items=[
            ContextMenuTemplates.button(
                text="Закрыть все окна",
                on_release=self._close_all_windows,
            ),
            ContextMenuTemplates.spinner(
                text="Оконный менеджер",
                values=self.property("window_manager").options,
                selected=self.window_manager,
                value_to_host=lambda x: x.title,
                on_select=self.set_window_manager
            )
        ])
        ctx_menu.open(self, pos=self.to_window(*pos))

    def set_window_manager(self, _, window_manager):
        self.window_manager = window_manager

    def _close_all_windows(self, _):
        for mdi in self.mdi_list_showed[:]:
            mdi.close()
