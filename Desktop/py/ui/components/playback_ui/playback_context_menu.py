from typing import Any, List

from kivy.lang import Builder
from kivy.properties import AliasProperty, ListProperty

import libs.uix.menu_components  # lazy kv import initialize
from database.playback.playback import RowPlayback
from libs.uix.layouts import ModalBoxLayout

Builder.load_file("ui/components/playback_ui/playback_context_menu.kv")


class PlaybackContextMenu(ModalBoxLayout):
    playback_list: List[RowPlayback] = ListProperty()
    first_playback: RowPlayback = AliasProperty(
        lambda self: self.playback_list[0],
        bind=("playback_list",)
    )

    def edit_playbacks_title(self, title: str):
        for i, playback in enumerate(self.playback_list):
            if len(self.playback_list) == 1:
                playback.edit(title=title)
            else:
                playback.edit(title=f"{title} #{i + 1}")

    def edit_playbacks(self, **kwargs: Any):
        for playback in self.playback_list:
            playback.edit(**kwargs)

    def edit_playbacks_player(self, **kwargs: Any):
        for playback in self.playback_list:
            playback.player.edit(**kwargs)

    def edit_playbacks_renderer(self, **kwargs: Any):
        for playback in self.playback_list:
            playback.renderer.edit(**kwargs)
