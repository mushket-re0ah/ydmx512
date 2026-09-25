from kivy.properties import ObjectProperty, AliasProperty
from libs.uix.layouts import SectionPanel
from libs.uix.workspace_manager import WorkspaceBehavior
from libs.uix.button import HoverToggleButton
from ui.mdi.desktops.desktop_uix import DesktopUix
from ui.mdi.desktops.desktop_rotary import DesktopRotaryUix
from ui.mdi.desktops.desktop_slider_2d import DesktopSlider2D
from database.scene import RowScene
from kivy.uix.widget import Widget
from collections import defaultdict
from database import db
from database.desktop_uix import DesktopUixType, RowDesktopUix
from typing import List, Tuple
from kivy.lang import Builder


Builder.load_file("ui/mdi/desktops/desktop_map_section.kv")


widget_to_desktop_uix_type = {
    DesktopRotaryUix: DesktopUixType.rotary_button,
    DesktopSlider2D: DesktopUixType.slider2d
}


desktop_uix_type_to_widget = {
    DesktopUixType.rotary_button: DesktopRotaryUix,
    DesktopUixType.slider2d: DesktopSlider2D
}


class MapFreezeToggleDesktop(HoverToggleButton):
    desktop_map_section = ObjectProperty()


class DesktopMapSection(SectionPanel):
    desktops = ObjectProperty()
    workspace_manager = ObjectProperty()
    freeze_toggle = ObjectProperty()

    workspace_now = None
    def on_kv_post(self, _):
        self.workspace_manager.menu.add_widget(Widget(size_hint=(1, 1)))
        self.freeze_toggle = MapFreezeToggleDesktop(desktop_map_section=self)
        self.workspace_manager.menu.add_widget(self.freeze_toggle)

        self.workspace_now = self.workspace_manager.workspace_now
        self.workspace_now.bind(selected=self._dispatch_selected)
        self.workspace_manager.bind(on_workspace_opened=self.on_workspace_opened)
        self.__init_workspace_manager()
        db.desktop_uix.bind(
            on_add_row=self.on_add_desktop_uix,
            on_remove_row=self.on_remove_desktop_uix,
            on_scene_change=self.on_scene_change
        )
        self.on_workspace_opened(
            self.workspace_manager,
            self.workspace_manager.workspace_now_index,
            self.workspace_manager.workspace_now
        )

    freeze = AliasProperty(lambda self: self.freeze_toggle.is_down)
    selected = AliasProperty(lambda self: self.workspace_manager.workspace_now.selected, cache=True)

    def _get_desktop_uix_list_by_hotkey(self, key: str) -> Tuple[RowDesktopUix]:
        return (ui.desktop_uix for ui in self.workspace_now.layout.children
                    if ui.desktop_uix.player.hotkey == key)

    key_down = set()
    def on_key_down(self, key: str):
        if key in self.key_down:
            return
        self.key_down.add(key)
        for desktop_uix in self._get_desktop_uix_list_by_hotkey(key):
            desktop_uix.active = not desktop_uix.active

    def on_key_up(self, key: str):
        if key in self.key_down:
            self.key_down.remove(key)
        for desktop_uix in self._get_desktop_uix_list_by_hotkey(key):
            if desktop_uix.player.is_moment:
                desktop_uix.active = False

    def _dispatch_selected(self, _, selected: List[DesktopUix]):
        self.property("selected").dispatch(self)

    def on_workspace_opened(self, _, workspace_index: int, workspace: WorkspaceBehavior):
        self.workspace_now.unbind(selected=self._dispatch_selected)
        self.workspace_now = workspace
        workspace.bind(selected=self._dispatch_selected)
        self.property("selected").dispatch(self)

    def on_add_desktop_uix(self, _, desktop_uix: RowDesktopUix):
        workspace = self.workspace_manager.create_workspace(desktop_uix.workspace)
        workspace.add_widget(
            self._create_desktop_uix(desktop_uix, workspace)
        )

    def _create_desktop_uix(
            self,
            desktop_uix: RowDesktopUix,
            workspace: WorkspaceBehavior,
            create_animation=True) -> RowDesktopUix:
        return desktop_uix_type_to_widget[desktop_uix.uix_type](
            create_animation=create_animation,
            desktop_uix=desktop_uix,
            desktop_map=workspace,
        )

    def on_remove_desktop_uix(self, _, desktop_uix: RowDesktopUix):
        workspace = self.workspace_manager.workspace_now
        desktop_uix_ui = next((i for i in workspace.layout.children if i.desktop_uix is desktop_uix), None)
        if desktop_uix_ui is not None:
            desktop_uix_ui._self_destroy()

    def on_scene_change(self, table, old_scene: RowScene, new_scene: RowScene):
        self.__init_workspace_manager()

    def __init_workspace_manager(self):
        wm = self.workspace_manager
        for workspace in wm.workspaces.values():
            if workspace:
                workspace.clear_widgets()

        grouped = defaultdict(list)
        for item in db.desktop_uix.rows.values():
            key = item.workspace
            grouped[key].append(item)

        for workspace_index, desktop_uix_list in grouped.items():
            workspace = wm.create_workspace(workspace_index)
            for desktop_uix in desktop_uix_list:
                workspace.add_widget(
                    self._create_desktop_uix(desktop_uix, workspace, create_animation=False)
                )
        # wm.set_workspace(self.view_context.workspace)
