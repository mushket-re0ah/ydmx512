from kivy.properties import ObjectProperty
from kivy.lang import Builder
from libs.uix.layouts import ModalBoxLayout
from libs.uix.button import HoverButton
from database import db


Builder.load_file("ui/mdi/patch_list/map_context_menu.kv")


class PatchMapContextMenuButton(HoverButton):
    patch_map = ObjectProperty()
    fixture = ObjectProperty()

    def on_release(self):
        db.patch.add_row(
            fixture=self.fixture,
            workspace=self.patch_map.index,
            universe=1
        )


class PatchMapContextMenu(ModalBoxLayout):
    patch_map = ObjectProperty()
    scroll_layout = ObjectProperty()

    def on_kv_post(self, _):
        self.scroll_layout.scrollview.data = [
            {"fixture": fixture, "patch_map": self.patch_map}
            for fixture in db.fixture.rows.values()
        ]
