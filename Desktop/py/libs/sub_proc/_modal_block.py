from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.utils import platform


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
        text: "modal block"
"""
)


class SubProcModalBlock(BoxLayout):
    process = ObjectProperty()

    def on_window_focus(self, window, focus: bool):
        if focus:
            _set_focus_on_process_window(self.process)

    def on_touch_down(self, touch):
        return True

    def on_touch_up(self, touch):
        return True

    def on_touch_move(self, touch):
        return True


_modal_block_widget = None

def start(process):
    global _modal_block_widget
    _modal_block_widget = SubProcModalBlock(process=process)
    Window.add_widget(_modal_block_widget)
    Window.bind(focus=_modal_block_widget.on_window_focus)


def stop():
    global _modal_block_widget
    Window.unbind(focus=_modal_block_widget.on_window_focus)
    if _modal_block_widget:
        Window.remove_widget(_modal_block_widget)
    _modal_block_widget = None


_set_focus_on_process_window = None
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

    def _get_main_hwnd(pid):
        main_hwnd = None
        
        @EnumWindowsProc
        def callback(hwnd, l_param):
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


    def _set_focus_on_process_window(process):
        hwnd = _get_main_hwnd(process.pid)
        if hwnd:
            win32gui.SetForegroundWindow(hwnd)
            win32gui.SetActiveWindow(hwnd)

elif platform == "linux":
    def _set_focus_on_process_window(process):
        pass
elif platform == "macosx":
    def _set_focus_on_process_window(process):
        pass
else:
    def _set_focus_on_process_window(process):
        pass
