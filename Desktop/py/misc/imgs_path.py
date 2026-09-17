from misc.constants import IMGS_PATH


def _img(name):
    return (IMGS_PATH / name).as_posix()


window_icon = _img("logo-Y DMX контроллер.png")

button_background_normal = _img("btn_std.png")
button_background_down = _img("btn_active.png")
button_thumb_normal = _img("btnThumb_std.png")


playback_status_work = _img("pb_go.png")
playback_status_stop = _img("play.png")
playback_status_attack = _img("time.png")
playback_status_release = _img("time.png")
playback_status_edit = _img("edit.png")


mdi_lock_normal = _img("btnLock_std.png")
mdi_lock_down = _img("btnLock_active.png")
mdi_expand_normal = _img("btnFull_std.png")
mdi_expand_down = _img("btnFull_active.png")
mdi_close_normal = _img("btnClose_std.png")
mdi_close_down = _img("btnClose_active.png")


rotary_button = _img("rotary.png")


processing_normal = _img("btnProcess_normal.png")
processing_down = _img("btnProcess_down.png")
editor_normal = _img("btnEditor_normal.png")
editor_down = _img("btnEditor_down.png")
patch_list_normal = _img("btnPatchList_normal.png")
patch_list_down = _img("btnPatchList_down.png")
library_normal = _img("btnLibrary_normal.png")
library_down = _img("btnLibrary_down.png")
checker_normal = _img("btnChecker_normal.png")
checker_down = _img("btnChecker_down.png")
monitor_normal = _img("btnMonitor_normal.png")
monitor_down = _img("btnMonitor_down.png")
scene_normal = _img("btnScenes_normal.png")
scene_down = _img("btnScenes_down.png")
desktops_normal = _img("btnDesktops_normal.png")
desktops_down = _img("btnDesktops_down.png")
settings_normal = _img("btnSettings_normal.png")
settings_down = _img("btnSettings_down.png")


connect_state_normal = _img("check_custom_std.png")
connect_state_wait = _img("check_custom_act.png")
connect_state_active = _img("check_green_act.png")


beat_label = _img("beat_label.png")
tap_temp_button_normal = _img("btnTap_normal.png")
tap_temp_button_down = _img("btnTap_down.png")


button_add_normal = _img("btn_add_79x52_std.png")
button_add_down = _img("btn_add_79x52_active.png")


button_import_normal = _img("btn_import_79x52_std.png")
button_import_down = _img("btn_import_79x52_active.png")


button_export_normal = _img("btn_export_79x52_std.png")
button_export_down = _img("btn_export_79x52_active.png")


automationToolbar_spam_mode_normal = _img("tool_draw_std.png")
automationToolbar_spam_mode_down = _img("tool_draw_active.png")
automationToolbar_discard_normal = _img("tool_discard_std.png")
automationToolbar_discard_down = _img("tool_discard_active.png")
automationToolbar_play_normal = _img("tool_play_std.png")
automationToolbar_play_down = _img("tool_play_active.png")
automationToolbar_cycle_normal = _img("tool_loop_std.png")
automationToolbar_cycle_down = _img("tool_loop_active.png")

automationRowLeftTexture = _img("dark_metal_texture.png")

slider_2d_bg = _img("bg_monitor.png")

slider2d_bg_thumb = _img("slider2d_bg_thumb.png")
