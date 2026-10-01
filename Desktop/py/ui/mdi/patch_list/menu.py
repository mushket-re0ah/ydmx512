from kivy.lang import Builder
from kivy.properties import ObjectProperty

from libs.uix.input import NumericInput
from libs.uix.layouts import MenuPanel
from libs.uix.snippet import Snippet
from ui.mdi.patch_list import MDIPatchList
from ui.mdi.patch_list.patch_map import PatchMap

Builder.load_file("ui/mdi/patch_list/menu.kv")


class PatchListMenu(MenuPanel):
    patch_list: MDIPatchList = ObjectProperty()
    patch_map: PatchMap = ObjectProperty()

    input_count_create_patch: NumericInput = ObjectProperty()
    input_address_create_patch: NumericInput = ObjectProperty()
    input_universe_create_patch: NumericInput = ObjectProperty()
    input_fixture: Snippet = ObjectProperty()
    input_add_address: NumericInput = ObjectProperty()
    input_set_universe: NumericInput = ObjectProperty()
    input_set_workspace: NumericInput = ObjectProperty()

    def create_patch(self):
        self.patch_list.create_patch(
            self.input_fixture.selected,
            self.input_count_create_patch.value,
            self.input_universe_create_patch.value,
            self.input_address_create_patch.value,
        )
