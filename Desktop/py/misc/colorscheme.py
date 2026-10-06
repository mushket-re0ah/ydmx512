from libs.uix.colorscheme import create_colorscheme, hex_str_to_color

BeatLabel = create_colorscheme(
    default_bg=hex_str_to_color("#00CC00FF"),
    active_bg=hex_str_to_color("#003B00FF"),
    halfbeat_bg=hex_str_to_color("#00A100FF"),
    upbeat_bg=hex_str_to_color("#FFA500FF"),
    default_fg=hex_str_to_color("#FFFFFFFF"),
    active_fg=hex_str_to_color("#99FF99FF"),
    progress_bg=hex_str_to_color("#0000FF33"),
)

SerialDevices = create_colorscheme(
    bg=hex_str_to_color("#243137FF"),
    fg=hex_str_to_color("#99FFFFFF"),
)

MidiDevices = create_colorscheme(
    bg=hex_str_to_color("#243137FF"),
    fg=hex_str_to_color("#99FFFFFF"),
)

BaseDatabaseGridItem = create_colorscheme(
    bg_delete=hex_str_to_color("#FF0000FF"),
)

PatchUi = create_colorscheme(
    bg=hex_str_to_color("#252E32FF"),
    addr_info_normal=hex_str_to_color("#EEEEEEFF"),
    addr_info_addr_conflict=hex_str_to_color("#FF0000FF"),
)

EditorPatchUi = create_colorscheme(
    bg_normal=hex_str_to_color("#252E32FF"),
    bg_selected=hex_str_to_color("#10191DFF"),
    bg_hover=hex_str_to_color("#252E02FF"),
    bg_blocked=hex_str_to_color("#000000FF"),
    border_normal=hex_str_to_color("#00000000"),
    border_data_exist=hex_str_to_color("#00FFFFFF"),
    border_interpatch_phase=hex_str_to_color("#FF00FFFF")
)

PlaybackUi = create_colorscheme(
    bg_work_normal=hex_str_to_color("#00FFFFFF"),
    bg_stop_normal=hex_str_to_color("#FFFFFFFF"),
    bg_attack_normal=hex_str_to_color("#FFB200FF"),
    bg_release_normal=hex_str_to_color("#FF3333FF"),
    bg_edit_normal=hex_str_to_color("#FFFFFFFF"),
)

EditorPlaybackUi = create_colorscheme(
    selected_edit_color=hex_str_to_color("#FF3333FF"),
)

PlaybackPlayButton = create_colorscheme(
    background_color=hex_str_to_color("#33333347"),
    background_color_normal=hex_str_to_color("#14272EFF"),
    background_color_down=hex_str_to_color("#14272EFF"),
    background_color_hover=hex_str_to_color("#146B2EFF"),
    background_color_disabled=hex_str_to_color("#412E27FF"),
)

AutomationToolbar = create_colorscheme(
    bg=hex_str_to_color("#2E393EFF"),
)

AutomationHeader = create_colorscheme(
    bg=hex_str_to_color("#162229FF"),
    beat_delimiters=hex_str_to_color("#70797EFF"),
    halfbeat_delimiters=hex_str_to_color("#70797EFF"),
)

Automation = create_colorscheme(
    play_line=hex_str_to_color("#00FFFFFF"),
    cursor_line=hex_str_to_color("#CCCCCCFF"),
)

RowPanel = create_colorscheme(
    bg=hex_str_to_color("#1E2A31FF"),
)

AutomationRowParam = create_colorscheme(
    fg_param_title_active=hex_str_to_color("#FFFFFFFF"),
    fg_param_title_not_active=hex_str_to_color("#BBBBBBFF"),
)

AutomationTactBox = create_colorscheme(
    padding_bg=hex_str_to_color("#1C2C36FF"),
    bg=hex_str_to_color("#24343EFF"),
    bg_active=hex_str_to_color("#34444EFF"),
    bg_hovered=hex_str_to_color("#34443CFF"),
    bg_focused=hex_str_to_color("#3B4B3CFF"),
    bg_row_phase=hex_str_to_color("#362E38FF"),
    bg_row_phase_active=hex_str_to_color("#44343EFF"),
    bg_row_phase_hovered=hex_str_to_color("#54443CFF"),
    bg_row_phase_focused=hex_str_to_color("#5B4B3CFF"),

    bg_selected=hex_str_to_color("#304060FF"),
    bg_disabled=hex_str_to_color("#24343EFF"),
    bg_phase=hex_str_to_color("#44444EFF"),
    bg_phase_selected=hex_str_to_color("#504060FF"),
    bg_phase_disabled=hex_str_to_color("#34343EFF"),
    beat_delimiters=hex_str_to_color("#1E2A31FF"),
    halfbeat_delimiters=hex_str_to_color("#70797EFF"),
)

CheckboxPhaseInterpatchX = create_colorscheme(
    fg_normal=hex_str_to_color("#FFFFFFDD"),
    fg_active=hex_str_to_color("#FF5FFFDD"),
    fg_active_disabled=hex_str_to_color("#DF3FDFDD"),
    fg_disabled=hex_str_to_color("#CFDFCFDD"),
)

CheckerSlider = create_colorscheme(
    border_color_normal=hex_str_to_color("#6C7275FF"),
    title_bg=hex_str_to_color("#262F34FF"),
    fixture_param_default=hex_str_to_color("000000FF")
)

CheckerPatchOverlayWidget = create_colorscheme(
    border_color=hex_str_to_color("#565F64FF")
)

RowParam = create_colorscheme(
    dot_color_linear=hex_str_to_color("#00FFFFFF"),
    dot_color_linear_selected=hex_str_to_color("#FF00FFFF"),
    dot_color_linear_hovered=hex_str_to_color("#FFAA66FF"),
    dot_color_linear_selected_hovered=hex_str_to_color("#FFAAAAFF"),
    dot_color_spline=hex_str_to_color("#FF0000FF"),
    dot_color_spline_selected=hex_str_to_color("#AA00AAFF"),
    dot_color_spline_hovered=hex_str_to_color("#AAAA00FF"),
    dot_color_spline_selected_hovered=hex_str_to_color("#FF00FFFF"),
)

RowDotsSelector = create_colorscheme(
    bg=hex_str_to_color("#00FFFF33"),
    border=hex_str_to_color("00FFFFFF"),
)

DesktopUix = create_colorscheme(
    tx_led_disabled=hex_str_to_color("#000000FF"),
    tx_led_active=hex_str_to_color("#00FF00FF"),
)

EditorMapLayout = create_colorscheme(
    outbound_background_color=hex_str_to_color("#4D5559FF"),
)

ClampedDimmerSlider = create_colorscheme(
    global_dimmer_mask=hex_str_to_color("#D69C291A")
)
