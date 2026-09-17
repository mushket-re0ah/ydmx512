from kivy.properties import StringProperty
from ui.components.mdi_window import MDIWindow


class MDIMonitor(MDIWindow):
    _db_title_id = "monitor"
    title_id = StringProperty(_db_title_id)
    title = StringProperty("DMX512 монитор")
