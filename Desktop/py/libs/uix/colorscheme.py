from kivy.utils import get_color_from_hex as _kivy_get_color_from_hex
from collections import namedtuple
from libs.animation import ColorDiff


def _h(s):
    return tuple(_kivy_get_color_from_hex(s))


def _cs(**kwargs) -> namedtuple:
    return namedtuple("Colorscheme", kwargs)(**kwargs)


general = _cs(
    menu_bg=_h("#2C3235FF"),
    menu_wrap_bg=_h("#596267FF"),
)

Label = _cs(
    fg=_h("#FFFFFFFF"),
    fg_disabled=_h("#AFAFAFFF"),
)

WorkspaceToggleButton = _cs(
    color_if_contain=_h("#00FF00FF"),
    color_if_not_contain=_h("#E5E5E5FF"),
)

HoverSlider = _cs(
    background_color_normal=_h("#2C3235FF"),
    background_color_hover=_h("#2C3223FF"),
    background_color_disabled=_h("#1C2225FF"),
    background_color_focused=_h("#33392AFF"),
    
    value_track_color_normal=_h("#00FFFF99"),
    value_track_color_hover=_h("#00FFFFFF"),
    value_track_color_disabled=_h("#009999FF"),
    value_track_color_focused=_h("#44FFFFFF"),
)

TitleNumericSlider = _cs(
    title_bg=_h("#262F34FF"),
)

Slider2D = _cs(
    dot_color_normal=_h("#00DDDDFF"),
    dot_color_hover=_h("#00DD89FF"),
    dot_color_disabled=_h("#00AAAAFF"),
    dot_color_focused=_h("#FFFFFFFF"),
    
    line_color_normal=_h("#00DDDDFF"),
    line_color_hover=_h("#00DD89FF"),
    line_color_disabled=_h("#00AAAAFF"),
    line_color_focused=_h("#FFFFFFFF"),
)

HoverButton = _cs(
    background_color_normal=_h("#FFFFFFFF"),
    background_color_down=_h("#FFFFFFFF"),
    background_color_hover=_h("#FFFFCBFF"),
    background_color_disabled=_h("#AAAAAAFF"),
)

ColorToggleButton = _cs(
    border_color_normal=_h("#00000000"),
    border_color_hover=_h("#0000FFFF"),
    border_color_is_select=_h("#00FFFFFF"),
)

ArrowToggleButton = _cs(
    arrow_color_normal=_h("#AFAFAFFF"),
    arrow_color_down=_h("#D1D127FF"),
    arrow_color_hover=_h("#D1D127FF"),
    arrow_color_disabled=_h("#7C7C7CFF"),
)

RotaryButton = _cs(
    texture_color_normal=_h("#FFFFFFFF"),
    texture_color_hover_diff=ColorDiff(0, 0, -0x32, 0x00),  # FFFFCD
    texture_color_disabled_diff=ColorDiff(-0x55, -0x55, -0x55, 0x00),  # AAAAAA
    texture_color_focused_diff=ColorDiff(-0x32, -0x32, -0x66, 0x00),  # CDCD99
    
    rotary_active_color_normal=_h("#AFFF80FF"),
    rotary_active_color_hover_diff=ColorDiff(-0x10, -0x10, -0x30, 0x00),  # 9FEF50FF
    rotary_active_color_disabled_diff=ColorDiff(-0x30, -0x20, -0x30, 0x00),  # 7FDF50FF
    rotary_active_color_focused_diff=ColorDiff(0x10, 0x00, 0x10, 0x00),  # BFFF90FF
    
    rotary_passive_color_normal=_h("#2C3235FF"),
    rotary_passive_color_hover_diff=ColorDiff(0x00, 0x00, 0x00, 0x00),  # 2C3235FF
    rotary_passive_color_disabled_diff=ColorDiff(-0x10, -0x10, 0x0F, 0x00),  # 1C2244FF
    rotary_passive_color_focused_diff=ColorDiff(0x10, 0x10, 0x0F, 0x00),  # 3C4244FF
)

PanRotaryButton = _cs(
    rotary_active_color_right_normal=_h("#96FFFFDD"),
    rotary_active_color_left_normal=_h("#BD7FF4FF"),
)
