from enum import Enum, auto
from typing import Any, Iterable, Iterator, Optional, Tuple

from kivy.core.window import Window
from kivy.event import EventDispatcher
from kivy.properties import Property
from kivy.uix.widget import Widget

from libs import logger


def _values_differ(obj: EventDispatcher, prop: Property, old: Any, new: Any) -> bool:
    comparator = getattr(prop, "comparator", None)
    if comparator is not None:
        try:
            return not comparator(old, new)
        except Exception as e:
            logger.warning(
                f'Property: Value comparison failed for {obj} with "{e}". Consider setting '
                'force_dispatch to True to avoid this.')
            return True
    try:
        return not bool(old == new)
    except Exception as e:
        logger.warning(
            f'Property: Value comparison failed for {obj} with "{e}". Consider setting '
            'force_dispatch to True to avoid this.')
        return True


def detach_event_dispatcher(obj: EventDispatcher, keys: Iterable[str]) -> dict:
    saved = {}
    for key in keys:
        observers = obj.get_property_observers(key, args=True)
        saved[key] = []
        for callback, largs, kw, is_ref, uid in observers:
            # Получаем исходную функцию (для bind это разыменованный WeakMethod)
            func = callback() if is_ref else callback
            if uid is not None:
                obj.unbind_uid(key, uid)
            else:
                # bind-случай: uid=None, удаляем через funbind
                obj.funbind(key, func)
            saved[key].append((func, largs, kw, is_ref))
    return saved


def atomic_setattrs(obj: EventDispatcher, dispatch:bool=True, **kwargs: Any):
    saved = detach_event_dispatcher(obj, kwargs.keys())

    changed = []
    for key, value in kwargs.items():
        prop = obj.property(key)
        current = getattr(obj, key)
        setattr(obj, key, value)
        new = getattr(obj, key)
        value_changed = _values_differ(obj, prop, current, new)
        if value_changed or getattr(prop, 'force_dispatch', False):
            changed.append(key)

    # Восстанавливаем bindings
    for key, bindings in saved.items():
        for func, largs, kw, is_ref in bindings:
            obj.fbind(key, func, *largs, **kw, ref=is_ref)

    # Dispatch только действительно изменившихся свойств
    # или свойств с force_dispatch=True
    if dispatch:
        for key in changed:
            obj.property(key).dispatch(obj)


def walk_by_parents(widget: Widget) -> Iterator[Widget]:
    parent = widget.parent
    while parent is not Window and parent is not None:
        yield parent
        parent = parent.parent


def walk_by_children(widget: Widget, x: float, y: float) -> Optional[Widget]:
    # x, y — в системе родителя widget
    if not widget.collide_point(x, y):
        return None
    lx, ly = widget.to_local(x, y)
    for child in reversed(widget.children):  # сверху вниз по z-order
        hit = walk_by_children(child, lx, ly)
        if hit is not None:
            return hit
    return widget


class WidgetSide(Enum):
    VOID = auto()  # Вне виджета или внутри (не на границе)
    TOP = auto()
    BOTTOM = auto()
    LEFT = auto()
    RIGHT = auto()
    TOP_LEFT = auto()
    TOP_RIGHT = auto()
    BOTTOM_LEFT = auto()
    BOTTOM_RIGHT = auto()


WIDGET_SIDE_CURSOR = {
    WidgetSide.VOID: "arrow",
    WidgetSide.TOP: "size_ns",
    WidgetSide.BOTTOM: "size_ns",
    WidgetSide.LEFT: "size_we",
    WidgetSide.RIGHT: "size_we",
    WidgetSide.TOP_LEFT: "size_nwse",
    WidgetSide.TOP_RIGHT: "size_nesw",
    WidgetSide.BOTTOM_LEFT: "size_nesw",
    WidgetSide.BOTTOM_RIGHT: "size_nwse"
}


def get_cursor_zone(widget: Widget, mouse_pos: Tuple[float, float],
                    accuracy: float = 6.0) -> WidgetSide:
    x, y = mouse_pos

    left = (x - widget.x) <= accuracy
    right = (x - widget.x) >= (widget.width - accuracy)
    bottom = (y - widget.y) <= accuracy
    top = (y - widget.y) >= (widget.height - accuracy)

    if left and top:
        return WidgetSide.TOP_LEFT
    if left and bottom:
        return WidgetSide.BOTTOM_LEFT
    if right and top:
        return WidgetSide.TOP_RIGHT
    if right and bottom:
        return WidgetSide.BOTTOM_RIGHT
    if left:
        return WidgetSide.LEFT
    if right:
        return WidgetSide.RIGHT
    if top:
        return WidgetSide.TOP
    if bottom:
        return WidgetSide.BOTTOM
    return WidgetSide.VOID


LEFT_WIDGET_SIDES = {
    WidgetSide.LEFT,
    WidgetSide.TOP_LEFT,
    WidgetSide.BOTTOM_LEFT
}
RIGHT_WIDGET_SIDES = {
    WidgetSide.RIGHT,
    WidgetSide.TOP_RIGHT,
    WidgetSide.BOTTOM_RIGHT
}
TOP_WIDGET_SIDES = {WidgetSide.TOP, WidgetSide.TOP_LEFT, WidgetSide.TOP_RIGHT}
BOTTOM_WIDGET_SIDES = {
    WidgetSide.BOTTOM,
    WidgetSide.BOTTOM_LEFT,
    WidgetSide.BOTTOM_RIGHT
}
