from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Tuple

from libs.kivy_json_orm.fields import BooleanField, ColorField, NumericField, StringField
from libs.kivy_json_orm.table_implementation import DatabaseRow, DatabaseTable
from libs.typecheck import RGBA

if TYPE_CHECKING:
    from database import YdmxDatabase


class RowFixtureParam(DatabaseRow):
    database: "YdmxDatabase"  # pyright: ignore[reportIncompatibleMethodOverride]
    table: "TableFixtureParam" # pyright: ignore[reportIncompatibleVariableOverride]

    title_id: Optional[str] = StringField(allownone=True)  # None - пользовательский
    title: str = StringField("Без названия")
    title_alias: str = StringField("")
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
    database: "YdmxDatabase" # pyright: ignore[reportIncompatibleVariableOverride]
    get_row_by_id: Callable[[int], Optional[RowFixtureParam]] # pyright: ignore[reportIncompatibleMethodOverride]
    rows: Dict[int, RowFixtureParam] # pyright: ignore[reportIncompatibleVariableOverride]
    get_row_by_attribute: Callable[[str, Any], Optional[RowFixtureParam]] # pyright: ignore[reportIncompatibleMethodOverride]
    on_add_row: Callable[[RowFixtureParam], None] # pyright: ignore[reportIncompatibleMethodOverride]
    on_remove_row: Callable[[RowFixtureParam], None] # pyright: ignore[reportIncompatibleMethodOverride]
    add_row: Callable[..., RowFixtureParam] # pyright: ignore[reportIncompatibleMethodOverride]
    remove_row: Callable[[RowFixtureParam], None] # pyright: ignore[reportIncompatibleMethodOverride]
    __getattr__: Callable[[str], Callable[[Any], Optional[RowFixtureParam]]] # pyright: ignore[reportIncompatibleMethodOverride]

    cls_row = RowFixtureParam
    filename = "fixture_param.json"

    def _get_default_rows_for_create(self) -> Tuple[Dict[str, Any], ...]:
        def _default_row(
                title_id: str,
                title: str,
                title_alias: str,
                color: str,
                is_dynamic: bool,
                default: int
            ) -> Dict[str, Any]:
            return {
                "title_id": title_id,
                "title": title,
                "title_alias": title_alias,
                "color": color,
                "is_dynamic": is_dynamic,
                "default_value": default
            }
        default_rows: Tuple[Dict[str, Any], ...] = (
            _default_row(PAN_TITLE_ID, "пан", "пан", "#1AA2A7FF", True, 127),
            _default_row(PAN_16_BIT_TITLE_ID, "пан (16 бит)", "пан16", "#1AA2A799", True, 0),
            _default_row(PAN_SPD_TITLE_ID, "пан спд", "пан спд", "#1AA2A7FF", False, 0),
            _default_row(TILT_TITLE_ID, "тилт", "тилт", "#1AA2A7FF", True, 127),
            _default_row(TILT_16_BIT_TITLE_ID, "тилт (16 бит)", "тилт16", "#1AA2A799", True, 0),
            _default_row(TILT_SPD_TITLE_ID, "тилт спд", "тилт спд", "#1AA2A7FF", False, 0),
            _default_row(SPEED_TITLE_ID, "скорость", "скор", "#1AA2A7FF", False, 0),
            _default_row(DIMMER_TITLE_ID, "диммер", "диммер", "#AFFF80FF", False, 0),
            _default_row(RED_TITLE_ID, "красный", "красн", "#A3291CFF", False, 0),
            _default_row(GREEN_TITLE_ID, "зеленый", "зелен", "#43A01DFF", False, 0),
            _default_row(BLUE_TITLE_ID, "синий", "синий", "#1F669BFF", False, 0),
            _default_row(WHITE_TITLE_ID, "белый", "белый", "#EAEAEAFF", False, 0),
            _default_row(AMBER_TITLE_ID, "янтарь", "янтарь", "#D69C29FF", False, 0),
            _default_row(UV_TITLE_ID, "uv", "uv", "#BD7FF4FF", False, 0),
            _default_row(COLOR_TITLE_ID, "цвет", "цвет", "#1AA2A7FF", False, 0),
            _default_row(STROBE_TITLE_ID, "строб", "строб", "#1AA2A7FF", False, 0),
            _default_row(GOBO_TITLE_ID, "гобо", "гобо", "#1AA2A7FF", False, 0),
            _default_row(GOBO_ROTARY_TITLE_ID, "поворот гобо", "пов гобо", "#1AA2A7FF", False, 0),
            _default_row(PRISM_TITLE_ID, "призма", "призма", "#1AA2A7FF", False, 0),
            _default_row(PRISM_ROTARY_TITLE_ID, "поворот призмы", "пов призм", "#1AA2A7FF", False, 0),
            _default_row(FOCUS_TITLE_ID, "фокус", "фокус", "#1AA2A7FF", False, 0),
            _default_row(ZOOM_TITLE_ID, "зум", "зум", "#1AA2A7FF", False, 0),
            _default_row(FROST_TITLE_ID, "frost", "frost", "#1AA2A7FF", False, 0),
            _default_row(LAMP_ON_TITLE_ID, "лампа", "лампа", "#1AA2A7FF", False, 0),
            _default_row(FUNC_TITLE_ID, "функция", "функц", "#1AA2A7FF", False, 0),
            _default_row(FUNC_SPD_TITLE_ID, "скорость функции", "скор функц", "#1AA2A7FF", False, 0),
            _default_row(RESET_TITLE_ID, "сброс", "сброс", "#1AA2A7FF", False, 0),
            _default_row(RESERVE_TITLE_ID, "резерв.", "резерв", "#1AA2A7FF", False, 0)
        )
        return default_rows

    def get_default_row(self) -> RowFixtureParam:
        return self.rows[next(iter(self.rows))]
