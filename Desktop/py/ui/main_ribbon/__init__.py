from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from libs.uix.mdi.mdi_window import MDIWindow
from libs.uix.button import ImageToggleButton, HoverToggleButton
from libs.uix.overflow_layout import OverflowLayout
from kivy.properties import ObjectProperty, BooleanProperty, ListProperty
from kivy.clock import Clock
from typing import List, Optional
import ui.main_ribbon.scene_temp
import ui.main_ribbon.serial_devices
import ui.main_ribbon.midi_devices
from ui.mdi.processing import MDIProcessing
from ui.mdi.editor import MDIEditor
from ui.mdi.patch_list import MDIPatchList
from ui.mdi.library import MDILibrary
from ui.mdi.checker import MDIChecker
from ui.mdi.monitor import MDIMonitor
from ui.mdi.scenes import MDIScenes
from ui.mdi.desktops import MDIDesktops
from ui.mdi.settings import MDISettings
from misc import imgs_path
from libs.sdl2_keyboard import KeyboardBehavior, KeyboardInputContext
from database import db


class MDIToggleButton(ImageToggleButton):
    """Управляет показом/скрытием MDI окон. Синхронизирован с состоянием
    конкретного окна."""
    mdi_container_manager = ObjectProperty()
    mdi = ObjectProperty()

    def on_kv_post(self, _):
        self.mdi.bind(hidden=self._set_state_by_mdi)
        self._set_state_by_mdi(self.mdi, self.mdi.hidden)

    def _set_state_by_mdi(self, _, hidden: bool):
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
    mdi_container_manager = ObjectProperty()

    def init(self, mdi_container_manager):
        self.mdi_container_manager = mdi_container_manager
        self.mdi_list = []
        for mdi_cls in (
                MDIProcessing, MDIEditor, MDIPatchList, MDILibrary,
                MDIChecker, MDIMonitor, MDIScenes, MDIDesktops
            ):
            mdi_id = mdi_cls._db_title_id
            mdi = self.create_mdi(mdi_cls, mdi_id)
            self.add_widget(self.create_toggle(mdi, mdi_id))
            self.mdi_list.append(mdi)
        self.register_keyboard_context()

    def create_hotkeys(self) -> Optional[dict]:
        return {
            frozenset({f"F{i + 1}"}): lambda mdi=mdi: self.toggle_mdi(mdi)
            for i, mdi in enumerate(self.mdi_list)
        }

    def toggle_mdi(self, mdi: MDIWindow):
        if mdi.hidden:
            self.mdi_container_manager.show_mdi(mdi)
        else:
            self.mdi_container_manager.hide_mdi(mdi)

    def create_mdi(self, mdi_cls: "class MDIWindow", mdi_id: str) -> MDIWindow:
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


class MainRibbon(BoxLayout):
    mdi_container_manager = ObjectProperty()

    mdi_menu = ObjectProperty()
    scene_dimmer = ObjectProperty()
    serial_devices = ObjectProperty()
    midi_devices = ObjectProperty()
    settings = ObjectProperty()

    def on_kv_post(self, _):
        mdi = self.mdi_menu.box.init(self.mdi_container_manager)
        mdi_cls = MDISettings
        mdi_id = mdi_cls._db_title_id
        mdi = self.mdi_menu.box.create_mdi(mdi_cls, mdi_id)
        self.settings = mdi
        self.mdi_menu.box.mdi_list.append(mdi)
        toggle = self.mdi_menu.box.create_toggle(mdi, mdi_id)
        self.add_widget(toggle)
        self.mdi_list = self.mdi_menu.box.mdi_list
