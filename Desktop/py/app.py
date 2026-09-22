from kivy.app import App
from kivy.lang import Builder
from kivy.metrics import Metrics
from kivy.core.window import Window
from kivy.core.text import Label as CoreLabel
from kivy.clock import Clock
from kivy.properties import ObjectProperty, ListProperty, StringProperty
from libs import logger
from misc import constants
from libs.mouse_manager import cursor_manager
from libs.sdl2_keyboard import KeyboardBehavior
from libs.serial.observer import observer as serial_observer
from libs.dmx512.serial.device import DMXSerialDevice
from libs.kivy_patches import builder_sync, on_touch_double_tap, recycle
from database import db
import presets
from misc import event_thread
from ui.root import Root
from typing import Optional, List
import sys


class DesktopApp(KeyboardBehavior, App):
    use_kivy_settings = False
    root = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        builder_sync.apply_patch()
        on_touch_double_tap.apply_patch()
        recycle.apply_patch()
        self._window_size_trigger = None
        self._window_position_trigger = None
        self._if_window_minimize = False
        self._save_maximize = False
        self.__register_fonts()
        self.__init_metrics()
        self.__init_window()

        db.misc.bind(do_filter_serial_names=serial_observer.setter("do_filter_devices"))
        serial_observer.do_filter_devices = db.misc.do_filter_serial_names
        serial_observer.filter_name_list = {
            "Univer DMX A1",
            "U-DMX A11",
            "U-DMX K12",
            "U-DMX K23",
            "U-DMX K46",
        }
        serial_observer.device_cls = DMXSerialDevice

        cursor_manager.init(lambda: db.misc.use_system_cursor)
        _cur = lambda name: (constants.CURSOR_PATH / name).as_posix()
        cursor_manager.register_software_cursor(
            arrow=_cur("arrow.png"),
            ibeam=_cur("ibeam.png"),
            crosshair=_cur("arrow.png"),
            size_nwse=_cur("size_nwse.png"),
            size_nesw=_cur("size_nesw.png"),
            size_we=_cur("size_we.png"),
            size_ns=_cur("size_ns.png"),
            size_all=_cur("size_all.png"),
            hand=_cur("hand.png"),
            on_render_line=_cur("cursor_on_render_line.png")
        )
        self.register_keyboard_context()
        presets.init()
        c = constants
        self.title = f"{c.APP_NAME} v.{c.VERSION}{c.SUB_VERSION} (Сцена: none)"
        event_thread.init()

    def create_hotkeys(self) -> Optional[dict]:
        return {
            frozenset({"F12"}): self.fullscreen_toggle
        }

    def on_stop(self):
        if constants.PROFILING_CPU:
            import yappi
            yappi.stop()
            threads = yappi.get_thread_stats()
            for thread in threads:
                print(
                    "Function stats for (%s) (%d)" % (thread.name, thread.id)
                )  # it is the Thread.__class__.__name__
                for stat in yappi.get_func_stats(ctx_id=thread.id):
                    print(f"{stat.module}.{stat.name}:" +
                          f"{stat.lineno} {stat.ncall} {stat.ttot}")
        if constants.PROFILING_RAM:
            from pympler import muppy, summary

            all_objects = muppy.get_objects()
            summ = summary.summarize(all_objects)
            summary.print_(summ)

    def build(self):
        Builder.load_file("ui/root.kv")
        self.root = Root()
        return self.root

    def __init_window(self):
        """Создание событий отслеживания состояний окна для сохранения"""
        self._window_size_trigger = Clock.create_trigger(
            self._on_window_size, 1.0)
        self._window_position_trigger = Clock.create_trigger(
            self._on_window_position, 1.0)
        Window.bind(on_minimize=self._on_window_minimize,
                    on_maximize=self._on_window_maximize,
                    on_restore=self._on_window_restore,
                    size=self._window_size_trigger,
                    left=self._window_position_trigger,
                    top=self._window_position_trigger)

    def _on_window_size(self, dt):
        db.misc.edit(window_size=Window.size)

    def _on_window_position(self, dt):
        db.misc.edit(window_position=(Window.left, Window.top))

    def __init_metrics(self):
        Metrics.density = max(db.misc.density, 0.5)
        Metrics.fontscale = max(db.misc.scale_font, 0.5)

        db.misc.bind(density=self._set_density, scale_font=self._set_scale_font)

    def __register_fonts(self):
        for name, file in (
                ("Ebrima", "ebrima.ttf"),
                ("Arial", "arial.ttf"),
                ("Roboto Mono", "robotomono.ttf"),
                ("Calibri", "calibri.ttf"),
            ):
            try:
                CoreLabel.register(name, (constants.FONTS_PATH / file).as_posix())
            except Exception:
                logger.error(f"Failed to register font '{name}'", exc_info=True)
                sys.exit(1)

    def fullscreen_toggle(self):
        if Window.fullscreen:
            Window.fullscreen = False
            db.misc.edit(fullscreen=False)
        else:
            Window.fullscreen = "auto"
            db.misc.edit(fullscreen=True)

    def _on_window_maximize(self, window):
        db.misc.edit(maximize=True)
        self._save_maximize = True

    def _on_window_minimize(self, window):
        self._if_window_minimize = True
        self._save_maximize = db.misc.maximize

    def _on_window_restore(self, window):
        if self._if_window_minimize:
            db.misc.edit(maximize=self._save_maximize)
        else:
            db.misc.edit(maximize=False)
        self._if_window_minimize = False

    def _set_density(self, _, value: float):
        Metrics.density = value

    def _set_scale_font(self, _, value: float):
        Metrics.fontscale = value

    def open_settings(self, *largs):
        """
                Отключение меню настроек на F1
        """
        pass
