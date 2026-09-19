from libs.uix.input import HEXAInput
from ui.components.database_table import ColumnConfigTemplates
from ui.mdi.library.table import LibraryTable
from kivy.utils import get_hex_from_color
from database import db


_columns_config = [
    ColumnConfigTemplates.checkbox_id(),
    ColumnConfigTemplates.text_field(header_text="Название",
                                     data_attribute="title"),
    ColumnConfigTemplates.spinner(
        header_text="Тип",
        value_getter=lambda db_row: "Динамический" if db_row.is_dynamic else "Статический",
        sync_setter_widget=lambda widget, config, db_row, value: setattr(
            widget, 
            config.data_attribute, 
            "Динамический" if db_row.is_dynamic else "Статический",
        ),
        sync_setter_row=lambda db_row, config, widget, value: db_row.edit(is_dynamic=value == "Динамический"),
        sorting_rule=lambda db_row: "Динамический" if db_row.is_dynamic else "Статический",
        other_attributes={
            "values": ("Статический", "Динамический"),
            "values_getter": lambda this: this.values,
            "selected": None
        }
    ),
    ColumnConfigTemplates.hexa_field(
        header_text="Цвет",
        widget_class=HEXAInput,
        data_attribute="color",
        value_getter=lambda db_row: get_hex_from_color(db_row.color).upper(),
    ),
    ColumnConfigTemplates.button_copy(),
    ColumnConfigTemplates.button_remove()
]


class LibraryTableFixtureParams(LibraryTable):
    table = db.fixture_param
    columns_config = _columns_config

    def activate_menu_toggle(self):
        self.library.menu.toggle_params.trigger_action(0)
