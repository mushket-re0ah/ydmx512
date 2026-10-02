from kivy.lang import Builder
from kivy.properties import ObjectProperty

import libs.uix.menu_components  # lazy kv import initialize  # noqa: F401
from database.desktop_uix.desktop_uix import RowDesktopUix
from libs.uix.layouts import ModalBoxLayout

Builder.load_file("ui/mdi/desktops/uix_context_menu.kv")


class DesktopUixContextMenu(ModalBoxLayout):
    desktop_uix: RowDesktopUix = ObjectProperty()
