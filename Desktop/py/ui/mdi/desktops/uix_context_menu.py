from kivy.properties import ObjectProperty
from kivy.lang import Builder
from libs.uix.layouts import ModalBoxLayout


Builder.load_file("ui/mdi/desktops/uix_context_menu.kv")
Builder.load_file("ui/components/menu_components.kv")


class DesktopUixContextMenu(ModalBoxLayout):
    desktop_uix = ObjectProperty()
