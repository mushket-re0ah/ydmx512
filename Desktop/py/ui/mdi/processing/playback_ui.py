from typing import Any

from misc.player.status import PlayerStatus
from ui.components.playback_ui import BasePlaybackUi


class PlaybackUiProcessing(BasePlaybackUi):
    def __init__(self, **kwargs: Any):
        self.bind(grid_pos=self._save_pos)
        super().__init__(selectable=True, **kwargs)

    def on_release_play_button(self):
        self.playback.player.start_or_stop()

    def on_press_play_button(self):
        player = self.playback.player
        if not player.is_moment:
            return
        if player.status is not PlayerStatus.WORK:
            player.start()
