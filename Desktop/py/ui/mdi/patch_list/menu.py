from kivy.properties import ObjectProperty
from kivy.lang import Builder
from libs.uix.layouts import MenuPanel


Builder.load_file("ui/mdi/patch_list/menu.kv")


class PatchListMenu(MenuPanel):
    patch_list = ObjectProperty()
    patch_map = ObjectProperty()

    input_count_create_patch = ObjectProperty()
    input_address_create_patch = ObjectProperty()
    input_universe_create_patch = ObjectProperty()
    input_fixture = ObjectProperty()
    input_add_address = ObjectProperty()
    input_set_universe = ObjectProperty()
    input_set_workspace = ObjectProperty()

    def create_patch(self):
        self.patch_list.create_patch(
            self.input_fixture.selected,
            self.input_count_create_patch.value,
            self.input_universe_create_patch.value,
            self.input_address_create_patch.value,
        )
