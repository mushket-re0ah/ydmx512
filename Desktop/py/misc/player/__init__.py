from typing import Any, Optional

from kivy.properties import ObjectProperty

from libs.beat_counter import BeatCounter
from libs.kivy_json_orm.fields import BooleanField, ClampedNumericField, StringField
from libs.kivy_json_orm.table_implementation import DatabaseRow
from libs.kivy_mixins import AutoUnbindBehavior
from libs.midi import midi
from libs.properties import BindableObjectProperty, EnumProperty
from libs.serialize import SerializableMixin
from libs.typecheck import Number
from misc import constants
from misc.player.render_utils import SoftEffectsRenderer
from misc.player.status import PlayerStatus


class BasePlayer(SerializableMixin, AutoUnbindBehavior):
    parent_row: DatabaseRow = ObjectProperty()

    temp: Number = ClampedNumericField(120, constants.TEMP_MINIMUM, constants.TEMP_MAXIMUM)
    is_moment: bool = BooleanField(False)
    is_attack: bool = BooleanField(False)
    is_release: bool = BooleanField(False)
    soft_play: bool = BooleanField(False)
    midi_channel: Optional[int] = ClampedNumericField(None, 0, constants.MIDI_MAXIMUM_CHANNEL, allownone=True)
    hotkey: str = StringField("A")

    status: PlayerStatus = EnumProperty(PlayerStatus, PlayerStatus.STOP, rebind=True)

    __events__ = ("on_start", "on_stop")

    def __init__(self, **kwargs: Any):
        self.soft_renderer = SoftEffectsRenderer()
        super().__init__(**kwargs)
        self.bind_to(
            midi,
            on_note_on=self.on_midi_note_on,
            on_note_off=self.on_midi_note_off
        )

    def on_parent_row(self, _, parent_row: DatabaseRow):
        parent_row.bind(
            on_remove=self.on_remove
        )

    def save(self):
        if self.parent_row:
            self.parent_row._table.save()

    def on_remove(self, _):
        self.unbind_all()

    def on_midi_note_on(self, _, channel: int, intensive: Number):
        pass

    def on_midi_note_off(self, _, channel: int, intensive: Number):
        pass

    def edit(self, **kwargs: Any):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.parent_row.save()

    def start(self):
        if self.status is not PlayerStatus.STOP:
            return
        if self.is_attack:
            self.status = PlayerStatus.ATTACK
        else:
            self.status = PlayerStatus.WORK

    def stop(self):
        if self.status in (PlayerStatus.STOP, PlayerStatus.RELEASE):
            return
        if self.is_release:
            self.status = PlayerStatus.RELEASE
        else:
            self.status = PlayerStatus.STOP

    def on_status(self, _, status: PlayerStatus):
        if status is PlayerStatus.STOP:
            self.dispatch("on_stop", self.beat_counter)
            self._remove_beat_counter()
            self.soft_renderer.reset(status)
        elif self.beat_counter is None:
            self.beat_counter = self._create_beat_counter()
            self.dispatch("on_start", self.beat_counter)
        if status == PlayerStatus.WORK:
            self._remove_beat_counter()
            self.soft_renderer.reset(status)

    def on_soft_play(self, _, _soft_play: bool):
        self.soft_renderer.reset(PlayerStatus.STOP)

    beat_counter: Optional[BeatCounter] = BindableObjectProperty(
        None, allownone=True,
        bind={
            "beat_now": "on_bc_beat_now",
            "on_downbeat": "on_bc_downbeat",
            "frame_now": "on_frame_now"
        }
    )

    def on_bc_beat_now(self, _, beat_now: int):
        pass

    def on_bc_downbeat(self, _):
        if self.status is PlayerStatus.ATTACK:
            self.status = PlayerStatus.WORK
        elif self.status is PlayerStatus.RELEASE:
            self.status = PlayerStatus.STOP
        self._on_bc_downbeat_extra()

    def _on_bc_downbeat_extra(self):
        pass

    def on_frame_now(self, _, frame: int):
        pass

    def _create_beat_counter(self) -> BeatCounter:
        raise NotImplementedError

    def _remove_beat_counter(self):
        raise NotImplementedError
