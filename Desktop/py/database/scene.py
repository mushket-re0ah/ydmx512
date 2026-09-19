from misc import constants
from kivy.clock import Clock
from libs.kivy_json_orm.table_implementation import DatabaseTable, DatabaseRow
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, AliasProperty
import time
from libs.midi import midi
from libs.kivy_json_orm.fields import table_ref_serializer
from libs.properties import ClampedNumericProperty
from libs.beat_counter import BeatCounter
from libs.kivy_json_orm.fields import *
from libs.kivy_utils import detach_event_dispatcher
from pathlib import Path


class RowScene(DatabaseRow):
    title = StringField("default")
    note = StringField("")
    date_add = NumericField()
    date_edit = NumericField()
    temp = ClampedNumericField(120, constants.TEMP_MINIMUM, constants.TEMP_MAXIMUM)
    dimmer = ClampedNumericField(100, constants.DIMMER_MINIMUM, constants.DIMMER_MAXIMUM)
    beats_count = ClampedNumericField(4, constants.BEATS_COUNT_MINIMIUM, constants.BEATS_COUNT_MAXIMUM)

    def on_temp(self, _, temp: int):
        if self._table.scene_now is self:
            from libs import logger
            logger.debug(temp)
            self._table.scene_now_temp = temp

    def on_dimmer(self, _, dimmer: int):
        if self._table.scene_now is self:
            self._table.scene_now_dimmer = dimmer

    def on_beats_count(self, _, beats_count: int):
        if self._table.scene_now is self:
            self._table.scene_now_beats_count = beats_count

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.date_add = time.time()
        self.date_edit = time.time()


class TableScene(DatabaseTable):
    cls_row = RowScene
    filename = "scene.json"

    scene_now = RefField(
        table_source="scene",
        deserialize=lambda self, scene_now_id: (
            self.get_row_by_id(scene_now_id)
            or (next(iter(self.rows.values())) if self.rows else self.add_row(title="default"))
        )
    )
    __events__ = ("on_scene_change",)

    scene_now_bc = None
    def __init__(self, scene_tables_order: tuple, **kwargs):
        self.SCENE_TABLES_ORDER = scene_tables_order
        super().__init__(**kwargs)
        self.cache_channel_126 = 0
        self.cache_channel_127 = 0
        midi.bind(
            on_note_on=self.on_midi_set_global_temp,
            on_controller_change=self.on_midi_set_global_temp,
        )

    def init(self):
        super().init()
        self.create_scene_now_beat_counter()

    def create_scene_now_beat_counter(self):
        scene_now_bc = BeatCounter(
            temp=self.scene_now_temp,
            beats_count=self.scene_now_beats_count
        )
        self.bind(
            scene_now_temp=scene_now_bc.setter("temp"),
            scene_now_beats_count=scene_now_bc.setter("beats_count")
        )
        scene_now_bc.link()
        self.scene_now_bc = scene_now_bc

    def on_midi_set_global_temp(self, _, channel:int, intensive:int):
        res = None
        if channel == 126:
            intensive = int(max(0, intensive))
            cache_channel_126 = intensive
            cache_channel_126 = cache_channel_126 if cache_channel_126 < 100 else 100
            self.cache_channel_126 = cache_channel_126
            cache_channel_127 = self.cache_channel_127
            res = cache_channel_126 + cache_channel_127 if cache_channel_126 + cache_channel_127 > 0 else 1
        if channel == 127:
            intensive = int(max(0, intensive))
            cache_channel_127 = intensive
            cache_channel_126 = self.cache_channel_126
            self.cache_channel_127 = cache_channel_127
            res = cache_channel_126 + cache_channel_127 if cache_channel_126 + cache_channel_127 > 0 else 1
        def set_temp(_):
            self.scene_now_temp = int(res)
        if res:
            Clock.schedule_once(set_temp, -1)

    def change_scene(self, new_scene: RowScene):
        old_scene = self.scene_now
        if old_scene is new_scene:
            return
        self.scene_now = new_scene
        self.dispatch("on_scene_change", old_scene, new_scene)

    def _create_default(self):
        self.scene_now = self.add_row()

    def get_scene_now_temp(self) -> float:
        return self.scene_now.temp

    def set_scene_now_temp(self, temp: float):
        if self.scene_now.temp != temp:
            self.scene_now.edit(temp=temp)
        return True
    scene_now_temp = AliasProperty(
        lambda self: self.scene_now.temp, set_scene_now_temp,
        bind=["scene_now"]
    )

    def set_scene_now_dimmer(self, dimmer: float):
        if self.scene_now.dimmer != dimmer:
            self.scene_now.edit(dimmer=dimmer)
        return True
    scene_now_dimmer = AliasProperty(
        lambda self: self.scene_now.dimmer, set_scene_now_dimmer,
        bind=["scene_now"]
    )

    def set_scene_now_beats_count(self, beats_count: float):
        if self.scene_now.beats_count != beats_count:
            self.scene_now.edit(beats_count=beats_count)
        return True
    scene_now_beats_count = AliasProperty(
        lambda self: self.scene_now.beats_count, set_scene_now_beats_count,
        bind=["scene_now"]
    )

    def on_scene_change(self, old_scene: RowScene, new_scene: RowScene):
        for table_name in self.SCENE_TABLES_ORDER:
            self.database[table_name].sync_scene_change(old_scene, new_scene)


class SceneTableMixin:
    """Таблица, данные которой хранятся отдельным файлом на каждую сцену.
    Наследник может переопределить on_scene_change для пост-обработки
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_event_type("on_scene_change")

    def sync_scene_change(self, old_scene: RowScene, new_scene: RowScene):
        self._save()
        self.filepath = self._make_filepath()
        for row in self.rows.values():
            row.unload()
        self._load()
        self.dispatch("on_scene_change", old_scene, new_scene)

    def on_scene_change(self, old_scene: RowScene, new_scene: RowScene):
        pass

    def _make_filepath(self) -> Path:
        scene_id = self.database.scene.scene_now._id
        table_dir = constants.DATABASE_PATH / self.name
        table_dir.mkdir(parents=True, exist_ok=True)
        return table_dir / f"{scene_id}.json"


class SceneRowMixin:
    """Строка сценозависимой таблицы. При выгрузке сцены снимает бинды.
    Требует дополнительного наследования от AutoUnbindBehavior.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_event_type("on_unload")

    def unload(self):
        self.dispatch("on_unload")

    def on_unload(self):
        self.unbind_all()
        detach_event_dispatcher(self, self.properties())
