from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
from kivy.clock import Clock
from libs.uix.layouts import ModalBoxLayout, WindowModalBoxLayout
from pathlib import Path
from kivy.lang import Builder
from libs import logger

Builder.load_file("ui/components/file_preset_manager.kv")


class FilePresetModal(WindowModalBoxLayout):
    asset_manager = ObjectProperty()
    category_key = ObjectProperty()
    title_collision = BooleanProperty(False)
    title = StringProperty("")
    _save_error = BooleanProperty(False)
    _time_save_error_discard = 2.5

    title_preset_list = None
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        preset_list = self.asset_manager.get_asset_list(self.category_key)
        self.title_preset_list = [i.title for i in preset_list]
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

    def create_preset(self):
        raise NotImplementedError()

    def _discard_save_error(self, _):
        self._save_error = False


class MenuPresetManager(ModalBoxLayout):
    title = StringProperty("BLANK")
    asset_manager = ObjectProperty()
    category_key = ObjectProperty()
    filelist = ObjectProperty()
    allow_create_preset = BooleanProperty(False)

    def on_kv_post(self, _):
        rootpath = self.asset_manager._get_asset_dirname(self.category_key)
        self.filelist.rootpath = rootpath
        self.filelist.bind(on_submit=self.on_filelist_submit)

    def on_filelist_submit(self, filelist, path: Path):
        preset = self.asset_manager.get_asset_by_path(path)
        if preset:
            self.load_preset(preset)
        self.dismiss()

    def load_preset(self, preset):
        raise NotImplementedError()

    def save_preset(self):
        modal = self.create_modal()
        modal.bind(on_save_success=lambda modal: self.dismiss())
        modal.open(None)

    def create_modal(self) -> FilePresetModal:
        raise NotImplementedError()
