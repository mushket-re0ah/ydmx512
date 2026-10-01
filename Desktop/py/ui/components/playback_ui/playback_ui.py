from typing import Any, Tuple

from kivy.animation import Animation
from kivy.lang.builder import Builder
from kivy.properties import AliasProperty, ObjectProperty, StringProperty
from kivy.uix.widget import Widget

from database.playback import PlaybackPlayer, RowPlayback
from libs.animation import StatefulColorProperty
from libs.typecheck import RGBA
from libs.uix.button import ImageButton
from libs.uix.input import HotkeyInput, HoverInput, MidiInput
from libs.uix.label import RestrictedLabel
from libs.uix.rotary_button import RotaryButton
from misc import colorscheme as cs
from misc.player.status import PlayerStatus
from ui.components.base_database_grid_item import BaseDatabaseGridItem

Builder.load_file("ui/components/playback_ui/playback_ui.kv")


class PlaybackPlayButton(ImageButton):
    playback: RowPlayback = ObjectProperty(rebind=True)
    player: PlaybackPlayer = ObjectProperty(rebind=True)

    _image: str = StringProperty()

    background_color: RGBA = StatefulColorProperty(
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

    def set_image(self, _: PlaybackPlayer, status: PlayerStatus):
        self._image = status.value.img
        self._trigger_animate()


class BasePlaybackUi(BaseDatabaseGridItem):
    lbl_cur_beat: RestrictedLabel = ObjectProperty()
    play_button: PlaybackPlayButton = ObjectProperty()
    input_title: HoverInput = ObjectProperty()
    input_hotkey: HotkeyInput = ObjectProperty()
    input_midi: MidiInput = ObjectProperty()
    rotary_intensive: RotaryButton = ObjectProperty()

    def _set_playback(self, playback: RowPlayback) -> bool:
        if self.db_row != playback:
            self.db_row = playback
            return True
        return False
    playback: RowPlayback = AliasProperty(
        lambda self: self.db_row,
        _set_playback,
        bind=("db_row",)
    )

    def __init__(self, **kwargs: Any):
        super().__init__(bg=cs.PlaybackUi.bg_stop_normal, **kwargs)

    def on_kv_post(self, base_widget: Widget):
        super().on_kv_post(base_widget)
        playback = self.playback
        playback.player.bind(status=self.on_player_status)
        self.on_player_status(playback.player, playback.player.status)

    def on_player_status(self, _: PlaybackPlayer, status: PlayerStatus):
        self.animation = Animation(bg=status.value.bg, duration=0.2)
        self.animation.start(self)

    def _open_context_menu(self, pos: Tuple[float, float]):
        from ui.components.playback_ui.playback_context_menu import PlaybackContextMenu
        PlaybackContextMenu(
            playback_list=[self.playback]
        ).open(self)

    def on_release_play_button(self):
        pass

    def on_press_play_button(self):
        pass
