from functools import partial
from typing import Any, Tuple

from kivy.uix.widget import Widget

from database import db
from database.scene import RowScene, TableScene
from libs.uix.database_table import ColumnConfigTemplates, DatabaseTableUi
from libs.uix.database_table.column_config import ColumnConfig
from misc import constants


def _update_select_button(widget: Widget, db_row: RowScene, *_):
    widget.disabled = db_row is db.scene.scene_now

def _select_button_setter(widget: Widget, db_row: RowScene):
    widget.text = "Выбрать"
    old = getattr(widget, "_scene_now_cb", None)
    if old is not None:
        db.scene.unbind(scene_now=old)
    cb = partial(_update_select_button, widget, db_row)
    widget._scene_now_cb = cb
    db.scene.bind(scene_now=cb)
    _update_select_button(widget, db_row)


_columns_config = (
    ColumnConfigTemplates.text_field(header_text="Название",
                                     data_attribute="title"),
    ColumnConfigTemplates.text_field(header_text="Описание",
                                     data_attribute="note"),
    ColumnConfigTemplates.numeric_field(
        header_text="Темп",
        data_attribute="temp",
        other_attributes={
            "minimum": constants.TEMP_MINIMUM,
            "maximum": constants.TEMP_MAXIMUM
        },
    ),
    ColumnConfigTemplates.numeric_field(
        header_text="Диммер",
        data_attribute="dimmer",
        other_attributes={
            "minimum": constants.DIMMER_MINIMUM,
            "maximum": constants.DIMMER_MAXIMUM
        }
    ),
    ColumnConfigTemplates.numeric_field(
        header_text="Такты",
        data_attribute="beats_count",
        other_attributes={
            "minimum": constants.BEATS_COUNT_MINIMIUM,
            "maximum": constants.BEATS_COUNT_MAXIMUM
        }
    ),
    ColumnConfigTemplates.button_copy(),
    ColumnConfigTemplates.button_remove(),
    ColumnConfigTemplates.button(
        header_text="Выбрать",
        value_setter=_select_button_setter,
        sorting_block=True,
        other_attributes={
            "__custom_event__on_release": lambda instance:\
                instance.table_row_ui.data["table_ui"].table.change_scene(
                    instance.table_row_ui.data["row"]
            )
        }
    )
)


class SceneTable(DatabaseTableUi):
    table: TableScene = db.scene  # pyright: ignore[reportIncompatibleVariableOverride]
    columns_config: Tuple[ColumnConfig, ...] = _columns_config

    def __init__(self, **kwargs: Any):
        super().__init__(
            table=self.table,
            columns_config=self.columns_config,
            **kwargs
        )
