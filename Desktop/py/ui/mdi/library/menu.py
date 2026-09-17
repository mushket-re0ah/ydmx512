from kivy.properties import ObjectProperty
from libs.uix.layouts import MenuPanel
from kivy.lang import Builder
from database import db


Builder.load_file("ui/mdi/library/menu.kv")


class LibraryMenu(MenuPanel):
    library = ObjectProperty()

    toggle_fixture = ObjectProperty()
    toggle_params = ObjectProperty()
    toggle_brands = ObjectProperty()

    def change_table(self, table):
        self.library.change_table_now(table)

    def on_create_release(self):
        context_tables = self.library.ContextTables
        table_context = self.library.view_context.table_now
        if table_context is context_tables.FIXTURE:
            self._open_fixture_editor()
        elif table_context is context_tables.FIXTURE_PARAMS:
            self._create_fixture_param()
        elif table_context is context_tables.BRAND:
            self._create_brand()

    def _create_brand(self):
        db.brand.add_row()

    def _create_fixture_param(self):
        db.fixture_param.add_row()

    def _open_fixture_editor(self):
        self.library.change_context_now(self.library.Contexts.EDITOR)
