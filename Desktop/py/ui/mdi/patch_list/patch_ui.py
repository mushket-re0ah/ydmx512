from typing import Any

from kivy.lang.builder import Builder
from kivy.properties import ObjectProperty

from libs.uix.button import HoverButton
from ui.components.patch_ui import BasePatchUi

Builder.load_file("ui/mdi/patch_list/patch_ui.kv")


class PatchUi(BasePatchUi):
    btn_remove: HoverButton = ObjectProperty()
    btn_add: HoverButton = ObjectProperty()

    def __init__(self, **kwargs: Any):
        self.bind(grid_pos=self._save_pos)
        super().__init__(selectable=True, **kwargs)
