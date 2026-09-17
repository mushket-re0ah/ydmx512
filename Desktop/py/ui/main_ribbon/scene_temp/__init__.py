from kivy.properties import NumericProperty, ColorProperty
from kivy.clock import Clock
from ui.components.button import ImageButton
from database import db
from collections import deque
import time
from misc import colorscheme as cs
from misc import constants
from libs.uix.label import RestrictedLabel
from kivy.graphics import Color, Line


class BeatLabel(RestrictedLabel):
    _led_color = ColorProperty(cs.BeatLabel.default_bg)
    _fg_color = ColorProperty(cs.BeatLabel.default_fg)
    _progressbar_width = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.trigger_beat = Clock.create_trigger(self.on_beat, -1)
        self.trigger_downbeat = Clock.create_trigger(self.on_downbeat, -1)
        self.trigger_halfbeat = Clock.create_trigger(self.on_halfbeat, -1)
        self.trigger_frame = Clock.create_trigger(self.on_frame, -1)
        db.scene.scene_now_bc.bind(
            beat_now=self.trigger_beat,
            on_halfbeat=self.trigger_halfbeat,
            on_downbeat=self.trigger_downbeat,
            frame_now=self.trigger_frame
        )

    def on_frame(self, _):
        # return
        scene_bc = db.scene.scene_now_bc
        progress = scene_bc._frame_now / (constants.FRAMES_IN_BEAT * scene_bc.beats_count)
        self._progressbar_width = self.width * progress

    def on_beat(self, _):
        if db.scene.scene_now_bc.beat_now == 0:
            self.on_downbeat()
        else:
            self._led_color = cs.BeatLabel.default_bg
        self._fg_color = cs.BeatLabel.default_fg

    def on_halfbeat(self, _):
        self._led_color = cs.BeatLabel.halfbeat_bg

    def on_downbeat(self, _=None):
        self._led_color = cs.BeatLabel.upbeat_bg


class ButtonTapSceneTemp(ImageButton):
    max_tap_count = NumericProperty(4)
    timeout = NumericProperty(1)
    clicks_count_for_calc = NumericProperty(2)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._click_list = deque(maxlen=self.max_tap_count)

    def _check_if_clear_list(self):
        """
                Если последнее нажатие было произведено более секунды назад,
        то список нажатий очищается.
        """
        click_list = self._click_list
        if click_list:
            diff = time.perf_counter() - click_list[-1]
            if diff >= self.timeout:
                click_list.clear()

    def on_release(self):
        self._check_if_clear_list()
        self._click_list.append(time.perf_counter())
        self._calc_temp()

    def _calc_temp(self):
        click_list = self._click_list
        if len(click_list) >= self.clicks_count_for_calc:
            # Время, закоторое были произведены последние 4 нажатия
            time_diff = click_list[-1] - click_list[0]

            # Beat Per Second (BPS) количество нажатий в секунду
            bps = (len(click_list) - 1) / time_diff

            db.scene.scene_now_temp = int(60 * bps)
