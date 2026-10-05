from typing import TYPE_CHECKING, Tuple

from kivy.properties import ObjectProperty

from libs.kivy_json_orm.table_implementation import DatabaseTable
from libs.uix.database_table import DatabaseTableUi
from libs.uix.database_table.column_config import ColumnConfig

if TYPE_CHECKING:
    from ui.mdi.library import MDILibrary


class LibraryTable(DatabaseTableUi):
    library: "MDILibrary" = ObjectProperty()
    table: DatabaseTable
    columns_config: Tuple[ColumnConfig, ...]
