from kivy.clock import Clock
from ui.components.playback_ui import BasePlaybackUi
from ui.components.scroll_layout_map import SelectableBehavior
from misc.player.status import PlayerStatus


class PlaybackUiProcessing(SelectableBehavior, BasePlaybackUi):
    trigger_save_pos = None
    def __init__(self, create_animation=True, **kwargs):
        self.trigger_save_pos = Clock.create_trigger(self._save_pos, 0)
        self.bind(
            grid_x=self.trigger_save_pos,
            grid_y=self.trigger_save_pos,
        )
        super().__init__(**kwargs)

    def on_self_destroy(self, *args):
        self.unselect()
        self.parent.remove_widget(self)

    def _save_pos(self, _):
        self.playback.edit(grid_pos=[self.grid_x, self.grid_y])

    def on_release_play_button(self):
        self.playback.player.start_or_stop()

    def on_press_play_button(self):
        player = self.playback.player
        if not player.is_moment:
            return
        if player.status is not PlayerStatus.WORK:
            player.start()
