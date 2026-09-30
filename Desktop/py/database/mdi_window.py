from typing import Any, Dict

from libs.kivy_json_orm.fields import DictField, ObjectField, StringField
from libs.kivy_json_orm.table_implementation import DatabaseRow, DatabaseTable
from libs.serialize import serializable_or_raw_serializer


class RowMDIWindow(DatabaseRow):
    title_id: str = StringField()
    layout_state: Dict[str, Any] = DictField()
    view_context: Dict[str, Any] = ObjectField(serialize=serializable_or_raw_serializer(), deserialize=lambda self, v: v, allownone=True)


class TableMDIWindow(DatabaseTable):
    cls_row = RowMDIWindow
    filename = "mdi_window.json"
