from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Tuple

from database.playback.player import PlaybackPlayer
from database.playback.renderer import PlaybackRenderer
from database.scene import SceneRowMixin, SceneTableMixin
from libs.kivy_json_orm.fields import ColorField, ListField, NestedField, StringField
from libs.kivy_json_orm.table_implementation import DatabaseRow, DatabaseTable
from libs.typecheck import RGBA

if TYPE_CHECKING:
    from database import YdmxDatabase


class RowPlayback(SceneRowMixin, DatabaseRow):
    database: "YdmxDatabase"  # pyright: ignore[reportIncompatibleMethodOverride]
    table: "TablePlayback" # pyright: ignore[reportIncompatibleVariableOverride]

    title: str = StringField("Без названия")
    grid_pos: Tuple[int, int] = ListField([None, None])
    color: RGBA = ColorField((1, 1, 1, 1))
    player: PlaybackPlayer = NestedField(
        PlaybackPlayer,
        default_factory=PlaybackPlayer,
        rebind=True
    )
    renderer: PlaybackRenderer = NestedField(
        PlaybackRenderer,
        default_factory=PlaybackRenderer,
        rebind=True
    )

    def on_player(self, _, player: PlaybackPlayer):
        player.parent_row = self

    def on_renderer(self, _, renderer: PlaybackRenderer):
        renderer.playback = self


class TablePlayback(SceneTableMixin, DatabaseTable):
    database: "YdmxDatabase" # pyright: ignore[reportIncompatibleVariableOverride]
    get_row_by_id: Callable[[int], Optional[RowPlayback]] # pyright: ignore[reportIncompatibleMethodOverride]
    rows: Dict[int, RowPlayback] # pyright: ignore[reportIncompatibleVariableOverride]
    get_row_by_attribute: Callable[[str, Any], Optional[RowPlayback]] # pyright: ignore[reportIncompatibleMethodOverride]
    on_add_row: Callable[[RowPlayback], None] # pyright: ignore[reportIncompatibleMethodOverride]
    on_remove_row: Callable[[RowPlayback], None] # pyright: ignore[reportIncompatibleMethodOverride]
    add_row: Callable[..., RowPlayback] # pyright: ignore[reportIncompatibleMethodOverride]
    remove_row: Callable[[RowPlayback], None] # pyright: ignore[reportIncompatibleMethodOverride]
    __getattr__: Callable[[str], Callable[[Any], Optional[RowPlayback]]] # pyright: ignore[reportIncompatibleMethodOverride]

    cls_row = RowPlayback
