from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Tuple

from libs.kivy_json_orm.fields import ListField, StringField
from libs.kivy_json_orm.table_implementation import DatabaseRow, DatabaseTable

if TYPE_CHECKING:
    from database import YdmxDatabase


class RowPhaseCurveType(DatabaseRow):
    database: "YdmxDatabase"  # pyright: ignore[reportIncompatibleMethodOverride]
    table: "TablePhaseCurveType" # pyright: ignore[reportIncompatibleVariableOverride]

    title_id = StringField(allownone=True)  # None - пользовательский
    title = StringField("Без названия")
    dots = ListField()


LINEAR_TITLE_ID = "linear"
IN_OUT_TITLE_ID = "in_out"
SIN_TITLE_ID = "sin"
EXP_TITLE_ID = "exp"
LINEAR_WITH_SPEEDUP_TITLE_ID = "linear_with_speedup"
LINEAR_WITH_SPEEDDOWN_TITLE_ID = "linear_with_speeddown"
class TablePhaseCurveType(DatabaseTable):
    database: "YdmxDatabase" # pyright: ignore[reportIncompatibleVariableOverride]
    get_row_by_id: Callable[[int], Optional[RowPhaseCurveType]] # pyright: ignore[reportIncompatibleMethodOverride]
    rows: Dict[int, RowPhaseCurveType] # pyright: ignore[reportIncompatibleVariableOverride]
    get_row_by_attribute: Callable[[str, Any], Optional[RowPhaseCurveType]] # pyright: ignore[reportIncompatibleMethodOverride]
    on_add_row: Callable[[RowPhaseCurveType], None] # pyright: ignore[reportIncompatibleMethodOverride]
    on_remove_row: Callable[[RowPhaseCurveType], None] # pyright: ignore[reportIncompatibleMethodOverride]
    add_row: Callable[..., RowPhaseCurveType] # pyright: ignore[reportIncompatibleMethodOverride]
    remove_row: Callable[[RowPhaseCurveType], None] # pyright: ignore[reportIncompatibleMethodOverride]
    __getattr__: Callable[[str], Callable[[Any], Optional[RowPhaseCurveType]]] # pyright: ignore[reportIncompatibleMethodOverride]

    filename = "phase_curve_type.json"
    cls_row = RowPhaseCurveType

    def _get_default_rows_for_create(self) -> Tuple[Dict[str, Any], ...]:
        return (
            {
                "title_id": LINEAR_TITLE_ID,
                "title": "Линейная",
                "dots": ((0.0, 0.0), (1.0, 1.0))
            },
            {
                "title_id": IN_OUT_TITLE_ID,
                "title": "Изнутри наружу",
                "dots": ((0.0, 1.0), (0.5, 0.0), (1.0, 1.0))
            },
            {
                "title_id": SIN_TITLE_ID,
                "title": "Синус",
                "dots": ((0.0, 0.0), (0.25, 1.0), (0.5, 0.0), (0.75, -1.0), (1.0, 0.0))
            },
            {
                "title_id": EXP_TITLE_ID,
                "title": "Экспонента",
                "dots": ((0.0, 0.0), (0.2, 0.5), (0.4, 0.75), (0.6, 0.85), (0.8, 0.99), (1.0, 1.0))
            },
            {
                "title_id": LINEAR_WITH_SPEEDUP_TITLE_ID,
                "title": "Линейная с ускорением",
                "dots": ((0.0, 0.0), (0.5, 0.25), (1.0, 1.0))
            },
            {
                "title_id": LINEAR_WITH_SPEEDDOWN_TITLE_ID,
                "title": "Линейная с замедлением",
                "dots": ((0.0, 0.0), (0.5, 0.75), (1.0, 1.0))
            },
        )

    def get_default_row(self) -> RowPhaseCurveType:
        return self.rows[next(iter(self.rows))]
