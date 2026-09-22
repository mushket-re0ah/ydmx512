from kivy.core.window import Window
from kivy.event import EventDispatcher
from kivy.uix.widget import Widget
from kivy.clock import Clock
from enum import Enum, auto
from typing import Tuple, Iterable
from libs import logger


def _values_differ(prop, old, new):
    comparator = getattr(prop, "comparator", None)
    if comparator is not None:
        try:
            return not comparator(old, new)
        except Exception as e:
            logger.warn(
                'Property: Value comparison failed for {} with "{}". Consider setting '
                'force_dispatch to True to avoid this.'.format(self, e))
            return True
    try:
        return not bool(old == new)
    except Exception:
        logger.warn(
            'Property: Value comparison failed for {} with "{}". Consider setting '
            'force_dispatch to True to avoid this.'.format(self, e))
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


def atomic_setattrs(obj: EventDispatcher, dispatch=True, **kwargs):
    saved = detach_event_dispatcher(obj, kwargs.keys())

    changed = []
    for key, value in kwargs.items():
        prop = obj.property(key)
        current = getattr(obj, key)
        setattr(obj, key, value)
        new = getattr(obj, key)
        value_changed = _values_differ(prop, current, new)
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


class AutoUnbindBehavior:
    """Миксин для управления внешними привязками"""
    def __init__(self, *args, **kwargs):
        self._bindings_to = {}  # {obj: [(event, callback), ...]}
        super().__init__(*args, **kwargs)

    def bind_to(self, obj, **kwargs):
        """Привязаться к другому объекту и запомнить это."""
        obj.bind(**kwargs)
        if obj not in self._bindings_to:
            self._bindings_to[obj] = []
        self._bindings_to[obj].extend(kwargs.items())

    def unbind_from(self, obj):
        """Снять все привязки к данному объекту, сделанные через bind_to."""
        bindings = self._bindings_to.pop(obj, None)
        if bindings:
            for name, callback in bindings:
                obj.unbind(**{name: callback})

    def unbind_all(self):
        """Снять все внешние привязки (ко всем объектам)."""
        for obj, bindings in self._bindings_to.items():
            for name, callback in bindings:
                obj.unbind(**{name: callback})
        self._bindings_to.clear()


class ViewContextSaverMixin:
    """Микшин для MDIWindow. Автоматически сохраняет состояние виджетов
    по плоскому списку путей, в том числе с динамическими ключами @var."""
    view_context_template = {}  # переопределить в наследнике

    def __init__(self, *args, **kwargs):
        self._view_context_loaded = False
        super().__init__(*args, **kwargs)

    def load_view_context(self, view_context=None):
        if view_context is None:
            view_context = self.get_view_context() or {}
        self._saved_vc = view_context.copy()
        self._bindings = {}
        Clock.schedule_once(self._load_view_context, 0)

    def _load_view_context(self, _):
        for path, params in self.view_context_template.items():
            self._setup_path(path, params)
        self._view_context_loaded = True

    def get_view_context(self):
        return {}

    def set_view_context(self, view_context: dict):
        pass

    def _get_params(self, params):
        """Если params — словарь с ключом 'default', это расширенный формат.
        Иначе это просто значение по умолчанию без сериализаторов.
        """
        if isinstance(params, dict) and 'default' in params:
            return (params.get('default'), params.get('serialize'), params.get('deserialize'))
        return (params, None, None)

    def _setup_path(self, path, params):
        # Разделяем путь на "объект" и "свойство@var"
        default, serialize, deserialize = self._get_params(params)
        obj_path, _, rest = path.rpartition('/')
        if not obj_path:
            obj_path, rest = '', path
        if rest:
            prop, _, dynamic_var = rest.partition('@')
        else:
            prop, dynamic_var = obj_path, None
            obj_path = ''

        # Поиск целевого объекта по цепочке obj_path (через точки)
        if obj_path:
            obj = self
            for attr in obj_path.split('.'):
                child = getattr(obj, attr, None)
                if child is None:
                    obj.bind(**{attr: lambda i, v, a=attr, p=path, pr=params: self._rebind_path(p, pr) if v else None})
                    return
                obj = child
        else:
            obj = self

        if dynamic_var:
            self._bind_dynamic(obj, prop, dynamic_var, path, default, serialize, deserialize)
        else:
            self._bind_static(obj, prop, path, default, serialize, deserialize)

    def _apply_value(self, obj, prop, key, default, serialize, deserialize):
        """Восстанавливает значение из _saved_vc или устанавливает default."""
        if key in self._saved_vc:
            val = self._saved_vc[key]
            if deserialize:
                val = deserialize(obj, val)
            setattr(obj, prop, val)
        else:
            setattr(obj, prop, default)

    def _add_change_tracker(self, path, obj, prop, key_func, serialize):
        """Добавляет бинд на изменение свойства и сохранение в _saved_vc.
        key_func вызывается без аргументов и возвращает актуальный ключ для сохранения.
        """
        def on_change(instance, value):
            key = key_func()
            stored = serialize(instance, value) if serialize else value
            self._saved_vc[key] = stored
            self._save_vc()
        obj.bind(**{prop: on_change})
        self._bindings.setdefault(path, []).append((obj, prop, on_change))

    def _bind_static(self, obj, prop, path, default, serialize, deserialize):
        self._apply_value(obj, prop, path, default, serialize, deserialize)
        self._add_change_tracker(path, obj, prop, lambda: path, serialize)

    def _bind_dynamic(self, obj, prop, var, path, default, serialize, deserialize):
        current_var = getattr(self, var, None)
        if current_var is not None:
            actual_key = path.replace(f'@{var}', f'_{current_var}')
            self._apply_value(obj, prop, actual_key, default, serialize, deserialize)

        # Отслеживаем изменение свойства (с динамическим ключом)
        self._add_change_tracker(
            path, obj, prop,
            key_func=lambda: path.replace(f'@{var}', f'_{getattr(self, var, "")}'),
            serialize=serialize
        )

        # Отслеживаем изменение переменной (восстановление значения при переключении)
        def on_var_change(instance, new_var):
            new_key = path.replace(f'@{var}', f'_{new_var}')
            self._apply_value(obj, prop, new_key, default, serialize, deserialize)
        self.bind(**{var: on_var_change})
        self._bindings.setdefault(path, []).append((self, var, on_var_change))

    def _rebind_path(self, path, params):
        """Вызывается, когда нужный объект появляется в дереве."""
        self._unbind_path(path)
        self._setup_path(path, params)

    def _unbind_path(self, path):
        for obj, prop, func in self._bindings.get(path, []):
            obj.unbind(**{prop: func})
        self._bindings.pop(path, None)

    def _unbind_all(self):
        for path in list(self._bindings):
            self._unbind_path(path)

    def _save_vc(self):
        if self._view_context_loaded:
            self.set_view_context(self._saved_vc)


def walk_by_parents(widget: Widget) -> Widget:
    parent = widget.parent
    while parent is not Window:
        yield parent
        if parent is None:
            return None
        parent = parent.parent


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


def get_cursor_zone(widget, mouse_pos: Tuple[float, float],
                    accuracy: int = 6) -> WidgetSide:
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
