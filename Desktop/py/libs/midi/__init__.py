from typing import Any

from kivy.event import EventDispatcher

from libs.utils import ThrottledCall


class MIDIDispatcher(EventDispatcher):
    __events__ = ("on_note_on", "on_note_off", "on_controller_change",)

    def __init__(
            self,
            messages_call_interval: float,
            try_connection_time: float,
            **kwargs: Any
        ):
        super().__init__(**kwargs)
        self.TRY_CONNECTION_TIME = try_connection_time
        self.loop = ThrottledCall(
            self._loop, messages_call_interval
        )

    def on_note_on(self, channel: int, intensive: int):
        pass

    def on_note_off(self, channel: int, intensive: int):
        pass

    def on_controller_change(self, channel: int, intensive: int):
        pass

    def _loop(self):
        from libs.midi.observer import observer
        for device in observer.devices:
            device.check_messages()


midi = None
def init(
       messages_call_interval: float,
       try_connection_time: float,
    ):
    global midi
    if midi is not None:
        raise RuntimeError("MIDI модуль уже инициализирован")
    midi = MIDIDispatcher(
        messages_call_interval,
        try_connection_time
    )
