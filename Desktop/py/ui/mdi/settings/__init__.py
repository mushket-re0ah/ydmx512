from kivy.properties import ObjectProperty, StringProperty
from ui.components.database_mdi_window import DatabaseMDIWindow
from kivy.uix.boxlayout import BoxLayout


class MDISettings(DatabaseMDIWindow):
    _db_title_id = "settings"
    title = StringProperty("Настройки")

    content = ObjectProperty()

    def on_hidden(self, _, hidden: bool):
        super().on_hidden(_, hidden)
        if hidden or self.content:
            return
        self.__create_content()

    def __create_content(self):
        from ui.mdi.settings.content import SettingsContent
        self.content = SettingsContent(settings=self)
        self.add_widget(self.content)
