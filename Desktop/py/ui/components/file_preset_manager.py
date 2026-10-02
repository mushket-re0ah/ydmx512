from pathlib import Path
from typing import Any, Tuple

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ObjectProperty, StringProperty
from kivy.uix.widget import Widget

from libs.asset_manager import FileAssetManager
from libs.serialize import SerializableMixin
from libs.uix.filelist import Filelist
from libs.uix.layouts import ModalBoxLayout, WindowModalBoxLayout

Builder.load_file("ui/components/file_preset_manager.kv")


class FilePresetModal(WindowModalBoxLayout):
    asset_manager: FileAssetManager = ObjectProperty()
    category_key: Any = ObjectProperty()
    title_collision: bool = BooleanProperty(False)
    title: str = StringProperty("")
    _save_error: bool = BooleanProperty(False)
    _time_save_error_discard: float = 2.5

    title_preset_list: Tuple[str, ...]
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        preset_list = self.asset_manager.get_asset_list(self.category_key)
        self.title_preset_list = tuple(i.title for i in preset_list)
        self.register_event_type("on_save_success")

    def on_save_success(self):
        pass

    def on_title(self, _, preset_title: str):
        self.title_collision = preset_title in self.title_preset_list

    def on_ok(self):
        if not self.title:
            return
        preset = self.create_preset()
        if self.asset_manager.add_asset(self.category_key, preset):
            self.dispatch("on_save_success")
            self.dismiss()
        else:
            self._save_error = True
            Clock.schedule_once(self._discard_save_error, self._time_save_error_discard)

    def create_preset(self) -> Any:
        raise NotImplementedError()

    def _discard_save_error(self, _: Any):
        self._save_error = False


class MenuPresetManager(ModalBoxLayout):
    title: str = StringProperty("BLANK")
    asset_manager: FileAssetManager = ObjectProperty()
    category_key: Any = ObjectProperty()
    filelist: Filelist = ObjectProperty()
    allow_create_preset: bool = BooleanProperty(False)

    def on_kv_post(self, base_widget: Widget):
        rootpath = self.asset_manager.get_asset_dirname(self.category_key)
        self.filelist.rootpath = rootpath
        self.filelist.bind(on_submit=self.on_filelist_submit)

    def on_filelist_submit(self, filelist: Filelist, path: Path):
        preset = self.asset_manager.get_asset_by_path(path)
        if preset:
            self.load_preset(preset)
        self.dismiss()

    def load_preset(self, preset: SerializableMixin) -> Any:
        raise NotImplementedError()

    def save_preset(self):
        modal = self.create_modal()
        modal.bind(on_save_success=lambda modal: self.dismiss())
        modal.open(None)

    def create_modal(self) -> FilePresetModal:
        raise NotImplementedError()
