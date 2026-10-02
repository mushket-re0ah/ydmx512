from typing import Any, Dict, Optional, Tuple

from libs.kivy_json_orm.fields import BooleanField, ColorField, NumericField, StringField
from libs.kivy_json_orm.table_implementation import DatabaseRow, DatabaseTable
from libs.typecheck import RGBA


class RowFixtureParam(DatabaseRow):
    title_id: Optional[str] = StringField(allownone=True)  # None - пользовательский
    title: str = StringField("Без названия")
    is_dynamic: bool = BooleanField(False)
    color: RGBA = ColorField("#1AA2A7FF")
    default_value: int = NumericField(0)


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

    def _get_default_rows_for_create(self) -> Tuple[Dict[str, Any], ...]:
        def _default_row(
                title_id: str,
                title: str,
                color: str,
                is_dynamic: bool,
                default: int
            ) -> Dict[str, Any]:
            return {
                "title_id": title_id,
                "title": title,
                "color": color,
                "is_dynamic": is_dynamic,
                "default_value": default
            }
        default_rows: Tuple[Dict[str, Any], ...] = (
            _default_row(PAN_TITLE_ID, "пан", "#1AA2A7FF", True, 127),
            _default_row(PAN_16_BIT_TITLE_ID, "пан (16 бит)", "#1AA2A799", True, 0),
            _default_row(PAN_SPD_TITLE_ID, "пан спд", "#1AA2A7FF", False, 0),
            _default_row(TILT_TITLE_ID, "тилт", "#1AA2A7FF", True, 127),
            _default_row(TILT_16_BIT_TITLE_ID, "тилт (16 бит)", "#1AA2A799", True, 0),
            _default_row(TILT_SPD_TITLE_ID, "тилт спд", "#1AA2A7FF", False, 0),
            _default_row(SPEED_TITLE_ID, "скорость", "#1AA2A7FF", False, 0),
            _default_row(DIMMER_TITLE_ID, "диммер", "#AFFF80FF", False, 0),
            _default_row(RED_TITLE_ID, "красный", "#A3291CFF", False, 0),
            _default_row(GREEN_TITLE_ID, "зеленый", "#43A01DFF", False, 0),
            _default_row(BLUE_TITLE_ID, "синий", "#1F669BFF", False, 0),
            _default_row(WHITE_TITLE_ID, "белый", "#EAEAEAFF", False, 0),
            _default_row(AMBER_TITLE_ID, "янтарь", "#D69C29FF", False, 0),
            _default_row(UV_TITLE_ID, "uv", "#BD7FF4FF", False, 0),
            _default_row(COLOR_TITLE_ID, "цвет", "#1AA2A7FF", False, 0),
            _default_row(STROBE_TITLE_ID, "строб", "#1AA2A7FF", False, 0),
            _default_row(GOBO_TITLE_ID, "гобо", "#1AA2A7FF", False, 0),
            _default_row(GOBO_ROTARY_TITLE_ID, "поворот гобо", "#1AA2A7FF", False, 0),
            _default_row(PRISM_TITLE_ID, "призма", "#1AA2A7FF", False, 0),
            _default_row(PRISM_ROTARY_TITLE_ID, "поворот призмы", "#1AA2A7FF", False, 0),
            _default_row(FOCUS_TITLE_ID, "фокус", "#1AA2A7FF", False, 0),
            _default_row(ZOOM_TITLE_ID, "зум", "#1AA2A7FF", False, 0),
            _default_row(FROST_TITLE_ID, "frost", "#1AA2A7FF", False, 0),
            _default_row(LAMP_ON_TITLE_ID, "лампа", "#1AA2A7FF", False, 0),
            _default_row(FUNC_TITLE_ID, "функция", "#1AA2A7FF", False, 0),
            _default_row(FUNC_SPD_TITLE_ID, "скорость функции", "#1AA2A7FF", False, 0),
            _default_row(RESET_TITLE_ID, "сброс", "#1AA2A7FF", False, 0),
            _default_row(RESERVE_TITLE_ID, "резерв.", "#1AA2A7FF", False, 0)
        )
        return default_rows

    def get_default_row(self) -> RowFixtureParam:
        return self.rows[next(iter(self.rows))]
