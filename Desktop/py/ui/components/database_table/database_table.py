from kivy.properties import (
    ObjectProperty, ListProperty, NumericProperty, BooleanProperty,
    StringProperty
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.widget import Widget
from typing import List, Optional, Tuple
from libs.kivy_json_orm.table_implementation import DatabaseTable, DatabaseRow
from libs.mouse_manager import cursor_manager
from kivy.lang import Builder
from ui.components.database_table.column_config import ColumnConfig
from libs.uix.button import ArrowToggleButton, HoverToggleButton
from functools import partial
from kivy.clock import Clock


Builder.load_file("ui/components/database_table/database_table.kv")


class TableHeaderToggle(ArrowToggleButton):
    table_ui = ObjectProperty()
    header = ObjectProperty()

    sorting_active = BooleanProperty(False)
    sorting_reverse = BooleanProperty(False)
    column_config: ColumnConfig = ObjectProperty(rebind=True)

    def on_release(self):
        super().on_release()
        self.header.set_sort_active_btn(self)
        self.sorting_reverse = not self.sorting_reverse
        self.table_ui.scroll_layout.scrollview.data.sort(
            key=lambda item: self.column_config.sorting_rule(item["row"]),
            reverse=self.sorting_reverse
        )

    def on_sorting_active(self, _, sorting_active):
        self.sorting_reverse = True


class DatabaseTableHeader(BoxLayout):
    columns_config = ListProperty()
    table_ui = ObjectProperty()

    def on_columns_config(self, _, columns_config: List[ColumnConfig]):
        for column in self.columns_config:
            self.add_widget(TableHeaderToggle(
                    table_ui=self.table_ui,
                    header=self,
                    column_config=column
                )
            )

    def update_data(self):
        for i in self.children:
            i.property("column_config").dispatch(i)

    def set_sort_active_btn(self, btn: TableHeaderToggle):
        for i in self.children:
            i.sorting_active = i is btn


class DatabaseTableRow(RecycleDataViewBehavior, BoxLayout):
    selected = BooleanProperty(False)
    columns_config = None
    data = None
    config_was_created = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sync_method = {}
        self.sync_method_row = {}

    def __create_content(self, columns_config: List[ColumnConfig],
                         row: DatabaseRow):
        if self.config_was_created:
            return
        for config in columns_config:
            kwargs = config.other_attributes or {}
            attributes, events = self.__split_other_attributes(kwargs)
            widget = config.widget_class()
            widget.size_hint_y = 1
            for attr, value in attributes.items():
                setattr(widget, attr, value)
            widget.bind(**events)
            widget.table_row_ui = self
            self.add_widget(widget)
        self.config_was_created = True

    def __split_other_attributes(self,
                                 other_attributes: dict) -> Tuple[dict, dict]:
        other_keys = {}
        custom_event_keys = {}
        for key, value in other_attributes.items():
            if key.startswith("__custom_event__"):
                new_key = key[len("__custom_event__"):]
                custom_event_keys[new_key] = value
            else:
                other_keys[key] = value
        return other_keys, custom_event_keys

    def __set_content_data(self, columns_config: List[ColumnConfig],
                           row: DatabaseRow):
        self._unbind_sync_database(columns_config)
        for idx, config in enumerate(columns_config):
            widget = self.children[len(columns_config) - idx - 1]
            config.value_setter(widget, row)
            widget.size_hint_x = config.size_hint_x
            id_column = self.__get_id_column()
            if id_column:
                id_column.is_down = self.data["selected"]
            self.__bind_sync_database(widget, row, config)

    def _unbind_sync_database(self, columns_config: List[ColumnConfig]):
        for idx, config in enumerate(columns_config):
            widget = self.children[len(columns_config) - idx - 1]
            if config in self.sync_method:
                row, sync_method = self.sync_method[config]
                row.funbind(config.data_attribute, sync_method)
            if config in self.sync_method_row:
                row, sync_method = self.sync_method_row[config]
                widget.funbind(config.value_attribute, sync_method)
        self.sync_method = {}
        self.sync_method_row = {}

    def __bind_sync_database(self, widget: Widget, row: DatabaseRow,
                             config: ColumnConfig):
        if config.sync_setter_widget and config.data_attribute:
            sync_method = partial(config.sync_setter_widget, widget, config)
            self.sync_method[config] = (row, sync_method)
            row.fbind(config.data_attribute, sync_method)
        if config.sync_setter_row and config.value_attribute:
            sync_method_row = partial(config.sync_setter_row, row, config)
            self.sync_method_row[config] = (row, sync_method_row)
            widget.fbind(config.value_attribute, sync_method_row)

    def __get_id_column(self) -> Optional[HoverToggleButton]:
        columns_config = self.columns_config
        for idx, config in enumerate(columns_config):
            if config.data_attribute == "_id":
                return self.children[len(columns_config) - idx - 1]

    def change_select_id_state(self):
        id_column = self.__get_id_column()
        if not id_column:
            return
        selected = id_column.is_down
        self.selected = selected
        self.data["selected"] = selected
        if selected:
            self.data["table_ui"].select_id_row(self.data["row"])
        else:
            self.data["table_ui"].unselect_id_row(self.data["row"])

    def refresh_view_attrs(self, rv, index, data):
        self.data = data
        row = data["row"]
        columns_config = data["table_ui"].columns_config
        self.columns_config = columns_config
        self.__create_content(columns_config, row)
        self.__set_content_data(columns_config, row)
        RecycleDataViewBehavior.refresh_view_attrs(self, rv, index, data)


class DatabaseTableUi(BoxLayout):
    header = ObjectProperty()
    scroll_layout = ObjectProperty()

    table: DatabaseTable = ObjectProperty()
    columns_config: List[ColumnConfig] = ListProperty()
    cls_height = NumericProperty("30dp")

    def default_filter_function(self, row: DatabaseRow) -> bool:
        return self.filter_value.upper() in getattr(row, self.filter_attribute).upper()

    filter_attribute = StringProperty("title")
    filter_value = ObjectProperty("")
    filter_function = ObjectProperty(default_filter_function)


    allow_resizing = BooleanProperty(False)
    _resizing = BooleanProperty(False)

    selected_rows = ListProperty()

    _resizing_column_index_left = None
    _resizing_column_index_right = None

    RESIZING_PRECISION = 3

    def __init__(self, **kwargs):
        self.trigger_build_rows = Clock.create_trigger(self._build_rows, -1)
        self.bind(
            filter_attribute=self.trigger_build_rows,
            filter_value=self.trigger_build_rows,
        )
        super().__init__(**kwargs)

    def on_kv_post(self, _):
        self.__build_header()
        self.trigger_build_rows()
        self.table.bind(
            on_add_row=self.on_add_row,
            on_remove_row=self.on_remove_row
        )
        self.set_sort_by_default()

    def set_sort_by_default(self):
        self.header.children[-1].dispatch("on_release")

    def do_filter(self, _):
        if not self.filter_value or not self.filter_attribute:
            self.trigger_build_rows()
        else:
            self.trigger_build_rows(do_filter=True)

    def on_mouse_move(self, mouse_pos: Tuple[float, float]):
        if self._resizing:
            self.property("allow_resizing").dispatch(self)
            return
        if not self.collide_point(*mouse_pos):
            self.allow_resizing = False
            return
        self.__set_allow_resizing(mouse_pos[0])

    def __set_allow_resizing(self, x: float) -> bool:
        precision = self.RESIZING_PRECISION
        widgets = tuple(reversed(self.header.children))
        for i, (current, next_widget) in enumerate(zip(widgets, widgets[1:])):
            right_edge = current.right - precision
            next_left_edge = next_widget.x + precision
            if (right_edge <= x <= next_left_edge):
                self.allow_resizing = True
                self._resizing_column_index_left = i
                self._resizing_column_index_right = i + 1
                self.property("allow_resizing").dispatch(self)
                return
        self.allow_resizing = False

    def on_add_row(self, table: DatabaseTable, row: DatabaseRow):
        self.trigger_build_rows()

    def on_remove_row(self, table: DatabaseTable, row: DatabaseRow):
        self.trigger_build_rows()

    def on_allow_resizing(self, _, allow_resizing: bool):
        if allow_resizing:
            cursor_manager.set_cursor("size_we")

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and self.allow_resizing and\
           touch.button == "left":
            self._resizing = True
            return False
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._resizing:
            c = tuple(reversed(self.header.children))
            index_left = self._resizing_column_index_left
            index_right = self._resizing_column_index_right
            wleft, wright = c[index_left], c[index_right]
            config_left = self.columns_config[index_left]
            config_right = self.columns_config[index_right]
            right_hint, left_hint = self.__calc_hints(
                wleft.size_hint_x + wright.size_hint_x,
                wleft.width + wright.width,
                touch.x - wleft.x)
            config_left.size_hint_x = left_hint
            config_right.size_hint_x = right_hint
            self.header.update_data()
            self.scroll_layout.scrollview.refresh_from_data()
            return True
        return super().on_touch_move(touch)

    def __calc_hints(self,
                     sum_hint: float,
                     sum_size: float,
                     mouse_local: float) -> Tuple[float, float]:
        size_hint_min = 0.2

        ratio = mouse_local / sum_size
        slave_hint = max(
            size_hint_min, min(
                ratio * sum_hint, sum_hint - size_hint_min))
        master_hint = max(size_hint_min, sum_hint - slave_hint)
        return (master_hint, slave_hint)

    def on_touch_up(self, touch):
        self._resizing = False
        self.allow_resizing = False
        super().on_touch_up(touch)

    def __build_header(self):
        self.header.table_ui = self
        self.header.columns_config = self.columns_config

    def _build_rows(self, _):
        for row_ui in self.scroll_layout.scrollview.layout_manager.children:
            row_ui._unbind_sync_database(self.columns_config)
        self.scroll_layout.scrollview.data = [
            self.__make_row_data(row, row._id in self.selected_rows)
            for row in self.table.rows.values()
            if self.filter_function(self, row)
        ]

    def select_id_row(self, row: DatabaseRow):
        self.selected_rows.append(row._id)

    def unselect_id_row(self, row: DatabaseRow):
        self.selected_rows.remove(row._id)

    def __make_row_data(self, row: DatabaseRow, selected: bool) -> dict:
        return {
            "row": row,
            "table_ui": self,
            "selected": selected
        }
