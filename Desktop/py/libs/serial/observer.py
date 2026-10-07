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

    def _get_ports(self) -> List[ListPortInfo]:
        return list_ports.comports()  # pyright: ignore[reportReturnType]

    def _make_device(self, port: ListPortInfo) -> SerialDevice:  # pyright: ignore[reportIncompatibleMethodOverride]
        return self.device_cls(
            port_info=port,
            product_name=get_product_name_by_port(port)
        )


observer = SerialObserver()
