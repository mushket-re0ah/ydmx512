from kivy.properties import ObjectProperty, StringProperty, DictProperty
from kivy.lang import Builder
from ui.components.database_mdi_window import DatabaseMDIWindow
from ui.mdi.library.table import LibraryTable
from database import db
from database.fixture import RowFixture, FixtureChannelsGroup
from database.brand import RowBrand
from typing import Union, List, Optional
from enum import Enum, auto
from dataclasses import dataclass, field
from misc import constants
from libs.serialize import *
from abc import ABC, abstractmethod
import json
from libs.kivy_json_orm.fields import *


class LibraryContexts(Enum):
    MENU = auto()
    EDITOR = auto()


class LibraryContextTables(Enum):
    FIXTURE = auto()
    FIXTURE_PARAMS = auto()
    BRAND = auto()


class LibraryTableContext(SerializableMixin):
    selected_rows = ListField()
    size_hint_x = ListField()
    scroll_y = NumericField(1.0)


class LibraryEditorContext(SerializableMixin):
    fixture = RefField(lambda: db.get("fixture"))
    title = StringField()
    note = StringField()
    brand = RefField(lambda: db.get("brand"), lambda: db.get("brand").get_default_row(), default_factory=lambda: db.get("brand").get_default_row())
    icon = StringField(constants.DEFAULT_FIXTURE_ICON.as_posix())
    temp_dependence = NumericField(0)
    channels_groups = ListNestedField(FixtureChannelsGroup)


class LibraryViewContext(SerializableMixin):
    context_now = EnumField(LibraryContexts, LibraryContexts.MENU)
    table_now = EnumField(LibraryContextTables, LibraryContextTables.FIXTURE)
    fixture_now = RefField(lambda: db.get("fixture"), allownone=True)

    fixture_editor_create = NestedField(LibraryEditorContext, default_factory=LibraryEditorContext)
    fixture_editor_edit = NestedField(LibraryEditorContext, default_factory=LibraryEditorContext)

    table_fixture = NestedField(LibraryTableContext, default_factory=LibraryTableContext)
    table_fixture_params = NestedField(LibraryTableContext, default_factory=LibraryTableContext)
    table_brand = NestedField(LibraryTableContext, default_factory=LibraryTableContext)

    def get_table_data_by_context(self, table_context: LibraryContextTables) -> LibraryTableContext:
        if table_context is LibraryContextTables.FIXTURE:
            return self.table_fixture
        elif table_context is LibraryContextTables.FIXTURE_PARAMS:
            return self.table_fixture_params
        elif table_context is LibraryContextTables.BRAND:
            return self.table_brand


def _get_class_table_by_context(table_context: LibraryContextTables) -> LibraryTable:
    if table_context is LibraryContextTables.FIXTURE:
        from ui.mdi.library.table_fixture import LibraryTableFixture
        return LibraryTableFixture
    elif table_context is LibraryContextTables.FIXTURE_PARAMS:
        from ui.mdi.library.table_fixture_params import LibraryTableFixtureParams
        return LibraryTableFixtureParams
    elif table_context is LibraryContextTables.BRAND:
        from ui.mdi.library.table_brand import LibraryTableBrand
        return LibraryTableBrand


class ContextState(ABC):
    @abstractmethod
    def enter(self, library: "MDILibrary"):
        pass

    @abstractmethod
    def exit(self, library: "MDILibrary"):
        pass


class MenuState(ContextState):
    def enter(self, library: "MDILibrary"):
        # Восстанавливаем предыдущее состояние таблицы
        library.table_now = library._create_table_by_context()
        library.table_now.activate_menu_toggle()
        library.add_widget(library.menu)
        library.add_widget(library.table_now)
        library.view_context.context_now = LibraryContexts.MENU
        library.property("view_context").dispatch(library)

    def exit(self, library: "MDILibrary"):
        library.remove_widget(library.menu)
        library.remove_widget(library.table_now)
        library.property("view_context").dispatch(library)


class EditorState(ContextState):
    def __init__(self, row: Optional[RowFixture] = None):
        self.row = row

    def enter(self, library: "MDILibrary"):
        library.editor = self._create_editor(library)
        library.add_widget(library.editor)
        library.view_context.context_now = LibraryContexts.EDITOR
        library.view_context.fixture_now = self.row
        library.property("view_context").dispatch(library)

    def exit(self, library: "MDILibrary"):
        library.remove_widget(library.editor)
        library.editor = None
        library.property("view_context").dispatch(library)

    def _create_editor(self, library: "MDILibrary") -> "LibraryFixtureEditor":
        from ui.mdi.library.fixture_editor import LibraryFixtureEditor
        return LibraryFixtureEditor(library=library,
                                    fixture=self.row,
                                    context=self.__get_fixture_editor_context(library))

    def __get_fixture_editor_context(self, library: "MDILibrary") -> LibraryEditorContext:
        if self.row is None:
            return library.view_context.fixture_editor_create
        else:
            return library.view_context.fixture_editor_edit


class MDILibrary(DatabaseMDIWindow):
    _db_title_id = "library"
    title = StringProperty("Библиотека")

    menu = ObjectProperty()
    editor = ObjectProperty(allownone=True)
    table_now = ObjectProperty()

    # view_context_template = {
    #     "workspace": 0,
    # }

    Contexts = LibraryContexts
    ContextTables = LibraryContextTables

    context_state: ContextState = None
    def on_hidden(self, _, hidden: bool):
        super().on_hidden(_, hidden)
        if hidden or self.menu:
            return
        self.__create_menu()
        self.__init_context()



    # Костыль для нового view_context
    def get_view_context(self):
        return self.state.get("view_context", {})
    def set_view_context(self, view_context):
        state = self.state.copy()
        state["view_context"] = view_context
        self.state = state
        return True
    view_context = AliasProperty(
        get_view_context,
        set_view_context,
    )
    def on_view_context(self, _, view_context):
        self._save_vc()
    def _save_vc(self):
        self.mdi_db_row.edit(view_context=self.view_context)





    def change_context_now(self, context: LibraryContexts, row: RowFixture = None):
        new_state = self._state_factory(context, row)
        
        if isinstance(self.context_state, new_state.__class__):
            return

        self.context_state.exit(self)
        self.context_state = new_state
        self.context_state.enter(self)

    def __init_context(self):
        # костыльные обращения к view_context
        if not self.mdi_db_row.view_context:
            self.view_context = LibraryViewContext()
        else:
            self.view_context = LibraryViewContext.from_data(self.mdi_db_row.view_context)

        self.context_state = self._state_factory(
            self.view_context.context_now,
            self.view_context.fixture_now
        )
        self.context_state.enter(self)

    def __switch_table(self, new_context: LibraryContextTables):
        if self.table_now in self.children:
            self._save_table_context()
            self.remove_widget(self.table_now)

        self.view_context.table_now = new_context
        self.table_now = self._create_table_by_context()
        self.add_widget(self.table_now)

    def change_table_now(self, context: LibraryContextTables):
        if self.view_context.table_now == context:
            return
        self.__switch_table(context)
        self.property("view_context").dispatch(self)

    def _save_table_context(self, *args):
        if self.table_now is not None:
            self.table_now.save_context()

    def _create_table_by_context(self) -> LibraryTable:
        table_context = self.view_context.table_now
        table_data_context = self.view_context.get_table_data_by_context(table_context)
        table_class = _get_class_table_by_context(table_context)
        table = table_class(library=self,
                            context=table_data_context)
        return table

    def __create_menu(self):
        from ui.mdi.library.menu import LibraryMenu
        self.menu = LibraryMenu(library=self)

    def _state_factory(self, context: LibraryContexts, row: RowFixture = None) -> ContextState:
        return {
            LibraryContexts.MENU: MenuState(),
            LibraryContexts.EDITOR: EditorState(row)
        }[context]
