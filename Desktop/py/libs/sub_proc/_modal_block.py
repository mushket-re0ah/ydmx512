from multiprocessing import Process
from multiprocessing.connection import Connection
from typing import Any, Callable, Dict, FrozenSet, Optional

from kivy.clock import Clock
from kivy.core.window import Window, WindowBase
from kivy.input.motionevent import MotionEvent
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import platform

from libs import logger
from libs.sdl2_keyboard.behavior import KeyboardBehavior
from libs.sub_proc.ipc import PROCESS_CANCEL_MSG

Builder.load_string("""
<SubProcModalBlock>:  # BoxLayout
    size_hint: (1, 1)
    pos_hint: {"x": 0, "y": 0}
    canvas.before:
        Color:
            rgba: (0, 0, 0, 0.7)
        Rectangle:
            pos: self.pos
            size: self.size
    RestrictedLabel:
        text: "modal block (for interrupt press esc)"
"""
)


class SubProcModalBlock(BoxLayout, KeyboardBehavior):
    process: Process = ObjectProperty()
    send_connection: Connection = ObjectProperty()

    def on_window_focus(self, window: WindowBase, focus: bool):
        if focus and self.process.is_alive():
            _set_focus_on_process_window(self.process)

    def on_touch_down(self, touch: MotionEvent) -> bool:
        return True

    def on_touch_up(self, touch: MotionEvent) -> bool:
        return True

    def on_touch_move(self, touch: MotionEvent) -> bool:
        return True

    def create_hotkeys(self) -> Dict[FrozenSet[str], Callable[[], None]]:
        return {
            frozenset({"esc"}): self._force_stop
        }

    def _force_stop(self):
        try:
            self.send_connection.send(PROCESS_CANCEL_MSG)
            Clock.schedule_once(self._check_force_stop_timeout, 2.0)
        except (BrokenPipeError, OSError):
            pass  # ребёнок уже умер

    def _check_force_stop_timeout(self, _:Any):
        if self.process.is_alive():
            try:
                self.process.terminate()
            except Exception:
                pass


_modal_block_widget: Optional[SubProcModalBlock] = None

def start(process: Process, send_connection: Connection):
    global _modal_block_widget
    if _modal_block_widget is not None:
        raise RuntimeError()
    _modal_block_widget = SubProcModalBlock(
        process=process,
        send_connection=send_connection
    )
    Window.add_widget(_modal_block_widget)
    _modal_block_widget.register_keyboard_context()
    Window.bind(focus=_modal_block_widget.on_window_focus)


def stop():
    global _modal_block_widget
    if _modal_block_widget is None:
        logger.warning("_modal_block.stop, _modal_block_widget is None")
        return
    Window.unbind(focus=_modal_block_widget.on_window_focus)
    if _modal_block_widget:
        _modal_block_widget.unregister_keyboard_context()
        Window.remove_widget(_modal_block_widget)
    _modal_block_widget = None


if platform == "win":
    import ctypes
    from ctypes import wintypes

    import win32gui

    user32 = ctypes.WinDLL('user32', use_last_error=True)
    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    user32.IsWindowVisible.argtypes = (wintypes.HWND,)
    user32.GetWindowTextLengthW.argtypes = (wintypes.HWND,)
    user32.GetWindowTextW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
    user32.GetClassNameW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
    user32.GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))

    def _get_main_hwnd(pid) -> wintypes.HWND:
        main_hwnd = None

        @EnumWindowsProc
        def callback(hwnd, l_param) -> bool:
            nonlocal main_hwnd

            # Проверяем PID
            process_id = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
            if process_id.value != pid:
                return True

            # Пропускаем невидимые окна
            if not user32.IsWindowVisible(hwnd):
                return True

            # Проверяем наличие заголовка
            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True

            # Получаем заголовок окна
            title = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title, length + 1)

            if not main_hwnd:
                main_hwnd = hwnd
                return False

            return True

        user32.EnumWindows(callback, 0)
        return main_hwnd


    def _set_focus_on_process_window(process: Process):
        hwnd = _get_main_hwnd(process.pid)
        if hwnd:
            win32gui.SetForegroundWindow(hwnd)
            win32gui.SetActiveWindow(hwnd)

elif platform == "linux":
    def _set_focus_on_process_window(process: Process):
        pass
elif platform == "macosx":
    def _set_focus_on_process_window(process: Process):
        pass
else:
    def _set_focus_on_process_window(process: Process):
        pass
