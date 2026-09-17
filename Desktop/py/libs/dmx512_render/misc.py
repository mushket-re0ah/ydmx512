from typing import Optional, Tuple, Union, List
from enum import Enum, auto
from dataclasses import dataclass, field
import itertools


class XYGrid:
    size_x_getter = None
    size_y_getter = None

    def __init__(self, size_x_getter, size_y_getter=lambda: 255):
        self.size_x_getter = size_x_getter
        self.size_y_getter = size_y_getter

    def size_xy_getter(self) -> Tuple[int, int]:
        return (self.size_x_getter(), self.size_y_getter())

    @property
    def last_x_frame(self) -> int:
        return self.size_x_getter() - 1

    def to_frame_x(self, norm_x: float, allow_negative=False) -> int:
        norm_x = self._boundary(norm_x, 1.0, allow_negative)
        return round(norm_x * self.last_x_frame)

    def to_normalized_x(self, frame_x: int, allow_negative=False) -> float:
        frame_x = self._boundary(frame_x, self.last_x_frame, allow_negative)
        return frame_x / self.last_x_frame

    def to_frame_y(self, norm_y: float, allow_negative=False) -> int:
        norm_y = self._boundary(norm_y, 1.0, allow_negative)
        return round(norm_y * self.size_y_getter())

    def to_normalized_y(self, frame_y: int, allow_negative=False) -> float:
        frame_y = self._boundary(frame_y, self.size_y_getter(), allow_negative)
        return frame_y / self.size_y_getter()

    def _boundary(self, value: Union[int, float], maximum: Union[int, float], allow_negative: bool) -> Union[int, float]:
        if allow_negative:
            return min(max(value, -maximum), maximum)
        else:
            return min(max(value, 0), maximum)


class InterpolationType(int, Enum):
    LINEAR = auto()
    SPLINE = auto()

    @staticmethod
    def get_next_type(interp) -> "InterpolationType":
        if interp is InterpolationType.LINEAR:
            return InterpolationType.SPLINE
        else:
            return InterpolationType.LINEAR


@dataclass(frozen=False)
class DMXRenderDot:
    x: float  # [0.0 ... 1.0]
    y: float  # [0.0 ... 1.0]
    dot_type: InterpolationType

    def __iter__(self):
        """Для поддержки распаковки"""
        return iter((self.x, self.y, self.dot_type))

    def __getitem__(self, index):
        return (self.x, self.y, self.dot_type)[index]

    def __hash__(self):
        return hash(id(self))

    def __eq__(self, other):
        return id(self) == id(other)


def calc_phase_shift(
        index: int,
        count: int,
        phase_amount: float,
        curve_points: List[Tuple[float, float]]) -> float:
    if count <= 1:
        return 0.0
    x = index / (count - 1)
    for (x1, y1), (x2, y2) in zip(curve_points, curve_points[1:]):
        if x1 <= x <= x2:
            if x1 == x2:
                return float(y1 * phase_amount)
            return float((y1 + (y2 - y1) * (x - x1) / (x2 - x1)) * phase_amount)
    return 0.0


def apply_cycle_shift(render: bytes, shift: int) -> bytes:
    if not shift:
        return render
    n = len(render)
    if n == 0:
        return render
    shift %= n
    return render[-shift:] + render[:-shift]
