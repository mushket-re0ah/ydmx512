from kivy.properties import ObjectProperty, AliasProperty, StringProperty
from libs.uix.mdi.mdi_window import MDIWindow
from database import db


class DatabaseMDIWindow(MDIWindow):
    _db_title_id = None
    mdi_db_row = ObjectProperty(None, allownone=True)

    def __init__(self, *args, **kwargs):
        mdi_db_row = db.mdi_window.by_title_id(self._db_title_id)
        if mdi_db_row is None:
            mdi_db_row = db.mdi_window.add_row(title_id=self._db_title_id)
        self.mdi_db_row = mdi_db_row
        super().__init__(
            mdi_db_row.view_context,
            mdi_db_row.layout_state,
            *args,
            **kwargs
        )

    def on_state(self, _, state: dict):
        self.mdi_db_row.edit(layout_state=self.state.get("layout_state"))

    def _save_vc(self):
        self.mdi_db_row.edit(view_context=self._saved_vc)
