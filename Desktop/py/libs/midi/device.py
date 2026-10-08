from typing import Any, Optional, Tuple

import rtmidi
from kivy.properties import ObjectProperty, StringProperty
from rtmidi.midiconstants import (
    # CHANNEL_PRESSURE,
    CONTROLLER_CHANGE,
    NOTE_OFF,
    NOTE_ON,
    # PITCH_BEND,
    # PROGRAM_CHANGE,
)

from libs import logger
from libs.device_observer import ConnectionState, StatefulDevice


class MidiDevice(StatefulDevice):
    port: str = StringProperty()
    connection: Optional[rtmidi.MidiIn] = ObjectProperty(allownone=True)

    def __init__(self, port: str, **kwargs: Any):
        self.port = port
        name = port.rsplit(' ', 1)[0]
        from libs.midi import midi
        super().__init__(
            name=name,
            try_connection_time=midi.TRY_CONNECTION_TIME,
            **kwargs
        )
    # --- интерфейс для observer'а ---

    def matches_port(self, port: str) -> bool:
        return self.port == port

    # --- хуки StatefulDevice ---

    def _has_connection(self) -> bool:
        return self.connection is not None

    def _open_connection(self) -> None:
        midi_in = rtmidi.MidiIn()
        ports = midi_in.get_ports()
        if self.port not in ports:
            return
        midi_in.open_port(ports.index(self.port), name="YDMX")
        self.connection = midi_in
        self.state = ConnectionState.CONNECTED

    def _close_resource(self) -> None:
        if self.connection is None:
            return
        try:
            self.connection.close_port()
        except Exception:
            logger.warning(
                f"MidiDevice [{self.name}]: close failed", exc_info=True
            )
        self.connection = None

    def _read_messages(self) -> None:
        if self.connection is None:
            return
        try:
            midi_msg = self.connection.get_message()
            while midi_msg:
                self._decode_midi_message(midi_msg)
                midi_msg = self.connection.get_message()
        except Exception:
            logger.error(
                f"MidiDevice [{self.name}]: read failed", exc_info=True
            )
            self._lost_connection()

    def _decode_midi_message(
            self,
            midi_message: Optional[Tuple[bytes, float]]
        ):
        # | Тип              | Status | Data bytes |
        # | ---------------- | -----: | ---------: |
        # | Note Off         |  0x8n  |          2 |
        # | Note On          |  0x9n  |          2 |
        # | Poly Aftertouch  |  0xAn  |          2 |
        # | Control Change   |  0xBn  |          2 |
        # | Program Change   |  0xCn  |          1 |
        # | Channel Pressure |  0xDn  |          1 |
        # | Pitch Bend       |  0xEn  |          2 |
        if midi_message is None:
            return
        from libs.midi import midi

        msg_data, delta_time = midi_message
        status = msg_data[0]
        if status < 0xF0:
            message_type = status & 0xF0
            # channel = status & 0x0F

            if message_type == NOTE_ON:
                note = msg_data[1]
                velocity = msg_data[2]
                midi.dispatch("on_note_on", note, velocity)

            elif message_type == NOTE_OFF:
                note = msg_data[1]
                velocity = msg_data[2]
                midi.dispatch("on_note_off", note, velocity)

            elif message_type == CONTROLLER_CHANGE:
                controller = msg_data[1]
                value = msg_data[2]
                midi.dispatch("on_controller_change", controller, value)

            # elif message_type == PROGRAM_CHANGE:
            #     program = msg_data[1]

            # elif message_type == CHANNEL_PRESSURE:
            #     pressure = msg_data[1]

            # elif message_type == PITCH_BEND:
            #     value_lo = msg_data[1]
            #     value_hi = msg_data[2]

    def __repr__(self) -> str:
        return (f"MidiDevice(port={self.port}, name={self.name})")
