from kivy.properties import ObjectProperty, AliasProperty
from kivy.clock import Clock
from typing import Tuple
from misc import constants
from libs.dmx512 import dmx512
from database.fixture_param import RowFixtureParam
from database import db
from misc.player.status import PlayerStatus
from misc.player import BasePlayer
from misc.player import render_utils
from libs.beat_counter import BeatCounter


class DesktopUixPlayer(BasePlayer):
    desktop_uix = ObjectProperty()

    BEATS_COUNT = 4
    FRAME_COUNT = BEATS_COUNT * constants.FRAMES_IN_BEAT

    trigger_update_force_value = None

    def on_parent_row(self, _, row):
        super().on_parent_row(_, row)
        self.desktop_uix = row

        self.trigger_update_force_value = Clock.create_trigger(self.update_force_value, -1)
        row.bind(
            patch=self.trigger_update_force_value,
            fixture_param_1_index=self.trigger_update_force_value,
            fixture_param_2_index=self.trigger_update_force_value,
            active=self.trigger_update_force_value,
            value_1=self.trigger_update_force_value,
            value_2=self.trigger_update_force_value,
        )
        row.bind(active=self.on_active)
        db.scene.bind(scene_now_dimmer=self.trigger_update_force_value)
        self.on_active(None, row.active)
        self.trigger_update_force_value()

    def on_remove(self, instance):
        self.desktop_uix.active = False
        super().on_remove(instance)

    def _create_beat_counter(self):
        bc = BeatCounter(temp=self.temp, beats_count=self.BEATS_COUNT)
        bc.link()
        return bc

    def _remove_beat_counter(self):
        if self.beat_counter:
            self.beat_counter.unlink()
            self.beat_counter = None
        if self.soft_play and (self.is_release or self.is_attack):
            self.set_value_delay(self.start_value_1, self.start_value_2)

    def on_start(self, beat_counter):
        self.start_value_1 = self.desktop_uix.value_1
        self.start_value_2 = self.desktop_uix.value_2

    def on_stop(self, beat_counter):
        if self.soft_play and self.is_release:
            self.set_value_delay(self.start_value_1, self.start_value_2)

    def on_active(self, _, active: bool):
        if active and self.status is PlayerStatus.STOP:
            self.start()
        elif self.status is PlayerStatus.WORK or self.status is PlayerStatus.ATTACK:
            self.stop()

    start_value_1 = None
    start_value_2 = None
    def on_frame_now(self, _, frame: int):
        duix = self.desktop_uix
        if not self.soft_play or self.status == PlayerStatus.WORK:
            return

        is_attack = self.status == PlayerStatus.ATTACK
        total_frames = self.FRAME_COUNT
        vals = []

        for i in (1, 2):
            val = self.soft_renderer.get_soft_value(
                is_attack, f"value_{i}", frame, total_frames,
                getattr(duix, f"value_{i}"),
                getattr(duix, f"value_{i}_minimum")
            )
            if val is None:
                return
            vals.append(self.apply_modifiers(val, getattr(duix, f"fixture_param_{i}")))

        self.set_value_delay(*vals)

    def set_value_delay(self, value_1: int, value_2: int):
        def set_value(_):
            self.desktop_uix.value_1 = value_1
            self.desktop_uix.value_2 = value_2
        Clock.schedule_once(set_value, -1)

    def set_force_delay(self, universe: int, address: int, value: int):
        def set_value(_):
            dmx512.set_force_value(universe, address, value)
        Clock.schedule_once(set_value, -1)

    def set_force_value(self, n):
        if self.status is not PlayerStatus.STOP and getattr(self.desktop_uix, f"value_{n}_allow"):
            universe = self.desktop_uix.patch.universe
            address = self.desktop_uix.patch.start_address + getattr(self.desktop_uix, f"fixture_param_{n}_index")
            setattr(self, f"force_full_addr_{n}", (universe, address))

            value = self.apply_modifiers(getattr(self.desktop_uix, f"value_{n}"), getattr(self.desktop_uix, f"fixture_param_{n}"))
            self.set_force_delay(universe, address, value)
        else:
            setattr(self, f"force_full_addr_{n}", None)

    def discard_force_value(self, n):
        full_addr = getattr(self, f"force_full_addr_{n}")
        if full_addr:
            dmx512.discard_force_value(*full_addr)

    _force_full_addr_1 = ObjectProperty(allownone=True)
    _force_full_addr_2 = ObjectProperty(allownone=True)

    def set_force_full_addr_1(self, full_addr):
        if full_addr != self._force_full_addr_1:
            self.discard_force_value(1)
        self._force_full_addr_1 = full_addr

    def set_force_full_addr_2(self, full_addr):
        if full_addr != self._force_full_addr_2:
            self.discard_force_value(2)
        self._force_full_addr_2 = full_addr

    force_full_addr_1 = AliasProperty(
        lambda self: self._force_full_addr_1,
        set_force_full_addr_1,
        cache=True
    )
    force_full_addr_2 = AliasProperty(
        lambda self: self._force_full_addr_2,
        set_force_full_addr_2,
        cache=True
    )

    def update_force_value(self, _):
        self.set_force_value(1)
        self.set_force_value(2)

    def apply_modifiers(self, value: int, fixture_param: RowFixtureParam) -> int:
        if fixture_param is None:
            return value
        patch = self.desktop_uix.patch
        return render_utils.apply_value_modifiers(
            value, fixture_param.title_id, patch.invert_pan, patch.invert_tilt
        )
