def init(backup_mode=False):
    import os

    os.environ["KIVY_WINDOW"] = "sdl2"
    os.environ["KIVY_TEXT"] = "sdl2"
    os.environ["KIVY_IMAGE"] = "sdl2"
    # os.environ["KIVY_VIDEO"] = "ffpyplayer"

    # os.environ["KIVY_NO_CONFIG"] = "1"
    os.environ["KIVY_NO_FILELOG"] = "1"

    os.environ["KIVY_NO_CONSOLELOG"] = "1"

    # if config.graphics.dpi:
    # os.environ["KIVY_DPI"] = str(config.graphics.dpi)
# os.environ["KIVY_METRICS_DENSITY"] = str(config.graphics.scale)
# os.environ["KIVY_METRICS_FONTSCALE"] = str(config.graphics.scale_fonts)
    from kivy.config import Config
    from misc import imgs_path
    # from kivy_process.database.db_table import colorscheme_table as cs
    # Config.set("kivy", "desktop", config.misc.desktop)
    Config.set("kivy", "exit_on_escape", backup_mode)

    # Config.set("kivy", "keyboard_mode", )
    Config.set("kivy", "window_icon", imgs_path.window_icon)

    Config.set("graphics", "minimum_width", "800")
    Config.set("graphics", "minimum_height", "600")

    from misc import constants
    import json
    data = {}
    try:
        with open(constants.DATABASE_PATH / "misc.json", "r", encoding="utf8") as fptr:
            data = json.loads(fptr.read())
    except:
        pass
    maximize = data.get("maximize", False)
    fullscreen = data.get("fullscreen", False)
    window_size = data.get("window_size", None)
    window_position = data.get("window_position", None)
    fps = data.get("fps", 60)
    multisamples = data.get("multisamples", 0)
    vsync =  data.get("vsync", "Off")

    if fullscreen:
        Config.set("graphics", "fullscreen", "auto")
    elif maximize:
        Config.set("graphics", "window_state", "maximized")
    else:
        if window_size:
            Config.set("graphics", "width", window_size[0])
            Config.set("graphics", "height", window_size[1])
        if window_position:
            Config.set("graphics", "left", window_position[0])
            Config.set("graphics", "top", window_position[1])
            Config.set("graphics", "position", "custom")

    Config.set("graphics", "maxfps", fps)
    Config.set("graphics", "multisamples", multisamples)

    vsync = 1 if vsync == "On" else (-1 if vsync == "Adaptive" else 0)
    Config.set("graphics", "vsync", vsync)

    # Отключает появление меток при нажатии правой кнопкой мыши
    Config.set("input", "mouse", "mouse,multitouch_on_demand")

    from kivy.logger import Logger, LOG_LEVELS
    Logger.setLevel(LOG_LEVELS["error"])
    Logger.propagate = False
