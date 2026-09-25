from kivy.properties import ObjectProperty, AliasProperty
from kivy.lang import Builder
from libs.uix.layouts import SectionPanel
from database.scene import RowScene
from typing import List, Tuple
from database import db
from database.playback import RowPlayback
from ui.mdi.processing.playback_ui import PlaybackUiProcessing
from libs.uix.context_menu import ContextMenu, ContextMenuTemplates
from libs.uix.map_layout import MapLayout


Builder.load_file("ui/mdi/processing/processing_map.kv")


class PlaybackMapSection(SectionPanel):
    processing = ObjectProperty()
    pb_map = ObjectProperty()
    view_context = ObjectProperty()


class PlaybackMap(MapLayout):
    def _get_player_list_by_hotkey(self, key: str) -> Tuple[RowPlayback]:
        return (ui.playback.player for ui in self.grid_items
                    if ui.playback.player.hotkey == key)

    key_down = set()
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

    def on_kv_post(self, _):
        super().on_kv_post(_)
        self.__init_map()
        db.playback.bind(on_add_row=self.on_add_playback)
        db.playback.bind(on_remove_row=self.on_remove_playback)
        db.playback.bind(on_scene_change=self.on_scene_change)

    def on_add_playback(self, _, playback: RowPlayback):
        self.add_widget(PlaybackUiProcessing(
                playback_map=self,
                playback=playback
            )
        )

    def on_remove_playback(self, _, playback: RowPlayback):
        playback_ui = next((i for i in self.grid_items if i.playback is playback), None)
        if playback_ui is not None:
            playback_ui._self_destroy()

    def on_scene_change(self, table, old_scene: RowScene, new_scene: RowScene):
        self.__init_map()

    def __init_map(self):
        self.clear_widgets()
        for playback in db.playback.rows.values():
            self.add_widget(PlaybackUiProcessing(
                    create_animation=False,
                    playback_map=self,
                    playback=playback
                )
            )

    def start_all(self, *args):
        for ui in self.grid_items:
            ui.playback.player.start()

    def stop_all(self, *args):
        for ui in self.grid_items:
            ui.playback.player.stop()

    def start_selected(self, *args):
        for ui in self.selected:
            ui.playback.player.start()

    def stop_selected(self, *args):
        for ui in self.selected:
            ui.playback.player.stop()

    def delete_selected(self, *args):
        for ui in self.selected:
            db.playback.remove_row(ui.playback)

    def edit_selected(self, *args):
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
