from types import SimpleNamespace
from typing import Union, cast

from kivy.utils import get_color_from_hex as _kivy_get_color_from_hex

from libs.animation import ColorDiff
from libs.typecheck import RGBA


def hex_str_to_color(hex_str: str) -> RGBA:
    return cast(RGBA, tuple(_kivy_get_color_from_hex(hex_str)))


def create_colorscheme(**kwargs: Union[ColorDiff, RGBA]) -> SimpleNamespace:
    return SimpleNamespace(**kwargs)


def compute_diff(base_hex: str, target_hex: str) -> ColorDiff:
    """Посчитать ColorDiff от base_hex к target_hex"""
    b = hex_str_to_color(base_hex)
    t = hex_str_to_color(target_hex)
    return ColorDiff(*(
        round((tc - bc) * 255)
        for bc, tc in zip(b, t)
    ))


def format_diff(diff: ColorDiff) -> str:
    """строка вида 'ColorDiff(0x00, 0x00, -0x32, 0x00)'"""
    def fmt(v: int) -> str:
        sign = "-" if v < 0 else ""
        return f"{sign}0x{abs(v):02X}"
    _diff = (diff.dr, diff.dg, diff.db, diff.da)
    return f"ColorDiff({', '.join(fmt(int(v * 255)) for v in _diff)})"


general = create_colorscheme(
    menu_bg=hex_str_to_color("#2C3235FF"),
    menu_wrap_bg=hex_str_to_color("#596267FF"),
)

Label = create_colorscheme(
    fg=hex_str_to_color("#FFFFFFFF"),
    fg_disabled=hex_str_to_color("#AFAFAFFF"),
)

WorkspaceToggleButton = create_colorscheme(
    color_if_contain=hex_str_to_color("#00FF00FF"),
    color_if_not_contain=hex_str_to_color("#E5E5E5FF"),
)

HoverSlider = create_colorscheme(
    background_color_normal=hex_str_to_color("#2C3235FF"),
    background_color_hover=ColorDiff(0x00, 0x00, -0x12, 0x00),  # 2C3223FF
    background_color_disabled=ColorDiff(-0x10, -0x10, -0x10, 0x00),  # 1C2225FF
    background_color_focused=ColorDiff(0x07, 0x07, -0x0B, 0x00),  # 33392AFF

    value_track_color_normal=hex_str_to_color("#00AAAAFF"),
    value_track_color_hover=ColorDiff(0x00, 0x00, 0x00, 0x00),  # 00AAAAFF
    value_track_color_disabled=ColorDiff(0x00, -0x66, -0x66, 0x00),  # 005555FF
    value_track_color_focused=ColorDiff(0x44, 0x44, 0x44, 0x00),  # 44FFFFFF
)


TitleNumericSlider = create_colorscheme(
    title_bg=hex_str_to_color("#262F34FF"),
)

Slider2D = create_colorscheme(
    dot_color_normal=hex_str_to_color("#00DDDDFF"),
    dot_color_hover=hex_str_to_color("#00DD89FF"),
    dot_color_disabled=hex_str_to_color("#00AAAAFF"),
    dot_color_focused=hex_str_to_color("#FFFFFFFF"),

    line_color_normal=hex_str_to_color("#00DDDDFF"),
    line_color_hover=hex_str_to_color("#00DD89FF"),
    line_color_disabled=hex_str_to_color("#00AAAAFF"),
    line_color_focused=hex_str_to_color("#FFFFFFFF"),
)

HoverButton = create_colorscheme(
    background_color_normal=hex_str_to_color("#FFFFFFFF"),
    background_color_down=hex_str_to_color("#FFFFFFFF"),
    background_color_hover=hex_str_to_color("#FFFFCBFF"),
    background_color_disabled=hex_str_to_color("#AAAAAAFF"),
)

ColorToggleButton = create_colorscheme(
    border_color_normal=hex_str_to_color("#00000000"),
    border_color_hover=hex_str_to_color("#0000FFFF"),
    border_color_is_select=hex_str_to_color("#00FFFFFF"),
)

ArrowToggleButton = create_colorscheme(
    arrow_color_normal=hex_str_to_color("#AFAFAFFF"),
    arrow_color_down=hex_str_to_color("#D1D127FF"),
    arrow_color_hover=hex_str_to_color("#D1D127FF"),
    arrow_color_disabled=hex_str_to_color("#7C7C7CFF"),
)

RotaryButton = create_colorscheme(
    texture_color_normal=hex_str_to_color("#FFFFFFFF"),
    texture_color_hover_diff=ColorDiff(0x00, 0x00, -0x32, 0x00),  # FFFFCD
    texture_color_disabled_diff=ColorDiff(-0x55, -0x55, -0x55, 0x00),  # AAAAAA
    texture_color_focused_diff=ColorDiff(-0x32, -0x32, -0x66, 0x00),  # CDCD99

    rotary_active_color_normal=hex_str_to_color("#AFFF80FF"),
    rotary_active_color_hover_diff=ColorDiff(-0x10, -0x10, -0x30, 0x00),  # 9FEF50FF
    rotary_active_color_disabled_diff=ColorDiff(-0x30, -0x20, -0x30, 0x00),  # 7FDF50FF
    rotary_active_color_focused_diff=ColorDiff(0x10, 0x00, 0x10, 0x00),  # BFFF90FF

    rotary_passive_color_normal=hex_str_to_color("#2C3235FF"),
    rotary_passive_color_hover_diff=ColorDiff(0x00, 0x00, 0x00, 0x00),  # 2C3235FF
    rotary_passive_color_disabled_diff=ColorDiff(-0x10, -0x10, 0x0F, 0x00),  # 1C2244FF
    rotary_passive_color_focused_diff=ColorDiff(0x10, 0x10, 0x0F, 0x00),  # 3C4244FF
)

PanRotaryButton = create_colorscheme(
    rotary_active_color_right_normal=hex_str_to_color("#96FFFFDD"),
    rotary_active_color_left_normal=hex_str_to_color("#BD7FF4FF"),
)

FileListButton = create_colorscheme(
    dir_bg=hex_str_to_color("#CCCCCCCC"),
    file_bg=hex_str_to_color("#FFFFFFFF"),
)

HoverInput = create_colorscheme(
    background_color_normal=hex_str_to_color("#2C3235FF"),
    background_color_hover=hex_str_to_color("#2C3227FF"),
    background_color_disabled=hex_str_to_color("#1C2225FF"),
    background_color_focused=hex_str_to_color("#1C2225FF"),

    border_color_normal=hex_str_to_color("#00000000"),
    border_color_hover=hex_str_to_color("#BCC1C4FF"),
    border_color_disabled=hex_str_to_color("#000000FF"),
    border_color_focused=hex_str_to_color("#BCC1C4FF"),

    foreground_color_normal=hex_str_to_color("#99FFFFFF"),
    foreground_color_hover=hex_str_to_color("#99FFFFFF"),
    foreground_color_disabled=hex_str_to_color("#99FFFFFF"),
    foreground_color_focused=hex_str_to_color("#99FFFFFF"),
)

MidiInput = create_colorscheme(
    background_color_normal=hex_str_to_color("#005500FF"),
    foreground_color_normal=hex_str_to_color("#99FFFFFF"),
)

DatabaseTable = create_colorscheme(
    bg=hex_str_to_color("#1C2225FF"),
)

MenuPanel = create_colorscheme(
    bg=hex_str_to_color("#677075FF"),
    border=hex_str_to_color("#596267FF"),
)

SectionPanel = create_colorscheme(
    bg=hex_str_to_color("#677075FF"),
    fg=hex_str_to_color("#2C3235FF"),
)

SubSectionPanel = create_colorscheme(
    bg=hex_str_to_color("#717A7FFF"),
    fg=hex_str_to_color("#2C3235FF"),
)

Modal = create_colorscheme(
    bg=hex_str_to_color("#2E393EFF"),
    border_color=hex_str_to_color("#888888FF"),
)

LabelRow = create_colorscheme(
    bg=hex_str_to_color("#495257FF"),
    fg=hex_str_to_color("#BCBCBCFF"),
)

ModalMenu = create_colorscheme(
    title_bg=hex_str_to_color("#1F292EFF"),
)

MapSelector = create_colorscheme(
    bg=hex_str_to_color("#00FFFF33"),
    border=hex_str_to_color("00FFFFFF"),
)

MapGridItemBehavior = create_colorscheme(
    border_color_normal=hex_str_to_color("#00000000"),
    border_color_hover=hex_str_to_color("#0000FFFF"),
    border_color_is_select=hex_str_to_color("#00FFFFFF"),
)

MapLayout = create_colorscheme(
    bg=hex_str_to_color("#525A5EFF"),
    grid_color=hex_str_to_color("#646B6EFF"),
)

MDIWindow = create_colorscheme(
    border_normal=hex_str_to_color("#00000000"),
    border_focused=hex_str_to_color("#00FFFFFF"),
    border_selected=hex_str_to_color("#44FF88FF"),
)
