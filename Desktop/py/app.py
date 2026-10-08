import sys
from pathlib import Path
from typing import Any, Callable, Dict, FrozenSet, Tuple

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import Metrics
from kivy.properties import ObjectProperty

import presets
from database import db
from database.misc import SerialDeviceListInfo
from libs import logger
from libs.dmx512.serial.device import DMXSerialDevice
from libs.kivy_patches import builder_sync, linux_clipboard_xclip, on_touch_double_tap, recycle
from libs.midi.device import MidiDevice
from libs.midi.observer import MidiObserver
from libs.midi.observer import observer as midi_observer
from libs.mouse_manager import cursor_manager
from libs.sdl2_keyboard import KeyboardBehavior
from libs.serial.observer import SerialObserver
from libs.serial.observer import observer as serial_observer
from libs.sub_proc.exit_code import ExitCode
from misc import constants, event_thread
from ui.root import Root


class DesktopApp(KeyboardBehavior, App):
    use_kivy_settings: bool = False
    root: Root = ObjectProperty()

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        builder_sync.apply_patch()
        on_touch_double_tap.apply_patch()
        recycle.apply_patch()
        linux_clipboard_xclip.apply_patch()
        self._window_size_trigger = None
        self._window_position_trigger = None
        self._if_window_minimize = False
        self._save_maximize = False
        self.__register_fonts()
        self.__init_metrics()
        self.__init_window()

        serial_observer.device_cls = DMXSerialDevice
        self._load_active_serial_devices()
        serial_observer.bind(active_devices=self._save_active_serial_devices)
        self._load_active_midi_devices()
        midi_observer.bind(active_devices=self._save_active_midi_devices)

        cursor_manager.init(lambda: db.misc.use_system_cursor)
        def _cur(name: str) -> Path:
            return constants.CURSOR_PATH / name
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

    def _save_active_serial_devices(
            self,
            observer: SerialObserver,
            active_devices: Tuple[DMXSerialDevice]
        ):
        db.misc.edit(serial_connected_port_list=tuple(
                SerialDeviceListInfo(
                    serial_number=device.port_info.serial_number,
                    manufacturer=device.port_info.manufacturer,
                    interface=device.port_info.interface,
                    universe=device.universe,
                    product_name=device.product_name
                )
                for device in active_devices
            )
        )

    def _load_active_serial_devices(self):
        serial_connected_port_list = db.misc.serial_connected_port_list[:]
        def _load(observer: SerialObserver, devices: Tuple[DMXSerialDevice]):
            observer.unbind(devices=_load)
            for device in devices[:]:
                for save_device in serial_connected_port_list:
                    if (
                        device.port_info.serial_number == save_device["serial_number"] and
                        device.port_info.manufacturer == save_device["manufacturer"] and
                        device.port_info.interface == save_device["interface"] and
                        device.product_name == save_device["product_name"]
                    ):
                        device.universe = int(save_device["universe"])
                        device.connect()
        serial_observer.bind(devices=_load)

    def _save_active_midi_devices(self, observer: MidiObserver, active_devices: Tuple[MidiDevice]):
        db.misc.edit(midi_connected_port_list=tuple(device.port for device in active_devices))

    def _load_active_midi_devices(self):
        midi_connected_port_list = db.misc.midi_connected_port_list[:]
        def _load(observer: MidiObserver, devices: Tuple[MidiDevice]):
            observer.unbind(devices=_load)
            for device in devices[:]:
                if device.port in midi_connected_port_list:
                    device.connect()
        midi_observer.bind(devices=_load)

    def create_hotkeys(self) -> Dict[FrozenSet[str], Callable[[], None]]:
        return {
            frozenset({"F12"}): self.fullscreen_toggle
        }

    def _stop_profile(self):
        if constants.PROFILING_CPU:
            import yappi
            yappi.stop()
            threads = yappi.get_thread_stats()
            for thread in yappi.get_thread_stats():
                logger.info(f"=== Thread {thread.name} ({thread.id}) ===")
                stats = yappi.get_func_stats(ctx_id=thread.id)
                stats.sort("tsub", "desc")
                for stat in stats:
                    if stat.tsub < 0.001:
                        continue
                    logger.info(
                        f"{stat.module}.{stat.name}:{stat.lineno} "
                        f"ncall={stat.ncall} "
                        f"tsub={stat.tsub:.6f} "
                        f"ttot={stat.ttot:.6f}"
                    )
        if constants.PROFILING_RAM:
            from pympler import muppy, summary

            all_objects = muppy.get_objects()
            summ = summary.summarize(all_objects)
            summary.print_(summ)

    def on_stop(self):
        self._stop_profile()

    def build(self) -> Root:
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

    def _on_window_size(self, dt: float):
        db.misc.edit(window_size=Window.size)

    def _on_window_position(self, dt: float):
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
                sys.exit(ExitCode.FAILURE)

    def fullscreen_toggle(self):
        if Window.fullscreen:
            Window.fullscreen = False
            db.misc.edit(fullscreen=False)
        else:
            Window.fullscreen = "auto"
            db.misc.edit(fullscreen=True)

    def _on_window_maximize(self, _: Any):
        db.misc.edit(maximize=True)
        self._save_maximize = True

    def _on_window_minimize(self, _: Any):
        self._if_window_minimize = True
        self._save_maximize = db.misc.maximize

    def _on_window_restore(self, _: Any):
        if self._if_window_minimize:
            db.misc.edit(maximize=self._save_maximize)
        else:
            db.misc.edit(maximize=False)
        self._if_window_minimize = False

    def _set_density(self, _, value: float):
        Metrics.density = value

    def _set_scale_font(self, _, value: float):
        Metrics.fontscale = value

    def open_settings(self, *_):
        """
                Отключение меню настроек на F1
        """
        return
