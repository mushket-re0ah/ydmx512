from libs.uix.mdi.workspace_mdi_container_manager import WorkspaceMDIContainerManager
from libs.uix.mdi.layout_mode import TilingLayoutMode, FloatingLayoutMode
from libs.uix.mdi.mdi_window import MDIWindow
from libs.uix.workspace_manager import WorkspaceBehavior
from database import db
from typing import List
from itertools import chain


class DatabaseWorkspaceMDIContainerManager(WorkspaceMDIContainerManager):
    def __init__(self, *args, **kwargs):
        self._database_loaded = False
        super().__init__(*args, **kwargs)

    def load_database_data(self, mdi_list: List[MDIWindow]):
        self.workspace_now_index = db.mdi_manager.workspace_index
        for index in self.workspaces.keys():
            self._load_workspace_database_data(index, mdi_list)
        self._database_loaded = True

    def _load_workspace_database_data(self, index: int, mdi_list: List[MDIWindow]):
        from libs import logger
        db_row = db.mdi_manager.by_workspace_index(index)
        if not db_row.layout:
            return
        workspace = self.create_workspace(index)

        if db_row.layout_mode == TilingLayoutMode.layout_state_key:
            workspace.layout_mode = TilingLayoutMode
        elif db_row.layout_mode == FloatingLayoutMode.layout_state_key:
            workspace.layout_mode = FloatingLayoutMode

        workspace_layout = self._deserialize_workspace_layout(db_row.layout, mdi_list)
        workspace.layout_mode.load_layout(workspace_layout)

        if db_row.layout_mode == FloatingLayoutMode.layout_state_key:
            float_layout = workspace_layout
        elif db_row.layout_mode == TilingLayoutMode.layout_state_key:
            float_layout = list(chain.from_iterable(workspace_layout))
        mdi_focused = next((mdi for mdi in float_layout if mdi._db_title_id == db_row.mdi_focused))
        workspace.set_focus(mdi_focused)

    def on_workspace_opened(self, workspace_index: int, workspace: WorkspaceBehavior):
        if not self._database_loaded:
            return
        db.mdi_manager.edit(workspace_index=workspace_index)
        super().on_workspace_opened(workspace_index, workspace)

    def on_workspace_closed(self, workspace_index: int, workspace: WorkspaceBehavior):
        super().on_workspace_closed(workspace_index, workspace)

    def on_workspace_created(self, workspace_index: int, workspace: WorkspaceBehavior):
        db_row = db.mdi_manager.by_workspace_index(workspace.index)
        layout_mode = db_row.layout_mode
        if layout_mode == TilingLayoutMode.layout_state_key:
            workspace.layout_mode = TilingLayoutMode
        elif layout_mode == FloatingLayoutMode.layout_state_key:
            workspace.layout_mode = FloatingLayoutMode
        self.bind_to(
            workspace,
            mdi_focused=lambda v, w=workspace: self._save_data(workspace),
            layout_mode=lambda v, w=workspace: self._save_data(workspace)
        )
        self.bind_to(
            workspace.layout_mode,
            on_layout_changed=lambda v, w=workspace: self._save_data(workspace)
        )
        self._save_data(workspace)
        super().on_workspace_created(workspace_index, workspace)

    def on_workspace_removed(self, workspace_index: int, workspace: WorkspaceBehavior):
        self.unbind_from(workspace.layout_mode)
        self.unbind_from(workspace)
        self._save_data(workspace)

    def _save_data(self, workspace):
        self._save_mdi_focused(workspace)
        self._save_layout_mode(workspace)
        self._save_layout(workspace)

    def _save_layout(self, workspace):
        if not self._database_loaded:
            return
        db_row = db.mdi_manager.by_workspace_index(workspace.index)
        db_row.edit(layout=self._get_serialized_workspace_layout(workspace))

    def _save_layout_mode(self, workspace):
        if not self._database_loaded:
            return
        db_row = db.mdi_manager.by_workspace_index(workspace.index)
        db_row.edit(layout_mode=workspace.layout_mode.layout_state_key)

    def _save_mdi_focused(self, workspace):
        if not self._database_loaded:
            return
        db_row = db.mdi_manager.by_workspace_index(workspace.index)
        mdi_focused = workspace.mdi_focused
        if mdi_focused is None:
            db_row.edit(mdi_focused=None)
        else:
            db_row.edit(mdi_focused=mdi_focused._db_title_id)

    def _get_serialized_workspace_layout(self, workspace) -> list:
        layout_mode = workspace.layout_mode
        if isinstance(layout_mode, FloatingLayoutMode):
            return [i._db_title_id for i in layout_mode.get_layout()]
        elif isinstance(layout_mode, TilingLayoutMode):
            return [
                [mdi._db_title_id for mdi in mdi_group]
                for mdi_group in layout_mode.get_layout()
            ]
        else:
            raise RuntimeError()

    def _deserialize_workspace_layout(self, layout: list, mdi_list: List[MDIWindow]) -> List[MDIWindow]:
        mdi_by_title_id = {mdi._db_title_id: mdi for mdi in mdi_list}
        def deserialize(value):
            if isinstance(value, list):
                return [deserialize(item) for item in value]
            return mdi_by_title_id[value]

        return deserialize(layout)
