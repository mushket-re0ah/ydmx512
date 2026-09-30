from pathlib import Path
from typing import Any, Dict, Optional, Union

from kivy.event import EventDispatcher
from kivy.properties import NumericProperty

from libs.kivy_json_orm.table_implementation import BaseTable
from libs.sub_proc import AsyncProcessCallback
from libs.utils import ThrottledCall


class Database(EventDispatcher):
    save_interval: Optional[float] = NumericProperty(None, allownone=True)
    backup_interval: Optional[float] = NumericProperty(None, allownone=True)

    save_throttled: Optional[ThrottledCall] = None
    backup_throttled: Optional[ThrottledCall] = None
    def __init__(self,
            root_dir: Union[str, Path],
            save_interval: Optional[float]=None,
            backup_interval: Optional[float]=None,
            backup_callback: Optional[AsyncProcessCallback]=None,
            **kwargs: Any):
        self.root_dir = Path(root_dir)
        self.tables: Dict[str, BaseTable] = {}
        self._backup_callback: Optional[AsyncProcessCallback] = backup_callback
        super().__init__(save_interval=save_interval, backup_interval=backup_interval, **kwargs)

    def on_save_interval(self, _, save_interval: float):
        if self.save_throttled:
            self.save_throttled.interval = save_interval
        else:
            self.save_throttled = ThrottledCall(self.save_all, save_interval)

    def on_backup_interval(self, _, backup_interval: float):
        if self.backup_throttled:
            self.backup_throttled.interval = backup_interval
        else:
            if self._backup_callback is None:
                raise ValueError("backup_interval setted, but backup_callback is not")
            self.backup_throttled = ThrottledCall(self._backup_callback, backup_interval)

    def register(self, name: str, table: BaseTable) -> BaseTable:
        if name in self.tables:
            raise ValueError(f"Table '{name}' already registered")
        self.tables[name] = table
        table.database = self
        table.name = name
        return table

    def init(self):
        for table in self.tables.values():
            table.init()

    def get(self, name: str) -> BaseTable:
        return self.tables[name]

    def save_all(self):
        for table in self.tables.values():
            table.try_save()

    def __getattr__(self, name: str) -> BaseTable:
        try:
            return self.tables[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __getitem__(self, name: str) -> BaseTable:
        try:
            return self.tables[name]
        except KeyError as exc:
            raise KeyError(name) from exc
