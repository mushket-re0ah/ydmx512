from typing import TYPE_CHECKING

from kivy.properties import ObjectProperty, StringProperty

from ui.components.database_mdi_window import DatabaseMDIWindow

if TYPE_CHECKING:
    from ui.mdi.settings.content import SettingsContent


class MDISettings(DatabaseMDIWindow):
    _db_title_id: str = "settings"
    title: str = StringProperty("Настройки")

    content: "SettingsContent" = ObjectProperty()

    def on_hidden(self, _, hidden: bool):
        super().on_hidden(_, hidden)
        if hidden or self.content:
            return
        self.__create_content()

    def __create_content(self):
        from ui.mdi.settings.content import SettingsContent
        self.content = SettingsContent(settings=self)
        self.add_widget(self.content)
