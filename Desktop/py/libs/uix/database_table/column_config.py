from dataclasses import dataclass, field
from operator import attrgetter
from typing import Any, Callable, Dict, Optional, Type

from kivy.uix.widget import Widget

from libs.kivy_json_orm.table_implementation import DatabaseRow
from libs.uix.button import HoverButton, HoverToggleButton
from libs.uix.input import HEXAInput, HoverInput, NumericInput
from libs.uix.recycle_spinner import RecycleSpinner
from libs.utils import merge_kwargs


@dataclass
class ColumnConfig:
    header_text: str = ""
    data_attribute: Optional[str] = None
    value_attribute: str = "text"
    value_getter: Optional[Callable[[DatabaseRow], Any]] = None
    value_setter: Callable[[Widget, DatabaseRow], None] = None
    sync_setter_widget: Optional[Callable[[Widget, "ColumnConfig", DatabaseRow, Any], None]] = None
    sync_setter_row: Optional[Callable[[Widget, "ColumnConfig", DatabaseRow, Any], None]] = None
    sorting_rule: Optional[Callable[[DatabaseRow], Any]] = None
    sorting_block: bool = False
    widget_class: Type[Widget] = Widget
    size_hint_x: float = 1.0
    other_attributes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if '.' in self.value_attribute:
            raise NotImplementedError()

        if self.value_getter is None:
            self.value_getter = self.default_value_getter

        if self.value_setter is None:
            self.value_setter = self.default_value_setter

        if self.sync_setter_widget is None and self.data_attribute:
            self.sync_setter_widget = self.default_sync_setter_widget

        if self.sync_setter_row is None and self.data_attribute:
            self.sync_setter_row = self.default_sync_setter_row

        if self.sorting_rule is None and not self.sorting_block:
            self.sorting_rule = self.default_sorting_rule

    def default_value_getter(self, db_row: DatabaseRow) -> Any:
        if self.data_attribute is None:
            raise ValueError("value_getter is required when data_attribute is None")
        return attrgetter(self.data_attribute)(db_row)

    def default_value_setter(self, widget: Widget, db_row: DatabaseRow):
        if self.value_getter is None:
            raise ValueError("value_getter is None")
        setattr(widget, self.value_attribute, self.value_getter(db_row))

    def default_sync_setter_widget(
            self,
            widget: Widget,
            config: "ColumnConfig",
            db_row: DatabaseRow,
            value: Any
        ):
        if self.value_getter is None:
            raise ValueError("value_getter is None")
        setattr(widget, self.value_attribute, self.value_getter(db_row))

    def default_sync_setter_row(
            self,
            db_row: DatabaseRow,
            config: "ColumnConfig",
            widget: Widget,
            value: Any
        ):
        if self.data_attribute is None:
            raise ValueError("data_attribute is None")
        db_row.edit(**{self.data_attribute: getattr(widget, self.value_attribute)})

    def default_sorting_rule(self, db_row: DatabaseRow) -> Any:
        if self.data_attribute is None:
            raise ValueError("data_attribute is None")
        return attrgetter(self.data_attribute)(db_row)

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: Any) -> bool:
        return self is other


class ColumnConfigTemplates:
    @staticmethod
    def checkbox_id(**kwargs: Any) -> ColumnConfig:
        return ColumnConfigTemplates._apply_kwargs({
            "header_text": "ID",
            "widget_class": HoverToggleButton,
            "data_attribute": "_id",
            "value_getter": ColumnConfigTemplates._checkbox_id_value_getter,
            "other_attributes": {
                "__custom_event__on_press": ColumnConfigTemplates._on_checkbox_id_press
            },
        }, kwargs)

    @staticmethod
    def _on_checkbox_id_press(instance: Widget):
        instance.table_row_ui.change_select_id_state()

    @staticmethod
    def _checkbox_id_value_getter(db_row: DatabaseRow) -> str:
        return str(int(db_row._id))

    @staticmethod
    def text_field(**kwargs: Any) -> ColumnConfig:
        return ColumnConfigTemplates._apply_kwargs({
            "widget_class": HoverInput,
        }, kwargs)

    @staticmethod
    def numeric_field(**kwargs: Any) -> ColumnConfig:
        return ColumnConfigTemplates._apply_kwargs({
            "widget_class": NumericInput,
            "value_attribute": "value"
        }, kwargs)

    @staticmethod
    def hexa_field(**kwargs: Any) -> ColumnConfig:
        return ColumnConfigTemplates._apply_kwargs({
            "widget_class": HEXAInput,
        }, kwargs)

    @staticmethod
    def spinner(**kwargs: Any) -> ColumnConfig:
        return ColumnConfigTemplates._apply_kwargs({
            "widget_class": RecycleSpinner,
            "value_attribute": "selected",
            "other_attributes": {
                "arrow_offset_right": "8dp"
            },
        }, kwargs)

    @staticmethod
    def button(**kwargs: Any) -> ColumnConfig:
        return ColumnConfigTemplates._apply_kwargs({
            "widget_class": HoverButton,
            "data_attribute": None,
            "sorting_rule": None,
        }, kwargs)

    @staticmethod
    def static_value_setter(widget: Widget, attr: str, value: Any):
        setattr(widget, attr, value)

    @staticmethod
    def button_copy(**kwargs: Any) -> ColumnConfig:
        return ColumnConfigTemplates.button(**merge_kwargs({
            "header_text": "Копировать",
            "value_setter": lambda widget, db_row: ColumnConfigTemplates.static_value_setter(widget, "text", "Копировать"),
            "sorting_block": True,
            "other_attributes": {
                "__custom_event__on_release": ColumnConfigTemplates._on_copy_press
            }
        }, kwargs))

    @staticmethod
    def _on_copy_press(instance: Widget):
        instance.table_row_ui.data["row"].copy()

    @staticmethod
    def button_edit(**kwargs: Any) -> ColumnConfig:
        return ColumnConfigTemplates.button(**merge_kwargs({
            "header_text": "Редактировать",
            "value_setter": lambda widget, db_row: ColumnConfigTemplates.static_value_setter(widget, "text", "Редактировать"),
            "sorting_block": True,
            "other_attributes": {
                "__custom_event__on_release": ColumnConfigTemplates._on_edit_press
            }
        }, kwargs))

    @staticmethod
    def _on_edit_press(instance: Widget):
        instance.table_row_ui.data["table_ui"].edit(instance.table_row_ui.data["row"])

    @staticmethod
    def button_remove(**kwargs: Any) -> ColumnConfig:
        return ColumnConfigTemplates.button(**merge_kwargs({
            "header_text": "Удалить",
            "value_setter": lambda widget, db_row: ColumnConfigTemplates.static_value_setter(widget, "text", "Удалить"),
            "sorting_block": True,
            "other_attributes": {
                "__custom_event__on_release": ColumnConfigTemplates._on_remove_press,
                "color": (1, 0, 0, 1)
            }
        }, kwargs))

    @staticmethod
    def _on_remove_press(instance: Widget):
        instance.table_row_ui.data["row"].remove()

    @staticmethod
    def _apply_kwargs(default_kwargs: Dict[str, Any], kwargs: Dict[str, Any]) -> ColumnConfig:
        return ColumnConfig(**merge_kwargs(default_kwargs, kwargs))
