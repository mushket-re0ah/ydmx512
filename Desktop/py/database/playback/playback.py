from typing import Tuple

from database.playback.player import PlaybackPlayer
from database.playback.renderer import PlaybackRenderer
from database.scene import SceneRowMixin, SceneTableMixin
from libs.kivy_json_orm.fields import ColorField, ListField, NestedField, StringField
from libs.kivy_json_orm.table_implementation import DatabaseRow, DatabaseTable
from libs.typecheck import RGBA


class RowPlayback(SceneRowMixin, DatabaseRow):
    title: str = StringField("Без названия")
    grid_pos: Tuple[int, int] = ListField([None, None])
    color: RGBA = ColorField((1, 1, 1, 1))
    player: PlaybackPlayer = NestedField(PlaybackPlayer, default_factory=PlaybackPlayer, rebind=True)
    renderer: PlaybackRenderer = NestedField(PlaybackRenderer, default_factory=PlaybackRenderer, rebind=True)

    def on_player(self, _, player: PlaybackPlayer):
        player.parent_row = self

    def on_renderer(self, _, renderer: PlaybackRenderer):
        renderer.playback = self


class TablePlayback(SceneTableMixin, DatabaseTable):
    cls_row = RowPlayback
