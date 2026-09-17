from kivy.properties import ObjectProperty, ListProperty, NumericProperty, AliasProperty
from libs.uix.layouts import ModalBoxLayout
from kivy.clock import Clock
from kivy.utils import boundary
import ui.mdi.editor.automation.toolbar
import ui.mdi.editor.automation.rows
from libs.uix.layouts import MenuPanel
from database.patch import RowPatch
from database.playback import RowPlayback
from database.playback.player import PlaybackPlayer
from typing import List, Tuple, NamedTuple, Optional, Type
from libs.beat_counter import BeatCounter
from misc import constants
from libs.kivy_utils import AutoUnbindBehavior
from kivy.core.text import Label as CoreLabel
from kivy.lang import Builder
from misc import colorscheme as cs
from kivy.graphics import *
from ui.mdi.editor.automation.tools import EditorTool


class AutomationXWidth(NamedTuple):
    x: float
    width: float


Builder.load_file("ui/mdi/editor/automation/automation.kv")


class HeaderCursorFrameWidget(ModalBoxLayout):
    automation = ObjectProperty()
    frame = NumericProperty()
    opacity_animation_duration = NumericProperty(0.0)
    PADDING_LEFT = NumericProperty("20dp")

    def on_frame(self, _, frame: int):
        x = self.automation.xwidth.x
        quant_width = self.automation.quant_width
        self.pos_fix = (x + self.PADDING_LEFT + frame * quant_width, self.automation.toolbar.y)
        self._trigger_reposition()


class Automation(AutoUnbindBehavior, MenuPanel):
    row_panel = ObjectProperty(rebind=True)
    toolbar = ObjectProperty(rebind=True)

    _playback = ObjectProperty(None, allownone=True, rebind=True)
    renderer = AliasProperty(lambda self: self.playback.renderer if self.playback else None, bind=["playback"], cache=True)
    xy_grid = AliasProperty(lambda self: self.renderer.xy_grid if self.playback else None, bind=["playback"], cache=True)
    active_patch: List[RowPatch] = ListProperty([])
    row_count_view = NumericProperty(8)

    player_frame = NumericProperty(None, allownone=True)
    cursor_frame = NumericProperty(0)

    scrollbar_vertical = ObjectProperty(allownone=True)

    LEFT_SECTION_ROW_WIDTH = NumericProperty("178dp")

    header_beat_line_points = ListProperty(rebind=True)
    header_halfbeat_line_points = ListProperty(rebind=True)
    HEADER_HEIGHT = NumericProperty("25dp")
    HEADER_MINIMUM_WIDTH_TO_DRAW = NumericProperty("35dp")
    HEADER_LABEL_PADDING_X = NumericProperty("6dp")
    HEADER_LABEL_PADDING_Y = NumericProperty("2dp")
    HEADER_LINE_WIDTH = NumericProperty(1)
    HEADER_BEAT_HEIGHT = NumericProperty("8dp")
    HEADER_HALFBEAT_HEIGHT = NumericProperty("4dp")

    TACT_BOX_PADDING_X = NumericProperty("5dp")
    TACT_BOX_PADDING_Y = NumericProperty("10dp")
    _editor_tool = ObjectProperty(None, allownone=True)

    calc_header_beats_ev = None
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.calc_header_beats_ev = Clock.create_trigger(self.calc_header_beats, 0)
        self.bind(
            beats_x_pos=self.calc_header_beats_ev,
            toolbar=self.calc_header_beats_ev,
            pos=self.calc_header_beats_ev,
            size=self.calc_header_beats_ev,
        )

    def on_kv_post(self, _):
        self.row_panel.bind(scrollbar_vertical=self.setter("scrollbar_vertical"))
        self.scrollbar_vertical = self.row_panel.scrollbar_vertical

    def set_tool(self, tool_cls: Optional[EditorTool], *args, **kwargs) -> Optional[EditorTool]:
        if not self.playback:
            if self._editor_tool:
                self._editor_tool = None

            return None
        old_tool = self._editor_tool
        new_tool = None

        old_requires = old_tool.requires_session if old_tool else False
        new_requires = tool_cls.requires_session if tool_cls else False

        if not old_requires and new_requires:
            # Переход от несессионного к сессионному — открываем сессию
            if not self.playback.renderer.is_session_opened():
                self.playback.renderer.start_session()
        elif old_requires and not new_requires:
            # Переход от сессионного к несессионному — закрываем сессию
            if self.playback.renderer.is_session_opened():
                self.playback.renderer.end_session()

        tool = tool_cls(self, *args, **kwargs) if tool_cls else None
        self._editor_tool = tool
        if tool and tool.auto_execute:
            self.tool_action("execute")
            return None
        return tool

    def tool_action(self, action: str, *args, **kwargs) -> bool:
        if not self._editor_tool:
            return False
        if not hasattr(self._editor_tool, action):
            raise Exception(f"Инструмент {self._editor_tool} не имеет действия \"{action}\"")
        getattr(self._editor_tool, action)(*args, **kwargs)
        return True

    def check_tool(self, tool_cls: Optional[Type[EditorTool]]) -> bool:
        if tool_cls is None:
            return self._editor_tool is None
        return isinstance(self._editor_tool, tool_cls)

    def set_playback(self, playback: RowPlayback):
        self.player_frame = None
        self.cursor_frame = 0
        if self._playback:
            self._unbind_beat_counter()
            self.unbind_from(self._playback.player)
            if self.playback.renderer.is_session_opened():
                self.playback.renderer.end_session()
        self._playback = playback
        if playback:
            player = playback.player
            self.bind_to(player,
                         real_beats_count=self._update_xwidth,
                         on_start=self._on_player_start,
                         on_stop=self._on_player_stop)
            if player.play:
                self._bind_beat_counter(player.beat_counter)
        return True
    playback = AliasProperty(lambda self: self._playback, set_playback, rebind=True)

    binded_beat_counter = None
    def _bind_beat_counter(self, beat_counter):
        if self.binded_beat_counter:
            self._unbind_beat_counter()
        self.binded_beat_counter = beat_counter
        if beat_counter:
            self.bind_to(beat_counter, frame_now=self.setter("player_frame"))

    def _unbind_beat_counter(self):
        if self.binded_beat_counter:
            self.unbind_from(self.binded_beat_counter)
            self.binded_beat_counter = None

    def _on_player_start(self, player: PlaybackPlayer, beat_counter: BeatCounter):
        self._bind_beat_counter(beat_counter)
        from misc import logger
        logger.debug("_on_player_start")

    def _on_player_stop(self, player: PlaybackPlayer, beat_counter: BeatCounter):
        self._unbind_beat_counter()
        self.player_frame = None
        from misc import logger
        logger.debug("_on_player_stop")

    def _update_xwidth(self, *args):
        self.property("xwidth").dispatch(self)

    cursor_frame_widget = ObjectProperty(allownone=True)
    def on_touch_down(self, touch):
        if self.playback is None:
            return super().on_touch_down(touch)
        x, width = self.xwidth
        right = x + width
        if x <= touch.x <= right and self.y <= touch.y <= self.toolbar.y:
            cf_w = HeaderCursorFrameWidget(automation=self)
            cf_w.bind_to(self, cursor_frame=cf_w.setter("frame"))
            cf_w.open(self)
            self.cursor_frame_widget = cf_w
            self.cursor_frame = int((touch.x - x) / self.quant_width)
            self.property("cursor_frame").dispatch(self)
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.cursor_frame_widget:
            self.cursor_frame_widget.unbind_from(self)
            self.cursor_frame_widget.dismiss()
            self.cursor_frame_widget = None
        return super().on_touch_up(touch)

    def on_touch_move(self, touch):
        if self.playback is None:
            return super().on_touch_move(touch)
        if self.cursor_frame_widget:
            cursor_frame = int((touch.x - self.xwidth.x) / self.quant_width)
            self.cursor_frame = boundary(cursor_frame, 0, self.xy_grid.last_x_frame)
        return super().on_touch_move(touch)

    def get_xwidth(self) -> AutomationXWidth:
        scrollbar = self.scrollbar_vertical
        padding_left = self.LEFT_SECTION_ROW_WIDTH
        padding_right = scrollbar.width if scrollbar else 0
        width = self.width - padding_left - padding_right
        padding_x = self.TACT_BOX_PADDING_X
        width -= padding_x * 2
        x = self.x + padding_left + padding_x
        return AutomationXWidth(x, width)
    xwidth = AliasProperty(
        get_xwidth,
        bind=["x", "width", "LEFT_SECTION_ROW_WIDTH", "scrollbar_vertical"],
        cache=True, rebind=True
    )

    def get_quant_width(self) -> float:
        if not self.playback:
            return 0
        return self.xwidth.width / self.xy_grid.last_x_frame
    quant_width = AliasProperty(
        get_quant_width,
        bind=["xwidth", "playback", "xy_grid"],
        cache=True
    )

    def calc_line_x(self, frame: int) -> int:
        if self.playback is None or frame is None or self.xwidth.width <= 0:
            return 0
        return self.xwidth.x + frame * self.quant_width

    player_line_x = AliasProperty(
        lambda self: self.calc_line_x(self.player_frame),
        bind=["playback", "xwidth", "quant_width", "player_frame"],
        cache=True
    )
    cursor_line_x = AliasProperty(
        lambda self: self.calc_line_x(self.cursor_frame),
        bind=["playback", "xwidth", "quant_width", "cursor_frame"],
        cache=True
    )

    def get_beats_x_pos(self) -> List[Tuple[float, float]]:
        if not self.playback:
            return []
        x = self.xwidth.x
        step_x = self.quant_width * constants.FRAMES_IN_HALFBEAT
        return [(x + step_x * i, x + step_x * (i +  1)) for i in range(0, self.playback.player.real_beats_count * 2, 2)]
    beats_x_pos = AliasProperty(
        get_beats_x_pos,
        bind=["xwidth", "quant_width"],
        cache=True
    )

    def calc_header_beats(self, _):
        self.canvas.after.remove_group("label")
        self.header_beat_line_points = []
        self.header_halfbeat_line_points = []
        if not self.playback:
            return
        if self.xwidth.width <= self.HEADER_MINIMUM_WIDTH_TO_DRAW:
            return
        y = self.toolbar.y - self.HEADER_HEIGHT
        beat_line_points = []
        halfbeat_line_points = []
        with self.canvas.after:
            Color(1, 1, 1, 1)
            for i, beat_pos in enumerate(self.beats_x_pos):
                x_beat, x_halfbeat = beat_pos
                label = self.create_corelabel(str(i + 1))
                Rectangle(
                    size=label.texture.size,
                    pos=(x_beat + self.HEADER_LABEL_PADDING_X, y + self.HEADER_LABEL_PADDING_Y),
                    texture=label.texture,
                    group="label"
                )
                beat_line_points.extend([x_beat, y, x_beat, y + self.HEADER_BEAT_HEIGHT, float("nan"), float("nan")])
                halfbeat_line_points.extend([x_halfbeat, y, x_halfbeat, y + self.HEADER_HALFBEAT_HEIGHT, float("nan"), float("nan")])
        self.header_beat_line_points = beat_line_points
        self.header_halfbeat_line_points = halfbeat_line_points

    label_cache = {}
    LABEL_FONT_SIZE = NumericProperty("14sp")
    def on_LABEL_FONT_SIZE(self, *args):
        self.label_cache.clear()
        self.calc_header_beats_ev()

    def create_corelabel(self, text: str) -> CoreLabel:
        if text not in self.label_cache:
            label = CoreLabel(text=text,
                              font_size=self.LABEL_FONT_SIZE,
                              color=cs.Label.fg)
            self.label_cache[text] = label
            label.refresh()
        return self.label_cache.get(text, None)
