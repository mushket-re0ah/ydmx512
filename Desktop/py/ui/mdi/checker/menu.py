from kivy.properties import ObjectProperty
from kivy.lang import Builder
from libs.uix.layouts import MenuPanel


Builder.load_file("ui/mdi/checker/menu.kv")


class CheckerMenu(MenuPanel):
    checker = ObjectProperty()
