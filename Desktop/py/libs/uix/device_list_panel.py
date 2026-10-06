from typing import Any, Type

from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.lang import Builder
from kivy.properties import ColorProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from libs.typecheck import RGBA
from libs.uix.layouts import SectionPanel
from libs.uix.restricted_scrollview import RestrictedScrollView
from libs.uix.scroll_layout import ScrollLayout

Builder.load_string(
"""
<DeviceListPanel>:  # SectionPanel
    scroll_layout: scroll_layout
    scrollview: scrollview
    box: box
    title_text: root.title
    size_hint: (None, 1)
    ScrollLayout:
        id: scroll_layout
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
    device: EventDispatcher = ObjectProperty(rebind=True)

    def on(self):
        self.device.connect()

    def off(self):
        self.device.close_connection()


class DeviceListPanel(SectionPanel):
    device_cls: Type[DeviceUi] = ObjectProperty(DeviceUi)  # переопределить в наследнике
    observer: EventDispatcher = ObjectProperty()  # переопределить в наследнике

    title: str = StringProperty("untitled")  # переопределить в наследнике
    bg_scrollview: RGBA = ColorProperty()  # переопределить в наследнике

    scroll_layout: ScrollLayout = ObjectProperty()
    scrollview: RestrictedScrollView = ObjectProperty()
    box: BoxLayout = ObjectProperty()

    def on_kv_post(self, base_widget: Widget):
        self._update_device_list()
        self.observer.bind(
            on_new_device=self.on_new_device,
            on_remove_device=self.on_remove_device
        )

    def _update_device_list(self, *_ :Any):
        self.box.clear_widgets()
        for dev in self.observer.devices:
            self._add_device(dev)

    def on_new_device(self, _, device: EventDispatcher):
        def add_device(_: Any):
            self._add_device(device)
        Clock.schedule_once(add_device, -1)

    def _add_device(self, device: EventDispatcher):
        self.box.add_widget(self.device_cls(device=device))

    def on_remove_device(self, _, device: EventDispatcher):
        def remove_device(_: Any):
            self._remove_device(device)
        Clock.schedule_once(remove_device, -1)

    def _remove_device(self, device: EventDispatcher):
        serial_ui = next((i for i in self.box.children if i.device is device), None)
        if serial_ui is not None:
            self.box.remove_widget(serial_ui)
