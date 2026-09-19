from kivy.properties import ObjectProperty
from kivy.clock import Clock
from kivy.lang import Builder
from libs.uix.layouts import SectionPanel
from libs.uix.scroll_layout import ScrollLayout
from libs.uix.slider import TitleNumericHoverSlider
from misc import constants
from libs.dmx512.universe import DMX512Universe
from libs.dmx512 import dmx512
from misc import colorscheme as cs


Builder.load_file("ui/mdi/checker/channels_ui.kv")


class CheckerSlider(TitleNumericHoverSlider):
    checker = ObjectProperty()
    _write_allow = False

    def on_kv_post(self, _):
        self.slider.step_mouse_scroll = 5
        self.numeric.normal_border_color = cs.CheckerSlider.border_color_normal

    def on_index(self, _, index: str):
        self.update()

    def on_value(self, _, value: int):
        if self._write_allow:
            dmx512.set_value(self.checker.universe_now, self.address, value)

    def update(self):
        universe = self.checker.universe_now
        self._write_allow = False
        self.value = dmx512.get_value(universe, self.address)
        self._write_allow = True
        self.disabled = dmx512.check_address_force(universe, self.address)

    @property
    def address(self) -> int:
        return int(self.index)


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
        self.on_universe_now(self.checker, self.checker.universe_now)

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
                "index": str(i),
            } for i in range(1, constants.DMX_ADDRESS_COUNT + 1)
        ]

    def _update_faders(self, _):
        if self.checker.hidden:
            return
        for fader in self.scrollview.layout_manager.children:
            fader.update()


class CheckerChannelsUi(SectionPanel):
    checker = ObjectProperty()
    box = ObjectProperty()
