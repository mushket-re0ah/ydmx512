from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type

from kivy.properties import NumericProperty

from libs.file_utils import atomic_json_save, json_load
from libs.kivy_json_orm.fields import DictField, NumericField
from libs.kivy_mixins import AutoUnbindBehavior
from libs.kivy_utils import atomic_setattrs
from libs.serialize import SerializableMixin

if TYPE_CHECKING:
    from libs.kivy_json_orm.database import Database


class BaseTable(SerializableMixin):
    name: Optional[str] = None
    filename: Optional[str] = None
    filepath: Optional[Path] = None
    _save_flag: bool = False
    _events_block: bool = True
    is_loading: bool = True
    database: Optional["Database"] = None
    _it_is_table: bool = True

    def init(self):
        self.filepath = self._make_filepath()
        self._save_flag = False
        self._load()
        self._events_block = False

    def save(self):
        self._save_flag = True

    def try_save(self):
        if self._save_flag:
            self._save()

    def edit(self, **kwargs: Any):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.save()

    def _make_filepath(self) -> Path:
        if self.database is None:
            raise ValueError("table is not registered")
        return self.database.root_dir / self.filename

    def _save(self):
        if self.filepath is None:
            raise ValueError("table is not registered")
        atomic_json_save(self.filepath, self.serialize())
        self._save_flag = False

    def _load(self):
        raise NotImplementedError()


class ConfigTable(BaseTable):
    def _load(self):
        if self.filepath is None:
            raise ValueError("table is not registered")
        self.is_loading = True
        json_data = json_load(self.filepath)
        if json_data:
            self.deserialize(json_data)
        self.is_loading = False


class DatabaseRow(SerializableMixin, AutoUnbindBehavior):
    _id: int = NumericProperty()
    _table: "DatabaseTable"

    __events__ = ("on_remove",)

    def __init__(self, _id: int, table: "DatabaseTable", **kwargs: Any):
        self._id = _id
        self._table = table
        super().__init__(**kwargs)

    def on_remove(self):
        pass

    def edit(self, **kwargs: Any):
        if len(kwargs) == 1:
            for key, value in kwargs.items():
                setattr(self, key, value)
        else:
            atomic_setattrs(self, **kwargs)
        self.save()

    def save(self):
        self._table.save()

    def copy(self, **kwargs: Any) -> "DatabaseRow":
        return self._table.add_row(
            **{attr: kwargs[attr] if attr in kwargs else getattr(self, attr)
                                  for attr in self.serialization_keys}
        )

    def remove(self):
        self._table.remove_row(self)
        self.dispatch("on_remove")

    @property
    def database(self) -> "Database":
        return self._table.database

    def __repr__(self):
        attrs = ', '.join(f'{k}={getattr(self, k)!r}' for k in self.__class__._get_serialization_keys(self.__class__))
        return f'{type(self).__name__}({attrs})'


class DatabaseTable(BaseTable):
    cls_row: Type[DatabaseRow]
    counter_id: int = NumericField(1)

    def deserialize_rows(self, rows: Dict[int, Dict[str, Any]]) -> Dict[int, DatabaseRow]:
        result: Dict[int, DatabaseRow] = {}
        for _id, row_data in rows.items():
            row = self.cls_row(int(_id), self)
            row.deserialize(row_data)
            result[int(_id)] = row
        return result

    rows: Dict[int, DatabaseRow] = DictField(
        serialize=lambda self, rs: {_id: r.serialize() for _id, r in rs.items()},
        deserialize=deserialize_rows
    )

    default_rows: List[Dict[str, Any]] = []  # Должен быть переопределен

    __events__ = ("on_add_row", "on_remove_row")

    def on_add_row(self, added_row: DatabaseRow):
        pass

    def on_remove_row(self, removed_row: DatabaseRow):
        pass

    def add_row(self, **kwargs: Any) -> DatabaseRow:
        _id = self._get_next_id()
        row = self.cls_row(_id, self)
        self.rows[_id] = row
        atomic_setattrs(row, **kwargs)
        row.after_deserialize()
        if not self._events_block:
            self.dispatch("on_add_row", row)
        self._save_flag = True
        return row

    def remove_row(self, row: DatabaseRow):
        del self.rows[row._id]
        self.dispatch("on_remove_row", row)
        self._save_flag = True

    def get_row_by_id(self, _id: int) -> Optional[DatabaseRow]:
        _id = int(_id)
        if _id in self.rows:
            return self.rows[_id]
        return None

    def get_row_by_attribute(self,
                             attr: str,
                             value: Any) -> Optional[DatabaseRow]:
        return next((i for i in self.rows.values() if
                     getattr(i, attr) == value), None)

    def _load(self):
        if self.filepath is None:
            raise ValueError("table is not registered")
        self.is_loading = True
        json_data = json_load(self.filepath)
        self.counter_id = 1
        self.rows = {}
        if json_data:
            self.deserialize(json_data)
        else:
            self._create_default()
        self.is_loading = False

    def _get_next_id(self) -> int:
        _id = self.counter_id
        self.counter_id += 1
        return _id

    def _create_default(self):
        for kwargs in self.default_rows:
            self.add_row(**kwargs)

    def __getattr__(self, name: str) -> Optional[DatabaseRow]:
        if name.startswith('by_'):
            attr = name[3:]
            return lambda val: self.get_row_by_attribute(attr, val)
        raise AttributeError(name)
