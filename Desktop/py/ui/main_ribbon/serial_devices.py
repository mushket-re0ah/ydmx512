from kivy.properties import ObjectProperty, StringProperty, ColorProperty
from ui.components.device_list_panel import DeviceUi, DeviceListPanel
from libs.uix.button import HoverToggleButton
from kivy.uix.boxlayout import BoxLayout
from libs.serial.observer import observer as serial_observer
from misc import colorscheme


class SerialUi(DeviceUi):
    pass


class SerialDevicesNameFilterToggle(HoverToggleButton):
    pass


class TitleFilterSerialDeviceBox(BoxLayout):
    pass


class SerialDevices(DeviceListPanel):
    device_cls = ObjectProperty(SerialUi)
    observer = ObjectProperty(serial_observer)

    title = StringProperty("DMX устройства")
    bg_scrollview = ColorProperty(colorscheme.SerialDevices.bg)

    def on_kv_post(self, _):
        super().on_kv_post(_)
        self.remove_widget(self.section_label)
        box = TitleFilterSerialDeviceBox()
        box.add_widget(self.section_label)
        box.add_widget(SerialDevicesNameFilterToggle())
        self.add_widget(box, 1)
