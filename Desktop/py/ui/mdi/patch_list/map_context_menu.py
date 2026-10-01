from typing import TYPE_CHECKING

from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.widget import Widget

from database import db
from database.fixture import RowFixture
from libs.uix.button import HoverButton
from libs.uix.layouts import ModalBoxLayout
from libs.uix.scroll_layout import ScrollLayout
from ui.mdi.patch_list.patch_map import PatchMap

Builder.load_file("ui/mdi/patch_list/map_context_menu.kv")


class PatchMapContextMenuButton(HoverButton):
    patch_map: PatchMap = ObjectProperty()
    fixture: RowFixture = ObjectProperty()

    def on_release(self):
        db.patch.add_row(
            fixture=self.fixture,
            workspace=self.patch_map.index,
            universe=1
        )


class PatchMapContextMenu(ModalBoxLayout):
    patch_map: PatchMap = ObjectProperty()
    scroll_layout: ScrollLayout = ObjectProperty()

    def on_kv_post(self, base_widget: Widget):
        self.scroll_layout.scrollview.data = [
            {"fixture": fixture, "patch_map": self.patch_map}
            for fixture in db.fixture.rows.values()
        ]
