from kivy.properties import ObjectProperty
from kivy.lang import Builder
from libs.uix.layouts import MenuPanel
from libs.uix.context_menu import (
    ContextMenu, ContextMenuTemplates
)
from database import db
from database.playback import RowPlayback
from database.scene import RowScene
from misc import constants
from ui.mdi.editor.maps.playback.playback_ui import EditorPlaybackUi
from ui.mdi.editor.maps.map_layout import EditorMapLayout


Builder.load_file("ui/mdi/editor/maps/playback/playback_map.kv")


class PlaybackEditorMapSection(MenuPanel):
    editor = ObjectProperty()
    pb_map = ObjectProperty()
    playback = ObjectProperty(None, allownone=True, rebind=True)


class PlaybackEditorMap(EditorMapLayout):
    playback = ObjectProperty(None, allownone=True, rebind=True)

    def on_kv_post(self, _):
        super().on_kv_post(_)
        self.__init_map()
        db.playback.bind(on_add_row=self.on_add_playback)
        db.playback.bind(on_remove_row=self.on_remove_playback)
        db.playback.bind(on_scene_change=self.on_scene_change)

    def on_add_playback(self, _, playback: RowPlayback):
        self.add_widget(EditorPlaybackUi(
                map_layout=self,
                playback=playback
            )
        )

    def on_remove_playback(self, _, playback: RowPlayback):
        playback_ui = next((i for i in self.grid_items
                                    if i.playback is playback), None)
        if playback_ui is not None:
            playback_ui._self_destroy()

    def on_scene_change(self, _table, _old_scene: RowScene, _new_scene: RowScene):
        self.__init_map()

    def __init_map(self):
        self.clear_widgets()
        for playback in db.playback.rows.values():
            self.add_widget(EditorPlaybackUi(
                    create_animation=False,
                    map_layout=self,
                    playback=playback
                )
            )

    def _ctx_create_playback(self, _):
        db.playback.add_row(grid_pos=self.find_empty_pos(*constants.BASE_PLAYBACK_GRID_SIZE))

    def _create_context_menu(self) -> ContextMenu:
        return ContextMenu(items=[
            ContextMenuTemplates.button(
                text="Создать плейбек",
                on_release=self._ctx_create_playback,
            ),
            ]
        )
