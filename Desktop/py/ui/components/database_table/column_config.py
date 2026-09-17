from kivy.uix.widget import Widget
from typing import Optional, Callable, Dict
from libs.kivy_json_orm.table_implementation import DatabaseRow
from ui.components.recycle_spinner import RecycleSpinner
from ui.components.input import HoverInput, HEXAInput, NumericInput
from ui.components.button import HoverButton, HoverToggleButton
from dataclasses import dataclass, field
from operator import attrgetter
from libs.utils import merge_kwargs


@dataclass
class ColumnConfig:
    header_text: str = ""
    data_attribute: Optional[str] = None
    value_attribute: str = "text"
    value_getter: Optional[Callable] = None
    value_setter: Optional[Callable] = None
    sync_setter_widget: Optional[Callable] = None
    sync_setter_row: Optional[Callable] = None
    sorting_rule: Optional[Callable] = None
    sorting_block: bool = False
    widget_class: Optional[any] = None
    size_hint_x: float = 1.0
    other_attributes: Dict[str, any] = field(default_factory=dict)

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

    def default_value_getter(self, db_row: DatabaseRow) -> any:
        return attrgetter(self.data_attribute)(db_row)

    def default_value_setter(self, widget: Widget, db_row: DatabaseRow) -> str:
        setattr(widget, self.value_attribute, self.value_getter(db_row))

    def default_sync_setter_widget(self, widget: Widget, _, db_row: DatabaseRow, value: any) -> Callable:
        setattr(widget, self.value_attribute, self.value_getter(db_row))

    def default_sync_setter_row(self, db_row: DatabaseRow, _, widget: Widget, value: any) -> Callable:
        db_row.edit(**{self.data_attribute: getattr(widget, self.value_attribute)})

    def default_sorting_rule(self, db_row: DatabaseRow) -> any:
        return attrgetter(self.data_attribute)(db_row)

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: any) -> bool:
        return self is other


class ColumnConfigTemplates:
    @staticmethod
    def checkbox_id(**kwargs) -> ColumnConfig:
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
    def _on_checkbox_id_press(instance):
        instance.table_row_ui.change_select_id_state()

    @staticmethod
    def _checkbox_id_value_getter(db_row: DatabaseRow) -> str:
        return str(int(db_row._id))

    @staticmethod
    def text_field(**kwargs) -> ColumnConfig:
        return ColumnConfigTemplates._apply_kwargs({
            "widget_class": HoverInput,
        }, kwargs)

    @staticmethod
    def numeric_field(**kwargs) -> ColumnConfig:
        return ColumnConfigTemplates._apply_kwargs({
            "widget_class": NumericInput,
            "value_attribute": "value"
        }, kwargs)

    @staticmethod
    def hexa_field(**kwargs) -> ColumnConfig:
        return ColumnConfigTemplates._apply_kwargs({
            "widget_class": HEXAInput,
        }, kwargs)

    @staticmethod
    def spinner(**kwargs) -> ColumnConfig:
        return ColumnConfigTemplates._apply_kwargs({
            "widget_class": RecycleSpinner,
            "value_attribute": "selected",
            "other_attributes": {
                "arrow_offset_right": "8dp"
            },
        }, kwargs)

    @staticmethod
    def button(**kwargs) -> ColumnConfig:
        return ColumnConfigTemplates._apply_kwargs({
            "widget_class": HoverButton,
            "data_attribute": None,
            "sorting_rule": None,
        }, kwargs)

    @staticmethod
    def static_value_setter(widget: Widget, attr: str, value: any):
        setattr(widget, attr, value)

    @staticmethod
    def button_copy(**kwargs) -> ColumnConfig:
        return ColumnConfigTemplates.button(**merge_kwargs({
            "header_text": "Копировать",
            "value_setter": lambda widget, db_row: ColumnConfigTemplates.static_value_setter(widget, "text", "Копировать"),
            "sorting_block": True,
            "other_attributes": {
                "__custom_event__on_release": ColumnConfigTemplates._on_copy_press
            }
        }, kwargs))

    @staticmethod
    def _on_copy_press(instance):
        instance.table_row_ui.data["row"].copy()

    @staticmethod
    def button_edit(**kwargs) -> ColumnConfig:
        return ColumnConfigTemplates.button(**merge_kwargs({
            "header_text": "Редактировать",
            "value_setter": lambda widget, db_row: ColumnConfigTemplates.static_value_setter(widget, "text", "Редактировать"),
            "sorting_block": True,
            "other_attributes": {
                "__custom_event__on_release": ColumnConfigTemplates._on_edit_press
            }
        }, kwargs))

    @staticmethod
    def _on_edit_press(instance):
        instance.table_row_ui.data["table_ui"].edit(instance.table_row_ui.data["row"])

    @staticmethod
    def button_remove(**kwargs) -> ColumnConfig:
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
    def _on_remove_press(instance):
        instance.table_row_ui.data["row"].remove()

    @staticmethod
    def _apply_kwargs(default_kwargs: dict, kwargs: dict) -> ColumnConfig:
        return ColumnConfig(**merge_kwargs(
                                        default_kwargs, kwargs))
