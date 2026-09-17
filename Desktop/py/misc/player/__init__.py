from kivy.properties import ObjectProperty
from libs.beat_counter import BeatCounter
from misc.player.status import PlayerStatus
from misc.player.render_utils import SoftEffectsRenderer
from libs.properties import EnumProperty, BindableObjectProperty
from libs.serialize import SerializableMixin
from libs.kivy_utils import AutoUnbindBehavior
from misc import constants
from libs.kivy_json_orm.fields import *
from libs.midi import midi


class BasePlayer(SerializableMixin, AutoUnbindBehavior):
    parent_row = ObjectProperty()

    temp = ClampedNumericField(120, constants.TEMP_MINIMUM, constants.TEMP_MAXIMUM)
    is_moment = BooleanField(False)
    is_attack = BooleanField(False)
    is_release = BooleanField(False)
    soft_play = BooleanField(False)
    midi_channel = ClampedNumericField(None, 0, constants.MIDI_MAXIMUM_CHANNEL, allownone=True)
    hotkey = StringField("A")

    status = EnumProperty(PlayerStatus, PlayerStatus.STOP, rebind=True)

    __events__ = ("on_start", "on_stop")

    def __init__(self, **kwargs):
        self.soft_renderer = SoftEffectsRenderer()
        super().__init__(**kwargs)
        self.bind_to(
            midi,
            on_note_on=self.on_midi_note_on,
            on_note_off=self.on_midi_note_off
        )

    def on_parent_row(self, _, parent_row):
        parent_row.bind(
            on_remove=self.on_remove
        )

    def save(self):
        if self.parent_row:
            self.parent_row._table.save()

    def on_remove(self, instance):
        self.unbind_all()

    def on_midi_note_on(self, _, channel: int, intensive: int):
        pass

    def on_midi_note_off(self, _, channel: int, intensive: int):
        pass

    def edit(self, **kwargs):
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

    def on_status(self, _, status):
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

    def on_soft_play(self, _, soft_play):
        self.soft_renderer.reset(PlayerStatus.STOP)

    beat_counter = BindableObjectProperty(
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
