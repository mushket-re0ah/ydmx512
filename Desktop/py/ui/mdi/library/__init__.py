from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Tuple, Type, Union

from kivy.properties import AliasProperty, BooleanProperty, ObjectProperty, StringProperty

from database import db
from database.fixture import FixtureChannelsGroup, RowFixture
from libs.kivy_json_orm.fields import table_ref_deserializer, table_ref_serializer
from libs.kivy_mixins import ViewContextDefaultData, ViewContextTemplateInnerDict
from libs.properties import EnumProperty
from libs.serialize import (
    enum_deserializer,
    enum_serializer,
    list_of_serializable_deserializer,
    list_of_serializable_serializer,
)
from libs.typecheck import UNSET
from libs.uix.button import HoverToggleButton
from ui.components.database_mdi_window import DatabaseMDIWindow
from ui.mdi.library.table import LibraryTable

if TYPE_CHECKING:
    from ui.mdi.library.fixture_editor import LibraryFixtureEditor
    from ui.mdi.library.menu import LibraryMenu


class LibraryTableEnum(Enum):
    FIXTURE = auto()
    FIXTURE_PARAMS = auto()
    BRAND = auto()


class LibraryContentEnum(Enum):
    FIXTURE = auto()
    FIXTURE_PARAMS = auto()
    BRAND = auto()
    FIXTURE_EDITOR = auto()


class MDILibrary(DatabaseMDIWindow):
    db_title_id: str = "library"
    title: str = StringProperty("Библиотека")

    menu: "LibraryMenu" = ObjectProperty()

    table_now_enum: LibraryTableEnum = EnumProperty(
        LibraryTableEnum,
        LibraryTableEnum.FIXTURE
    )
    table_now: Optional[LibraryTable] = ObjectProperty(None, allownone=True)

    table_now_dynamic_var = AliasProperty(
        lambda self: self.table_now_enum.value,
        bind=("table_now_enum",)
    )

    content_enum: LibraryContentEnum = EnumProperty(
        LibraryContentEnum,
        LibraryContentEnum.FIXTURE
    )
    content_now: Optional[Union[LibraryTable, "LibraryFixtureEditor"]] = ObjectProperty(
        None,
        allownone=True
    )

    fixture_editor: Optional["LibraryFixtureEditor"] = ObjectProperty(
        None,
        allownone=True
    )
    fixture_editor_edit_mode: bool = BooleanProperty(False)
    context_fixture: Optional[RowFixture] = ObjectProperty(allownone=True)

    FIXTURE_EDITOR_TEMPLATE_KEYS: Dict[
            str,
            Tuple[
                Union[ViewContextDefaultData, ViewContextTemplateInnerDict],
                Callable[[RowFixture], Any]
            ]
        ] = {
        "fixture_editor/title@fixture_editor_edit_mode": (
            UNSET,
            lambda fixture: fixture.title
        ),
        "fixture_editor/note@fixture_editor_edit_mode": (
            UNSET,
            lambda fixture: fixture.note
        ),
        "fixture_editor/brand@fixture_editor_edit_mode": (
            {
                "default": db.brand.get_default_row,
                "serialize": table_ref_serializer(),
                "deserialize": table_ref_deserializer(
                    lambda: db.brand,
                    fallback_fn=db.brand.get_default_row
                )
            },
            lambda fixture: fixture.brand
        ),
        "fixture_editor/icon@fixture_editor_edit_mode": (
            UNSET,
            lambda fixture: fixture.icon
        ),
        "fixture_editor/temp_dependence@fixture_editor_edit_mode": (
            UNSET,
            lambda fixture: fixture.temp_dependence
        ),
        "fixture_editor/channels_groups@fixture_editor_edit_mode": (
            {
                "default": tuple,
                "serialize": list_of_serializable_serializer(),
                "deserialize": list_of_serializable_deserializer(FixtureChannelsGroup)
            },
            lambda fixture: tuple(i.get_copy() for i in fixture.channels_groups)
        )
    }

    view_context_template = {
        "fixture_editor_edit_mode": UNSET,
        "context_fixture": {
            "default": UNSET,
            "serialize": table_ref_serializer(),
            "deserialize": table_ref_deserializer(
                lambda: db.fixture,
                fallback_fn=lambda: None,
            ),
        },

        "content_enum": {
            "default": LibraryContentEnum.FIXTURE,
            "serialize": enum_serializer(),
            "deserialize": enum_deserializer(LibraryContentEnum)
        },
        "table_now_enum": {
            "default": LibraryTableEnum.FIXTURE,
            "serialize": enum_serializer(),
            "deserialize": enum_deserializer(LibraryTableEnum)
        },
        "table_now.scroll_layout.scrollview/scroll_element@table_now_dynamic_var": UNSET,
        "table_now/selected_rows@table_now_dynamic_var": UNSET,

        **{
            vc_path: value[0]
            for vc_path, value in FIXTURE_EDITOR_TEMPLATE_KEYS.items()
        }
    }

    def on_hidden(self, _, hidden: bool):
        super().on_hidden(_, hidden)
        if hidden or self.menu:
            return
        self.__create_menu()

    def __create_menu(self):
        from ui.mdi.library.menu import LibraryMenu
        self.menu = LibraryMenu(library=self)
        self.add_widget(self.menu)
        self._try_init_content()

    def on__view_context_loaded(self, *_:Any):
        self._try_init_content()

    def _try_init_content(self):
        if self.menu is None or not self._view_context_loaded:
            return
        if self.content_now is not None:
            return
        self.property("content_enum").dispatch(self)

    def on_content_enum(self, _, content_enum: LibraryContentEnum):
        if self.menu is None or not self._view_context_loaded:
            return

        if content_enum is LibraryContentEnum.FIXTURE:
            from ui.mdi.library.table_fixture import LibraryTableFixture
            self._show_table(
                LibraryTableFixture,
                LibraryTableEnum.FIXTURE,
                self.menu.toggle_fixture
            )

        elif content_enum is LibraryContentEnum.FIXTURE_PARAMS:
            from ui.mdi.library.table_fixture_params import LibraryTableFixtureParams
            self._show_table(
                LibraryTableFixtureParams,
                LibraryTableEnum.FIXTURE_PARAMS,
                self.menu.toggle_params
            )

        elif content_enum is LibraryContentEnum.BRAND:
            from ui.mdi.library.table_brand import LibraryTableBrand
            self._show_table(
                LibraryTableBrand,
                LibraryTableEnum.BRAND,
                self.menu.toggle_brands
            )

        elif content_enum is LibraryContentEnum.FIXTURE_EDITOR:
            self._show_editor()

    def _hide_menu(self):
        if self.menu.parent:
            self.remove_widget(self.menu)

    def _show_menu(self):
        if self.menu.parent is None:
            self.add_widget(self.menu)

    def _show_table(
            self,
            table_cls: Type[LibraryTable],
            table_enum: LibraryTableEnum,
            menu_toggle: HoverToggleButton
        ):
        self.fixture_editor = None
        self.table_now_enum = table_enum
        self.table_now = table_cls(library=self)
        self._show_menu()
        self._show_content(self.table_now)
        menu_toggle.trigger_action(0)

    def _show_editor(self):
        from ui.mdi.library.fixture_editor import LibraryFixtureEditor
        self.table_now = None
        self.fixture_editor = LibraryFixtureEditor(library=self)
        self.fixture_editor.init()
        self._hide_menu()
        self._show_content(self.fixture_editor)

    def _show_content(self, content: Union[LibraryTable, "LibraryFixtureEditor"]):
        if self.content_now is not None:
            self.content_now.parent.remove_widget(self.content_now)
        self.content_now = content
        self.add_widget(content)

    def _prepare_editor_data(self, fixture: Optional[RowFixture]):
        edit_mode = fixture is not None
        self.fixture_editor_edit_mode = edit_mode
        if edit_mode:
            if self.context_fixture is not fixture:
                for vc_path, value in self.FIXTURE_EDITOR_TEMPLATE_KEYS.items():
                    _, fixture_getter = value
                    self._set_vc(vc_path, fixture_getter(fixture), edit_mode)
                self.context_fixture = fixture

    def reset_editor_data(self):
        for vc_path, _ in self.FIXTURE_EDITOR_TEMPLATE_KEYS.items():
            self._wipe_vc(vc_path, self.fixture_editor_edit_mode)
        self.context_fixture = None

    def change_content(
            self,
            content_enum: LibraryContentEnum,
            fixture: Optional[RowFixture]=None
        ):
        if content_enum is LibraryContentEnum.FIXTURE_EDITOR:
            self._prepare_editor_data(fixture)
        self.content_enum = content_enum
