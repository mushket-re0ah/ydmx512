from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple, TypedDict, Union, cast

from kivy.clock import Clock
from kivy.event import EventDispatcher

from libs.serialize import Deserializer, Serializer
from libs.typecheck import AnyCallback, EventDispatcherProtocol, KivyCallback


class AutoUnbindBehavior(EventDispatcherProtocol):
    """Миксин для управления внешними привязками"""
    _bindings_to: Dict[EventDispatcher, List[Tuple[str, AnyCallback]]]
    def __init__(self, *args: Any, **kwargs: Any):
        self._bindings_to = {}
        super().__init__(*args, **kwargs)

    def bind_to(self, obj: EventDispatcher, **kwargs: AnyCallback):
        """Привязаться к другому объекту и запомнить это."""
        obj.bind(**kwargs)
        if obj not in self._bindings_to:
            self._bindings_to[obj] = []
        self._bindings_to[obj].extend(kwargs.items())

    def unbind_from(self, obj: EventDispatcher):
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


class ViewContextTemplateInnerDict(TypedDict):
    default: Any
    serialize: Serializer
    deserialize: Deserializer


class ViewContextSaverMixin(EventDispatcherProtocol):
    """Микшин для MDIWindow. Автоматически сохраняет состояние виджетов
    по плоскому списку путей, в том числе с динамическими ключами @var."""
    view_context_template: Mapping[
        str,
        Union[Any, ViewContextTemplateInnerDict]
    ] = {}  # переопределить в наследнике

    def __init__(self, *args: Any, **kwargs: Any):
        self._view_context_loaded = False
        super().__init__(*args, **kwargs)

    def load_view_context(self, view_context:Optional[Dict[str, Any]]=None):
        if view_context is None:
            view_context = self.get_view_context() or {}
        self._saved_vc: Dict[str, Any] = view_context.copy()
        self._bindings: Dict[str, List[Tuple[EventDispatcher, str, KivyCallback]]] = {}
        Clock.schedule_once(self._load_view_context, 0)

    def _load_view_context(self, _dt: float):
        for path, params in self.view_context_template.items():
            self._setup_path(path, params)
        self._view_context_loaded = True

    def get_view_context(self) -> Dict[str, Any]:
        return {}

    def set_view_context(self, view_context: Dict[str, Any]) -> bool:
        return True

    def _get_params(
        self,
        params: Union[Any, ViewContextTemplateInnerDict]
        ) -> Union[
            Tuple[Any, Serializer, Deserializer],
            Tuple[Any, None, None]
    ]:
        """Если params — словарь с ключом 'default', это расширенный формат.
        Иначе это просто значение по умолчанию без сериализаторов.
        """
        if isinstance(params, dict) and 'default' in params:
            params = cast(ViewContextTemplateInnerDict, params)
            default = params.get('default')
            serialize = params.get('serialize')
            deserialize = params.get('deserialize')
            if serialize is None or deserialize is None:
                raise ValueError(f"object {self} has invalid ser/deserialize params dict {params}")
            return (default, serialize, deserialize)
        params = cast(Any, params)
        return (params, None, None)

    def _setup_path(self, path: str, params: Union[Any, ViewContextTemplateInnerDict]):
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
                    obj.bind(
                        **{attr: lambda i, v, a=attr, p=path, pr=params:
                            self._rebind_path(p, pr) if v else None
                        }
                    )
                    return
                obj = child
        else:
            obj = self

        if dynamic_var:
            self._bind_dynamic(obj, prop, dynamic_var, path, default, serialize, deserialize)
        else:
            self._bind_static(obj, prop, path, default, serialize, deserialize)

    def _apply_value(
            self,
            obj: EventDispatcher,
            prop: str,
            key: str,
            default: Any,
            _:Optional[Serializer],
            deserialize: Optional[Deserializer]):
        """Восстанавливает значение из _saved_vc или устанавливает default."""
        if key in self._saved_vc:
            val = self._saved_vc[key]
            if deserialize:
                val = deserialize(obj, val)
            setattr(obj, prop, val)
        else:
            setattr(obj, prop, default)

    def _add_change_tracker(
            self,
            path: str,
            obj: EventDispatcher,
            prop: str,
            key_func: Callable[[], str],
            serialize: Optional[Serializer]):
        """Добавляет бинд на изменение свойства и сохранение в _saved_vc.
        key_func вызывается без аргументов и возвращает актуальный ключ для сохранения.
        """
        def on_change(instance: EventDispatcher, value: Any):
            key = key_func()
            stored = serialize(instance, value) if serialize else value
            self._saved_vc[key] = stored
            self._save_vc()
        obj.bind(**{prop: on_change})
        self._bindings.setdefault(path, []).append((obj, prop, on_change))

    def _bind_static(
            self,
            obj: EventDispatcher,
            prop: str,
            path: str,
            default: Any,
            serialize: Optional[Serializer],
            deserialize: Optional[Deserializer]):
        self._apply_value(obj, prop, path, default, serialize, deserialize)
        self._add_change_tracker(path, obj, prop, lambda: path, serialize)

    def _bind_dynamic(
            self,
            obj: EventDispatcher,
            prop: str,
            var: str,
            path: str,
            default: Any,
            serialize: Optional[Serializer],
            deserialize: Optional[Deserializer]):
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
        def on_var_change(_: EventDispatcher, new_var: Any):
            new_key = path.replace(f'@{var}', f'_{new_var}')
            self._apply_value(obj, prop, new_key, default, serialize, deserialize)
        self.bind(**{var: on_var_change})
        self._bindings.setdefault(path, []).append((self, var, on_var_change))

    def _rebind_path(self, path: str, params: Union[Any, Dict[str, Any]]):
        """Вызывается, когда нужный объект появляется в дереве."""
        self._unbind_path(path)
        self._setup_path(path, params)

    def _unbind_path(self, path: str):
        for obj, prop, func in self._bindings.get(path, []):
            obj.unbind(**{prop: func})
        self._bindings.pop(path, None)

    def _unbind_all(self):
        for path in list(self._bindings):
            self._unbind_path(path)

    def _save_vc(self):
        if self._view_context_loaded:
            self.set_view_context(self._saved_vc)
