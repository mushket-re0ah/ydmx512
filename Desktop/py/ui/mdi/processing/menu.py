from kivy.properties import ObjectProperty
from kivy.lang import Builder
from libs.uix.layouts import MenuPanel


Builder.load_file("ui/mdi/processing/menu.kv")


class ProcessingMenu(MenuPanel):
    processing = ObjectProperty()
    processing_map = ObjectProperty()
    view_context = ObjectProperty()
