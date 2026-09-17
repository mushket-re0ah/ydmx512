from kivy.properties import BooleanProperty, ObjectProperty, AliasProperty
from kivy.clock import Clock
from typing import Optional
from misc import constants
from libs.dmx512 import dmx512
from libs.beat_counter import BeatCounter
from database.patch import RowPatch
from misc.player import BasePlayer
from misc.player.status import PlayerStatus
from misc.player.render_utils import SoftEffectsRenderer
from database.playback.player.effects_renderer import PlayerEffectsRenderer
from database.playback.player.master_player import master_player
from libs.kivy_json_orm.fields import *
import time


class PlaybackPlayer(BasePlayer):
    playback = ObjectProperty()

    beats_count = ClampedNumericField(4, constants.BEATS_COUNT_MINIMIUM, constants.BEATS_COUNT_MAXIMUM)
    is_link_global_temp = BooleanField(True)
    is_cycle = BooleanField(True)
    is_cycle_last_frame = BooleanField(False)
    fade_to_black = BooleanField(False)
    fade_to_black_time = ClampedNumericField(1000, constants.FADE_TO_BLACK_MS_MINIMUM, constants.FADE_TO_BLACK_MS_MAXIMUM)
    blackout_activate = BooleanField(False)
    bounce = BooleanField(False)

    _bounce_direction = 1
    play = BooleanProperty(False)

    def on_parent_row(self, _, row):
        self.time_start = None
        super().on_parent_row(_, row)
        self.playback = row
        self.effects_renderer = PlayerEffectsRenderer(self)
        self.bind_to(dmx512, on_blackout=self.on_blackout)
        self.bind_to(self.playback.database.scene, scene_now_beats_count=self._update_real_beats_count)

    def on_remove(self, instance):
        self.stop()
        super().on_remove(instance)

    def _update_real_beats_count(self, *args):
        self.property("is_link_global_temp").dispatch(self)

    _save_intensive = None
    def on_midi_note_on(self, _, channel: int, intensive: int):
        renderer = self.playback.renderer
        if channel == self.midi_channel:
            self._save_intensive = renderer.intensive
            renderer.intensive = intensive
            self.start()

    def on_midi_note_off(self, _, channel: int, _intensive: int):
        renderer = self.playback.renderer
        if channel == self.midi_channel:
            renderer.intensive = self._save_intensive
            self.stop()

    def on_blackout(self, _):
        if self.blackout_activate:
            if self.status in (PlayerStatus.STOP, PlayerStatus.RELEASE):
                self.start()
        else:
            if self.status in (PlayerStatus.WORK, PlayerStatus.ATTACK):
                self.stop()

    def _on_bounce(self, player, bounce):
        if not bounce:
            self._bounce_direction = 1

    def _create_beat_counter(self):
        if self.is_link_global_temp:

            return self.playback.database.scene.scene_now_bc
        else:
            bc = BeatCounter(temp=self.temp, beats_count=self.real_beats_count)
            bc.link()
            return bc

    def _remove_beat_counter(self):
        if self.beat_counter and self.beat_counter is not self.playback.database.scene.scene_now_bc:
            self.beat_counter.unlink()
        self.beat_counter = None

    def _on_bc_downbeat_extra(self):
        self.update_bounce_direction()
        if not self.is_cycle:
            self.status = PlayerStatus.STOP
        self.effects_renderer.check_last_frame()

    def update_bounce_direction(self):
        self._bounce_direction *= -1

    def on_bc_beat_now(self, _, beat_now: int):
        self.property("beat_now").dispatch(self)

    def get_beat_now(self) -> int:
        bc = self.beat_counter
        if self.effects_renderer.do_cycle_last_frame:
            if self.status is PlayerStatus.STOP:
                return 1
            return bc.beats_count if bc else self.real_beats_count
        else:
            return bc.beat_now + 1 if bc else 1
    beat_now = AliasProperty(get_beat_now)

    def on_start(self, beat_counter: BeatCounter):
        self.play = True
        self.time_start = time.time()

    def on_stop(self, beat_counter: BeatCounter):
        self.play = False

    def on_status(self, _, status: PlayerStatus):
        self.add_or_remove_player_list(status)
        if status is PlayerStatus.WORK:
            self._bounce_direction = 1
        if status is PlayerStatus.STOP:
            self._bounce_direction = 1
            self.dispatch("on_stop", self.beat_counter)
            self._remove_beat_counter()
        elif self.beat_counter is None:
            self.beat_counter = self._create_beat_counter()
            self.dispatch("on_start", self.beat_counter)
        self.property("beat_now").dispatch(self)
        self.effects_renderer.on_status_change(status)

    def add_or_remove_player_list(self, status: PlayerStatus):
        if status is PlayerStatus.STOP:
            master_player.remove_playback(self)
        elif (status is PlayerStatus.WORK) or (status is PlayerStatus.ATTACK):
            master_player.add_playback(self)


    real_beats_count = AliasProperty(
        lambda self: self.playback.database.scene.scene_now_beats_count if self.is_link_global_temp else self.beats_count,
        bind=["is_link_global_temp", "beats_count"]
    )


    frame_count = AliasProperty(
        lambda self: self.real_beats_count * constants.FRAMES_IN_BEAT,
        bind=["real_beats_count"]
    )

    def get_patch_render(self, patch: RowPatch, fixture_index: int, frame: int) -> Optional[int]:
        return self.effects_renderer.get_patch_render(patch, fixture_index, frame)

    def start_or_stop(self):
        if self.status in (PlayerStatus.WORK, PlayerStatus.ATTACK):
            self.stop()
        elif self.status is PlayerStatus.STOP:
            self.start()
