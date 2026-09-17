from libs.kivy_json_orm.table_implementation import DatabaseTable, DatabaseRow
from kivy.properties import (
    StringProperty, ListProperty
)
from libs.kivy_json_orm.fields import *


class RowPhaseCurveType(DatabaseRow):
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
    filename = "phase_curve_type.json"
    cls_row = RowPhaseCurveType

    default_rows = [
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
    ]

    def get_default_row(self) -> RowPhaseCurveType:
        return self.rows[next(iter(self.rows))]
