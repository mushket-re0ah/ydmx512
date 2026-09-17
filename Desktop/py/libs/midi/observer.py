from kivy.event import EventDispatcher
from kivy.properties import ListProperty
from .device import MidiDevice
from typing import List
import rtmidi
import logging

logger = logging.getLogger(__name__)


class MidiObserver(EventDispatcher):
    devices: List[MidiDevice] = ListProperty()

    __events__ = ("on_new_device", "on_remove_device")

    def __init__(self):
        self.midi_in = rtmidi.MidiIn()
        super().__init__()

    def on_new_device(self, device: MidiDevice):
        logger.info(f"MidiObserver: new device {device}")

    def on_remove_device(self, device: MidiDevice):
        logger.info(f"MidiObserver: remove device {device}")

    def monitor_connections(self):
        midi_list = self.midi_in.get_ports()
        for midi in midi_list:
            is_device_found = any(device.port == midi
                                  for device in self.devices)
            if not is_device_found:
                device = MidiDevice(midi)
                self.devices.append(device)
                self.dispatch("on_new_device", device)

        for device in self.devices:
            is_device_found = any(device.port == midi
                                  for midi in midi_list)
            if not is_device_found:
                self.devices.remove(device)
                self.dispatch("on_remove_device", device)

        for device in self.devices:
            device.check_messages()


observer = MidiObserver()
