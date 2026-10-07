from typing import Type

from kivy.lang import Builder
from kivy.properties import ColorProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from database import db
from libs.serial.device import SerialDevice
from libs.serial.observer import SerialObserver
from libs.serial.observer import observer as serial_observer
from libs.typecheck import RGBA
from libs.uix.button import HoverToggleButton
from libs.uix.device_list_panel import DeviceListPanel, DeviceUi
from misc import colorscheme

Builder.load_file("ui/main_ribbon/serial_devices.kv")


class SerialUi(DeviceUi):
    pass


class SerialDevicesNameFilterToggle(HoverToggleButton):
    pass


class TitleFilterSerialDeviceBox(BoxLayout):
    pass


class SerialDevices(DeviceListPanel):
    device_cls: Type[DeviceUi] = ObjectProperty(SerialUi)
    observer: SerialObserver = ObjectProperty(serial_observer)  # pyright: ignore[reportIncompatibleVariableOverride]

    title: str = StringProperty("DMX устройства")
    bg_scrollview: RGBA = ColorProperty(colorscheme.SerialDevices.bg)
    title_filter_device_box: TitleFilterSerialDeviceBox = ObjectProperty()

    FILTER_NAME_LIST = frozenset({
        "Univer DMX A1",
        "U-DMX A11",
        "U-DMX K12",
        "U-DMX K23",
        "U-DMX K46",
    })

    def on_kv_post(self, base_widget: Widget):
        super().on_kv_post(base_widget)
        self.remove_widget(self.section_label)
        box = TitleFilterSerialDeviceBox()
        self.title_filter_device_box = box
        box.add_widget(self.section_label)
        box.add_widget(SerialDevicesNameFilterToggle())
        self.add_widget(box, 1)
        db.misc.bind(do_filter_serial_names=self._update_device_list)

    def _add_device(self, device: SerialDevice):  # pyright: ignore[reportIncompatibleMethodOverride]
        if not db.misc.do_filter_serial_names or device.product_name in self.FILTER_NAME_LIST:
            super()._add_device(device)  # pyright: ignore[reportArgumentType]
