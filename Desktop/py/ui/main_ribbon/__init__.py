from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from ui.components.mdi_window import MDIWindow
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

    main_ribbon = ObjectProperty()
    mdi = ObjectProperty()
    hidden = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mdi.bind(on_close=self.on_mdi_close, on_open=self.on_mdi_open)

    def on_mdi_close(self, mdi: MDIWindow):
        self.is_down = False

    def on_mdi_open(self, mdi: MDIWindow):
        self.is_down = True

    def on_is_down(self, _, is_down):
        if is_down:
            self.mdi.open()
        else:
            self.mdi.close()


class MDIMenuRibbonBox(KeyboardBehavior, OverflowLayout):
    """Меню, содержащее MDIToggleButton. Учитывает переполнение размера, и в
    случае переполнения создает выпадающий список с невлезающими MDI"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
            frozenset({f"F{i + 1}"}): lambda mdi=mdi: mdi.invert_hidden()
            for i, mdi in enumerate(self.mdi_list)
        }

    def create_mdi(self, mdi_cls: "class MDIWindow", mdi_id: str) -> MDIWindow:
        mdi_db_row = db.mdi_window.by_title_id(mdi_id)
        if mdi_db_row is None:
            mdi_db_row = db.mdi_window.add_row(title_id=mdi_cls._db_title_id)
        mdi = mdi_cls(mdi_db_row=mdi_db_row)
        setattr(App.get_running_app(), mdi_id, mdi)
        setattr(self, mdi_id, mdi)
        return mdi

    def create_toggle(self, mdi: MDIWindow, mdi_id: str) -> MDIToggleButton:
        icon_normal = getattr(imgs_path, f"{mdi_id}_normal")
        icon_down = getattr(imgs_path, f"{mdi_id}_down")
        return MDIToggleButton(
            main_ribbon=self,
            mdi=mdi,
            background_normal=icon_normal,
            background_down=icon_down
        )


class MainRibbon(BoxLayout):
    mdi_menu = ObjectProperty()
    scene_dimmer = ObjectProperty()
    serial_devices = ObjectProperty()
    midi_devices = ObjectProperty()
    settings = ObjectProperty()

    def on_kv_post(self, _):
        mdi_cls = MDISettings
        mdi_id = mdi_cls._db_title_id
        mdi = self.mdi_menu.box.create_mdi(mdi_cls, mdi_id)
        self.settings = mdi
        toggle = self.mdi_menu.box.create_toggle(mdi, mdi_id)
        self.add_widget(toggle)
