from typing import Type

from kivy.lang import Builder
from kivy.properties import ColorProperty, ObjectProperty, StringProperty

from libs.midi.observer import MidiObserver
from libs.midi.observer import observer as midi_observer
from libs.typecheck import RGBA
from libs.uix.device_list_panel import DeviceListPanel, DeviceUi
from misc import colorscheme

Builder.load_file("ui/main_ribbon/midi_devices.kv")


class MidiUi(DeviceUi):
    pass


class MidiDevices(DeviceListPanel):
    device_cls: Type[DeviceUi] = ObjectProperty(MidiUi)
    observer: MidiObserver = ObjectProperty(midi_observer)

    title: str = StringProperty("MIDI устройства")
    bg_scrollview: RGBA = ColorProperty(colorscheme.MidiDevices.bg)
