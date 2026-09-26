from kivy.properties import ObjectProperty, ColorProperty
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from libs.uix.layouts import SectionPanel
from libs.uix.scroll_layout import ScrollLayout
from libs.uix.label import RestrictedLabel
from libs.properties import ClampedNumericProperty
from misc import constants
from libs.dmx512.universe import DMX512Universe
from libs.dmx512 import dmx512
from misc import colorscheme as cs
from database import db
import libs.uix.slider


Builder.load_file("ui/mdi/checker/channels_ui.kv")


class CheckerSlider(BoxLayout):
    checker = ObjectProperty()

    address = ClampedNumericProperty(1, 1, constants.DMX_ADDRESS_COUNT)
    value = ClampedNumericProperty(0, 0, 255)
    fixture_param_color = ColorProperty(cs.CheckerSlider.fixture_param_default)

    _write_allow = False

    def on_kv_post(self, _):
        prop = self.numeric.property("border_color")
        prop.set_normal(self.numeric, cs.CheckerSlider.border_color_normal)

    def on_address(self, _, address: int):
        self.update()

    def on_value(self, _, value: int):
        if self._write_allow:
            dmx512.set_value(self.checker.universe_now, self.address, value)

    def update(self):
        universe = self.checker.universe_now
        address = self.address
        self._write_allow = False
        self.value = dmx512.get_value(universe, address)
        address_info = db.patch.get_address_info(universe, address)
        if address_info is not None:
            patch, fixture_param = address_info[0]
            self.fixture_param_color = fixture_param.color
        else:
            self.fixture_param_color = cs.CheckerSlider.fixture_param_default
        self._write_allow = True
        self.disabled = dmx512.check_address_force(universe, address)


class CheckerChannelsUiList(ScrollLayout):
    checker = ObjectProperty()
    _trigger_update_faders = None
    _previous_universe = None

    def __init__(self, **kwargs):
        self._trigger_update_faders = Clock.create_trigger(self._update_faders, -1)
        super().__init__(**kwargs)

    def on_kv_post(self, _):
        super().on_kv_post(_)
        self.__create_faders()
        self.checker.bind(hidden=self._trigger_update_faders)
        self.checker.bind(universe_now=self.on_universe_now)
        db.patch.bind(address_info=self._trigger_update_faders)
        self.on_universe_now(self.checker, self.checker.universe_now)
        self._trigger_update_faders()

    def on_universe_now(self, checker, universe):
        if self._previous_universe is not None:
            dmx512.unregister_on_write_matrix(self._previous_universe, self._trigger_update_faders)
        dmx512.register_on_write_matrix(universe, self._trigger_update_faders)
        self._previous_universe = universe
        self._trigger_update_faders()

    def __create_faders(self):
        self.scrollview.data = [
            {
                "checker": self.checker,
                "address": i,
            } for i in range(1, constants.DMX_ADDRESS_COUNT + 1)
        ]

    def _update_faders(self, _):
        if self.checker.hidden:
            return
        for fader in self.scrollview.layout_manager.children:
            fader.update()


class CheckerAddressTitle(RestrictedLabel):
    pass


class PatchOverlayWidget(BoxLayout):
    patch = ObjectProperty()


class CheckerOverlay(BoxLayout):
    checker = ObjectProperty()
    channel_titles = ObjectProperty()
    channel_sliders = ObjectProperty()
    patch_overlay = ObjectProperty()

    def __init__(self, **kwargs):
        self._trigger_update_patch_overlay = Clock.create_trigger(self.update_patch_overlay, 0)
        super().__init__(**kwargs)

    def on_kv_post(self, _):
        super().on_kv_post(_)
        self.__create_address_titles()
        self.checker.bind(hidden=self._trigger_update_patch_overlay)
        db.patch.bind(address_info=self._trigger_update_patch_overlay)
        self.channel_sliders.scrollview.bind(
            scroll_element=self._trigger_update_patch_overlay
        )
        self.channel_titles.bind(
            size=self._trigger_update_patch_overlay,
            pos=self._trigger_update_patch_overlay
        )
        self._trigger_update_patch_overlay()

    def __create_address_titles(self):
        self.channel_titles.data = [
            {
                "text": str(i),
            } for i in range(1, constants.DMX_ADDRESS_COUNT + 1)
        ]
        self.channel_sliders.scrollview.bind(
            scroll_element=self.channel_titles.setter("scroll_element")
        )
        self._trigger_update_patch_overlay()

    def update_patch_overlay(self, _):
        if self.checker.hidden:
            return
        self.patch_overlay.clear_widgets()

        lm = self.channel_titles.layout_manager
        universe = self.checker.universe_now
        address_list = [int(i.text) for i in lm.children]

        patch_list = set()
        for address in address_list:
            address_info = db.patch.get_address_info(universe, address)
            if address_info is not None:
                patch, _ = address_info[0]
                patch_list.add(patch)

        first_x = lm._rv_positions[self.channel_titles.scroll_element] - lm.spacing
        item_width = lm.default_size[0]
        for patch in patch_list:
            x = lm._rv_positions[patch.start_address - 1]
            end_x = lm._rv_positions[patch.end_address - 1] - lm.spacing
            width = end_x - x + lm.default_size[0]
            overlay_widget = PatchOverlayWidget(
                patch=patch,
                pos=(x - first_x, 0),
                width=width
            )
            self.patch_overlay.add_widget(overlay_widget)


class CheckerChannelsUi(SectionPanel):
    checker = ObjectProperty()
    overlay = ObjectProperty()
    channel_sliders = ObjectProperty()
