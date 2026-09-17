from kivy.lang.builder import Builder
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from ui.components.scroll_layout_map import SelectableBehavior
from ui.components.patch_ui import BasePatchUi
from ui.components.scroll_layout_map import SelectableBehavior


Builder.load_file("ui/mdi/patch_list/patch_ui.kv")


class PatchUi(SelectableBehavior, BasePatchUi):
    btn_remove = ObjectProperty()
    btn_add = ObjectProperty()

    trigger_save_pos = None
    def __init__(self, create_animation=True, **kwargs):
        self.trigger_save_pos = Clock.create_trigger(self._save_pos, 0)
        self.bind(
            grid_x=self.trigger_save_pos,
            grid_y=self.trigger_save_pos,
        )
        super().__init__(**kwargs)

    def _save_pos(self, _):
        self.patch.edit(grid_pos=[self.grid_x, self.grid_y])

    def on_self_destroy(self, *args):
        self.unselect()
        self.parent.remove_widget(self)

    def _check_allow_move_widget(self, widget) -> bool:
        if widget is self:
            return True
        if widget in {
                self.input_start_address, self.input_universe, self.input_title,
                self.button_pan, self.button_tilt, self.btn_remove, self.btn_add,
                self.toggle_controller
            }:
            return False
        elif widget in (self.lbl_addr_info, self.image_fixture):
            return True
        else:
            raise ValueError(f"unexpected widget {widget}")
