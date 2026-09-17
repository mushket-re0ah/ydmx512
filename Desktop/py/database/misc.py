from misc import constants
from libs.kivy_json_orm.table_implementation import ConfigTable
from libs.midi.notes import MIDI_NOTES
from libs.kivy_json_orm.fields import (
    BooleanField, ListField, OptionField, StringField, ClampedNumericField
)


class TableMisc(ConfigTable):
    filename = "misc.json"

    # fields
    version: str = StringField(constants.VERSION)
    sub_version: str = StringField(constants.SUB_VERSION)

    # screen
    screen_resolution = ListField(None, allownone=True)

    # window
    window_size = ListField(None, allownone=True)
    window_position = ListField(None, allownone=True)
    maximize = BooleanField(False)
    fullscreen = BooleanField(False)

    # database
    database_save_interval = ClampedNumericField(5.0, 1.0, 60.0)
    database_backup_interval = ClampedNumericField(60.0, 30.0, 900.0)
    database_backup_max_count = ClampedNumericField(50, 1, 500)

    # metrics
    density = ClampedNumericField(1.0, constants.DENSITY_MINIMUM, constants.DENSITY_MAXIMUM)
    scale_font = ClampedNumericField(1.0, constants.DENSITY_MINIMUM, constants.DENSITY_MAXIMUM)

    # graphics
    fps = ClampedNumericField(60, 10, 240)
    multisamples = ClampedNumericField(0, 0, 8)
    vsync = OptionField("Off", options=["Off", "On", "Adaptive"])
    use_system_cursor = BooleanField(True)

    midi_notes = OptionField("CUBASE", options=list(MIDI_NOTES.keys()))

    do_filter_serial_names = BooleanField(False)
