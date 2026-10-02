from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Tuple

from libs.kivy_json_orm.fields import StringField
from libs.kivy_json_orm.table_implementation import DatabaseRow, DatabaseTable

if TYPE_CHECKING:
    from database import YdmxDatabase


class RowBrand(DatabaseRow):
    database: "YdmxDatabase"  # pyright: ignore[reportIncompatibleMethodOverride]
    table: "TableBrand" # pyright: ignore[reportIncompatibleVariableOverride]

    title: str = StringField("Без названия")


class TableBrand(DatabaseTable):
    database: "YdmxDatabase" # pyright: ignore[reportIncompatibleVariableOverride]
    get_row_by_id: Callable[[int], Optional[RowBrand]] # pyright: ignore[reportIncompatibleMethodOverride]
    rows: Dict[int, RowBrand] # pyright: ignore[reportIncompatibleVariableOverride]
    get_row_by_attribute: Callable[[str, Any], Optional[RowBrand]] # pyright: ignore[reportIncompatibleMethodOverride]
    on_add_row: Callable[[RowBrand], None] # pyright: ignore[reportIncompatibleMethodOverride]
    on_remove_row: Callable[[RowBrand], None] # pyright: ignore[reportIncompatibleMethodOverride]
    add_row: Callable[..., RowBrand] # pyright: ignore[reportIncompatibleMethodOverride]
    remove_row: Callable[[RowBrand], None] # pyright: ignore[reportIncompatibleMethodOverride]
    __getattr__: Callable[[str], Callable[[Any], Optional[RowBrand]]] # pyright: ignore[reportIncompatibleMethodOverride]

    cls_row = RowBrand
    filename = "brand.json"

    def _get_default_rows_for_create(self) -> Tuple[Dict[str, Any], ...]:
        return (
            {"title": "Noname"}, {"title": "Showlight"}, {"title": "Dipper"},
            {"title": "Shehds"}, {"title": "Martin"}, {"title": "Robe"},
            {"title": "Showteach"}, {"title": "LightSky"}, {"title": "Antary"},
            {"title": "Cameo"},
        )

    def get_default_row(self) -> RowBrand:
        return self.rows[next(iter(self.rows))]
