from kivy.properties import ObjectProperty
from libs.uix.database_table import DatabaseTableUi


class LibraryTable(DatabaseTableUi):
    library = ObjectProperty()
    context = ObjectProperty()
    table = None  # надо переопределять в наследнике
    columns_config = None  # надо переопределять в наследнике

    def __init__(self, **kwargs):
        context = kwargs["context"]
        super().__init__(
            table=self.table,
            columns_config=self.columns_config,
            selected_rows=context.selected_rows,
            **kwargs
        )

    def on_kv_post(self, _):
        super().on_kv_post(_)
        self.bind(selected_rows=self.save_context)
        self.scroll_layout.scrollview.scroll_y = self.context.scroll_y
        self.scroll_layout.scrollview.bind(_scroll_y=self.save_context)

    def activate_menu_toggle(self):
        self.library.menu.toggle_brands.trigger_action(0)

    def save_context(self, *args):
        self.context.selected_rows = self.selected_rows
        self.context.size_hint_x = [i.size_hint_x for i in self.columns_config]
        self.context.scroll_y = self.scroll_layout.scrollview.scroll_y
        self.library.property("view_context").dispatch(self.library)

    def close(self):
        self.unbind(selected_rows=self.save_context)
        self.scroll_layout.scrollview.unbind(_scroll_y=self.save_context)
