from kivy.properties import ObjectProperty, StringProperty
from ui.components.mdi_window import MDIWindow
from kivy.uix.boxlayout import BoxLayout


class MDISettings(MDIWindow):
    _db_title_id = "settings"
    title_id = StringProperty(_db_title_id)
    title = StringProperty("Настройки")

    content = ObjectProperty()

    def on_open(self):
        if not self.content:
            self.__create_content()

    def __create_content(self):
        from ui.mdi.settings.content import SettingsContent
        self.content = SettingsContent(settings=self)
        self.add_widget(self.content)
