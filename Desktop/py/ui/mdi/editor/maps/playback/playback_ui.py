from kivy.properties import BooleanProperty, ObjectProperty, NumericProperty
from kivy.clock import Clock
from ui.components.playback_ui import BasePlaybackUi
from kivy.graphics import *
from misc import colorscheme as cs


class EditorPlaybackUi(BasePlaybackUi):
    playback_section = ObjectProperty()
    is_limiters = BooleanProperty(False)
    edit_label_size = NumericProperty("20dp")
    edit_label_x = NumericProperty("76dp")
    edit_label_y = NumericProperty("76dp")

    def __init__(self, create_animation=True, **kwargs):
        playback = kwargs["playback"]
        playback_map = kwargs["playback_map"]
        playback.bind(grid_pos=playback_map.box._trigger_calc_resize)
        super().__init__(create_animation, **kwargs)

    select_edited_playback_ev = None
    def on_playback_section(self, _, playback_section):
        select_edited_playback_ev = Clock.create_trigger(self.on_select_edited_playback, -1)
        self.select_edited_playback_ev = select_edited_playback_ev
        playback_section.bind(playback=select_edited_playback_ev)
        self.bind(
            edit_label_size=select_edited_playback_ev,
            pos=select_edited_playback_ev,
            size=select_edited_playback_ev,
        )

    def on_select_edited_playback(self, _):
        self.canvas.remove_group("selected_edit")
        if self.playback is self.playback_section.playback:
            with self.canvas:
                Color(*cs.EditorPlaybackUi.selected_edit_color)
                SmoothEllipse(
                    size=(self.edit_label_size, self.edit_label_size),
                    pos=(self.edit_label_x, self.edit_label_y),
                    group="selected_edit"
                )

    def on_release_play_button(self):
        self.playback_section.playback = self.playback
