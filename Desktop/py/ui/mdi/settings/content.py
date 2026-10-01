from typing import TYPE_CHECKING

from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout

from ui.mdi.settings.sections import SettingsSections  # lazy kv import initialize

if TYPE_CHECKING:
    from ui.mdi.settings import MDISettings

Builder.load_file("ui/mdi/settings/content.kv")


class SettingsContent(BoxLayout):
    settings: "MDISettings" = ObjectProperty()
    sections: SettingsSections = ObjectProperty()
    section_now: BoxLayout = ObjectProperty()
