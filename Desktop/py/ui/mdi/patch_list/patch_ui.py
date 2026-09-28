from kivy.lang.builder import Builder
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from ui.components.patch_ui import BasePatchUi


Builder.load_file("ui/mdi/patch_list/patch_ui.kv")


class PatchUi(BasePatchUi):
    btn_remove = ObjectProperty()
    btn_add = ObjectProperty()

    def __init__(self, **kwargs):
        self.trigger_save_pos = Clock.create_trigger(self._save_pos, 0)
        self.bind(grid_pos=self.trigger_save_pos)
        super().__init__(selectable=True, **kwargs)
