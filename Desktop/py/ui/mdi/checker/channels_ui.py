from typing import TYPE_CHECKING, Any, Optional, Set

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ColorProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from database import db
from database.fixture_param import DIMMER_TITLE_ID, RowFixtureParam
from database.patch import RowPatch
from libs.dmx512 import dmx512
from libs.properties import BindableObjectProperty, ClampedNumericProperty
from libs.typecheck import RGBA
from libs.uix import colorscheme as uix_cs
from libs.uix.input.numeric_input import NumericInput
from libs.uix.label import RestrictedLabel
from libs.uix.layouts import SectionPanel, StencilRelativeLayout
from libs.uix.recycle_restricted_scrollview import RecycleRestrictedScrollView
from libs.uix.scroll_layout import ScrollLayout
from libs.uix.slider import HoverSlider  # lazy kv import initialize
from misc import colorscheme as cs
from misc import constants

if TYPE_CHECKING:
    from ui.mdi.checker import MDIChecker

Builder.load_file("ui/mdi/checker/channels_ui.kv")


class CheckerClampedSlider(HoverSlider):
    visual_maximum = ClampedNumericProperty(255, 0, 255)


class CheckerSlider(BoxLayout):
    checker: "MDIChecker" = ObjectProperty()

    numeric: NumericInput = ObjectProperty()
    slider: CheckerClampedSlider = ObjectProperty()

    address: int = ClampedNumericProperty(1, 1, constants.DMX_ADDRESS_COUNT)
    value: int = ClampedNumericProperty(0, 0, 255)
    maximum_value: int = ClampedNumericProperty(255, 0, 255)
    fixture_param_color: RGBA = ColorProperty(cs.CheckerSlider.fixture_param_default)
    fixture_param: Optional[RowFixtureParam] = BindableObjectProperty(
        None,
        allownone=True,
        bind={
            "title_alias": "dispatch_fixture_param"
        }
    )

    _write_allow: bool = False

    def on_kv_post(self, base_widget: Widget):
        prop = self.numeric.property("border_color")
        prop.set_normal(self.numeric, cs.CheckerSlider.border_color_normal)
        db.scene.bind(scene_now_dimmer=self.update)

    def on_address(self, _, address: int):
        self.update()

    def dispatch_fixture_param(self, *_:Any):
        self.property("fixture_param").dispatch(self)

    def on_value(self, _, value: int):
        if self._write_allow:
            dmx512.set_value(
                self.checker.universe_now,
                self.address,
                min(self.maximum_value, value)
            )

    def update(self, *_: Any):
        self._write_allow = False
        try:
            universe = self.checker.universe_now
            address = self.address

            self.value = dmx512.get_value(universe, address)
            address_info = db.patch.get_address_info(universe, address)

            if address_info is None:
                self.fixture_param_color = cs.CheckerSlider.fixture_param_default
                self.fixture_param = None
                self.maximum_value = 255
                value_track_color = uix_cs.HoverSlider.value_track_color_normal
            else:
                _patch, fixture_param = address_info[0]
                self.fixture_param_color = fixture_param.color
                self.fixture_param = fixture_param
                self.maximum_value = (
                    int(255 * db.scene.scene_now_dimmer / 100)
                    if fixture_param.title_id == DIMMER_TITLE_ID
                    else 255
                )
                value_track_color = fixture_param.color
            self.slider.property("value_track_color").set_normal(
                self.slider,
                value_track_color
            )

            self.disabled = (
                dmx512.check_address_force(universe, address)
                or self.maximum_value == 0
            )
        finally:
            self._write_allow = True


class CheckerChannelsUiList(ScrollLayout):
    checker: "MDIChecker" = ObjectProperty()
    _previous_universe: Optional[int] = None

    def __init__(self, **kwargs: Any):
        self._trigger_update_faders = Clock.create_trigger(self._update_faders, -1)
        super().__init__(**kwargs)

    def on_kv_post(self, base_widget: Widget):
        super().on_kv_post(base_widget)
        self.__create_faders()
        self.checker.bind(hidden=self._trigger_update_faders)
        self.checker.bind(universe_now=self.on_universe_now)
        db.patch.bind(address_info=self._trigger_update_faders)
        self.on_universe_now(self.checker, self.checker.universe_now)
        self._trigger_update_faders()

    def on_universe_now(self, checker: "MDIChecker", universe: int):
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

    def _update_faders(self, _:float):
        if self.checker.hidden:
            return
        for fader in self.scrollview.layout_manager.children:
            fader.update()


class CheckerAddressTitle(RestrictedLabel):
    pass


class PatchOverlayWidget(BoxLayout):
    patch: RowPatch = ObjectProperty()


class CheckerOverlay(BoxLayout):
    checker: "MDIChecker" = ObjectProperty()
    channel_titles: RecycleRestrictedScrollView = ObjectProperty()
    channel_sliders: CheckerChannelsUiList = ObjectProperty()
    patch_overlay: StencilRelativeLayout = ObjectProperty()

    def __init__(self, **kwargs: Any):
        self._trigger_update_patch_overlay = Clock.create_trigger(self.update_patch_overlay, 0)
        super().__init__(**kwargs)

    def on_kv_post(self, base_widget: Widget):
        super().on_kv_post(base_widget)
        self.__create_address_titles()
        self.checker.bind(
            hidden=self._trigger_update_patch_overlay,
            universe_now=self._trigger_update_patch_overlay
        )
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

    def update_patch_overlay(self, _:Any):
        if self.checker.hidden:
            return
        self.patch_overlay.clear_widgets()

        lm = self.channel_titles.layout_manager
        universe = self.checker.universe_now
        address_list = [int(i.text) for i in lm.children]

        patch_list: Set[RowPatch] = set()
        for address in address_list:
            address_info = db.patch.get_address_info(universe, address)
            if address_info is not None:
                patch, _ = address_info[0]
                patch_list.add(patch)

        first_x = lm._rv_positions[self.channel_titles.scroll_element] - lm.spacing
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
    checker: "MDIChecker" = ObjectProperty()
    overlay: CheckerOverlay = ObjectProperty()
    channel_sliders: CheckerChannelsUiList = ObjectProperty()
