from kivy.properties import StringProperty

from ui.components.database_mdi_window import DatabaseMDIWindow


class MDIMonitor(DatabaseMDIWindow):
    db_title_id: str = "monitor"
    title: str = StringProperty("DMX512 монитор")
