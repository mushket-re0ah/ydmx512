from kivy.core.window import Window
from kivy.clock import Clock

_initialized = False
_callback_list = []

def register_mouse_observer(callback):
    global _initialized
    global _callback_list
    if not _initialized:
        _callbacks_trigger = Clock.create_trigger(_processing_callbacks, 1/15)
        Clock.schedule_interval(_callbacks_trigger, 0)
        _initialized = True
    if callback in _callback_list:
        raise Exception(f"register_mouse_observer: callback({callback}) already in _callback_list")
    _callback_list.append(callback)


def _processing_callbacks(_):
    for callback in _callback_list:
        callback(Window.mouse_pos)
