from typing import Any, Literal, Optional, Tuple

from kivy.clock import Clock
from kivy.event import EventDispatcher

from libs.dmx512.serial.device import DMXSerialDevice
from libs.dmx512.universe import DMX512Universe
from libs.serial.observer import observer as serial_observer
from libs.typecheck import KivyCallback


class DMX512Dispatcher(EventDispatcher):
    __events__ = ("on_blackout",)

    trigger_sync_universe_device = None
    def __init__(self,
            dmx_universe_count: int,
            serial_timeout: float,
            serial_baudrate: int,
            serial_try_connection_time: float,
            dmx_hello_msg: bytes,
            dmx_message_byteorder: Literal["little", "big"],
            dmx_light_fps: int,
            dmx_address_count: int,
            dmx_key_frame_time: float,
            **kwargs: Any):
        self.DMX_UNIVERSE_COUNT = dmx_universe_count
        self.SERIAL_TIMEOUT = serial_timeout
        self.SERIAL_BAUDRATE = serial_baudrate
        self.SERIAL_TRY_CONNECTION_TIME = serial_try_connection_time
        self.DMX_HELLO_MSG = dmx_hello_msg
        self.DMX_MESSAGE_BYTEORDER = dmx_message_byteorder
        self.DMX_LIGHT_FPS = dmx_light_fps
        self.DMX_ADDRESS_COUNT = dmx_address_count
        self.DMX_KEY_FRAME_TIME = dmx_key_frame_time
        super().__init__(**kwargs)

    def init(self):
        self.universes = {universe: DMX512Universe(universe=universe)
                    for universe in range(1, self.DMX_UNIVERSE_COUNT + 1)}
        self.trigger_sync_universe_device = Clock.create_trigger(self.sync_universe_device, -1)
        serial_observer.bind(
            on_new_device=self.trigger_sync_universe_device,
            on_remove_device=self.trigger_sync_universe_device
        )

    def loop(self, time_diff: float):
        for universe in self.universes.values():
            universe.loop(time_diff)

    def on_blackout(self):
        pass

    def get_value(self, universe: int, address: int) -> int:
        return self.universes[universe].get_value(address)

    def set_value(self, universe: int, address: int, value: int):
        self.universes[universe].set_value(address, value)

    def set_force_value(self, universe: int, address: int, value: int):
        self.universes[universe].set_force_value(address, value)

    def check_address_force(self, universe: int, address: int) -> bool:
        return self.universes[universe].check_address_force(address)

    def discard_force_value(self, universe: int, address: int):
        self.universes[universe].discard_force_value(address)

    def clear_matrix(self, universe: int):
        self.universes[universe].clear_matrix()

    def set_default_value(self, universe: int, address: int):
        self.universes[universe].set_default_value(address)

    def clear_matrix_by_address_list(self, universe: int, address_list: Tuple[int]):
        self.universes[universe].clear_matrix_by_address_list(address_list)

    def clear_matrix_all(self):
        for universe in self.universes.values():
            universe.clear_matrix()

    def clear_default_matrix(self, universe: int):
        self.universes[universe].clear_default_matrix()

    def clear_default_matrix_all(self):
        for universe in self.universes.values():
            universe.clear_default_matrix()

    def blackout(self, universe: int):
        self.universes[universe].blackout()

    def blackout_all(self):
        for universe in self.universes.values():
            universe.blackout()
        self.dispatch("on_blackout")

    def set_default_matrix_value(self, universe: int, address: int, value: int):
        self.universes[universe].set_default_matrix_value(address, value)

    def set_universe_device(self, universe: int, device: DMXSerialDevice):
        self.universes[universe].device = device

    def sync_universe_device(self, _):
        device_dict = {device.universe: device for device in serial_observer.devices}
        for universe, universe_obj in self.universes.items():
            universe_obj.device = device_dict.get(universe, None)

    def register_on_write_matrix(self, universe: int, callback: KivyCallback):
        self.universes[universe].bind(on_write_matrix=callback)

    def unregister_on_write_matrix(self, universe: int, callback: KivyCallback):
        self.universes[universe].unbind(on_write_matrix=callback)

    def get_universe(self, universe: int) -> DMX512Universe:
        return self.universes[universe]

    def get_free_universe(self) -> Optional[int]:
        return next((universe for universe, data in self.universes.items()
                              if data.device is None), None)

dmx512 = None
def init(
        dmx_universe_count: int,
        serial_timeout: float,
        serial_baudrate: int,
        serial_try_connection_time: float,
        dmx_hello_msg: bytes,
        dmx_message_byteorder: Literal["little", "big"],
        dmx_light_fps: int,
        dmx_address_count: int,
        dmx_key_frame_time: float):
    global dmx512
    if dmx512 is not None:
        raise RuntimeError("DMX512 модуль уже инициализирован")
    dmx512 = DMX512Dispatcher(
        dmx_universe_count,
        serial_timeout,
        serial_baudrate,
        serial_try_connection_time,
        dmx_hello_msg,
        dmx_message_byteorder,
        dmx_light_fps,
        dmx_address_count,
        dmx_key_frame_time,
    )
    dmx512.init()
