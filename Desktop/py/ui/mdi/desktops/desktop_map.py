from libs.uix.map_layout import WorkspaceMapLayout
from kivy.lang import Builder


Builder.load_string("""
#:import constants misc.constants

<DesktopMap>:
    max_grid_size: [constants.MAP_LAYOUT_MAX_SIZE, constants.MAP_LAYOUT_MAX_SIZE]
    grid_padding: [2, 2, 2, 2]
    grid_spacing: [4, 4]
"""
)


class DesktopMap(WorkspaceMapLayout):
    def _create_context_menu(self):
        from ui.mdi.desktops.map_context_menu import DesktopMapContextMenu
        return DesktopMapContextMenu(desktop_map=self)
