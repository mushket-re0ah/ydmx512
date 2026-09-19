from kivy.properties import ObjectProperty, StringProperty, ColorProperty
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from libs.uix.layouts import SectionPanel
from kivy.lang import Builder

Builder.load_string(
"""
<DeviceListPanel>:  # SectionPanel
    box: box
    scrollview: scrollview
    title_text: root.title
    size_hint: (None, 1)
    ScrollLayout:
        size_hint: (None, 1)
        width: "175dp"
        scrollview: scrollview
        RestrictedScrollView:
            id: scrollview
            scroll_by_content: True
            canvas.before:
                Color:
                    rgba: root.bg_scrollview
                Rectangle:
                    pos: self.pos
                    size: self.size
            BoxLayout:
                id: box
                orientation: "vertical"
                size_hint: (1, None)
                height: self.minimum_height
"""
)


class DeviceUi(BoxLayout):
    device = ObjectProperty(rebind=True)

    def on(self):
        self.device.connect()

    def off(self):
        self.device.close_connection()


class DeviceListPanel(SectionPanel):
    device_cls = ObjectProperty(DeviceUi)  # переопределить в наследнике
    observer = ObjectProperty()  # переопределить в наследнике

    title = StringProperty("untitled")  # переопределить в наследнике
    bg_scrollview = ColorProperty()  # переопределить в наследнике

    scroll_layout = ObjectProperty()
    scrollview = ObjectProperty()
    box = ObjectProperty()

    def on_kv_post(self, _):
        for dev in self.observer.devices:
            self._add_device(dev)
        self.observer.bind(
            on_new_device=self.on_new_device,
            on_remove_device=self.on_remove_device
        )

    def on_new_device(self, _, device):
        def add_device(_):
            self._add_device(device)
        Clock.schedule_once(add_device, -1)

    def _add_device(self, device):
        self.box.add_widget(self.device_cls(device=device))

    def on_remove_device(self, _, device):
        def remove_device(_):
            serial_ui = next((i for i in self.box.children if i.device is device), None)
            if serial_ui is not None:
                self.box.remove_widget(serial_ui)
        Clock.schedule_once(remove_device, -1)
