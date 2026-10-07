from typing import Any, List, Tuple

import rtmidi

from libs.device_observer import DeviceObserver
from libs.midi.device import MidiDevice


class MidiObserver(DeviceObserver):
    name: str = "MidiObserver"
    devices: Tuple[MidiDevice, ...] # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(self, **kwargs: Any):
        self.midi_in = rtmidi.MidiIn()
        super().__init__(**kwargs)

    def _get_ports(self) -> List[str]:
        return self.midi_in.get_ports()

    def _make_device(self, port: str) -> MidiDevice:
        return MidiDevice(port)


observer = MidiObserver()
