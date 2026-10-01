from typing import TYPE_CHECKING

from kivy.lang import Builder
from kivy.properties import ObjectProperty

from libs.uix.layouts import MenuPanel

if TYPE_CHECKING:
    from ui.mdi.checker import MDIChecker

Builder.load_file("ui/mdi/checker/menu.kv")


class CheckerMenu(MenuPanel):
    checker: "MDIChecker" = ObjectProperty()
