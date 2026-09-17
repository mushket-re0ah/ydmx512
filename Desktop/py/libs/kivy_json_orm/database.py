from kivy.event import EventDispatcher
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from libs.utils import ThrottledCall
from libs.kivy_json_orm.table_implementation import BaseTable
from pathlib import Path
from typing import Dict, Optional, Callable, Union


class Database(EventDispatcher):
    save_interval = NumericProperty(None, allownone=True)
    backup_interval = NumericProperty(None, allownone=True)

    root_dir = None
    tables: Dict[str, BaseTable] = None
    _backup_callback = None
    save_throttled = None
    backup_throttled = None
    def __init__(self,
            root_dir: Union[str, Path],
            save_interval: Optional[float]=None,
            backup_interval: Optional[float]=None,
            backup_callback=None):
        self.root_dir = Path(root_dir)
        self.tables = {}
        self._backup_callback = backup_callback
        super().__init__(save_interval=save_interval, backup_interval=backup_interval)

    def on_save_interval(self, _, save_interval: float):
        if self.save_throttled:
            self.save_throttled.interval = save_interval
        else:
            self.save_throttled = ThrottledCall(self.save_all, save_interval)

    def on_backup_interval(self, _, backup_interval: float):
        if self.backup_throttled:
            self.backup_throttled.interval = backup_interval
        else:
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

    def __getattr__(self, name):
        try:
            return self.tables[name]
        except KeyError:
            raise AttributeError(name)

    def __getitem__(self, name):
        try:
            return self.tables[name]
        except KeyError:
            raise KeyError(name)
