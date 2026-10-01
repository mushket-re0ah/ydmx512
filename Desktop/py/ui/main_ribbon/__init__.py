from typing import TYPE_CHECKING, Callable, Dict, FrozenSet, List, Type

from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from libs.sdl2_keyboard import KeyboardBehavior
from libs.uix.button import ImageToggleButton
from libs.uix.layouts import SectionPanel
from libs.uix.mdi.mdi_window import MDIWindow
from libs.uix.overflow_layout import OverflowLayout
from misc import imgs_path
from ui.main_ribbon.midi_devices import MidiDevices  # lazy kv import initialize
from ui.main_ribbon.scene_dimmer import SceneDimmer  # lazy kv import initialize
from ui.main_ribbon.scene_temp import SceneTemp  # lazy kv import initialize
from ui.main_ribbon.serial_devices import SerialDevices  # lazy kv import initialize
from ui.mdi.checker import MDIChecker
from ui.mdi.desktops import MDIDesktops
from ui.mdi.editor import MDIEditor
from ui.mdi.library import MDILibrary
from ui.mdi.monitor import MDIMonitor
from ui.mdi.patch_list import MDIPatchList
from ui.mdi.processing import MDIProcessing
from ui.mdi.scenes import MDIScenes
from ui.mdi.settings import MDISettings

if TYPE_CHECKING:
    from ui.components.database_workspace_mdi_container_manager import DatabaseWorkspaceMDIContainerManager


Builder.load_file("ui/main_ribbon/main_ribbon.kv")


class MDIToggleButton(ImageToggleButton):
    """Управляет показом/скрытием MDI окон. Синхронизирован с состоянием
    конкретного окна."""
    mdi_container_manager: "DatabaseWorkspaceMDIContainerManager" = ObjectProperty()
    mdi: MDIWindow = ObjectProperty()

    def on_kv_post(self, base_widget: Widget):
        self.mdi.bind(hidden=self._set_state_by_mdi)
        self._set_state_by_mdi(self.mdi, self.mdi.hidden)

    def _set_state_by_mdi(self, mdi: MDIWindow, hidden: bool):
        self.state = "normal" if hidden else "down"

    def on_state(self, _, state: str):
        if not self.mdi_container_manager._database_loaded:
            return
        if state == "down":
            self.mdi_container_manager.show_mdi(self.mdi)
        elif state == "normal":
            self.mdi_container_manager.hide_mdi(self.mdi)


class MDIMenuRibbonBox(KeyboardBehavior, OverflowLayout):
    """Меню, содержащее MDIToggleButton. Учитывает переполнение размера, и в
    случае переполнения создает выпадающий список с невлезающими MDI"""
    mdi_container_manager: "DatabaseWorkspaceMDIContainerManager" = ObjectProperty()

    def init(self, mdi_container_manager: "DatabaseWorkspaceMDIContainerManager"):
        self.mdi_container_manager = mdi_container_manager
        self.mdi_list: List[MDIWindow] = []
        for mdi_cls in (
                MDIProcessing, MDIEditor, MDIPatchList, MDILibrary,
                MDIChecker, MDIMonitor, MDIScenes, MDIDesktops
            ):
            mdi_id = mdi_cls._db_title_id
            mdi = self.create_mdi(mdi_cls, mdi_id)
            self.add_widget(self.create_toggle(mdi, mdi_id))
            self.mdi_list.append(mdi)
        self.register_keyboard_context()

    def create_hotkeys(self) -> Dict[FrozenSet[str], Callable[[], None]]:
        return {
            frozenset({f"F{i + 1}"}): lambda mdi=mdi: self.toggle_mdi(mdi)
            for i, mdi in enumerate(self.mdi_list)
        }

    def toggle_mdi(self, mdi: MDIWindow):
        if mdi.hidden:
            self.mdi_container_manager.show_mdi(mdi)
        else:
            self.mdi_container_manager.hide_mdi(mdi)

    def create_mdi(self, mdi_cls: Type[MDIWindow], mdi_id: str) -> MDIWindow:
        mdi = mdi_cls(hidden=True)
        setattr(self, mdi_id, mdi)
        return mdi

    def create_toggle(self, mdi: MDIWindow, mdi_id: str) -> MDIToggleButton:
        icon_normal = getattr(imgs_path, f"{mdi_id}_normal")
        icon_down = getattr(imgs_path, f"{mdi_id}_down")
        return MDIToggleButton(
            mdi_container_manager=self.mdi_container_manager,
            mdi=mdi,
            background_normal=icon_normal,
            background_down=icon_down
        )


class MDIMenuRibbon(SectionPanel):
    box: MDIMenuRibbonBox = ObjectProperty()


class MainRibbon(BoxLayout):
    mdi_container_manager: "DatabaseWorkspaceMDIContainerManager" = ObjectProperty()

    mdi_menu: MDIMenuRibbon = ObjectProperty()
    scene_temp: SceneTemp = ObjectProperty()
    scene_dimmer: SceneDimmer = ObjectProperty()
    serial_devices: SerialDevices = ObjectProperty()
    midi_devices: MidiDevices = ObjectProperty()
    settings: MDISettings = ObjectProperty()

    def on_kv_post(self, base_widget: Widget):
        self.mdi_menu.box.init(self.mdi_container_manager)
        mdi_cls = MDISettings
        mdi_id = mdi_cls._db_title_id
        mdi = self.mdi_menu.box.create_mdi(mdi_cls, mdi_id)
        self.settings = mdi
        self.mdi_menu.box.mdi_list.append(mdi)
        toggle = self.mdi_menu.box.create_toggle(mdi, mdi_id)
        self.add_widget(toggle)
        self.mdi_list = self.mdi_menu.box.mdi_list
