from typing import Tuple

from database import db
from libs.uix.database_table import ColumnConfigTemplates
from libs.uix.database_table.column_config import ColumnConfig
from ui.mdi.library.table import LibraryTable

_columns_config = (
    ColumnConfigTemplates.checkbox_id(),
    ColumnConfigTemplates.text_field(
        header_text="Название",
        data_attribute="title",
        other_attributes={
            "valign": "center",
            "multiline": False
        }
    ),
    ColumnConfigTemplates.button_copy(),
    ColumnConfigTemplates.button_remove()
)


class LibraryTableBrand(LibraryTable):
    table = db.brand
    columns_config: Tuple[ColumnConfig, ...] = _columns_config

    def activate_menu_toggle(self):
        self.library.menu.toggle_brands.trigger_action(0)
