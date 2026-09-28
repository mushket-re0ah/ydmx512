from kivy.uix.relativelayout import RelativeLayout
from kivy.lang.builder import Builder
from kivy.properties import (
    ObjectProperty, ColorProperty, NumericProperty, StringProperty,
    AliasProperty
)
from kivy.animation import Animation
from libs.uix.map_layout import MapGridItemBehavior, MapLayout
from libs.uix.button import ImageButton
from database.playback import RowPlayback, PlaybackPlayer
from typing import Tuple
from misc import colorscheme as cs
from libs.animation import StatefulColorProperty
from misc.player.status import PlayerStatus
from ui.components.base_database_grid_item import BaseDatabaseGridItem


Builder.load_file("ui/components/playback_ui/playback_ui.kv")


class PlaybackPlayButton(ImageButton):
    playback = ObjectProperty(rebind=True)
    player = ObjectProperty(rebind=True)

    _image = StringProperty()

    background_color = StatefulColorProperty(
        normal=cs.PlaybackPlayButton.background_color_normal,
        states={
            "disabled": cs.PlaybackPlayButton.background_color_disabled,
            ("is_down", "hover"): cs.PlaybackPlayButton.background_color_hover,
            "is_down": cs.PlaybackPlayButton.background_color_down,
            "hover": cs.PlaybackPlayButton.background_color_hover,
        }
    )

    def on_player(self, _, player: PlaybackPlayer):
        player.bind(status=self.set_image)
        self.set_image(player, player.status)

    def set_image(self, _, status: PlayerStatus):
        self._image = status.value.img
        self._trigger_animate()


class BasePlaybackUi(BaseDatabaseGridItem):
    lbl_cur_beat = ObjectProperty()
    play_button = ObjectProperty()
    input_title = ObjectProperty()
    input_hotkey = ObjectProperty()
    input_midi = ObjectProperty()
    rotary_intensive = ObjectProperty()

    def _set_playback(self, playback: RowPlayback) -> bool:
        if self.db_row != playback:
            self.db_row = playback
            return True
        return False
    playback = AliasProperty(
        lambda self: self.db_row, _set_playback, bind=["db_row"]
    )

    def __init__(self, **kwargs):
        super().__init__(bg=cs.PlaybackUi.bg_stop_normal, **kwargs)

    def on_kv_post(self, _):
        super().on_kv_post(_)
        playback = self.playback
        playback.player.bind(status=self.on_player_status)
        self.on_player_status(playback.player, playback.player.status)

    def on_player_status(self, _, status: PlayerStatus):
        self.animation = Animation(bg=status.value.bg, duration=0.2).start(self)

    def _open_context_menu(self, pos: Tuple[float, float]):
        from ui.components.playback_ui.playback_context_menu import PlaybackContextMenu
        PlaybackContextMenu(
            playback_list=[self.playback]
        ).open(self)

    def on_release_play_button(self):
        pass

    def on_press_play_button(self):
        pass
