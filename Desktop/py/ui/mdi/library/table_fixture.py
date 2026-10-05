from typing import Tuple

from database import db
from database.fixture import RowFixture
from libs.uix.database_table import ColumnConfigTemplates
from libs.uix.database_table.column_config import ColumnConfig
from ui.mdi.library import LibraryContentEnum
from ui.mdi.library.table import LibraryTable

_columns_config = (
    ColumnConfigTemplates.checkbox_id(),
    ColumnConfigTemplates.text_field(header_text="Название",
                                     data_attribute="title"),
    ColumnConfigTemplates.text_field(header_text="Описание",
                                     data_attribute="note"),
    ColumnConfigTemplates.spinner(
        header_text="Бренд",
        data_attribute="brand",
        sorting_rule=lambda db_row: db_row.brand.title,
        other_attributes={
            "values": db.brand.rows,
            "values_getter": lambda this: list(this.values.values()),
            "value_to_host": lambda brand: brand.title
        }
    ),
    ColumnConfigTemplates.button_copy(),
    ColumnConfigTemplates.button_edit(),
    # ColumnConfigTemplates.button_remove()
)


class LibraryTableFixture(LibraryTable):
    table = db.fixture
    columns_config: Tuple[ColumnConfig, ...] = _columns_config

    def edit(self, fixture_row: RowFixture):
        self.library.change_content(
            LibraryContentEnum.FIXTURE_EDITOR,
            fixture_row
        )
