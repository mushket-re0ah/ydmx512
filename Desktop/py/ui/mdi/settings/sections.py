from kivy.properties import ObjectProperty, StringProperty
from libs.uix.scroll_layout import ScrollLayout
from libs.uix.button import HoverToggleButton
from kivy.lang import Builder


Builder.load_file("ui/mdi/settings/sections.kv")


class SettingsSectionToggle(HoverToggleButton):
    title = StringProperty("untitled")
    settings_section = ObjectProperty()

    def on_release(self):
        self.settings_section.on_select_section(self.title)


class SettingsSections(ScrollLayout):
    settings = ObjectProperty()

    def on_kv_post(self, _):
        super().on_kv_post(_)
        self.scrollview.data = [
            {
                "text": "Резервные копии",
                "settings_section": self
            },
        ]

    def on_select_section(self, section):
        print(self, section)

    # DATABASE
    #
    # database_save_interval = BoundedNumericProperty(
    #     5.0, min=1.0, max=60.0, errorhandler=lambda x: boundary(x, 1.0, 60.0))
    # database_backup_interval = BoundedNumericProperty(
    #     60.0, min=30.0, max=900.0, errorhandler=lambda x: boundary(x, 30.0, 900.0))
    # database_backup_max_count = BoundedNumericProperty(
    #     50, min=1, max=500, errorhandler=lambda x: boundary(x, 1, 500))

    # GRAPHICS
    #
    # fps = BoundedNumericProperty(60, min=10, max=240,
    #                              errorhandler=lambda x: boundary(x, 10, 240))
    # multisamples = BoundedNumericProperty(
    #     0, min=0, max=8, errorhandler=lambda x: boundary(x, 0, 8))
    # vsync = OptionProperty("Off", options=["Off", "On", "Adaptive"])
    # density = BoundedNumericProperty(
    #     1.0, min=constants.DENSITY_MINIMUM, max=constants.DENSITY_MAXIMUM,
    #     errorhandler=lambda x: boundary(x, constants.DENSITY_MINIMUM, constants.DENSITY_MAXIMUM))
    # scale_font = BoundedNumericProperty(
    #     1.0, min=constants.DENSITY_MINIMUM, max=constants.DENSITY_MAXIMUM,
    #     errorhandler=lambda x: boundary(x, constants.DENSITY_MINIMUM, constants.DENSITY_MAXIMUM))

    # MIDI
    #
    # midi_notes = OptionProperty("CUBASE", options=list(MIDI_NOTES.keys()))

    # BACKUPS
    #
