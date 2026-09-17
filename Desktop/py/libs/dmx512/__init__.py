from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty, NumericProperty
from kivy.clock import Clock
from .universe import DMX512Universe
from libs.serial.observer import observer as serial_observer
from .serial.device import DMXSerialDevice
from typing import Callable, Optional, Tuple
from libs.utils import ThrottledCall


class DMX512Dispatcher(EventDispatcher):
    __events__ = ("on_blackout",)

    trigger_sync_universe_device = None
    def __init__(self,
            DMX_UNIVERSE_COUNT,
            SERIAL_TIMEOUT,
            SERIAL_BAUDRATE,
            SERIAL_TRY_CONNECTION_TIME,
            DMX_HELLO_MSG,
            DMX_MESSAGE_BYTEORDER,
            DMX_LIGHT_FPS,
            DMX_ADDRESS_COUNT,
            DMX_KEY_FRAME_TIME,
            **kwargs):
        self.DMX_UNIVERSE_COUNT = DMX_UNIVERSE_COUNT
        self.SERIAL_TIMEOUT = SERIAL_TIMEOUT
        self.SERIAL_BAUDRATE = SERIAL_BAUDRATE
        self.SERIAL_TRY_CONNECTION_TIME = SERIAL_TRY_CONNECTION_TIME
        self.DMX_HELLO_MSG = DMX_HELLO_MSG
        self.DMX_MESSAGE_BYTEORDER = DMX_MESSAGE_BYTEORDER
        self.DMX_LIGHT_FPS = DMX_LIGHT_FPS
        self.DMX_ADDRESS_COUNT = DMX_ADDRESS_COUNT
        self.DMX_KEY_FRAME_TIME = DMX_KEY_FRAME_TIME
        super().__init__(**kwargs)

    def init(self):
        self.universes = {universe: DMX512Universe(universe=universe)
                    for universe in range(1, self.DMX_UNIVERSE_COUNT + 1)}
        self.trigger_sync_universe_device = Clock.create_trigger(
                                        self.sync_universe_device, -1)
        serial_observer.bind(
            on_new_device=self.trigger_sync_universe_device,
            on_remove_device=self.trigger_sync_universe_device
        )

    def loop(self, time_diff):
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

    def register_on_write_matrix(self, universe: int, callback: Callable):
        self.universes[universe].bind(on_write_matrix=callback)

    def unregister_on_write_matrix(self, universe: int, callback: Callable):
        self.universes[universe].unbind(on_write_matrix=callback)

    def get_universe(self, universe: int) -> DMX512Universe:
        return self.universes[universe]

    def get_free_universe(self) -> Optional[int]:
        return next((universe for universe, data in self.universes.items()
                              if data.device is None), None)

_initialized = False
def init(
    DMX_UNIVERSE_COUNT,
    SERIAL_TIMEOUT,
    SERIAL_BAUDRATE,
    SERIAL_TRY_CONNECTION_TIME,
    DMX_HELLO_MSG,
    DMX_MESSAGE_BYTEORDER,
    DMX_LIGHT_FPS,
    DMX_ADDRESS_COUNT,
    DMX_KEY_FRAME_TIME):
    global _initialized
    if _initialized:
        raise RuntimeError("DMX512 модуль уже инициализирован")
    _initialized = True
    globals()["dmx512"] = DMX512Dispatcher(
        DMX_UNIVERSE_COUNT,
        SERIAL_TIMEOUT,
        SERIAL_BAUDRATE,
        SERIAL_TRY_CONNECTION_TIME,
        DMX_HELLO_MSG,
        DMX_MESSAGE_BYTEORDER,
        DMX_LIGHT_FPS,
        DMX_ADDRESS_COUNT,
        DMX_KEY_FRAME_TIME
    )
    dmx512.init()

def __getattr__(name):
    # Согласно PEP 562, функция __getattr__ модуля вызывается только в том
    # случае, если атрибут не был найден обычным путём и ожидает AttributeError
    if name == "dmx512":
        raise RuntimeError("DMX512 не инициализирован. Сначала вызовите init().")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
