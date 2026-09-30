from enum import Enum
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, Type, TypeVar

from kivy.event import EventDispatcher
from kivy.utils import get_hex_from_color
from typing_extensions import TypeAlias

from libs.kivy_utils import atomic_setattrs
from libs.typecheck import RGBA, OptionalNumber

SerializableT = TypeVar("SerializableT", bound="SerializableMixin")
Serializer: TypeAlias = Callable[["SerializableMixin", Any], Any]
Deserializer: TypeAlias = Callable[["SerializableMixin", Any], Any]
FallbackCb: TypeAlias = Callable[..., Any]
DefaultFactoryCb: TypeAlias = Callable[[], Any]

class SerializableMixinProperty:
    is_ref = False

    serialize: Serializer
    deserialize: Deserializer
    fallback_fn: Optional[FallbackCb]
    default_factory:Optional[DefaultFactoryCb]
    def __init__(
            self,
            *args: Any,
            serialize:Optional[Serializer]=None,
            deserialize:Optional[Deserializer]=None,
            fallback_fn:Optional[FallbackCb]=None,
            default_factory:Optional[DefaultFactoryCb]=None,
            **kwargs: Any):
        self.fallback_fn = fallback_fn
        self.default_factory = default_factory
        super().__init__(*args, **kwargs)
        if serialize is not None:
            self.serialize = serialize
        elif "serialize" not in self.__dict__:
            self.serialize = default_serializer
        if deserialize is not None:
            self.deserialize = deserialize
        elif "deserialize" not in self.__dict__:
            self.deserialize = default_deserializer


class SerializableMeta(type):
    def __new__(mcs, name: str, bases: Tuple[type, ...], namespace: Dict[str, Any]) -> type:
        new_cls = super().__new__(mcs, name, bases, namespace)
        setattr(new_cls, "serialize", mcs._create_serialize_method(new_cls))
        setattr(new_cls, "deserialize", mcs._create_deserialize_method(new_cls))
        new_cls._get_serialization_keys(new_cls)
        return new_cls

    @staticmethod
    def _get_serialization_keys(target_cls: type) -> Tuple[str, ...]:
        if "serialization_keys" in target_cls.__dict__:
            return target_cls.__dict__["serialization_keys"]

        stop_classes = {EventDispatcher, object}
        keys: List[str] = []
        seen: Set[str] = set()

        for base in reversed(target_cls.__mro__):
            if base in stop_classes:
                continue
            for name, value in base.__dict__.items():
                if name in seen:
                    continue
                if isinstance(value, SerializableMixinProperty):
                    seen.add(name)
                    keys.append(name)

        target_cls.serialization_keys = tuple(keys)
        return target_cls.serialization_keys

    @staticmethod
    def _create_serialize_method(target_cls: type) -> Callable[["SerializableMixin"], Dict[str, Any]]:
        def _serialize(self: SerializableMixin) -> Dict[str, Any]:
            result: Dict[str, Any] = {}
            for key in SerializableMeta._get_serialization_keys(target_cls):
                prop = self.property(key)
                ser = prop.serialize
                defaultvalue = prop.defaultvalue
                value = getattr(self, key)
                if defaultvalue != value:
                    result[key] = ser(self, value) if ser else value
            return result
        return _serialize

    @staticmethod
    def _create_deserialize_method(target_cls: type) -> Callable[["SerializableMixin", Dict[str, Any]], "SerializableMixin"]:
        def deserialize(self: SerializableMixin, data: Dict[str, Any]) -> SerializableMixin:
            items = [(k, getattr(type(self), k))
                     for k in SerializableMeta._get_serialization_keys(target_cls)
                     if k in data and getattr(type(self), k, None) is not None]

            value_attrs = {
                k: f.deserialize(self, data[k])
                for k, f in items
                if not getattr(f, "is_ref", False)
            }
            atomic_setattrs(self, dispatch=False, **value_attrs)

            ref_attrs = {
                k: f.deserialize(self, data[k])
                for k, f in items
                if getattr(f, "is_ref", False)
            }
            atomic_setattrs(self, dispatch=False, **ref_attrs)

            for key, _ in items:
                self.property(key).dispatch(self)

            self.after_deserialize()
            return self
        return deserialize


class SerializableMixin(EventDispatcher, metaclass=SerializableMeta):
    def __init__(self, **kwargs: Any):
        for key in self.serialization_keys:
            if key not in kwargs:
                field = getattr(self.__class__, key, None)
                factory = getattr(field, "default_factory", None)
                if factory is not None:
                    kwargs[key] = factory()
        super().__init__(**kwargs)

    @classmethod
    def from_data(cls, data: Dict[str, Any]) -> "SerializableMixin":
        return cls().deserialize(data)

    def get_copy(self: SerializableT) -> SerializableT:
        return self.__class__.from_data(self.serialize())

    def set_default(self: "SerializableMixin"):
        default = self.__class__()
        for key in self.serialization_keys:
            setattr(self, key, getattr(default, key))

    def after_deserialize(self):
        pass


def default_serializer(_self: SerializableMixin, value: Any) -> Any:
    return value

def default_deserializer(_self: SerializableMixin, value: Any) -> Any:
    return value

def serializable_or_raw_serializer() -> Serializer:
    def serialize(_self: SerializableMixin, value: Any) -> Any:
        if isinstance(value, SerializableMixin):
            return value.serialize()
        return value
    return serialize

def rounded_tuple_serializer(decimals: int, allow_none:bool=False) -> Serializer:
    def serialize(_self: SerializableMixin, value: Iterable[OptionalNumber]) -> Tuple[OptionalNumber, ...]:
        if allow_none:
            return tuple(None if v is None else round(v, decimals) for v in value)
        return tuple(round(v, decimals) for v in value)
    return serialize

def hex_color_serializer() -> Serializer:
    def serialize(_self: SerializableMixin, color: RGBA) -> str:
        return get_hex_from_color(color)
    return serialize

def enum_serializer() -> Serializer:
    def serialize(_self: SerializableMixin, value: Any) -> Any:
        return value.value if value is not None else None
    return serialize

def enum_deserializer(enum_cls: Type[Enum]) -> Deserializer:
    def deserialize(_self: SerializableMixin, value: Any) -> Enum:
        return enum_cls(value)
    return deserialize

def nested_serializer() -> Serializer:
    def serialize(_self: SerializableMixin, value: Optional[SerializableMixin]) -> Optional[Dict[str, Any]]:
        return value.serialize() if value is not None else None
    return serialize

def nested_deserializer(cls: Type[SerializableMixin]) -> Deserializer:
    def deserialize(_self: SerializableMixin, value: Optional[SerializableMixin]) -> Optional[SerializableMixin]:
        return cls.from_data(value) if value is not None else None
    return deserialize

def list_of_serializable_serializer() -> Serializer:
    def serialize(_self: SerializableMixin, value: Iterable[SerializableMixin]) -> List[Dict[str, Any]]:
        return [item.serialize() for item in value]
    return serialize

def list_of_serializable_deserializer(item_cls: Type[SerializableMixin]) -> Deserializer:
    def deserialize(_self: SerializableMixin, value: Iterable[Dict[str, Any]]) -> List[SerializableMixin]:
        return [item_cls.from_data(item) for item in value]
    return deserialize

def nested_optional_pair(cls: Type[SerializableMixin]) -> Tuple[Serializer, Deserializer]:
    """Для полей типа Optional[SerializableMixin]"""
    return (
        lambda self, v: v.serialize() if v is not None else None,
        lambda self, v: cls.from_data(v) if v is not None else None
    )

def dict_of_serializable_pair(cls: Type[SerializableMixin]) -> Tuple[Serializer, Deserializer]:
    """Для полей типа Dict[str, SerializableMixin]"""
    return (
        lambda self, d: {k: v.serialize() for k, v in d.items()},
        lambda self, d: {k: cls.from_data(v) for k, v in d.items()}
    )
