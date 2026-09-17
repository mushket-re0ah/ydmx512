from libs.kivy_json_orm.table_implementation import DatabaseTable, DatabaseRow
from libs.kivy_json_orm.fields import StringField


class RowBrand(DatabaseRow):
    title = StringField("Без названия")


class TableBrand(DatabaseTable):
    cls_row = RowBrand
    filename = "brand.json"

    default_rows = [
        {"title": "Noname"}, {"title": "Showlight"}, {"title": "Dipper"},
        {"title": "Shehds"}, {"title": "Martin"}, {"title": "Robe"},
        {"title": "Showteach"}, {"title": "LightSky"}, {"title": "Antary"},
        {"title": "Cameo"},
    ]

    def get_default_row(self) -> RowBrand:
        return self.rows[next(iter(self.rows))]
