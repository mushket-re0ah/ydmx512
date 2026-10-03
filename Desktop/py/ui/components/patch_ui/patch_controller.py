from typing import Any

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import AliasProperty, NumericProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout

import libs.uix.menu_components  # lazy kv import initialize  # noqa: F401
from database.fixture_param import RowFixtureParam
from database.patch import RowPatch
from libs.dmx512 import dmx512
from libs.uix import slider  # lazy kv import initialize  # noqa: F401
from libs.uix.layouts import ModalBoxLayout
from libs.uix.scroll_layout import ScrollLayout

Builder.load_file("ui/components/patch_ui/patch_controller.kv")


class PatchControllerMenuChannel(BoxLayout):
    patch: RowPatch = ObjectProperty()
    fixture_param: RowFixtureParam = ObjectProperty()
    index: int = NumericProperty()
    value: int = NumericProperty()

    universe = AliasProperty(lambda self: self.patch.universe)
    address = AliasProperty(lambda self: self.patch.start_address + self.index)

    def __init__(self, *args: Any, **kwargs: Any):
        self._update_trigger = Clock.create_trigger(self.update, -1)
        super().__init__(*args, **kwargs)
        self.bind(
            patch=self._update_trigger,
            fixture_param=self._update_trigger,
            index=self._update_trigger,
            value=self._update_trigger,
        )

    def update(self, _:float):
        self.value = dmx512.get_value(self.universe, self.address)
        self.disabled = dmx512.check_address_force(self.universe, self.address)

    def on_value(self, _, value: int):
        dmx512.set_value(self.patch.universe, self.patch.start_address + self.index, value)


class PatchControllerMenu(ModalBoxLayout):
    patch: RowPatch = ObjectProperty()
    scroll_layout: ScrollLayout = ObjectProperty()

    def on_open(self):
        self.scroll_layout.scrollview.data = [
            {
               "patch": self.patch,
               "index": i,
               "fixture_param": fixture_param
            } for i, fixture_param in enumerate(self.patch.param_list_unpacked)
        ]
