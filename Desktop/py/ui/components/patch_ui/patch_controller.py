from typing import Any, Optional, TypedDict

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import AliasProperty, NumericProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.widget import Widget

import libs.uix.menu_components  # lazy kv import initialize  # noqa: F401
from database import db
from database.fixture_param import DIMMER_TITLE_ID, RowFixtureParam
from database.patch import RowPatch
from libs.dmx512 import dmx512
from libs.properties import BindableObjectProperty
from libs.uix import slider  # lazy kv import initialize  # noqa: F401
from libs.uix.input.numeric_input import NumericInput
from libs.uix.layouts import ModalBoxLayout
from libs.uix.recycle_restricted_scrollview import RecycleRestrictedScrollView
from libs.uix.scroll_layout import ScrollLayout
from ui.components.clamped_dimmer_slider import ClampedDimmerSlider

Builder.load_file("ui/components/patch_ui/patch_controller.kv")


class _PatchControllerViewDataDict(TypedDict):
    patch: RowPatch
    index: int
    fixture_param: RowFixtureParam


class PatchControllerMenuChannel(RecycleDataViewBehavior, BoxLayout):
    mapper_input: NumericInput = ObjectProperty()
    dmx_input: NumericInput = ObjectProperty()
    dmx_slider: ClampedDimmerSlider = ObjectProperty()

    patch: Optional[RowPatch] = BindableObjectProperty(
        None,
        allownone=True,
        bind={
            "mapper": "on_patch_mapper",
            "param_list_unpacked": "on_param_list_unpacked",
        }
    )
    fixture_param: Optional[RowFixtureParam] = ObjectProperty()
    index: Optional[int] = NumericProperty()
    value: int = NumericProperty()

    universe: Optional[int] = NumericProperty(allownone=True)
    address: Optional[int] = NumericProperty(allownone=True)

    mapper_value: Optional[int] = NumericProperty(allownone=True)
    mapped_address: Optional[int] = NumericProperty(allownone=True)
    mapped_fixture_param: Optional[RowFixtureParam] = ObjectProperty(allownone=True)

    maximum_value: int = NumericProperty(255, rebind=True)
    _allow_write: bool = False
    _allow_read: bool = True

    def on_kv_post(self, base_widget: Widget):
        self.trigger_recalc_mapped_values = Clock.create_trigger(self._recalc_mapped_values, 0)
        super().on_kv_post(base_widget)
        db.scene.bind(scene_now_dimmer=self.update)

    def _recalc_mapped_values(self, *_:Any):
        if self.patch is not None and self.index is not None:
            self.universe = self.patch.universe
            self.address = self.patch.start_address + self.index
            self.mapper_value = self.patch.get_mapper_value(self.index)
        else:
            self.mapper_value = None

        if self.mapper_value is not None and self.patch is not None:
            self.mapped_address = self.mapper_value + self.patch.start_address
            self.mapped_fixture_param = self.patch.param_list_unpacked[self.mapper_value]
        else:
            self.mapped_address = None
            self.mapped_fixture_param = None

        self.update()

    def on_patch(self, *_:Any):
        self.trigger_recalc_mapped_values()

    def on_index(self, *_:Any):
        self.trigger_recalc_mapped_values()

    def on_mapper_value(self, *_:Any):
        self.trigger_recalc_mapped_values()

    def on_param_list_unpacked(self, *_:Any):
        self.trigger_recalc_mapped_values()

    def on_patch_mapper(self, *_:Any):
        self._allow_read = False
        self._allow_write = False
        self.trigger_recalc_mapped_values()

    def remap_to(self, value: Optional[int]):
        if not self._allow_write or self.patch is None or self.index is None:
            return
        if value is not None:
            value -= 1
        self.patch.remap(self.index, value)

    def update(self, *_:Any):
        if self.fixture_param is not None:
            if self.mapped_address is not None and self.universe is not None:
                if self._allow_read:
                    self.value = dmx512.get_value(self.universe, self.mapped_address)
            if self.mapped_fixture_param is not None:
                if self.mapped_fixture_param.title_id == DIMMER_TITLE_ID:
                    self.maximum_value = int(255 * db.scene.scene_now_dimmer / 100)
                else:
                    self.maximum_value = 255
                value_track_color = self.mapped_fixture_param.color
            else:
                self.maximum_value = 255
                value_track_color = self.fixture_param.color
            self.dmx_slider.property("value_track_color").set_normal(
                self.dmx_slider,
                value_track_color
            )
        if self.universe is not None and self.mapped_address is not None:
            disabled = (
                dmx512.check_address_force(self.universe, self.mapped_address) or
                self.maximum_value == 0 or
                self.mapper_value is None
            )
            self.dmx_input.disabled = disabled
            self.dmx_slider.disabled = disabled
        self._allow_write = True
        self._allow_read = True

    def refresh_view_attrs( # pyright: ignore[reportIncompatibleMethodOverride]
            self,
            rv: RecycleRestrictedScrollView,
            index: int,
            data: _PatchControllerViewDataDict
        ):
        self._allow_write = False
        super().refresh_view_attrs(rv, index, data)  # pyright: ignore[reportArgumentType]
        self.trigger_recalc_mapped_values()
        self._allow_write = True

    def on_value(self, _, value: int):
        if not self._allow_write:
            return
        if self.mapped_address is None or self.patch is None:
            return
        dmx512.set_value(self.patch.universe, self.mapped_address, value)


class PatchControllerMenu(ModalBoxLayout):
    patch: RowPatch = ObjectProperty()
    scroll_layout: ScrollLayout = ObjectProperty()

    def on_open(self):
        self.scroll_layout.scrollview.data = [
            _PatchControllerViewDataDict({
               "patch": self.patch,
               "index": i,
               "fixture_param": fixture_param
            }) for i, fixture_param in enumerate(self.patch.param_list_unpacked)
        ]
