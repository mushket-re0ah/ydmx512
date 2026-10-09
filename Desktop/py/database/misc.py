from typing import TYPE_CHECKING, Literal, NamedTuple, Optional, Tuple

from libs.kivy_json_orm.fields import (
    BooleanField,
    ClampedNumericField,
    ListField,
    OptionField,
    StringField,
)
from libs.kivy_json_orm.table_implementation import ConfigTable
from libs.midi.notes import MIDI_NOTES
from misc import constants

if TYPE_CHECKING:
    from database import YdmxDatabase


class SerialDeviceListInfo(NamedTuple):
    serial_number: Optional[str]
    manufacturer: Optional[str]
    interface: Optional[str]
    product_name: Optional[str]


class TableMisc(ConfigTable):
    database: "YdmxDatabase" # pyright: ignore[reportIncompatibleVariableOverride]

    filename = "misc.json"

    # fields
    version: str = StringField(constants.VERSION)
    sub_version: str = StringField(constants.SUB_VERSION)

    # screen
    screen_resolution: Optional[Tuple[int, int]] = ListField(None, allownone=True)

    # window
    window_size: Optional[Tuple[int, int]] = ListField(None, allownone=True)
    window_position: Optional[Tuple[int, int]] = ListField(None, allownone=True)
    maximize: bool = BooleanField(False)
    fullscreen: bool = BooleanField(False)

    # database
    database_save_interval: float = ClampedNumericField(5.0, 1.0, 60.0)
    database_backup_interval: float = ClampedNumericField(60.0, 30.0, 900.0)
    database_backup_max_count: int = ClampedNumericField(50, 1, 500)

    # metrics
    density: float = ClampedNumericField(
        1.0,
        constants.DENSITY_MINIMUM,
        constants.DENSITY_MAXIMUM
    )
    scale_font: float = ClampedNumericField(
        1.0,
        constants.DENSITY_MINIMUM,
        constants.DENSITY_MAXIMUM
    )

    # graphics
    fps: int = ClampedNumericField(60, 10, 240)
    multisamples: int = ClampedNumericField(0, 0, 8)
    vsync: Literal["Off", "On", "Adaptive"] = OptionField("Off", options=["Off", "On", "Adaptive"])
    use_system_cursor: bool = BooleanField(True)

    midi_notes: str = OptionField("CUBASE", options=list(MIDI_NOTES.keys()))

    do_filter_serial_names: bool = BooleanField(False)

    def deserialize_serial_connected_port_list(
        self,
        port_list: Tuple[SerialDeviceListInfo, ...]
    ) -> Tuple[SerialDeviceListInfo, ...]:
        return tuple(
            SerialDeviceListInfo(*port_data)
            for port_data in port_list
        )

    serial_connected_port_list: Tuple[SerialDeviceListInfo, ...] = ListField(
        deserialize=deserialize_serial_connected_port_list
    )
    midi_connected_port_list: Tuple[str, ...] = ListField()
