from kivy.clock import Clock
from libs.kivy_json_orm.table_implementation import DatabaseTable, DatabaseRow
from libs.serialize import serializable_or_raw_serializer
from libs.kivy_json_orm.fields import StringField, BooleanField, DictField, ObjectField


class RowMDIWindow(DatabaseRow):
    title_id = StringField()
    layout_state = DictField()
    view_context = ObjectField(serialize=serializable_or_raw_serializer(), deserialize=lambda self, v: v, allownone=True)


class TableMDIWindow(DatabaseTable):
    cls_row = RowMDIWindow
    filename = "mdi_window.json"
