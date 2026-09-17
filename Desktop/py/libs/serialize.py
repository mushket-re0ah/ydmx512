from kivy.utils import get_hex_from_color
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar
from kivy.properties import Property, AliasProperty
from kivy.event import EventDispatcher
from libs.kivy_utils import atomic_setattrs
import logging

logger = logging.getLogger(__name__)


T = TypeVar("T")


def serializable_or_raw_serializer():
    def serialize(self, value):
        if isinstance(value, SerializableMixin):
            return value.serialize()
        return value
    return serialize

def rounded_tuple_serializer(decimals, allow_none=False):
    def serialize(self, value):
        if allow_none:
            return tuple(None if v is None else round(v, decimals) for v in value)
        return tuple(round(v, decimals) for v in value)
    return serialize

def hex_color_serializer():
    def serialize(self, color):
        return get_hex_from_color(color)
    return serialize

def enum_serializer():
    def serialize(self, value):
        return value.value if value else None
    return serialize

def enum_deserializer(enum_cls):
    def deserialize(self, value):
        return enum_cls(value)
    return deserialize

def nested_serializer():
    def serialize(self, value):
        return value.serialize() if value is not None else None
    return serialize

def nested_deserializer(cls: Type[T]) -> Callable[[dict], T]:
    def deserialize(self, value):
        return cls.from_data(value) if value is not None else None
    return deserialize

def list_of_serializable_serializer():
    def serialize(self, value):
        return [item.serialize() for item in value]
    return serialize

def list_of_serializable_deserializer(item_cls: Type[T]):
    def deserialize(self, value):
        return [item_cls.from_data(item) for item in value]
    return deserialize

def nested_optional_pair(cls):
    """Для полей типа Optional[SerializableMixin]"""
    return (
        lambda self, v: v.serialize() if v is not None else None,
        lambda self, v: cls.from_data(v) if v is not None else None
    )

def dict_of_serializable_pair(cls):
    """Для полей типа Dict[str, SerializableMixin]"""
    return (
        lambda self, d: {k: v.serialize() for k, v in d.items()},
        lambda self, d: {k: cls.from_data(v) for k, v in d.items()}
    )


class SerializableMixinProperty:
    is_ref = False

    def __init__(self, *args, serialize=None, deserialize=None, fallback_fn=None, default_factory=None, **kwargs):
        self.fallback_fn = fallback_fn
        self.default_factory = default_factory
        super().__init__(*args, **kwargs)
        if serialize is not None:
            self.serialize = serialize
        elif "serialize" not in self.__dict__:
            self.serialize = lambda self, v: v
        if deserialize is not None:
            self.deserialize = deserialize
        elif "deserialize" not in self.__dict__:
            self.deserialize = lambda self, v: v


T = TypeVar("T", bound="SerializableMixin")


class SerializationError(Exception):
    pass


class DeserializationError(Exception):
    pass


class SerializableMeta(type):
    def __new__(cls, name, bases, namespace):
        new_cls = super().__new__(cls, name, bases, namespace)
        new_cls.serialize = cls._create_serialize_method(new_cls)
        new_cls.deserialize = cls._create_deserialize_method(new_cls)
        new_cls._get_serialization_keys(new_cls)
        return new_cls

    @staticmethod
    def _get_serialization_keys(cls):
        if "serialization_keys" in cls.__dict__:
            return cls.__dict__["serialization_keys"]

        stop_classes = {EventDispatcher, object}
        keys = []
        seen = set()

        for base in reversed(cls.__mro__):
            if base in stop_classes:
                continue
            for name, value in base.__dict__.items():
                if name in seen:
                    continue
                if isinstance(value, SerializableMixinProperty):
                    seen.add(name)
                    keys.append(name)

        cls.serialization_keys = tuple(keys)
        return cls.serialization_keys

    @staticmethod
    def _create_serialize_method(cls):
        def _serialize(self):
            result = {}
            for key in cls._get_serialization_keys(cls):
                prop = self.property(key)
                ser = prop.serialize
                defaultvalue = prop.defaultvalue
                value = getattr(self, key)
                if defaultvalue != value:
                    result[key] = ser(self, value) if ser else value
            return result
        return _serialize

    @staticmethod
    def _create_deserialize_method(cls):
        def deserialize(self, data):
            items = [(k, getattr(type(self), k))
                     for k in cls._get_serialization_keys(cls)
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
    def __init__(self, **kwargs):
        for key in self.serialization_keys:
            if key not in kwargs:
                field = getattr(self.__class__, key, None)
                factory = getattr(field, "default_factory", None)
                if factory is not None:
                    kwargs[key] = factory()
        super().__init__(**kwargs)

    @classmethod
    def from_data(cls, data: Dict[str, Any]) -> T:
        return cls().deserialize(data)

    def get_copy(self: T) -> T:
        return self.__class__.from_data(self.serialize())

    def set_default(self: T):
        default = self.__class__()
        for key in self.serialization_keys:
            setattr(self, key, getattr(default, key))

    def after_deserialize(self):
        pass
