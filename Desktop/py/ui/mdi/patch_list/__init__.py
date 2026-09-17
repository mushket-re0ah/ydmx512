from ui.components.mdi_window import MDIWindow
from kivy.properties import StringProperty, ObjectProperty, NumericProperty
from database.fixture import RowFixture
from database.patch import RowPatch
from database import db
from typing import Optional
from dataclasses import dataclass, field
from libs.serialize import *
from libs.kivy_json_orm.fields import table_ref_serializer, table_ref_deserializer


class MDIPatchList(MDIWindow):
    _db_title_id = "patch_list"
    title_id = StringProperty(_db_title_id)  # Должно быть переназначено в наследнике
    title = StringProperty("Патч-лист")

    menu = ObjectProperty()
    patch_map = ObjectProperty()

    workspace = NumericProperty(0)

    view_context_template = {
        "workspace": 0,
        "menu.input_count_create_patch/value": 1,
        "menu.input_address_create_patch/value": None,
        "menu.input_universe_create_patch/value": 1,
        "menu.input_fixture/selected": {
            "default": db.fixture.get_default_row(),
            "serialize": table_ref_serializer(),
            "deserialize": table_ref_deserializer(lambda: db.fixture, fallback_fn=lambda: db.fixture.get_default_row())
        },
        "menu.input_add_address/value": 1,
        "menu.input_set_universe/value": 1,
        "menu.input_set_workspace/value": 1,
    }

    def on_open(self):
        if not self.menu:
            self.__create_patch_map()
            self.__create_menu()

    def create_patch(self,
                     fixture: RowFixture,
                     count=1,
                     universe=1,
                     start_address:Optional[int]=None):
        kwargs = {
            "fixture": fixture,
            "universe": universe,
            "workspace": self.patch_map.workspace_manager.workspace_now_index
        }
        if start_address:
            kwargs["start_address"] = start_address
        for i in range(count):
            db.patch.add_row(**kwargs)
            if start_address:
                kwargs["start_address"] += len(fixture.param_list_unpacked) + 1

    def __create_menu(self):
        from ui.mdi.patch_list.menu import PatchListMenu
        self.menu = PatchListMenu(patch_list=self, patch_map=self.patch_map)
        self.add_widget(self.menu, 1)

    def __create_patch_map(self):
        from ui.mdi.patch_list.patch_map import PatchMap
        self.patch_map = PatchMap(patch_list=self)
        self.add_widget(self.patch_map)
