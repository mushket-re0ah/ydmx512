from kivy.properties import ObjectProperty, StringProperty, ColorProperty
from libs.uix.device_list_panel import DeviceUi, DeviceListPanel
from libs.midi.observer import observer as midi_observer
from misc import colorscheme


class MidiUi(DeviceUi):
    pass


class MidiDevices(DeviceListPanel):
    device_cls = ObjectProperty(MidiUi)
    observer = ObjectProperty(midi_observer)

    title = StringProperty("MIDI устройства")
    bg_scrollview = ColorProperty(colorscheme.MidiDevices.bg)
