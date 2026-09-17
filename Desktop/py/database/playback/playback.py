from kivy.properties import (
    StringProperty, NumericProperty, ObjectProperty, ColorProperty
)
from kivy.utils import get_hex_from_color
from misc import constants
from libs.kivy_json_orm.table_implementation import DatabaseTable, DatabaseRow
from database.scene import RowScene, TableScene, SceneTableMixin, SceneRowMixin
from typing import Tuple
from database.playback.player import PlaybackPlayer
from database.playback.renderer import PlaybackRenderer
from libs.serialize import *
from libs.kivy_json_orm.fields import *


class RowPlayback(SceneRowMixin, DatabaseRow):
    title = StringField("Без названия")
    grid_pos = ListField([None, None])
    color = ColorField((1, 1, 1, 1))
    player = NestedField(PlaybackPlayer, default_factory=PlaybackPlayer, rebind=True)
    renderer = NestedField(PlaybackRenderer, default_factory=PlaybackRenderer, rebind=True)

    def on_player(self, _, player: PlaybackPlayer):
        player.parent_row = self

    def on_renderer(self, _, renderer: PlaybackRenderer):
        renderer.playback = self


class TablePlayback(SceneTableMixin, DatabaseTable):
    cls_row = RowPlayback
