from typing import Any, Dict, Tuple

from libs.kivy_json_orm.fields import StringField
from libs.kivy_json_orm.table_implementation import DatabaseRow, DatabaseTable


class RowBrand(DatabaseRow):
    title: str = StringField("Без названия")


class TableBrand(DatabaseTable):
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
