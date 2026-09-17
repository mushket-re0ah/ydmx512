from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
import ui.mdi.settings.sections


Builder.load_file("ui/mdi/settings/content.kv")


class SettingsContent(BoxLayout):
    settings = ObjectProperty()
    sections = ObjectProperty()
    section_now = ObjectProperty()
