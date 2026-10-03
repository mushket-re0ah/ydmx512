from typing import TYPE_CHECKING, Optional

from kivy.properties import NumericProperty, ObjectProperty, StringProperty

from database import db
from database.fixture import RowFixture
from libs.kivy_json_orm.fields import table_ref_deserializer, table_ref_serializer
from libs.typecheck import UNSET
from ui.components.database_mdi_window import DatabaseMDIWindow

if TYPE_CHECKING:
    from ui.mdi.patch_list.menu import PatchListMenu
    from ui.mdi.patch_list.patch_map_section import PatchMapSection


class MDIPatchList(DatabaseMDIWindow):
    db_title_id: str = "patch_list"
    title: str = StringProperty("Патч-лист")

    menu: "PatchListMenu" = ObjectProperty()
    patch_map: "PatchMapSection" = ObjectProperty()

    workspace: int = NumericProperty(0)

    view_context_template = {
        "workspace": UNSET,
        "menu.input_count_create_patch/value": UNSET,
        "menu.input_address_create_patch/value": UNSET,
        "menu.input_universe_create_patch/value": UNSET,
        "menu.input_fixture/selected": {
            "default": db.fixture.get_default_row,
            "serialize": table_ref_serializer(),
            "deserialize": table_ref_deserializer(
                lambda: db.fixture,
                fallback_fn=db.fixture.get_default_row
            )
        },
        "menu.input_add_address/value": UNSET,
        "menu.input_set_universe/value": UNSET,
        "menu.input_set_workspace/value": UNSET,
    }

    def on_hidden(self, _, hidden: bool):
        super().on_hidden(_, hidden)
        if hidden or self.menu:
            return
        self.__create_patch_map()
        self.__create_menu()

    def create_patch(self,
                     fixture: RowFixture,
                     count: int=1,
                     universe: int=1,
                     start_address:Optional[int]=None):
        kwargs = {
            "fixture": fixture,
            "universe": universe,
            "workspace": self.patch_map.workspace_manager.workspace_now_index
        }
        if start_address:
            kwargs["start_address"] = start_address
        for _ in range(count):
            db.patch.add_row(**kwargs)
            if start_address is not None:
                start_address += len(fixture.param_list_unpacked) + 1
                kwargs["start_address"] = start_address

    def __create_menu(self):
        from ui.mdi.patch_list.menu import PatchListMenu
        self.menu = PatchListMenu(patch_list=self, patch_map=self.patch_map)
        self.add_widget(self.menu, 1)

    def __create_patch_map(self):
        from ui.mdi.patch_list.patch_map_section import PatchMapSection
        self.patch_map = PatchMapSection(patch_list=self)
        self.add_widget(self.patch_map)
