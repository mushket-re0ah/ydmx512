from kivy.properties import ObjectProperty
from libs.uix.layouts import ModalBoxLayout
import libs.uix.menu_components
from database.patch import RowPatch
from kivy.lang import Builder


Builder.load_file("ui/components/patch_ui/patch_context_menu.kv")


class PatchContextMenu(ModalBoxLayout):
    patch: RowPatch = ObjectProperty()
    grid_box = ObjectProperty()
    toggle_invert_pan = ObjectProperty()
    label_invert_pan = ObjectProperty()
    toggle_invert_tilt = ObjectProperty()
    label_invert_tilt = ObjectProperty()
    input_correction_pan = ObjectProperty()
    label_correction_pan = ObjectProperty()
    input_correction_tilt = ObjectProperty()
    label_correction_tilt = ObjectProperty()

    def on_kv_post(self, _):
        if not self.patch.fixture.is_dynamic:
            self.grid_box.remove_widget(self.toggle_invert_pan)
            self.grid_box.remove_widget(self.label_invert_pan)
            self.grid_box.remove_widget(self.toggle_invert_tilt)
            self.grid_box.remove_widget(self.label_invert_tilt)
            self.grid_box.remove_widget(self.input_correction_pan)
            self.grid_box.remove_widget(self.label_correction_pan)
            self.grid_box.remove_widget(self.input_correction_tilt)
            self.grid_box.remove_widget(self.label_correction_tilt)

    def copy(self):
        self.patch.copy(grid_pos=[None, None])
        self.dismiss()

    def remove(self):
        self.patch.remove()
        self.dismiss()
