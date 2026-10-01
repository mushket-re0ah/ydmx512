from typing import TYPE_CHECKING

from kivy.lang import Builder

from libs.uix.map_layout import WorkspaceMapLayout

if TYPE_CHECKING:
    from ui.mdi.patch_list.map_context_menu import PatchMapContextMenu


Builder.load_string("""
#:import constants misc.constants

<PatchMap>:
    cell_size: constants.MAP_LAYOUT_CELL_SIZE
    max_grid_size: constants.MAP_LAYOUT_MAX_GRID_SIZE
    grid_padding: constants.MAP_LAYOUT_GRID_PADDING
    grid_spacing: constants.MAP_LAYOUT_GRID_SPACING
"""
)


class PatchMap(WorkspaceMapLayout):
    def _create_context_menu(self) -> "PatchMapContextMenu":
        from ui.mdi.patch_list.map_context_menu import PatchMapContextMenu
        return PatchMapContextMenu(patch_map=self)
