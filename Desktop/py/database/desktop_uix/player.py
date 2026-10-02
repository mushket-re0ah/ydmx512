from typing import TYPE_CHECKING, Any, List, Optional

from kivy.clock import Clock
from kivy.properties import AliasProperty, ObjectProperty

from database import db
from database.fixture_param import RowFixtureParam
from libs.beat_counter import BeatCounter
from libs.dmx512 import dmx512
from libs.dmx512.misc import FullAddress
from misc import constants
from misc.player import BasePlayer, render_utils
from misc.player.status import PlayerStatus

if TYPE_CHECKING:
    from database.desktop_uix import RowDesktopUix


class DesktopUixPlayer(BasePlayer):
    desktop_uix: "RowDesktopUix" = ObjectProperty()

    BEATS_COUNT: int = 4
    FRAME_COUNT: int = BEATS_COUNT * constants.FRAMES_IN_BEAT

    def on_parent_row(self, _: "DesktopUixPlayer", parent_row: "RowDesktopUix"): # pyright: ignore[reportIncompatibleMethodOverride]
        self.trigger_update_force_value = Clock.create_trigger(self.update_force_value, -1)
        super().on_parent_row(_, parent_row)
        self.desktop_uix = parent_row

        parent_row.bind(
            patch=self.trigger_update_force_value,
            fixture_param_1_index=self.trigger_update_force_value,
            fixture_param_2_index=self.trigger_update_force_value,
            active=self.trigger_update_force_value,
            value_1=self.trigger_update_force_value,
            value_2=self.trigger_update_force_value,
        )
        parent_row.bind(active=self.on_active)
        db.scene.bind(scene_now_dimmer=self.trigger_update_force_value)
        self.on_active(self, parent_row.active)
        self.trigger_update_force_value()

    def on_remove(self, instance: "RowDesktopUix"): # pyright: ignore[reportIncompatibleMethodOverride]
        self.desktop_uix.active = False
        super().on_remove(instance)

    def _create_beat_counter(self) -> BeatCounter:
        bc = BeatCounter(temp=self.temp, beats_count=self.BEATS_COUNT)
        bc.link()
        return bc

    def _remove_beat_counter(self):
        if self.beat_counter:
            self.beat_counter.unlink()
            self.beat_counter = None
        if self.soft_play and (self.is_release or self.is_attack):
            self.set_value_delay(self.start_value_1, self.start_value_2)

    def on_start(self, _):
        self.start_value_1 = self.desktop_uix.value_1
        self.start_value_2 = self.desktop_uix.value_2

    def on_stop(self, _):
        if self.soft_play and self.is_release:
            self.set_value_delay(self.start_value_1, self.start_value_2)

    def on_active(self, _: Any, active: bool):
        if active and self.status is PlayerStatus.STOP:
            self.start()
        elif self.status is PlayerStatus.WORK or self.status is PlayerStatus.ATTACK:
            self.stop()

    start_value_1: Optional[int] = None
    start_value_2: Optional[int] = None
    def on_frame_now(self, _, frame: int):
        duix = self.desktop_uix
        if not self.soft_play or self.status == PlayerStatus.WORK:
            return

        is_attack = self.status == PlayerStatus.ATTACK
        total_frames = self.FRAME_COUNT
        vals: List[Optional[int]] = [None, None]

        for i in (1, 2):
            val = self.soft_renderer.get_soft_value(
                is_attack, f"value_{i}", frame, total_frames,
                getattr(duix, f"value_{i}"),
                getattr(duix, f"value_{i}_minimum")
            )
            if val is not None:
                vals[i - 1] = self.apply_modifiers(val, getattr(duix, f"fixture_param_{i}"))

        self.set_value_delay(*vals)

    def set_value_delay(self, value_1: Optional[int], value_2: Optional[int]):
        def set_value(_:float):
            if value_1 is not None:
                self.desktop_uix.value_1 = value_1
            if value_2 is not None:
                self.desktop_uix.value_2 = value_2
        Clock.schedule_once(set_value, -1)

    def set_force_delay(self, universe: int, address: int, value: int):
        def set_value(_:float):
            dmx512.set_force_value(universe, address, value)
        Clock.schedule_once(set_value, -1)

    def set_force_value(self, n: int):
        patch = self.desktop_uix.patch
        if (
            self.status is not PlayerStatus.STOP and
            getattr(self.desktop_uix, f"value_{n}_allow") and
            patch is not None
        ):
            universe = patch.universe
            address = patch.start_address +\
                      getattr(self.desktop_uix, f"fixture_param_{n}_index")
            setattr(self, f"force_full_addr_{n}", FullAddress(universe, address))

            value = self.apply_modifiers(
                getattr(self.desktop_uix, f"value_{n}"),
                getattr(self.desktop_uix, f"fixture_param_{n}")
            )
            self.set_force_delay(universe, address, value)
        else:
            setattr(self, f"force_full_addr_{n}", None)

    def discard_force_value(self, n: int):
        full_addr = getattr(self, f"force_full_addr_{n}")
        if full_addr:
            dmx512.discard_force_value(*full_addr)

    _force_full_addr_1: Optional[FullAddress] = ObjectProperty(allownone=True)
    _force_full_addr_2: Optional[FullAddress] = ObjectProperty(allownone=True)

    def set_force_full_addr_1(self, full_addr: Optional[FullAddress]) -> bool:
        if full_addr != self._force_full_addr_1:
            self.discard_force_value(1)
        self._force_full_addr_1 = full_addr
        return True

    def set_force_full_addr_2(self, full_addr: Optional[FullAddress]) -> bool:
        if full_addr != self._force_full_addr_2:
            self.discard_force_value(2)
        self._force_full_addr_2 = full_addr
        return True

    force_full_addr_1 = AliasProperty(
        lambda self: self._force_full_addr_1,
        set_force_full_addr_1,
    )
    force_full_addr_2 = AliasProperty(
        lambda self: self._force_full_addr_2,
        set_force_full_addr_2,
    )

    def update_force_value(self, _: Any):
        self.set_force_value(1)
        self.set_force_value(2)

    def apply_modifiers(self, value: int, fixture_param: Optional[RowFixtureParam]) -> int:
        patch = self.desktop_uix.patch
        if fixture_param is None or patch is None:
            return value
        return render_utils.apply_value_modifiers(
            value, fixture_param.title_id, patch.invert_pan, patch.invert_tilt
        )
