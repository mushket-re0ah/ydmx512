from typing import FrozenSet, List, Optional, Tuple, Type

from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty, ListProperty, ObjectProperty
from serial.tools import list_ports
from serial.tools.list_ports_common import ListPortInfo

from libs import logger
from libs.serial.device import SerialDevice, SerialState
from libs.serial.get_name_serial_usb import get_product_name_by_port


class SerialObserver(EventDispatcher):
    devices: List[SerialDevice] = ListProperty()
    do_filter_devices: bool = BooleanProperty(False)
    filter_name_list: FrozenSet[str] = ObjectProperty()  # set of str
    device_cls: Type[SerialDevice] = ObjectProperty(SerialDevice)

    __events__ = ("on_new_device", "on_remove_device")

    def on_new_device(self, device: SerialDevice):
        logger.info(f"SerialObserver: new device {device}")

    def on_remove_device(self, device: SerialDevice):
        logger.info(f"SerialObserver: remove device {device}")

    def monitor_connections(self):
        ports = self._get_list_ports()
        port_info_list = [i[0] for i in ports]
        for port_info, product_name in ports:
            is_device_found = any(device.matches_port(port_info)
                                  for device in self.devices)
            if not is_device_found:
                device = self.device_cls(
                    port_info=port_info,
                    product_name=product_name
                )
                self.devices.append(device)
                self.dispatch("on_new_device", device)

        for device in self.devices:
            is_device_found = any(device.matches_port(port_info)
                                  for port_info in port_info_list)
            if not is_device_found:
                if device.state is SerialState.OFF:
                    self.devices.remove(device)
                    self.dispatch("on_remove_device", device)

    def _get_list_ports(self) -> List[Tuple[ListPortInfo, Optional[str]]]:
        result: List[Tuple[ListPortInfo, Optional[str]]] = []
        for port in list_ports.comports():
            product_name = get_product_name_by_port(port)
            if self.do_filter_devices:
                if product_name in self.filter_name_list:
                    result.append((port, product_name))
            else:
                result.append((port, product_name))
        return result

observer = SerialObserver()
