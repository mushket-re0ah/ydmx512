from kivy.properties import ObjectProperty, ListProperty
from kivy.lang import Builder
from libs.uix.layouts import MenuPanel
from database import db
from database.patch import RowPatch
from database.scene import RowScene
from ui.mdi.editor.maps.patch.patch_ui import EditorPatchUi
from libs.uix.workspace_manager import WorkspaceBehavior
from operator import attrgetter
from collections import defaultdict
from typing import List, Optional
from ui.components.context_menu import (
    ContextMenu, ContextMenuButton, ContextMenuItem
)


Builder.load_file("ui/mdi/editor/maps/patch/patch_map.kv")


class PatchEditorMap(MenuPanel):
    workspace_manager = ObjectProperty()
    editor = ObjectProperty()

    playback = ObjectProperty(None, allownone=True, rebind=True)
    active_patch: List[RowPatch] = ListProperty([], rebind=True)

    def on_workspace_opened(self, _, workspace_index: int, workspace: WorkspaceBehavior):
        self.workspace_now = workspace
        workspace.selectable = False
        workspace.resize_by_children = True
        workspace.invert_grid = True
        workspace.box.child_grid_pos_attrgetter = attrgetter("patch.grid_pos")
        workspace.box.open_context_menu = self.open_context_menu
        workspace.box._create_context_menu = self._create_context_menu

    def on_active_patch(self, _, active_patch: List[RowPatch]):
        for workspace in [i for i in self.workspace_manager.workspaces.values() if i is not None]:
            for patch_ui in workspace.box.children:
                patch_ui._activate_block = True
                patch_ui.is_down = patch_ui.patch in active_patch
                patch_ui._activate_block = False

    def on_kv_post(self, _):
        self.workspace_manager.bind(on_workspace_opened=self.on_workspace_opened)
        self.__init_workspace_manager()
        db.patch.bind(on_add_row=self.on_add_patch)
        db.patch.bind(on_remove_row=self.on_remove_patch)
        db.patch.bind(on_workspace_any_patch=self.on_workspace_any_patch)
        db.patch.bind(on_scene_change=self.on_scene_change)
        self.on_workspace_opened(
            self.workspace_manager,
            self.workspace_manager.workspace_now_index,
            self.workspace_manager.workspace_now
        )

    def activate_patch(self, patch: RowPatch):
        spec = self.playback.renderer.get_interpatch_spec(patch) if self.playback else None
        patches = spec.ordered_patches if spec else [patch]
        new_active = [x for x in self.active_patch if x not in patches]
        self.active_patch = [*new_active, *patches]

    def deactivate_patch(self, patch: RowPatch):
        spec = self.playback.renderer.get_interpatch_spec(patch) if self.playback else None
        patches = spec.ordered_patches if spec else [patch]
        self.active_patch = [x for x in self.active_patch if x not in patches]

    def on_add_patch(self, _, patch: RowPatch):
        workspace = self.workspace_manager.create_workspace(patch.workspace)
        workspace.add_widget(EditorPatchUi(
                patch_map=workspace,
                patch_map_editor=self,
                patch=patch
            )
        )

    def on_remove_patch(self, _, patch: RowPatch):
        wm = self.workspace_manager
        workspace = wm.workspaces[patch.workspace]
        patch_ui = next((i for i in workspace.box.children if i.patch is patch), None)
        if patch_ui is not None:
            patch_ui._self_destroy()

    def on_workspace_any_patch(self, _, patch: RowPatch, workspace: int):
        wm = self.workspace_manager
        workspace = wm.create_workspace(workspace)
        patch_ui = self.get_patch_ui_by_row_patch(patch)
        if not patch_ui:
            return
        patch_ui.parent.remove_widget(patch_ui)
        workspace.add_widget(patch_ui)

    def on_scene_change(self, table, old_scene: RowScene, new_scene: RowScene):
        self.__init_workspace_manager()

    def __init_workspace_manager(self):
        wm = self.workspace_manager
        for workspace in wm.workspaces.values():
            if workspace:
                workspace.box.clear_widgets()

        grouped = defaultdict(list)
        for patch in db.patch.rows.values():
            key = patch.workspace
            grouped[key].append(patch)

        for workspace_index, patch_list in grouped.items():
            workspace = wm.create_workspace(workspace_index)
            for patch in patch_list:
                patch_ui = EditorPatchUi(
                    create_animation=False,
                    patch_map=workspace,
                    patch_map_editor=self,
                    patch=patch
                )
                if patch in self.active_patch:
                    patch_ui.is_down = True
                workspace.add_widget(patch_ui)

    def get_patch_ui_by_row_patch(self, patch: RowPatch) -> Optional[EditorPatchUi]:
        for workspace in [i for i in self.workspace_manager.workspaces.values() if i is not None]:
            patch_ui = next((i for i in workspace.box.children if i.patch is patch), None)
            if patch_ui:
                return patch_ui
        return None

    def open_context_menu(self, pos: tuple):
        pass

    def _create_context_menu(self) -> ContextMenu:
        return None
        return ContextMenu(items=[
            ContextMenuItem(
                widget_class=ContextMenuButton,
                kwargs={
                    "text": "Создать плейбек",
                    "on_release": lambda _: db.playback.add_row(),
                }
            ),
            ]
        )
