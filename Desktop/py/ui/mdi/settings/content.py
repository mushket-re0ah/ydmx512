from typing import Type

from kivy.lang import Builder
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout

from ui.mdi.settings import MDISettings
from ui.mdi.settings.sections import SettingsSection, SettingsSections

Builder.load_file("ui/mdi/settings/content.kv")


class SettingsContent(BoxLayout):
    settings: MDISettings = ObjectProperty()
    sections: SettingsSections = ObjectProperty()
    section_now: SettingsSection = ObjectProperty()

    restart_required = BooleanProperty(False)

    def on_select_section(self, section_cls: Type[SettingsSection]):
        if isinstance(self.section_now, section_cls):
            return
        if self.section_now is not None:
            self.remove_widget(self.section_now)
        self.section_now = section_cls(settings_content=self)
        self.add_widget(self.section_now)
