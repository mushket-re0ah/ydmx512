from typing import List

from kivy.event import EventDispatcher
from kivy.properties import AliasProperty, NumericProperty

from libs.properties import ClampedNumericProperty


def _raise_error(*args, **kwargs):
    raise RuntimeError("beat_counter module is not initialized")
BeatCounter = _raise_error
loop = _raise_error
def init(TEMP_MINIMUM: int, TEMP_MAXIMUM: int, BEATS_COUNT_MINIMUM: int, BEATS_COUNT_MAXIMUM: int, FRAMES_IN_BEAT: int):
    global BeatCounter
    if BeatCounter is not _raise_error:
        raise Exception("beat_counter module already initialized")
    FRAMES_IN_HALFBEAT = FRAMES_IN_BEAT // 2

    class BeatCounter(EventDispatcher):
        temp: float = ClampedNumericProperty(120, TEMP_MINIMUM, TEMP_MAXIMUM)
        beats_count: int = ClampedNumericProperty(4, BEATS_COUNT_MINIMUM, BEATS_COUNT_MAXIMUM)
        _beat_now: int = NumericProperty(0)
        _frame_now: int = NumericProperty(0)

        _frame_counter: float = 0.0

        __events__ = ("on_halfbeat", "on_downbeat",)

        frames_per_seconds: float = AliasProperty(
            lambda self: (self.temp / 60) * FRAMES_IN_BEAT, None,
            bind=("temp",), cache=True
        )

        def set_beat_now(self, beat_now: int) -> bool:
            self.was_halfbeat = False
            if beat_now >= self.beats_count:
                self._beat_now = beat_now % self.beats_count
                self.dispatch("on_downbeat")
            else:
                self._beat_now = beat_now
            return True
        beat_now: int = AliasProperty(
            lambda self: self._beat_now, set_beat_now,
            bind=("_beat_now",)
        )

        was_halfbeat: bool = False
        def set_frame_now(self, frame_now: int) -> bool:
            if (frame_now // (FRAMES_IN_BEAT * (self.beat_now + 1))) > 0:
                self.beat_now += (frame_now - self._frame_now) // FRAMES_IN_BEAT + 1
            self._frame_now = frame_now % (
                FRAMES_IN_BEAT * self.beats_count)
            if not self.was_halfbeat:
                if (frame_now % FRAMES_IN_BEAT) >= FRAMES_IN_HALFBEAT:
                    self.dispatch("on_halfbeat")
            return True
        frame_now: int = AliasProperty(
            lambda self: self._frame_now, set_frame_now,
            bind=("_frame_now",)
        )

        def tick(self, time_diff: float):
            self._frame_counter += self.frames_per_seconds * time_diff
            frames_to_add, self._frame_counter = divmod(self._frame_counter, 1.0)
            self.frame_now += int(frames_to_add)

        def on_halfbeat(self):
            self.was_halfbeat = True

        def on_downbeat(self):
            pass

        def on_temp(self, _, temp: int):
            self.__reload()

        def on_beats_count(self, _, beats_count: int):
            self.__reload()

        def __reload(self):
            self._beat_now = self.beats_count - 1
            self._frame_now = self._beat_now * FRAMES_IN_BEAT
            self._frame_counter = 0

        def link(self):
            _add_beat_counter(self)

        def unlink(self):
            _remove_beat_counter(self)

    _beat_counter_list: List[BeatCounter] = []
    def loop(time_diff: float):
        for beat_counter in _beat_counter_list[:]:
            beat_counter.tick(time_diff)

    def _add_beat_counter(beat_counter: BeatCounter):
        _beat_counter_list.append(beat_counter)

    def _remove_beat_counter(beat_counter: BeatCounter):
        _beat_counter_list.remove(beat_counter)

    globals()["BeatCounter"] = BeatCounter
    globals()["loop"] = loop
