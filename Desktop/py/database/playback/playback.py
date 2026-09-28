from database.scene import SceneTableMixin, SceneRowMixin
from database.playback.player import PlaybackPlayer
from database.playback.renderer import PlaybackRenderer
from libs.kivy_json_orm.table_implementation import DatabaseTable, DatabaseRow
from libs.kivy_json_orm.fields import StringField, ListField, ColorField, NestedField


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
