from kivy.properties import ObjectProperty
from kivy.lang import Builder
from libs.uix.layouts import ModalBoxLayout
import libs.uix.menu_components  # lazy kv import initialize


Builder.load_file("ui/mdi/desktops/uix_context_menu.kv")


class DesktopUixContextMenu(ModalBoxLayout):
    desktop_uix = ObjectProperty()
