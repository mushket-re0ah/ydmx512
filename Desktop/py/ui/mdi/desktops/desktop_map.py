from typing import TYPE_CHECKING

from kivy.lang import Builder

from libs.uix.map_layout import WorkspaceMapLayout

if TYPE_CHECKING:
    from ui.mdi.desktops.map_context_menu import DesktopMapContextMenu

Builder.load_string("""
#:import constants misc.constants

<DesktopMap>:
    cell_size: constants.MAP_LAYOUT_CELL_SIZE
    max_grid_size: constants.MAP_LAYOUT_MAX_GRID_SIZE
    grid_padding: constants.MAP_LAYOUT_GRID_PADDING
    grid_spacing: constants.MAP_LAYOUT_GRID_SPACING
"""
)


class DesktopMap(WorkspaceMapLayout):
    def _create_context_menu(self) -> "DesktopMapContextMenu":
        from ui.mdi.desktops.map_context_menu import DesktopMapContextMenu
        return DesktopMapContextMenu(desktop_map=self)
