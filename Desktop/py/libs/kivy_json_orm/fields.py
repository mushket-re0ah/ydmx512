from kivy.properties import (
    NumericProperty, ObjectProperty, StringProperty, BooleanProperty, ListProperty,
    OptionProperty, DictProperty, ColorProperty, VariableListProperty
)
from libs.serialize import *
from libs.properties import ClampedNumericProperty, EnumProperty, ContextualNumericProperty, BindableObjectProperty
from typing import Callable, Union


def _resolve_table(table_source: Union[str, Callable], obj=None):
    if isinstance(table_source, str):
        return obj.database.get(table_source)
    else:
        return table_source()

def table_ref_serializer(id_attr: str = "_id"):
    def serialize(self, value):
        if value is None:
            return None
        return getattr(value, id_attr)
    return serialize

def table_ref_deserializer(table_source: Union[str, Callable], id_attr: str = "_id", fallback_fn: Callable = None):
    def deserialize(self, id_value):
        if id_value is None:
            return (fallback_fn(self.database) if isinstance(table_source, str) else fallback_fn()) if fallback_fn else None
        table = _resolve_table(table_source, self)
        row = table.get_row_by_id(id_value)
        if row is not None:
            return row
        if fallback_fn:
            return fallback_fn(self.database) if isinstance(table_source, str) else fallback_fn()
        return None
    return deserialize

def list_of_refs_serializer(id_attr="_id"):
    def serialize(self, value):
        return [getattr(item, id_attr) for item in value]
    return serialize

def list_of_refs_deserializer(table_source: Union[str, Callable], id_attr="_id", fallback_fn=None):
    def deserialize(self, value):
        table = _resolve_table(table_source, self)
        result = []
        for id_val in value:
            row = table.get_row_by_id(id_val)
            if row is not None:
                result.append(row)
            elif fallback_fn:
                result.append(fallback_fn(self.database) if isinstance(table_source, str) else fallback_fn())
        return result
    return deserialize

def dict_of_refs_set_serializer(id_attr="_id"):
    def serialize(self, value):
        return {k: [getattr(obj, id_attr) for obj in v] for k, v in value.items()}
    return serialize

def dict_of_refs_set_deserializer(table_source: Union[str, Callable], id_attr="_id", fallback_fn=None):
    def deserialize(self, value):
        table = _resolve_table(table_source, self)
        data = defaultdict(set)
        for k_str, id_list in value.items():
            k = int(k_str)
            for id_val in id_list:
                row = table.get_row_by_id(id_val)
                if row is not None:
                    data[k].add(row)
                elif fallback_fn:
                    data[k].add(fallback_fn(self.database) if isinstance(table_source, str) else fallback_fn())
        return data
    return deserialize


class FieldMixin(SerializableMixinProperty):
    def __init__(self, *args, **kwargs):
        """kivy не позволяет обращаться к полю force_dispatch из python.
        Это Cython поле. Так что ничего не остается, кроме как поймать его на
        этапе создания поля. Тогда надо и comparator сохранять
        """
        self.force_dispatch = bool(kwargs.get("force_dispatch", False))
        self.comparator = kwargs.get("comparator", None)
        super().__init__(*args, **kwargs)

    def set(self, obj, value):
        result = super().set(obj, value)
        if hasattr(obj, "_it_is_table"):
            is_loading = obj.is_loading
        else:
            is_loading = obj._table.is_loading if hasattr(obj, "_table") else False
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
    def __init__(self, nested_cls, *args, **kwargs):
        self.nested_cls = nested_cls
        self.serialize = list_of_serializable_serializer()
        self.deserialize = list_of_serializable_deserializer(nested_cls)
        super().__init__(*args, **kwargs)

class ListRefField(FieldMixin, ListProperty):
    is_ref = True

    def __init__(self, table_source: Union[str, Callable], *args, **kwargs):
        self.serialize = list_of_refs_serializer()
        self.deserialize = list_of_refs_deserializer(table_source)
        super().__init__(*args, **kwargs)

class EnumField(FieldMixin, EnumProperty):
    def __init__(self, enum_cls, *args, **kwargs):
        self.serialize = enum_serializer()
        self.deserialize = enum_deserializer(enum_cls)
        super().__init__(enum_cls, *args, **kwargs)

class ColorField(FieldMixin, ColorProperty):
    def __init__(self, *args, **kwargs):
        self.serialize = hex_color_serializer()
        super().__init__(*args, **kwargs)

class RefField(FieldMixin, ObjectProperty):
    is_ref = True

    def __init__(self, table_source: Union[str, Callable], *args, **kwargs):
        self.serialize = table_ref_serializer()
        self.deserialize = table_ref_deserializer(table_source, fallback_fn=kwargs.get("fallback_fn", None))
        super().__init__(*args, **kwargs)


def _nested_deserializer(prop) -> Callable[[dict], T]:
    def deserialize(self, value):
        if value is None:
            return None
        current = getattr(self, prop.name, None)

        if current is not None:
            current.deserialize(value)
            return current
        return prop.nested_cls.from_data(value) if value is not None else None
    return deserialize
class NestedField(FieldMixin, ObjectProperty):
    def __init__(self, nested_cls, *args, **kwargs):
        self.nested_cls = nested_cls
        self.serialize = nested_serializer()
        self.deserialize = _nested_deserializer(self)
        super().__init__(*args, **kwargs)

    def set(self, obj, value):
        if value is not None and hasattr(obj, "_table"):
            value._table = obj._table
        return super().set(obj, value)


class BindableObjectRefField(FieldMixin, BindableObjectProperty):
    is_ref = True

    def __init__(self, table_source: Union[str, Callable], *args, bind=None, on_set=None, **kwargs):
        self.serialize = table_ref_serializer()
        self.deserialize = table_ref_deserializer(table_source, fallback_fn=kwargs.get("fallback_fn", None))
        super().__init__(*args, bind=bind, on_set=on_set, **kwargs)

class ObjectField(FieldMixin, ObjectProperty):
    pass
