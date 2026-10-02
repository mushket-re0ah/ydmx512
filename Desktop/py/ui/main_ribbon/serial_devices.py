from typing import Type

from kivy.lang import Builder
from kivy.properties import ColorProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

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

    def on_kv_post(self, base_widget: Widget):
        super().on_kv_post(base_widget)
        self.remove_widget(self.section_label)
        box = TitleFilterSerialDeviceBox()
        self.title_filter_device_box = box
        box.add_widget(self.section_label)
        box.add_widget(SerialDevicesNameFilterToggle())
        self.add_widget(box, 1)
