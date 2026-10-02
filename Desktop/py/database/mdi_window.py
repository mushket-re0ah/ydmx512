from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from libs.kivy_json_orm.fields import DictField, ObjectField, StringField
from libs.kivy_json_orm.table_implementation import DatabaseRow, DatabaseTable
from libs.serialize import serializable_or_raw_serializer

if TYPE_CHECKING:
    from database import YdmxDatabase


class RowMDIWindow(DatabaseRow):
    database: "YdmxDatabase"  # pyright: ignore[reportIncompatibleMethodOverride]
    table: "TableMDIWindow" # pyright: ignore[reportIncompatibleVariableOverride]

    title_id: str = StringField()
    layout_state: Dict[str, Any] = DictField()
    view_context: Dict[str, Any] = ObjectField(
        serialize=serializable_or_raw_serializer(),
        deserialize=lambda self, v: v,
        allownone=True
    )


class TableMDIWindow(DatabaseTable):
    database: "YdmxDatabase" # pyright: ignore[reportIncompatibleVariableOverride]
    get_row_by_id: Callable[[int], Optional[RowMDIWindow]] # pyright: ignore[reportIncompatibleMethodOverride]
    rows: Dict[int, RowMDIWindow] # pyright: ignore[reportIncompatibleVariableOverride]
    get_row_by_attribute: Callable[[str, Any], Optional[RowMDIWindow]] # pyright: ignore[reportIncompatibleMethodOverride]
    on_add_row: Callable[[RowMDIWindow], None] # pyright: ignore[reportIncompatibleMethodOverride]
    on_remove_row: Callable[[RowMDIWindow], None] # pyright: ignore[reportIncompatibleMethodOverride]
    add_row: Callable[..., RowMDIWindow] # pyright: ignore[reportIncompatibleMethodOverride]
    remove_row: Callable[[RowMDIWindow], None] # pyright: ignore[reportIncompatibleMethodOverride]
    __getattr__: Callable[[str], Callable[[Any], Optional[RowMDIWindow]]] # pyright: ignore[reportIncompatibleMethodOverride]

    cls_row = RowMDIWindow
    filename = "mdi_window.json"
