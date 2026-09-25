from kivy.clock import Clock
from ui.components.playback_ui import BasePlaybackUi
from misc.player.status import PlayerStatus


class PlaybackUiProcessing(BasePlaybackUi):
    trigger_save_pos = None
    def __init__(self, create_animation=True, **kwargs):
        self.trigger_save_pos = Clock.create_trigger(self._save_pos, 0)
        self.bind(grid_pos=self.trigger_save_pos)
        super().__init__(selectable=True, **kwargs)

    def on_release_play_button(self):
        self.playback.player.start_or_stop()

    def on_press_play_button(self):
        player = self.playback.player
        if not player.is_moment:
            return
        if player.status is not PlayerStatus.WORK:
            player.start()
