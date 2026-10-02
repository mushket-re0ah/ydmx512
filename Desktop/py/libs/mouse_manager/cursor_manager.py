from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.utils import platform

from libs.mouse_manager import register_mouse_observer

# +------------+-----------+------------+-----------+---------------+
# |            | Windows   | MacOS      | Linux X11 | Linux Wayland |
# +============+===========+============+===========+===============+
# | arrow      | arrow     | arrow      | arrow     | arrow         |
# +------------+-----------+------------+-----------+---------------+
# | ibeam      | ibeam     | ibeam      | ibeam     | ibeam         |
# +------------+-----------+------------+-----------+---------------+
# | wait       | wait      | arrow      | wait      | wait          |
# +------------+-----------+------------+-----------+---------------+
# | crosshair  | crosshair | crosshair  | crosshair | hand          |
# +------------+-----------+------------+-----------+---------------+
# | wait_arrow | arrow     | arrow      | wait      | wait          |
# +------------+-----------+------------+-----------+---------------+
# | size_nwse  | size_nwse | size_all   | size_all  | hand          |
# +------------+-----------+------------+-----------+---------------+
# | size_nesw  | size_nesw | size_all   | size_all  | hand          |
# +------------+-----------+------------+-----------+---------------+
# | size_we    | size_we   | size_we    | size_we   | hand          |
# +------------+-----------+------------+-----------+---------------+
# | size_ns    | size_ns   | size_ns    | size_ns   | hand          |
# +------------+-----------+------------+-----------+---------------+
# | size_all   | size_all  | size_all   | size_all  | hand          |
# +------------+-----------+------------+-----------+---------------+
# | no         | no        | no         | no        | ibeam         |
# +------------+-----------+------------+-----------+---------------+
# | hand       | hand      | hand       | hand      | hand          |
# +------------+-----------+------------+-----------+---------------+
_system_cursor = {
    "arrow": {
        "win": "arrow",
        "macosx": "arrow",
        "linux": "arrow",
    }[platform],
    "ibeam": {
        "win": "ibeam",
        "macosx": "ibeam",
        "linux": "ibeam",
    }[platform],
    "crosshair": {
        "win": "crosshair",
        "macosx": "crosshair",
        "linux": "crosshair",
    }[platform],
    "size_nwse": {
        "win": "size_nwse",
        "macosx": "size_all",
        "linux": "size_nwse",
    }[platform],
    "size_nesw": {
        "win": "size_nesw",
        "macosx": "size_all",
        "linux": "size_nesw",
    }[platform],
    "size_we": {
        "win": "size_we",
        "macosx": "size_we",
        "linux": "size_we",
    }[platform],
    "size_ns": {
        "win": "size_ns",
        "macosx": "size_ns",
        "linux": "size_ns",
    }[platform],
    "size_all": {
        "win": "size_all",
        "macosx": "size_all",
        "linux": "size_all",
    }[platform],
    "no": {
        "win": "no",
        "macosx": "no",
        "linux": "no",
    }[platform],
    "hand": {
        "win": "hand",
        "macosx": "hand",
        "linux": "hand",
    }[platform],
}


_software_cursor: Dict[str, Path] = {}
_cursor: Optional[str] = None
_force: bool = False
_cursor_pos: Tuple[float, float] = (0, 0)

def _default_system_cursor_getter() -> bool:
    return True
_use_system_cursor_getter: Callable[[], bool] = _default_system_cursor_getter

def register_software_cursor(**kwargs: Path):
    global _software_cursor
    for key, path in kwargs.items():
        _software_cursor[key] = path

def set_use_system_cursor_getter(getter: Callable[[], bool]):
    global _use_system_cursor_getter
    _use_system_cursor_getter = getter
    _trigger_set_cursor()

def set_cursor(cursor: Optional[str]):
    if _force:
        return
    global _cursor
    _cursor = cursor
    _trigger_set_cursor()

def set_force(force: bool):
    global _force
    _force = force
    _trigger_set_cursor()

def set_cursor_pos(mouse_pos: Tuple[float, float]):
    global _cursor_pos
    _cursor_pos = mouse_pos
    _trigger_set_cursor()

def _complete(_:Any):
    """
        system_cursor_allowed = A
        use_system_cursor = B
        A B RESULT
        0 0 SOFTWARE
        0 1 SOFTWARE
        1 0 SOFTWARE
        1 1 SYSTEM
    """
    global _cursor
    cursor_key = _cursor or "arrow"
    system_cursor_allowed = _cursor in _system_cursor if _cursor else True

    if system_cursor_allowed and _use_system_cursor_getter():
        _set_system_cursor(_system_cursor[cursor_key])
    else:
        _set_software_cursor(
            _cursor_pos,
            _software_cursor[cursor_key].as_posix()
        )
    if not _force:
        _cursor = None

_trigger_set_cursor = Clock.create_trigger(_complete, -1)

_initialized = False
def init(use_system_cursor_getter: Optional[Callable[[], bool]]=None):
    global _initialized
    if use_system_cursor_getter:
        set_use_system_cursor_getter(use_system_cursor_getter)
    if not _initialized:
        register_mouse_observer(set_cursor_pos)
        _initialized = True
    else:
        raise RuntimeError("cursor_manager already initialized")

_software_cursor_color = Color(1, 1, 1, 1)
_software_cursor_rect = Rectangle(size=[32, 32])
def _set_system_cursor(cursor: str):
    global _software_cursor_color
    global _software_cursor_rect
    Window.set_system_cursor(cursor)
    if not Window.show_cursor:
        Window.show_cursor = True
        Window.canvas.after.remove(_software_cursor_color)
        Window.canvas.after.remove(_software_cursor_rect)

def _set_software_cursor(pos: Tuple[float, float], image: str):
    global _software_cursor_rect
    if Window.show_cursor:
        Window.show_cursor = False
        Window.canvas.after.add(_software_cursor_color)
        Window.canvas.after.add(_software_cursor_rect)
    _software_cursor_rect.pos = pos
    _software_cursor_rect.source = image
