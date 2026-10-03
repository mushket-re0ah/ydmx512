from typing import Optional, TypedDict

from kivy.lang import Builder
from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior

from database.fixture_param import RowFixtureParam
from database.patch import RowPatch
from libs.uix.input import NumericInput
from libs.uix.layouts import ModalBoxLayout
from libs.uix.recycle_restricted_scrollview import RecycleRestrictedScrollView
from libs.uix.scroll_layout import ScrollLayout

Builder.load_file("ui/components/patch_ui/patch_mapper.kv")


class _MapperViewDataDict(TypedDict):
    patch: RowPatch
    index: int
    fixture_param: RowFixtureParam


class PatchMapperMenuChannel(RecycleDataViewBehavior, BoxLayout):
    patch: RowPatch = ObjectProperty()
    index: int = NumericProperty()
    fixture_param: RowFixtureParam = ObjectProperty()

    mapper_numeric_input: NumericInput = ObjectProperty()

    _allow_write: bool = False
    def remap_to(self, value: Optional[int]):
        if not self._allow_write:
            return
        if value is not None:
            value -= 1
        self.patch.remap(self.index, value)

    def refresh_view_attrs( # pyright: ignore[reportIncompatibleMethodOverride]
            self,
            rv: RecycleRestrictedScrollView,
            index: int,
            data: _MapperViewDataDict
        ):
        self._allow_write = False
        super().refresh_view_attrs(rv, index, data)  # pyright: ignore[reportArgumentType]
        mapper_value = data["patch"].get_mapper_value(data["index"])
        if mapper_value is not None:
            mapper_value += 1
        self.mapper_numeric_input.value = mapper_value
        self._allow_write = True


class PatchMapperMenu(ModalBoxLayout):
    patch: RowPatch = ObjectProperty()
    scroll_layout: ScrollLayout = ObjectProperty()

    def on_open(self):
        self.scroll_layout.scrollview.data = [
            _MapperViewDataDict({
               "patch": self.patch,
               "index": i,
               "fixture_param": self.patch.param_list_unpacked[i]
            }) for i in self.patch.mapper.keys()
        ]
