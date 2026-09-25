from kivy.properties import ObjectProperty, AliasProperty
from kivy.lang import Builder
from libs.uix.layouts import SectionPanel
from libs.uix.workspace_manager import WorkspaceBehavior
from ui.mdi.patch_list.patch_ui import PatchUi
from database.scene import RowScene
from collections import defaultdict
from database import db
from database.patch import RowPatch
from typing import List, Optional
from libs.kivy_utils import AutoUnbindBehavior
from libs import logger


Builder.load_file("ui/mdi/patch_list/patch_map_section.kv")


class PatchMapSection(AutoUnbindBehavior, SectionPanel):
    patch_list = ObjectProperty()
    workspace_manager = ObjectProperty()

    selected = AliasProperty(lambda self: self.workspace_manager.workspace_now.selected)

    workspace_now = None
    def on_kv_post(self, _):
        self.workspace_now = self.workspace_manager.workspace_now
        self.bind_to(self.workspace_now, selected=self._dispatch_selected)
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

    def _dispatch_selected(self, _, selected: List[PatchUi]):
        self.property("selected").dispatch(self)

    def on_workspace_opened(self, _, workspace_index: int, workspace: WorkspaceBehavior):
        self.unbind_from(self.workspace_now)
        self.workspace_now = workspace
        self.bind_to(workspace, selected=self._dispatch_selected)
        self.property("selected").dispatch(self)
        self.patch_list.workspace = workspace_index

    def on_add_patch(self, _, patch: RowPatch):
        workspace = self.workspace_manager.create_workspace(patch.workspace)
        workspace.add_widget(PatchUi(
                patch_map=workspace,
                patch=patch
            )
        )

    def on_remove_patch(self, _, patch: RowPatch):
        workspace = self.workspace_manager.workspace_now
        patch_ui = next((i for i in workspace.grid_items if i.patch is patch), None)
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

    def add_address_to_selected(self, value: int):
        for widget in self.selected:
            widget.patch.edit(start_address=widget.patch.start_address + value)

    def set_universe_to_selected(self, value: int):
        for widget in self.selected:
            widget.patch.edit(universe=value)

    def set_workspace_to_selected(self, value: int):
        for widget in self.selected:
            widget.patch.edit(workspace=value - 1)

    def remove_selected(self):
        for widget in self.selected:
            widget.patch.remove()

    def invert_pan_selected(self):
        for widget in self.selected:
            widget.patch.edit(invert_pan=not widget.patch.invert_pan)

    def invert_tilt_selected(self):
        for widget in self.selected:
            widget.patch.edit(invert_tilt=not widget.patch.invert_tilt)

    def __init_workspace_manager(self):
        wm = self.workspace_manager
        for workspace in wm.workspaces.values():
            if workspace:
                workspace.clear_widgets()

        grouped = defaultdict(list)
        for item in db.patch.rows.values():
            key = item.workspace
            grouped[key].append(item)

        for workspace_index, patch_list in grouped.items():
            workspace = wm.create_workspace(workspace_index)
            for patch in patch_list:
                workspace.add_widget(PatchUi(
                        create_animation=False,
                        patch_map=workspace,
                        patch=patch
                    )
                )
        wm.set_workspace(self.patch_list.workspace)

    def get_patch_ui_by_row_patch(self, patch: RowPatch) -> Optional[PatchUi]:
        for workspace in [i for i in self.workspace_manager.workspaces.values() if i is not None]:
            patch_ui = next((i for i in workspace.grid_items if i.patch is patch), None)
            if patch_ui:
                return patch_ui
        return None
