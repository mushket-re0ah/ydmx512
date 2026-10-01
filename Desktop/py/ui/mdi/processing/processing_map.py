from typing import TYPE_CHECKING, Any, Dict, Set, Tuple

from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.widget import Widget

from database import db
from database.playback import RowPlayback
from database.playback.playback import TablePlayback
from database.playback.player import PlaybackPlayer
from database.scene import RowScene, TableScene
from libs.uix.context_menu import ContextMenu, ContextMenuTemplates
from libs.uix.layouts import SectionPanel
from libs.uix.map_layout import MapLayout
from ui.mdi.processing.playback_ui import PlaybackUiProcessing

if TYPE_CHECKING:
    from ui.mdi.processing import MDIProcessing

Builder.load_file("ui/mdi/processing/processing_map.kv")


class PlaybackMapSection(SectionPanel):
    processing: "MDIProcessing" = ObjectProperty()
    pb_map: "PlaybackMap" = ObjectProperty()
    view_context: Dict[str, Any] = ObjectProperty()


class PlaybackMap(MapLayout):
    grid_items: Tuple[PlaybackUiProcessing, ...]
    selected: Tuple[PlaybackUiProcessing, ...]

    def _get_player_list_by_hotkey(self, key: str) -> Tuple[PlaybackPlayer, ...]:
        return tuple(ui.playback.player for ui in self.grid_items
                    if ui.playback.player.hotkey == key)

    key_down: Set[str] = set()
    def on_key_down(self, key: str):
        if key in self.key_down:
            return
        self.key_down.add(key)
        for player in self._get_player_list_by_hotkey(key):
            player.start_or_stop()

    def on_key_up(self, key: str):
        if key in self.key_down:
            self.key_down.remove(key)
        for player in self._get_player_list_by_hotkey(key):
            if player.is_moment:
                player.stop()

    def on_kv_post(self, base_widget: Widget):
        super().on_kv_post(base_widget)
        self.__init_map()
        db.playback.bind(on_add_row=self.on_add_playback)
        db.playback.bind(on_remove_row=self.on_remove_playback)
        db.playback.bind(on_scene_change=self.on_scene_change)

    def on_add_playback(self, _: TablePlayback, playback: RowPlayback):
        self.add_widget(PlaybackUiProcessing(
                map_layout=self,
                playback=playback
            )
        )

    def on_remove_playback(self, _: TablePlayback, playback: RowPlayback):
        playback_ui = next((i for i in self.grid_items if i.playback is playback), None)
        if playback_ui is not None:
            playback_ui._self_destroy()

    def on_scene_change(self, table: TableScene, _old_scene: RowScene, _new_scene: RowScene):
        self.__init_map()

    def __init_map(self):
        self.clear_widgets()
        for playback in db.playback.rows.values():
            self.add_widget(PlaybackUiProcessing(
                    create_animation=False,
                    map_layout=self,
                    playback=playback
                )
            )

    def start_all(self, *_: Any):
        for ui in self.grid_items:
            ui.playback.player.start()

    def stop_all(self, *_: Any):
        for ui in self.grid_items:
            ui.playback.player.stop()

    def start_selected(self, *_: Any):
        for ui in self.selected:
            ui.playback.player.start()

    def stop_selected(self, *_: Any):
        for ui in self.selected:
            ui.playback.player.stop()

    def delete_selected(self, *_: Any):
        for ui in self.selected:
            db.playback.remove_row(ui.playback)

    def edit_selected(self, *_: Any):
        from ui.components.playback_ui.playback_context_menu import PlaybackContextMenu
        PlaybackContextMenu(
            playback_list=[ui.playback for ui in self.selected]
        ).open(self)

    def _create_context_menu(self) -> ContextMenu:
        return ContextMenu(items=[
            ContextMenuTemplates.button(
                text="Создать плейбек",
                on_release=lambda _: db.playback.add_row(),
            ),
            ContextMenuTemplates.button(
                text="Старт все",
                on_release=self.start_all,
            ),
            ContextMenuTemplates.button(
                text="Стоп все",
                on_release=self.stop_all,
            ),
            ContextMenuTemplates.button(
                text="Старт выделенные",
                on_release=self.start_selected,
            ),
            ContextMenuTemplates.button(
                text="Стоп выделенные",
                on_release=self.stop_selected,
            ),
            ContextMenuTemplates.button(
                text="Удалить выделенные",
                on_release=self.delete_selected,
            ),
            ContextMenuTemplates.button(
                text="Редактировать выделенные",
                on_release=self.edit_selected,
            ),
            ]
        )
