from typing import Any, Callable, List, Tuple

from kivy.clock import Clock
from kivy.core.window import Window

_initialized = False
_callback_list: List[Callable[[Tuple[float, float]], None]] = []

def register_mouse_observer(callback: Callable[[Tuple[float, float]], None]):
    global _initialized
    global _callback_list
    if not _initialized:
        _callbacks_trigger = Clock.create_trigger(_processing_callbacks, 1/15)
        Clock.schedule_interval(_callbacks_trigger, 0)
        _initialized = True
    if callback in _callback_list:
        raise ValueError(f"register_mouse_observer: callback({callback}) already in _callback_list")
    _callback_list.append(callback)


def _processing_callbacks(_:Any):
    for callback in _callback_list:
        callback(Window.mouse_pos)
