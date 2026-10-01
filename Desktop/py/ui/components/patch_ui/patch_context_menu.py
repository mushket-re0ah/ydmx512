from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget

from database.patch import RowPatch
from libs.uix.layouts import ModalBoxLayout
from libs.uix.menu_components import MenuLabel, MenuNumericInput, MenuToggleButton

Builder.load_file("ui/components/patch_ui/patch_context_menu.kv")


class PatchContextMenu(ModalBoxLayout):
    patch: RowPatch = ObjectProperty()
    grid_box: GridLayout = ObjectProperty()
    toggle_invert_pan: MenuToggleButton = ObjectProperty()
    label_invert_pan: MenuLabel = ObjectProperty()
    toggle_invert_tilt: MenuToggleButton = ObjectProperty()
    label_invert_tilt: MenuLabel = ObjectProperty()
    input_correction_pan: MenuNumericInput = ObjectProperty()
    label_correction_pan: MenuLabel = ObjectProperty()
    input_correction_tilt: MenuNumericInput = ObjectProperty()
    label_correction_tilt: MenuLabel = ObjectProperty()

    def on_kv_post(self, base_widget: Widget):
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
