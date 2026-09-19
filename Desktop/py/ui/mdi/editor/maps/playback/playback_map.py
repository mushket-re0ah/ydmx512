from kivy.properties import ObjectProperty
from kivy.lang import Builder
from libs.uix.layouts import MenuPanel
from database import db
from database.playback import RowPlayback
from database.scene import RowScene
from ui.mdi.editor.maps.playback.playback_ui import EditorPlaybackUi
from operator import attrgetter
from libs.uix.context_menu import (
    ContextMenu, ContextMenuTemplates
)


Builder.load_file("ui/mdi/editor/maps/playback/playback_map.kv")


class PlaybackEditorMap(MenuPanel):
    editor = ObjectProperty()
    pb_map = ObjectProperty()

    playback = ObjectProperty(None, allownone=True, rebind=True)

    def on_kv_post(self, _):
        self.pb_map.box._create_context_menu = self._create_context_menu
        self.pb_map.box.child_grid_pos_attrgetter = attrgetter("playback.grid_pos")
        self.__init_map()
        db.playback.bind(on_add_row=self.on_add_playback)
        db.playback.bind(on_remove_row=self.on_remove_playback)
        db.playback.bind(on_scene_change=self.on_scene_change)

    def on_add_playback(self, _, playback: RowPlayback):
        self.pb_map.add_widget(EditorPlaybackUi(
                playback_section=self,
                playback_map=self.pb_map,
                playback=playback
            )
        )

    def on_remove_playback(self, _, playback: RowPlayback):
        playback_ui = next((i for i in self.pb_map.box.children
                                    if i.playback is playback), None)
        if playback_ui is not None:
            playback_ui._self_destroy()

    def on_scene_change(self, table, old_scene: RowScene, new_scene: RowScene):
        self.__init_map()

    def __init_map(self):
        self.pb_map.box.clear_widgets()
        for playback in db.playback.rows.values():
            self.pb_map.add_widget(EditorPlaybackUi(
                    create_animation=False,
                    playback_section=self,
                    playback_map=self.pb_map,
                    playback=playback
                )
            )

    def _create_context_menu(self) -> ContextMenu:
        return ContextMenu(items=[
            ContextMenuTemplates.button(
                text="Создать плейбек",
                on_release=lambda _: db.playback.add_row(),
            ),
            ]
        )
