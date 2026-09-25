from kivy.uix.relativelayout import RelativeLayout
from kivy.lang.builder import Builder
from kivy.properties import (
    ObjectProperty, ColorProperty, NumericProperty, StringProperty
)
from kivy.animation import Animation
from libs.uix.map_layout import MapGridItemBehavior, MapLayout
from libs.uix.button import ImageButton
from database.playback import RowPlayback, PlaybackPlayer
from typing import Tuple
from misc import colorscheme as cs
from libs.animation import StatefulColorProperty
from misc.player.status import PlayerStatus


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


class BasePlaybackUi(MapGridItemBehavior, RelativeLayout):
    lbl_cur_beat = ObjectProperty()
    play_button = ObjectProperty()
    input_title = ObjectProperty()
    input_hotkey = ObjectProperty()
    input_midi = ObjectProperty()
    rotary_intensive = ObjectProperty()

    playback: RowPlayback = ObjectProperty(rebind=True)
    playback_map: MapLayout = ObjectProperty()
    bg = ColorProperty(cs.PlaybackUi.bg_stop_normal)
    opacity = NumericProperty(1)

    def __init__(self, create_animation=True, **kwargs):
        super().__init__(**kwargs)
        self._do_create_animation(create_animation)

    def on_kv_post(self, _):
        super().on_kv_post(_)
        playback = self.playback
        playback_map = self.playback_map
        self.grid_pos = self._get_init_attrs(playback, playback_map)
        if playback.grid_pos[0] is None:
            self._save_pos(None)
        playback.player.bind(status=self.on_player_status)
        self.on_player_status(playback.player, playback.player.status)

    def on_player_status(self, _, status: PlayerStatus):
        self.animation = Animation(bg=status.value.bg, duration=0.2).start(self)

    def _do_create_animation(self, create_animation: bool):
        if create_animation:
            self.opacity = 0
            self.animation = Animation(opacity=1, duration=0.2).start(self)

    def _get_init_attrs(self,
                        playback: RowPlayback,
                        playback_map: MapLayout) -> Tuple[int, int]:
        if playback.grid_pos[0] is None:
            return playback_map.find_empty_pos(*self.grid_size)
        else:
            return playback.grid_pos

    def _self_destroy(self):
        self.disabled = True
        anim = Animation(opacity=0, bg=cs.PlaybackUi.bg_delete, duration=0.2)
        anim.bind(on_complete=self.on_self_destroy)
        anim.start(self)

    def on_self_destroy(self, *args):
        self.parent.map_layout.remove_widget(self)

    def _save_pos(self, _):
        self.playback.edit(grid_pos=self.grid_pos)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        if super().on_touch_down(touch):
            return True
        if touch.button == "right":
            self._open_context_menu(touch.pos)
            return True
        return False

    def _open_context_menu(self, pos: Tuple[float, float]):
        from ui.components.playback_ui.playback_context_menu import PlaybackContextMenu
        PlaybackContextMenu(
            playback_list=[self.playback]
        ).open(self)

    def on_release_play_button(self):
        pass

    def on_press_play_button(self):
        pass
