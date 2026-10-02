from typing import Any, Optional

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import AliasProperty, NumericProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout

from database.fixture_param import RowFixtureParam
from database.patch import RowPatch
from libs.uix.layouts import ModalBoxLayout
from libs.uix.scroll_layout import ScrollLayout

Builder.load_file("ui/components/patch_ui/patch_mapper.kv")


class PatchMapperMenuChannel(BoxLayout):
    patch: RowPatch = ObjectProperty()
    index: int = NumericProperty()
    fixture_param: RowFixtureParam = ObjectProperty()

    def remap_to(self, value: Optional[int]):
        if value is None:
            self.patch.remap(self.index, value)
        else:
            self.patch.remap(self.index, value - 1)


class PatchMapperMenu(ModalBoxLayout):
    patch: RowPatch = ObjectProperty()
    scroll_layout: ScrollLayout = ObjectProperty()

    def on_open(self):
        self.scroll_layout.scrollview.data = [
            {
               "patch": self.patch,
               "index": i,
               "fixture_param": self.patch.param_list_unpacked[i]
            } for i in self.patch.mapper.keys()
        ]
