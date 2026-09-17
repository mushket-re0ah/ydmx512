from ui.components.database_table import DatabaseTableUi
from ui.components.database_table import ColumnConfigTemplates
from misc import constants
from database import db
from functools import partial


def _update_select_button(widget, db_row, *_):
    widget.disabled = db_row is db.scene.scene_now

def _select_button_setter(widget, db_row):
    widget.text = "Выбрать"
    old = getattr(widget, "_scene_now_cb", None)
    if old is not None:
        db.scene.funbind("scene_now", old)
    cb = partial(_update_select_button, widget, db_row)
    widget._scene_now_cb = cb
    db.scene.fbind("scene_now", cb)
    _update_select_button(widget, db_row)


_columns_config = [
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
            "__custom_event__on_release": lambda instance: instance.table_row_ui.data["table_ui"].table.change_scene(instance.table_row_ui.data["row"])
        }
    )
]


class SceneTable(DatabaseTableUi):
    table = db.scene
    columns_config = _columns_config

    def __init__(self, **kwargs):
        super().__init__(
            table=self.table,
            columns_config=self.columns_config,
            **kwargs
        )
