from kivy.properties import StringProperty
from ui.components.database_mdi_window import DatabaseMDIWindow


class MDIMonitor(DatabaseMDIWindow):
    _db_title_id = "monitor"
    title = StringProperty("DMX512 монитор")
