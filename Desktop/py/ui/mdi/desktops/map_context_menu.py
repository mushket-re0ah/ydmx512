from kivy.properties import ObjectProperty, StringProperty
from libs.uix.layouts import ModalBoxLayout
from libs.uix.button import HoverButton
from ui.components.rotary_button import RotaryButton
from ui.mdi.desktops.desktop_rotary import DesktopRotaryUix
from ui.mdi.desktops.desktop_slider_2d import DesktopSlider2D
from ui.mdi.desktops.desktop_map import widget_to_desktop_uix_type
from database import db
from kivy.lang import Builder


Builder.load_file("ui/mdi/desktops/map_context_menu.kv")


class DesktopMapContextMenuButton(HoverButton):
    desktop_map = ObjectProperty()
    widget_cls = ObjectProperty()
    widget_cls_text = StringProperty()

    def on_release(self):
        db.desktop_uix.add_row(
            workspace=self.desktop_map.index,
            uix_type=widget_to_desktop_uix_type[self.widget_cls]
        )


class DesktopMapContextMenu(ModalBoxLayout):
    desktop_map = ObjectProperty()
    scroll_layout = ObjectProperty()

    def on_kv_post(self, _):
        self.scroll_layout.scrollview.data = [
            {"widget_cls": DesktopRotaryUix, "widget_cls_text": "Rotary button", "desktop_map": self.desktop_map},
            {"widget_cls": DesktopSlider2D, "widget_cls_text": "Slider 2D", "desktop_map": self.desktop_map}
        ]
