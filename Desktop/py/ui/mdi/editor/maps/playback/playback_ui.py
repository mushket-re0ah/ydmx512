from typing import Any, Optional

from kivy.clock import Clock
from kivy.graphics import Color, SmoothEllipse
from kivy.properties import BooleanProperty, NumericProperty

from misc import colorscheme as cs
from ui.components.playback_ui import BasePlaybackUi
from ui.mdi.editor.maps.map_layout import EditorMapLayout


class EditorPlaybackUi(BasePlaybackUi):
    is_limiters: bool = BooleanProperty(False)
    edit_label_size: float = NumericProperty("20dp")
    edit_label_x: float = NumericProperty("76dp")
    edit_label_y: float = NumericProperty("76dp")

    map_layout: Optional[EditorMapLayout]
    def __init__(self, **kwargs: Any):
        playback = kwargs["playback"]
        playback.bind(grid_pos=self.setter("grid_pos"))
        super().__init__(**kwargs)

    def on_map_layout(self, _, map_layout: Optional[EditorMapLayout]):
        if map_layout is None:
            return
        select_edited_playback_ev = Clock.create_trigger(self.on_select_edited_playback, -1)
        self.select_edited_playback_ev = select_edited_playback_ev
        map_layout.bind(playback=select_edited_playback_ev)
        self.bind(
            edit_label_size=select_edited_playback_ev,
            pos=select_edited_playback_ev,
            size=select_edited_playback_ev,
        )

    def on_select_edited_playback(self, _:Any):
        self.canvas.remove_group("selected_edit")
        if self.map_layout is None:
            raise RuntimeError()
        if self.playback is self.map_layout.playback:
            with self.canvas:
                Color(*cs.EditorPlaybackUi.selected_edit_color)
                SmoothEllipse(
                    size=(self.edit_label_size, self.edit_label_size),
                    pos=(self.edit_label_x, self.edit_label_y),
                    group="selected_edit"
                )

    def on_release_play_button(self):
        if self.map_layout is None:
            raise RuntimeError()
        self.map_layout.playback = self.playback
