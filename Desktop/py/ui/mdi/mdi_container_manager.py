from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.widget import Widget
from libs.uix.workspace_manager import WorkspaceManager, WorkspaceBehavior
from ui.components.mdi_window import MDIWindow
from libs.uix.button import HoverToggleButton
from ui.mdi.window_manager import (
    TilingWindowManager, FloatingWindowManager
)
from misc import constants
from typing import Optional
from database import db
from libs.properties import BindableObjectProperty
from libs.kivy_utils import AutoUnbindBehavior


class WindowManagerSwitcher(HoverToggleButton):
    mdi_manager = ObjectProperty(rebind=True)


class TilingOrientationSwitcher(HoverToggleButton):
    mdi_manager = ObjectProperty(rebind=True)


class MDIContainerManager(AutoUnbindBehavior, WorkspaceManager):
    workspace_count = NumericProperty(constants.DATABASE_MDI_WORKSPACES_COUNT)
    window_switcher = ObjectProperty()
    orientation_switcher = ObjectProperty(allownone=True)

    def on_kv_post(self, _):
        super().on_kv_post(_)
        self.menu.add_widget(Widget(size_hint=(1, 1)))
        self.window_switcher = WindowManagerSwitcher(mdi_manager=self)
        self.menu.add_widget(self.window_switcher)
        for row in db.mdi_manager.rows.values():
            workspace = self.create_workspace(row.workspace_index)
        self.set_workspace(db.mdi_manager.workspace_index)
        self.bind(
            workspace_now_index=self.save_workspace_index,
            workspace_now=self.workspace_changed
        )
        self.workspace_changed(None, self.workspace_now)

    def save_workspace_index(self, _, workspace_index: int):
        db.mdi_manager.edit(workspace_index=workspace_index)

    prev_workspace = None
    def workspace_changed(self, _, workspace_now: WorkspaceBehavior):
        if self.prev_workspace:
            self.unbind_from(self.prev_workspace)
        self.refresh_menu()
        self.bind_to(workspace_now, window_manager=self.refresh_menu)
        self.prev_workspace = workspace_now

    def refresh_menu(self, *args):
        wm = self.workspace_now.window_manager

        if wm is TilingWindowManager:
            if not self.orientation_switcher:
                self.orientation_switcher = TilingOrientationSwitcher(mdi_manager=self)
                self.menu.add_widget(self.orientation_switcher, 1)
        elif wm is FloatingWindowManager:
            if self.orientation_switcher:
                self.menu.remove_widget(self.orientation_switcher)
                self.orientation_switcher = None
        else:
            raise ValueError()

    def show_mdi(self, mdi: MDIWindow, workspace_index: Optional[int] = None):
        workspace_index = self.workspace_now_index if workspace_index is None else workspace_index
        if self.workspaces[workspace_index] is None:
            self.create_workspace(workspace_index)
        self.workspaces[workspace_index].show_mdi(mdi)

    def _create_workspace_instance(self, workspace_index: int) -> WorkspaceBehavior:
        row = db.mdi_manager.by_workspace_index(workspace_index)
        return self.workspace_cls(index=workspace_index, db_row=row)
