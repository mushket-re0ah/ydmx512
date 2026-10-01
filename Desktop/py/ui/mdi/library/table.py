from typing import TYPE_CHECKING, Any, Tuple

from kivy.properties import ObjectProperty
from kivy.uix.widget import Widget

from libs.kivy_json_orm.table_implementation import DatabaseTable
from libs.uix.database_table import DatabaseTableUi
from libs.uix.database_table.column_config import ColumnConfig

if TYPE_CHECKING:
    from ui.mdi.library import LibraryTableContext, MDILibrary


class LibraryTable(DatabaseTableUi):
    library: "MDILibrary" = ObjectProperty()
    context: "LibraryTableContext" = ObjectProperty()
    table: DatabaseTable
    columns_config: Tuple[ColumnConfig, ...]

    def __init__(self, **kwargs: Any):
        context = kwargs["context"]
        super().__init__(
            table=self.table,
            columns_config=self.columns_config,
            selected_rows=context.selected_rows,
            **kwargs
        )

    def on_kv_post(self, base_widget: Widget):
        super().on_kv_post(base_widget)
        self.bind(selected_rows=self.save_context)
        self.scroll_layout.scrollview.scroll_y = self.context.scroll_y
        self.scroll_layout.scrollview.bind(_scroll_y=self.save_context)

    def activate_menu_toggle(self):
        self.library.menu.toggle_brands.trigger_action(0)

    def save_context(self, *_: Any):
        self.context.selected_rows = self.selected_rows
        self.context.size_hint_x = [i.size_hint_x for i in self.columns_config]
        self.context.scroll_y = self.scroll_layout.scrollview.scroll_y
        self.library.property("view_context").dispatch(self.library)

    def close(self):
        self.unbind(selected_rows=self.save_context)
        self.scroll_layout.scrollview.unbind(_scroll_y=self.save_context)
