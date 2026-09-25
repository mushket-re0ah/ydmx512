from kivy.lang.builder import Builder
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from ui.components.patch_ui import BasePatchUi


Builder.load_file("ui/mdi/patch_list/patch_ui.kv")


class PatchUi(BasePatchUi):
    btn_remove = ObjectProperty()
    btn_add = ObjectProperty()

    trigger_save_pos = None
    def __init__(self, create_animation=True, **kwargs):
        self.trigger_save_pos = Clock.create_trigger(self._save_pos, 0)
        self.bind(grid_pos=self.trigger_save_pos)
        super().__init__(selectable=True, **kwargs)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        if super().on_touch_down(touch):
            return True
        if touch.button == "right":
            self._open_context_menu(touch.pos)
            return True
        return False
