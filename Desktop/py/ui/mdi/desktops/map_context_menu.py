from typing import TYPE_CHECKING, Type

from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.widget import Widget

from database import db
from libs.uix.button import HoverButton
from libs.uix.layouts import ModalBoxLayout
from libs.uix.scroll_layout import ScrollLayout
from ui.mdi.desktops.desktop_map_section import widget_to_desktop_uix_type
from ui.mdi.desktops.desktop_rotary import DesktopRotaryUix
from ui.mdi.desktops.desktop_slider_2d import DesktopSlider2D
from ui.mdi.desktops.desktop_uix import DesktopUix

if TYPE_CHECKING:
    from ui.mdi.desktops.desktop_map import DesktopMap


Builder.load_file("ui/mdi/desktops/map_context_menu.kv")


class DesktopMapContextMenuButton(HoverButton):
    desktop_map: "DesktopMap" = ObjectProperty()
    widget_cls: Type[DesktopUix] = ObjectProperty()
    widget_cls_text: str = StringProperty()

    def on_release(self):
        db.desktop_uix.add_row(
            workspace=self.desktop_map.index,
            uix_type=widget_to_desktop_uix_type[self.widget_cls]
        )


class DesktopMapContextMenu(ModalBoxLayout):
    desktop_map: "DesktopMap" = ObjectProperty()
    scroll_layout: ScrollLayout = ObjectProperty()

    def on_kv_post(self, base_widget: Widget):
        self.scroll_layout.scrollview.data = [
            {
                "widget_cls": DesktopRotaryUix,
                "widget_cls_text": "Rotary button",
                "desktop_map": self.desktop_map
            },
            {
                "widget_cls": DesktopSlider2D,
                "widget_cls_text": "Slider 2D",
                "desktop_map": self.desktop_map
            }
        ]
