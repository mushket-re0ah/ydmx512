from kivy.utils import get_color_from_hex as _kivy_get_color_from_hex
from collections import namedtuple
from libs.animation import ColorDiff


# kivy method is
# def get_color_from_hex(s):
#     '''Transform a hex string color to a kivy
#     :class:`~kivy.graphics.Color`.
#     '''
#     if s.startswith('#'):
#         return get_color_from_hex(s[1:])

#     value = [int(x, 16) / 255.
#              for x in split('([0-9a-f]{2})', s.lower()) if x != '']
#     if len(value) == 3:
#         value.append(1.0)
#     return value


def _h(s):
    return tuple(_kivy_get_color_from_hex(s))


def _cs(**kwargs) -> namedtuple:
    return namedtuple("Colorscheme", kwargs)(**kwargs)


MDIWindow = _cs(
    border_normal=_h("#00000000"),
    border_focused=_h("#00FFFFFF"),
    border_selected=_h("#44FF88FF"),
)

BeatLabel = _cs(
    default_bg=_h("#00CC00FF"),
    active_bg=_h("#003B00FF"),
    halfbeat_bg=_h("#00A100FF"),
    upbeat_bg=_h("#FFA500FF"),
    default_fg=_h("#FFFFFFFF"),
    active_fg=_h("#99FF99FF"),
    progress_bg=_h("#0000FF33"),
)

SerialDevices = _cs(
    bg=_h("#243137FF"),
    fg=_h("#99FFFFFF"),
)

MidiDevices = _cs(
    bg=_h("#243137FF"),
    fg=_h("#99FFFFFF"),
)

PatchUi = _cs(
    bg=_h("#252E32FF"),
    bg_delete=_h("#FF0000FF"),
    addr_info_normal=_h("#EEEEEEFF"),
    addr_info_addr_conflict=_h("#FF0000FF"),
)

EditorPatchUi = _cs(
    bg_normal=_h("#252E32FF"),
    bg_selected=_h("#10191DFF"),
    bg_hover=_h("#252E02FF"),
    bg_blocked=_h("#000000FF"),
    border_normal=_h("#00000000"),
    border_data_exist=_h("#00FFFFFF"),
    border_interpatch_phase=_h("#FF00FFFF")
)

PlaybackUi = _cs(
    bg_work_normal=_h("#00FFFFFF"),
    bg_stop_normal=_h("#FFFFFFFF"),
    bg_attack_normal=_h("#FFB200FF"),
    bg_release_normal=_h("#FF3333FF"),
    bg_edit_normal=_h("#FFFFFFFF"),
    bg_delete=_h("#FF0000FF"),
)

EditorPlaybackUi = _cs(
    selected_edit_color=_h("#FF3333FF"),
)

PlaybackPlayButton = _cs(
    background_color=_h("#33333347"),
    background_color_normal=_h("#14272EFF"),
    background_color_down=_h("#14272EFF"),
    background_color_hover=_h("#146B2EFF"),
    background_color_disabled=_h("#412E27FF"),
)

AutomationToolbar = _cs(
    bg=_h("#2E393EFF"),
)

AutomationHeader = _cs(
    bg=_h("#162229FF"),
    beat_delimiters=_h("#70797EFF"),
    halfbeat_delimiters=_h("#70797EFF"),
)

Automation = _cs(
    play_line=_h("#00FFFFFF"),
    cursor_line=_h("#CCCCCCFF"),
)

RowPanel = _cs(
    bg=_h("#1E2A31FF"),
)

AutomationRowParam = _cs(
    fg_param_title_active=_h("#FFFFFFFF"),
    fg_param_title_not_active=_h("#BBBBBBFF"),
)

AutomationTactBox = _cs(
    padding_bg=_h("#1C2C36FF"),
    bg=_h("#24343EFF"),
    bg_active=_h("#34444EFF"),
    bg_hovered=_h("#34443CFF"),
    bg_focused=_h("#3B4B3CFF"),
    bg_row_phase=_h("#362E38FF"),
    bg_row_phase_active=_h("#44343EFF"),
    bg_row_phase_hovered=_h("#54443CFF"),
    bg_row_phase_focused=_h("#5B4B3CFF"),

    bg_selected=_h("#304060FF"),
    bg_disabled=_h("#24343EFF"),
    bg_phase=_h("#44444EFF"),
    bg_phase_selected=_h("#504060FF"),
    bg_phase_disabled=_h("#34343EFF"),
    beat_delimiters=_h("#1E2A31FF"),
    halfbeat_delimiters=_h("#70797EFF"),
)

CheckboxPhaseInterpatchX = _cs(
    fg_normal=_h("#FFFFFFDD"),
    fg_active=_h("#FF5FFFDD"),
    fg_active_disabled=_h("#DF3FDFDD"),
    fg_disabled=_h("#CFDFCFDD"),
)

CheckerSlider = _cs(
    border_color_normal=_h("#6C7275FF"),
    title_bg=_h("#262F34FF"),
    fixture_param_default=_h("000000FF")
)

CheckerPatchOverlayWidget = _cs(
    border_color=_h("#565F64FF")
)

RowParam = _cs(
    dot_color_linear=_h("#00FFFFFF"),
    dot_color_linear_selected=_h("#FF00FFFF"),
    dot_color_linear_hovered=_h("#FFAA66FF"),
    dot_color_linear_selected_hovered=_h("#FFAAAAFF"),
    dot_color_spline=_h("#FF0000FF"),
    dot_color_spline_selected=_h("#AA00AAFF"),
    dot_color_spline_hovered=_h("#AAAA00FF"),
    dot_color_spline_selected_hovered=_h("#FF00FFFF"),
)

RowDotsSelector = _cs(
    bg=_h("#00FFFF33"),
    border=_h("00FFFFFF"),
)

DesktopUix = _cs(
    tx_led_disabled=_h("#000000FF"),
    tx_led_active=_h("#00FF00FF"),
)

EditorMapLayout = _cs(
    outbound_background_color=_h("#4D5559FF"),
)
