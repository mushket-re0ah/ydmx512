from libs.kivy_json_orm.table_implementation import DatabaseTable, DatabaseRow
from kivy.properties import (
    StringProperty, ColorProperty, BooleanProperty, NumericProperty
)
from kivy.utils import get_hex_from_color
from libs.serialize import *
from typing import Tuple
from libs.kivy_json_orm.fields import *


class RowFixtureParam(DatabaseRow):
    title_id = StringField(allownone=True)  # None - пользовательский
    title = StringField("Без названия")
    is_dynamic = BooleanField(False)
    color = ColorField("#1AA2A7FF")
    default_value = NumericField(0)


PAN_TITLE_ID = "pan"
PAN_16_BIT_TITLE_ID = "pan_16_bit"
PAN_SPD_TITLE_ID = "pan_spd"
TILT_TITLE_ID = "tilt"
TILT_16_BIT_TITLE_ID = "tilt_16_bit"
TILT_SPD_TITLE_ID = "tilt_spd"
SPEED_TITLE_ID = "speed"
DIMMER_TITLE_ID = "dimmer"
RED_TITLE_ID = "red"
GREEN_TITLE_ID = "green"
BLUE_TITLE_ID = "blue"
WHITE_TITLE_ID = "white"
AMBER_TITLE_ID = "amber"
UV_TITLE_ID = "uv"
COLOR_TITLE_ID = "color"
STROBE_TITLE_ID = "strobe"
GOBO_TITLE_ID = "gobo"
GOBO_ROTARY_TITLE_ID = "gobo_rotary"
PRISM_TITLE_ID = "prism"
PRISM_ROTARY_TITLE_ID = "prism_rotary"
FOCUS_TITLE_ID = "focus"
ZOOM_TITLE_ID = "zoom"
FROST_TITLE_ID = "frost"
LAMP_ON_TITLE_ID = "lamp_on"
FUNC_TITLE_ID = "func"
FUNC_SPD_TITLE_ID = "func_spd"
RESET_TITLE_ID = "reset"
RESERVE_TITLE_ID = "reserve"
class TableFixtureParam(DatabaseTable):
    cls_row = RowFixtureParam
    filename = "fixture_param.json"

    default_rows = [
{"title_id": PAN_TITLE_ID, "title": "пан", "color": "#1AA2A7FF", "is_dynamic": True, "default_value": 127},
{"title_id": PAN_16_BIT_TITLE_ID, "title": "пан (16 бит)", "color": "#1AA2A799", "is_dynamic": True, "default_value": 0},
{"title_id": PAN_SPD_TITLE_ID, "title": "пан спд", "color": "#1AA2A7FF", "is_dynamic": False, "default_value": 0},
{"title_id": TILT_TITLE_ID, "title": "тилт", "color": "#1AA2A7FF", "is_dynamic": True, "default_value": 127},
{"title_id": TILT_16_BIT_TITLE_ID, "title": "тилт (16 бит)", "color": "#1AA2A799", "is_dynamic": True, "default_value": 0},
{"title_id": TILT_SPD_TITLE_ID, "title": "тилт спд", "color": "#1AA2A7FF", "is_dynamic": False, "default_value": 0},
{"title_id": SPEED_TITLE_ID, "title": "скорость", "color": "#1AA2A7FF", "is_dynamic": False, "default_value": 0},
{"title_id": DIMMER_TITLE_ID, "title": "диммер", "color": "#AFFF80FF", "is_dynamic": False, "default_value": 0},
{"title_id": RED_TITLE_ID, "title": "красный", "color": "#A3291CFF", "is_dynamic": False, "default_value": 0},
{"title_id": GREEN_TITLE_ID, "title": "зеленый", "color": "#43A01DFF", "is_dynamic": False, "default_value": 0},
{"title_id": BLUE_TITLE_ID, "title": "синий", "color": "#1F669BFF", "is_dynamic": False, "default_value": 0},
{"title_id": WHITE_TITLE_ID, "title": "белый", "color": "#EAEAEAFF", "is_dynamic": False, "default_value": 0},
{"title_id": AMBER_TITLE_ID, "title": "янтарь", "color": "#D69C29FF", "is_dynamic": False, "default_value": 0},
{"title_id": UV_TITLE_ID, "title": "uv", "color": "#BD7FF4FF", "is_dynamic": False, "default_value": 0},
{"title_id": COLOR_TITLE_ID, "title": "цвет", "color": "#1AA2A7FF", "is_dynamic": False, "default_value": 0},
{"title_id": STROBE_TITLE_ID, "title": "строб", "color": "#1AA2A7FF", "is_dynamic": False, "default_value": 0},
{"title_id": GOBO_TITLE_ID, "title": "гобо", "color": "#1AA2A7FF", "is_dynamic": False, "default_value": 0},
{"title_id": GOBO_ROTARY_TITLE_ID, "title": "поворот гобо", "color": "#1AA2A7FF", "is_dynamic": False, "default_value": 0},
{"title_id": PRISM_TITLE_ID, "title": "призма", "color": "#1AA2A7FF", "is_dynamic": False, "default_value": 0},
{"title_id": PRISM_ROTARY_TITLE_ID, "title": "поворот призмы", "color": "#1AA2A7FF", "is_dynamic": False, "default_value": 0},
{"title_id": FOCUS_TITLE_ID, "title": "фокус", "color": "#1AA2A7FF", "is_dynamic": False, "default_value": 0},
{"title_id": ZOOM_TITLE_ID, "title": "зум", "color": "#1AA2A7FF", "is_dynamic": False, "default_value": 0},
{"title_id": FROST_TITLE_ID, "title": "frost", "color": "#1AA2A7FF", "is_dynamic": False, "default_value": 0},
{"title_id": LAMP_ON_TITLE_ID, "title": "лампа", "color": "#1AA2A7FF", "is_dynamic": False, "default_value": 0},
{"title_id": FUNC_TITLE_ID, "title": "функция", "color": "#1AA2A7FF", "is_dynamic": False, "default_value": 0},
{"title_id": FUNC_SPD_TITLE_ID, "title": "скорость функции", "color": "#1AA2A7FF", "is_dynamic": False, "default_value": 0},
{"title_id": RESET_TITLE_ID, "title": "сброс", "color": "#1AA2A7FF", "is_dynamic": False, "default_value": 0},
{"title_id": RESERVE_TITLE_ID, "title": "резерв.", "color": "#1AA2A7FF", "is_dynamic": False, "default_value": 0}
    ]

    def get_default_row(self) -> RowFixtureParam:
        return self.rows[next(iter(self.rows))]
