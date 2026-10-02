import time
from collections import deque
from typing import Any, Deque

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ColorProperty, NumericProperty

from database import db
from libs.typecheck import RGBA, Number
from libs.uix.button import ImageButton
from libs.uix.label import RestrictedLabel
from libs.uix.layouts import SectionPanel
from misc import colorscheme as cs
from misc import constants

Builder.load_file("ui/main_ribbon/scene_temp/scene_temp.kv")


class BeatLabel(RestrictedLabel):
    _led_color: RGBA = ColorProperty(cs.BeatLabel.default_bg)
    _fg_color: RGBA = ColorProperty(cs.BeatLabel.default_fg)
    _progressbar_width: Number = NumericProperty(0)

    def __init__(self, **kwargs: Any):
        self.trigger_beat = Clock.create_trigger(self.on_beat, -1)
        self.trigger_downbeat = Clock.create_trigger(self.on_downbeat, -1)
        self.trigger_halfbeat = Clock.create_trigger(self.on_halfbeat, -1)
        self.trigger_frame = Clock.create_trigger(self.on_frame, -1)
        super().__init__(**kwargs)
        db.scene.scene_now_bc.bind(
            beat_now=self.trigger_beat,
            on_halfbeat=self.trigger_halfbeat,
            on_downbeat=self.trigger_downbeat,
            frame_now=self.trigger_frame
        )

    def on_frame(self, dt: float):
        # return
        scene_bc = db.scene.scene_now_bc
        progress = scene_bc.frame_now / (constants.FRAMES_IN_BEAT * scene_bc.beats_count)
        self._progressbar_width = self.width * progress

    def on_beat(self, dt: float):
        if db.scene.scene_now_bc.beat_now == 0:
            self.on_downbeat()
        else:
            self._led_color = cs.BeatLabel.default_bg
        self._fg_color = cs.BeatLabel.default_fg

    def on_halfbeat(self, dt: float):
        self._led_color = cs.BeatLabel.halfbeat_bg

    def on_downbeat(self, dt: float=0.0):
        self._led_color = cs.BeatLabel.upbeat_bg


class ButtonTapSceneTemp(ImageButton):
    max_tap_count: int = NumericProperty(4)
    timeout: float = NumericProperty(1.0)
    clicks_count_for_calc: int = NumericProperty(2)

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._click_list: Deque[float] = deque(maxlen=self.max_tap_count)

    def _check_if_clear_list(self):
        """
            Если последнее нажатие было произведено более timeout назад,
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


class SceneTemp(SectionPanel):
    pass
