from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty, NumericProperty
from kivy.clock import Clock
from typing import Union
from .serial.device import DMXSerialDevice, SerialState
from .lan.device import LanDevice
from . import message
from typing import List, Optional, Tuple
import time
import logging
from libs.utils import ThrottledCall

logger = logging.getLogger(__name__)


class DMX512Universe(EventDispatcher):
    universe = NumericProperty()
    device: Union[DMXSerialDevice, LanDevice] = ObjectProperty(allownone=True)
    force_value_set = ObjectProperty()

    matrix: bytearray = None
    default_matrix: bytearray = None

    def __init__(self, **kwargs):
        from . import dmx512
        self.register_event_type("on_write_matrix")
        self.matrix = bytearray([0] * dmx512.DMX_ADDRESS_COUNT)
        self.default_matrix = bytearray([0] * dmx512.DMX_ADDRESS_COUNT)
        self.force_value_set = set()
        super().__init__(**kwargs)

        self.address_changed = set()
        self.last_key_frame_time = 0
        self._loop_write_matrix = ThrottledCall(
            self._write_matrix, 1 / dmx512.DMX_LIGHT_FPS
        )

    def loop(self, time_diff):
        if self.device:
            self.device.loop()
            self._loop_write_matrix(time_diff)

    def on_write_matrix(self, address: int, value: int):
        pass

    def set_default_matrix_value(self, address: int, value: int):
        self.default_matrix[address] = value

    def clear_matrix(self):
        from . import dmx512
        for address in range(1, dmx512.DMX_ADDRESS_COUNT + 1):
            self.set_value(address, self.default_matrix[address - 1])

    def clear_default_matrix(self):
        from . import dmx512
        for address in range(1, dmx512.DMX_ADDRESS_COUNT + 1):
            self.default_matrix[address - 1] = 0

    def clear_matrix_by_address_list(self, address_list: Tuple[int]):
        for address in address_list:
            self.set_value(address, self.default_matrix[address])

    def set_default_value(self, address: int):
        self.set_value(address, self.default_matrix[address])

    def set_force_value(self, address: int, value: int):
        self.discard_force_value(address)
        self.set_value(address, value)
        self.force_value_set.add(address)

    def discard_force_value(self, address: int):
        if address in self.force_value_set:
            self.force_value_set.remove(address)
            self.set_value(address, self.default_matrix[address])

    def blackout(self):
        self.clear_matrix()

    def get_value(self, address: int) -> int:
        return self.matrix[address - 1]

    def set_value(self, address: int, value: int):
        if address in self.force_value_set:
            return
        if self.matrix[address - 1] != value:
            self.address_changed.add(address)
        self.matrix[address - 1] = value
        self.dispatch("on_write_matrix", address, value)

    def check_address_force(self, address: int) -> bool:
        return address in self.force_value_set

    def _write_matrix(self):
        if self.device and self.device.state is SerialState.CONNECTED:
            msg = self._create_dmx_message()
            if msg:
                self.device.write(msg)

    def _create_dmx_message(self) -> Optional[bytes]:
        from . import dmx512
        address_list = []
        value_list = []
        if (time.monotonic() - self.last_key_frame_time) > dmx512.DMX_KEY_FRAME_TIME:
            for address, value in enumerate(self.matrix, 1):
                address_list.append(address)
                value_list.append(value)
            self.last_key_frame_time = time.monotonic()
        else:
            if not self.address_changed:
                return None
            for address in sorted(self.address_changed):
                address_list.append(address)
                value_list.append(self.matrix[address - 1])
            self.address_changed.clear()

        return message.create_message(address_list, value_list)
