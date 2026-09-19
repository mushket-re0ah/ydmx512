from kivy.utils import get_color_from_hex as _kivy_get_color_from_hex
from collections import namedtuple


def _h(s):
    return tuple(_kivy_get_color_from_hex(s))


def _cs(**kwargs) -> namedtuple:
    return namedtuple("Colorscheme", kwargs)(**kwargs)

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
