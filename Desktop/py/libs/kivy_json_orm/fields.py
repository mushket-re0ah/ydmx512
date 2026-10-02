from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Type, Union

from kivy.event import EventDispatcher
from kivy.properties import (
    BooleanProperty,
    ColorProperty,
    DictProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
    OptionProperty,
    StringProperty,
    VariableListProperty,
)
from typing_extensions import TypeAlias

from libs.properties import (
    BindableObjectProperty,
    ClampedNumericProperty,
    ContextualNumericProperty,
    EnumProperty,
)
from libs.serialize import (
    Deserializer,
    FallbackCb,
    SerializableMixin,
    SerializableMixinProperty,
    Serializer,
    enum_deserializer,
    enum_serializer,
    hex_color_serializer,
    list_of_serializable_deserializer,
    list_of_serializable_serializer,
    nested_serializer,
)
from libs.typecheck import KivyCallback

if TYPE_CHECKING:
    from libs.kivy_json_orm.table_implementation import BaseTable, DatabaseRow

TableSource: TypeAlias = Union[str, Callable[[], "BaseTable"]]


def _resolve_table(table_source: TableSource, obj:Optional[SerializableMixin]=None) -> "BaseTable":
    if isinstance(table_source, str):
        return obj.database.get(table_source)
    return table_source()

def table_ref_serializer() -> Serializer:
    def serialize(self: SerializableMixin, value: Optional["DatabaseRow"]) -> Optional[int]:
        if value is None:
            return None
        return value.id_
    return serialize

def table_ref_deserializer(
    table_source: TableSource,
    fallback_fn: Optional[FallbackCb]=None,
) -> Deserializer:
    def deserialize(
        self: SerializableMixin,
        id_value: Optional[int],
    ) -> Optional["DatabaseRow"]:
        if id_value is not None:
            table = _resolve_table(table_source, self)
            row = table.get_row_by_id(id_value)
            if row is not None:
                return row
        if fallback_fn is None:
            return None
        return fallback_fn(self.database) if isinstance(table_source, str) else fallback_fn()

    return deserialize

def list_of_refs_serializer() -> Serializer:
    def serialize(self: SerializableMixin, value: List["DatabaseRow"]) -> List[int]:
        return [item.id_ for item in value]
    return serialize

def list_of_refs_deserializer(
        table_source: TableSource,
        fallback_fn:Optional[FallbackCb]=None
    ) -> Deserializer:
    def deserialize(self: SerializableMixin, value: List[int]) -> List["DatabaseRow"]:
        table = _resolve_table(table_source, self)
        result: List["DatabaseRow"] = []  # noqa: UP037
        for id_val in value:
            row = table.get_row_by_id(id_val)
            if row is not None:
                result.append(row)
            elif fallback_fn:
                result.append(
                    fallback_fn(self.database) if isinstance(table_source, str) else fallback_fn()
                )
        return result
    return deserialize


class FieldMixin(SerializableMixinProperty):
    def __init__(self, *args: Any, **kwargs: Any):
        """kivy не позволяет обращаться к полю force_dispatch из python.
        Это Cython поле. Так что ничего не остается, кроме как поймать его на
        этапе создания поля. Тогда надо и comparator сохранять
        """
        self.force_dispatch = bool(kwargs.get("force_dispatch", False))
        self.comparator = kwargs.get("comparator", None)
        super().__init__(*args, **kwargs)

    def set(self, obj: Union["BaseTable", "DatabaseRow"], value: Any) -> Any:
        result = super().set(obj, value)
        if hasattr(obj, "_it_is_table"):
            is_loading = obj.is_loading
        else:
            is_loading = obj.table.is_loading if hasattr(obj, "table") else False
        if result and hasattr(obj, "save") and not is_loading:
            obj.save()
        return result

class NumericField(FieldMixin, NumericProperty):
    pass

class StringField(FieldMixin, StringProperty):
    pass

class BooleanField(FieldMixin, BooleanProperty):
    pass

class OptionField(FieldMixin, OptionProperty):
    pass

class ListField(FieldMixin, ListProperty):
    pass

class VariableListField(FieldMixin, VariableListProperty):
    pass

class DictField(FieldMixin, DictProperty):
    pass

class ClampedNumericField(FieldMixin, ClampedNumericProperty):
    pass

class ContextualNumericField(FieldMixin, ContextualNumericProperty):
    pass

class ListNestedField(FieldMixin, ListProperty):
    def __init__(self, nested_cls: Type[SerializableMixin], *args: Any, **kwargs: Any):
        self.nested_cls = nested_cls
        self.serialize = list_of_serializable_serializer()
        self.deserialize = list_of_serializable_deserializer(nested_cls)
        super().__init__(*args, **kwargs)

class ListRefField(FieldMixin, ListProperty):
    is_ref = True

    def __init__(self, table_source: TableSource, *args: Any, **kwargs: Any):
        self.serialize = list_of_refs_serializer()
        self.deserialize = list_of_refs_deserializer(table_source)
        super().__init__(*args, **kwargs)

class EnumField(FieldMixin, EnumProperty):
    def __init__(self, enum_cls: Type[Enum], *args: Any, **kwargs: Any):
        self.serialize = enum_serializer()
        self.deserialize = enum_deserializer(enum_cls)
        super().__init__(enum_cls, *args, **kwargs)

class ColorField(FieldMixin, ColorProperty):
    def __init__(self, *args: Any, **kwargs: Any):
        self.serialize = hex_color_serializer()
        super().__init__(*args, **kwargs)

class RefField(FieldMixin, ObjectProperty):
    is_ref = True

    def __init__(self, table_source: TableSource, *args: Any, **kwargs: Any):
        self.serialize = table_ref_serializer()
        self.deserialize = table_ref_deserializer(
            table_source,
            fallback_fn=kwargs.get("fallback_fn", None)
        )
        super().__init__(*args, **kwargs)


def _nested_deserializer(prop: "NestedField") -> Deserializer:
    def deserialize(
            self: SerializableMixin,
            value: Optional[Dict[str, Any]]
        ) -> Optional[SerializableMixin]:
        if value is None:
            return None
        current = getattr(self, prop.name, None)

        if current is not None:
            current.deserialize(value)
            return current
        return prop.nested_cls.from_data(value) if value is not None else None
    return deserialize
class NestedField(FieldMixin, ObjectProperty):
    def __init__(self, nested_cls: Type[SerializableMixin], *args: Any, **kwargs: Any):
        self.nested_cls = nested_cls
        self.serialize = nested_serializer()
        self.deserialize = _nested_deserializer(self)
        super().__init__(*args, **kwargs)

    def set(self, obj: SerializableMixin, value: Optional[SerializableMixin]) -> Any:
        if value is not None and hasattr(obj, "table"):
            value.table = obj.table
        return super().set(obj, value)


class BindableObjectRefField(FieldMixin, BindableObjectProperty):
    is_ref = True

    def __init__(
            self,
            table_source: TableSource,
            *args: Any,
            bind:Dict[str, Union[str, KivyCallback]]=None,
            on_set:Optional[Union[str, Callable[[EventDispatcher], Any]]]=None,
            **kwargs: Any):
        self.serialize = table_ref_serializer()
        self.deserialize = table_ref_deserializer(
            table_source,
            fallback_fn=kwargs.get("fallback_fn", None)
        )
        super().__init__(*args, bind=bind, on_set=on_set, **kwargs)

class ObjectField(FieldMixin, ObjectProperty):
    pass
