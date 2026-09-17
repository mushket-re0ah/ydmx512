from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty, StringProperty
import rtmidi
from rtmidi.midiconstants import NOTE_OFF, NOTE_ON, CONTROLLER_CHANGE


class MidiDevice(EventDispatcher):
    name = StringProperty()
    port = StringProperty()
    connection = ObjectProperty(allownone=True)

    def __init__(self, port: str):
        self.port = port
        *name, _ = port.split(' ')
        self.name = ''.join(f"{i} " if i != name[-1] else i for i in name)
        self.connection = None

    def connect(self):
        midi_in = rtmidi.MidiIn()
        self.connection = midi_in.open_port(midi_in.get_ports().index(self.port))

    def close_connection(self):
        self.connection.close_port()
        self.connection = None

    def check_messages(self):
        from . import midi
        if self.connection:
            msg = self.connection.get_message()
            if msg:
                msg_type, channel, intensive = msg[0]
                if msg_type == NOTE_ON:
                    midi.dispatch("on_note_on", channel, intensive)
                elif msg_type == NOTE_OFF:
                    midi.dispatch("on_note_off", channel, intensive)
                elif msg_type == CONTROLLER_CHANGE:
                    midi.dispatch("on_controller_change", channel, intensive)

    def __eq__(self, other: "MidiDevice") -> bool:
        return self.name == other.name
