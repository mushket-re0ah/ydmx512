from typing import List, Tuple, Type

from kivy.properties import ObjectProperty
from serial.tools import list_ports
from serial.tools.list_ports_common import ListPortInfo

from libs.device_observer import DeviceObserver
from libs.serial.device import SerialDevice
from libs.serial.get_name_serial_usb import get_product_name_by_port


class SerialObserver(DeviceObserver):
    name: str = "SerialObserver"

    devices: Tuple[SerialDevice, ...]  # pyright: ignore[reportIncompatibleVariableOverride]
    device_cls: Type[SerialDevice] = ObjectProperty(SerialDevice)

    # def __init__(self, **kwargs: Any):
        # self._cached_names: Optional[FrozenSet[str]] = None
        # self._cached_ports: List[ListPortInfo] = []
        # super().__init__(**kwargs)

    def _get_ports(self) -> List[ListPortInfo]:  # pyright: ignore[reportReturnType]
        # current_names = self._quick_tty_names()  # os.listdir с фильтром
        # if current_names is not None and current_names == self._cached_names:
        #     return self._cached_ports
        # self._cached_names = current_names
        # self._cached_ports = list_ports.comports()  # pyright: ignore[reportAttributeAccessIssue]
        # return self._cached_ports
        return list_ports.comports()  # pyright: ignore[reportReturnType]

    def _make_device(self, port: ListPortInfo) -> SerialDevice:  # pyright: ignore[reportIncompatibleMethodOverride]
        return self.device_cls(
            port_info=port,
            product_name=get_product_name_by_port(port)
        )

    # def _quick_tty_names(self) -> Optional[FrozenSet[str]]:
    #     if platform == "linux":
    #         try:
    #             return frozenset(
    #                 n for n in os.listdir("/dev")
    #                 if n.startswith(("ttyUSB", "ttyACM"))
    #             )
    #         except OSError:
    #             return None
    #     elif platform == "win":
    #         return None
    #     elif platform == "macosx":
    #         return None
    #     return None

observer = SerialObserver()
