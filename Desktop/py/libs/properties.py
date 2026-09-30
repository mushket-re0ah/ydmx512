from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union
from weakref import finalize, ref

from kivy.event import EventDispatcher
from kivy.properties import (
    AliasProperty,
    BoundedNumericProperty,
    NumericProperty,
    ObjectProperty,
    OptionProperty,
)
from kivy.utils import boundary

from libs.typecheck import KivyCallback, Number, OptionalNumber


class ClampedNumericProperty(BoundedNumericProperty):
    def __init__(self, default: Number, min_val: Number, max_val: Number, **kwargs: Any):
        super().__init__(default, min=min_val, max=max_val,
                         errorhandler=lambda x: boundary(x, min_val, max_val), **kwargs)


class EnumProperty(OptionProperty):
    def __init__(self, enum_cls: Type[Enum], default:Optional[Any]=None, **kwargs: Any):
        self.enum_cls = enum_cls
        options = list(enum_cls.__members__.values())
        if default is None:
            default = options[0]
        super().__init__(default, options=options, **kwargs)


class BindableObjectProperty(ObjectProperty):
    def __init__(
            self,
            default:Optional[EventDispatcher]=None,
            bind:Dict[str, Union[str, KivyCallback]]=None,
            on_set:Optional[Union[str, Callable[[EventDispatcher], Any]]]=None,
            **kwargs:Any):
        super().__init__(default, **kwargs)
        self._bind_spec:Dict[str, Union[str, KivyCallback]] = bind or {}
        self._on_set:Optional[Union[str, Callable[[EventDispatcher], Any]]] = on_set

    def link(self, obj: EventDispatcher, name: str):
        super().link(obj, name)
        value = self.get(obj)
        if value is not None:
            self._bind_all(obj, value)

    def set(self, obj: EventDispatcher, value: EventDispatcher) -> bool:
        old = self.get(obj)
        if old is not None and self._bind_spec:
            self._unbind_all(obj, old)
        super().set(obj, value)
        if value is not None and self._bind_spec:
            self._bind_all(obj, value)
        self._call_on_set(obj, value)
        return True

    def _resolve_callback(self, obj: EventDispatcher, spec: Union[str, KivyCallback]) -> Optional[KivyCallback]:
        if isinstance(spec, str):
            return getattr(obj, spec, None)
        return spec

    def _bind_all(self, obj: EventDispatcher, target: EventDispatcher):
        for attr, cb_spec in self._bind_spec.items():
            cb = self._resolve_callback(obj, cb_spec)
            if cb:
                target.bind(**{attr: cb})

    def _unbind_all(self, obj: EventDispatcher, target: EventDispatcher):
        for attr, cb_spec in self._bind_spec.items():
            cb = self._resolve_callback(obj, cb_spec)
            target.unbind(**{attr: cb})

    def _call_on_set(self, obj: EventDispatcher, value: EventDispatcher):
        if self._on_set is not None:
            cb = self._resolve_callback(obj, self._on_set)
            cb(value)


class ContextualNumericProperty(NumericProperty):
    _min_getter: Callable[[EventDispatcher], Number]
    _max_getter: Callable[[EventDispatcher], Number]
    _dependencies: Tuple[str, ...]
    _bound_objects: Dict[EventDispatcher, List[Tuple[EventDispatcher, str]]]
    _decimals_getter: Optional[Callable[[EventDispatcher], Number]]
    def __init__(
            self,
            default: OptionalNumber=0,
            *,
            min_getter: Optional[Callable[[EventDispatcher], Number]]=None,
            max_getter: Optional[Callable[[EventDispatcher], Number]]=None,
            dependencies: Optional[Tuple[str, ...]]=None,
            decimals_getter: Optional[Callable[[EventDispatcher], Number]]=None,
            **kwargs: Any):
        super().__init__(default, **kwargs)
        self._min_getter = min_getter if min_getter is not None else ContextualNumericProperty._default_min_getter
        self._max_getter = max_getter if max_getter is not None else ContextualNumericProperty._default_max_getter
        self._dependencies = tuple(dependencies) if dependencies is not None else ()
        self._bound_objects = {}
        self._decimals_getter = decimals_getter

    @staticmethod
    def _default_min_getter(obj: EventDispatcher) -> Number:
        return float("-inf")

    @staticmethod
    def _default_max_getter(obj: EventDispatcher) -> Number:
        return float("inf")

    def link(self, obj: EventDispatcher, name: str):
        super().link(obj, name)
        unbinds: List[Tuple[EventDispatcher, str]] = []
        for dep in self._dependencies:
            obj.fbind(dep, self._on_dependency_changed)
            unbinds.append((obj, dep))
        self._bound_objects[obj] = unbinds

    def _on_dependency_changed(self, instance: EventDispatcher, _):
        prop_name = self.name
        current = getattr(instance, prop_name)
        if current is None:
            return
        clamped = self._clamp(instance, current)
        if clamped != current:
            setattr(instance, prop_name, clamped)

    def __set__(self, obj: EventDispatcher, value: OptionalNumber) -> bool:
        if value is None and self.allownone:
            super().__set__(obj, None)
            return
        if self._decimals_getter is not None:
            dec = self._decimals_getter(obj)
            if dec > 0:
                value = round(float(value), dec)
            else:
                value = int(value)
        else:
            value = int(value)
        super().__set__(obj, self._clamp(obj, value))

    def _clamp(self, obj: EventDispatcher, value: Number) -> Number:
        return boundary(value, self._min_getter(obj), self._max_getter(obj))


class DeepAliasProperty(AliasProperty):
    """Отслеживает внутренние аттрибуты. Можно подписываться как:
        a = ObjectProperty()
        deep = DeepAliasProperty(
            lambda self: self.a.b.c if self.a and self.a.b else None,
            bind=["a.b.c"],
            cache=True
        )
        Это не полноценный Alias и использовать его заместо обычного не надо
    """
    def __init__(self, *args: Any, **kwargs: Any):
        bind = kwargs.pop("bind", None)
        if not bind:
            raise ValueError("DeepAliasProperty: bind пуст")
        super().__init__(*args, **kwargs)
        self._all_prefixes: Set[str] = set()
        for path in bind:
            parts = path.split(".")
            self._all_prefixes.update(
                ".".join(parts[:i])
                for i in range(1, len(parts) + 1)
            )
        self._subscriptions: List[Tuple[EventDispatcher, str, int]] = []
        self._obj_ref = None
        self._finalizer = None

    def link_deps(self, obj: EventDispatcher, _):
        self._obj_ref = ref(obj)
        self._finalizer = finalize(obj, self._unsubscribe_all)
        self._rebind(obj, dispatch=False)

    def _rebind(self, obj: EventDispatcher, dispatch:bool=True):
        self._unsubscribe_all()
        for prefix in self._all_prefixes:
            self._subscribe_path(obj, prefix)
        if dispatch:
            self.trigger_change(obj, None)

    def _subscribe_path(self, obj: EventDispatcher, path: str):
        parts = path.split('.')
        current = obj
        for i, part in enumerate(parts):
            if current is None:
                break

            def make_callback(self_ref=ref(self), obj_ref=self._obj_ref):
                def cb(*_l, **_k):
                    instance = obj_ref()
                    prop = self_ref()
                    if instance is not None and prop is not None:
                        prop._rebind(instance)
                return cb

            cb = make_callback()
            uid = current.fbind(part, cb, ref=False)
            if not uid:
                self._unsubscribe_all()
                raise ValueError(
                    f"DeepAliasProperty: не удалось подписаться на '{part}' в пути '{path}'. "
                    f"Убедитесь, что '{part}' является Kivy-свойством."
                )
            self._subscriptions.append((current, part, uid))

            if i < len(parts) - 1:
                current = getattr(current, part, None)

    def _unsubscribe_all(self):
        for obj, attr, uid in self._subscriptions:
            obj.unbind_uid(attr, uid)
        self._subscriptions.clear()


# if __name__ == '__main__':
#     import unittest
#     from unittest.mock import Mock
#     from kivy.event import EventDispatcher
#     from kivy.properties import ObjectProperty, NumericProperty, AliasProperty

#     class B(EventDispatcher):
#         c = NumericProperty(0)

#     class A(EventDispatcher):
#         b = ObjectProperty(B())

#     class MyWidget(EventDispatcher):
#         a = ObjectProperty(A())
#         deep_value = DeepAliasProperty(
#             lambda self: self.a.b.c if self.a and self.a.b else None,
#             bind=["a.b.c"],
#             cache=True
#         )
#     # Тест
#     w = MyWidget()
#     w.bind(deep_value=lambda _, v: print(f"deep_value changed to {v}"))

#     w.a.b.c = 42   # -> deep_value changed to 42
#     w.a.b.c = 20   # -> deep_value changed to 42
#     w.a.b = B()    # -> deep_value сбросится в 0
