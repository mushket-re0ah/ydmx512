from database.patch import RowPatch
from typing import Optional, Tuple, List, Dict, Set, Iterable
from kivy.event import EventDispatcher
from kivy.properties import (
    BooleanProperty, ObjectProperty, ListProperty,
    NumericProperty, AliasProperty, DictProperty
)
from kivy.utils import boundary
from libs.serialize import SerializableMixin
import bisect
from database.phase_curve_type import RowPhaseCurveType
from libs.dmx512_render import (
    DMXRenderDot, InterpolationType, XYGrid, apply_cycle_shift, RenderPipeline
)
from database import db
from database.fixture_param import RowFixtureParam
from database.fixture import RowFixture
from collections import defaultdict
from enum import Enum
from libs.kivy_json_orm.fields import *
from libs.properties import ClampedNumericProperty, EnumProperty


class RenderDots(list):
    def __new__(cls, dots: Iterable[DMXRenderDot]):
        obj = super().__new__(cls, sorted(dots, key=lambda d: d.x))
        return obj

    def insert_dot_by_x(self, dot: DMXRenderDot):
        pos = bisect.bisect_left([d.x for d in self], dot.x)
        self.insert(pos, dot)

    def add_dot(self, x: float, y: float, dot_type: InterpolationType, grid: XYGrid) -> Optional[DMXRenderDot]:
        frame = grid.to_frame_x(x)
        if any(grid.to_frame_x(dot.x) == frame for dot in self):
            return None
        new_dot = DMXRenderDot(x, y, dot_type)
        self.insert_dot_by_x(new_dot)
        return new_dot

    def remove_dot(self, dot: DMXRenderDot) -> bool:
        if dot not in self:
            return False
        self.remove(dot)
        return True

    def remove_dot_by_x(self, x: float, grid: XYGrid) -> bool:
        dot = self.find_dot_by_x(x, grid)
        if dot:
            return self.remove_dot(dot)
        return False

    def move_dot_to(self, dot: DMXRenderDot, new_x: float, new_y: float, grid: XYGrid) -> bool:
        if dot not in self:
            return False
        dot_index = self.index(dot)

        if dot_index > 0:
            left_frame = grid.to_frame_x(self[dot_index - 1].x)
        else:
            left_frame = -1

        if dot_index < len(self) - 1:
            right_frame = grid.to_frame_x(self[dot_index + 1].x)
        else:
            right_frame = grid.size_x_getter()

        target_frame = boundary(
            grid.to_frame_x(new_x),
            left_frame + 1,
            right_frame - 1,
        )

        self.remove(dot)

        dot.x = grid.to_normalized_x(target_frame)
        dot.y = boundary(new_y, 0.0, 1.0)
        self.insert_dot_by_x(dot)
        return True

    def set_dot_type(self, dot: DMXRenderDot, dot_type: InterpolationType) -> bool:
        if dot not in self:
            return False
        dot.dot_type = dot_type
        return True

    def find_dot_by_x(self, x: float, grid: XYGrid) -> Optional[DMXRenderDot]:
        frame = grid.to_frame_x(x)
        for dot in self:
            if grid.to_frame_x(dot.x) == frame:
                return dot
        return None

    def find_dots_by_area(self, x: float, y: float, width: float, height: float) -> List[DMXRenderDot]:
        x_min = min(x, x + width)
        x_max = max(x, x + width)
        y_min = min(y, y + height)
        y_max = max(y, y + height)
        return [dot for dot in self if x_min <= dot.x <= x_max and y_min <= dot.y <= y_max]

    def get_dots_intersection(self, dots: List[DMXRenderDot]) -> List[DMXRenderDot]:
        return [dot for dot in self if dot in dots]


class RowPhaseSpec(SerializableMixin):
    patch = ObjectProperty()  # RowPatch
    indices = ListField()  # упорядоченный список fixture_index
    amount = ClampedNumericField(0.0, -1.0, 1.0)
    curve = RefField(lambda: db.phase_curve_type, default_factory=lambda: db.phase_curve_type.get_default_row())
    inverted = BooleanField(False)
    dots = ObjectField(
        default_factory=lambda: RenderDots([]),
        serialize=lambda self, value: [[dot.x, dot.y, dot.dot_type.value] for dot in value],
        deserialize=lambda self, value: RenderDots([
            DMXRenderDot(x, y, InterpolationType(t)) for (x, y, t) in value
        ])
    )


class InterpatchSpec(SerializableMixin):
    ordered_patches = ListField(  # упорядоченный список RowPatch
        serialize=lambda self, value: [patch._id for patch in value],
        deserialize=lambda self, value: [db.patch.get_row_by_id(pid) for pid in value]
    )
    linked_shifts = DictField(
        serialize=lambda self, value: {str(k): v for k, v in value.items()},
        deserialize=lambda self, value: {int(k): v for k, v in value.items()}
    )

    master_patch = AliasProperty(lambda self: self.ordered_patches[0])


class PlaybackRenderRow(SerializableMixin):
    active = BooleanField(False)
    _dots = ObjectField(
        serialize=lambda self, value: (
            [[dot.x, dot.y, dot.dot_type.value] for dot in value]
            if value is not None else []
        ),
        deserialize=lambda self, value: (
            RenderDots([DMXRenderDot(x, y, InterpolationType(t)) for x, y, t in value])
            if value else RenderDots([])
        ),
        default_factory=lambda: RenderDots([]),
        force_dispatch=True
    )

    fixture_index = NumericProperty()
    patch = ObjectProperty()
    renderer = ObjectProperty()
    playback = AliasProperty(lambda self: self.renderer.playback) 
    fixture = AliasProperty(lambda self: self.patch.fixture)
    fixture_param = AliasProperty(
        lambda self: self.fixture.param_list_unpacked[self.fixture_index]
    )
    row_phase_spec = AliasProperty(
        lambda self: self.renderer.get_row_phase_spec(self.patch, self.fixture_index),
        bind=("patch", "fixture_index")
    )
    interpatch_spec = AliasProperty(
        lambda self: self.renderer.get_interpatch_spec(self.patch, self.fixture_index),
        bind=("patch", "fixture_index")
    )

    def get_dots(self):
        if self.row_phase_spec:
            return self.row_phase_spec.dots
        return self._dots
    def set_dots(self, dots: RenderDots):
        self.renderer.set_dots_for_row(self, dots)

    dots = AliasProperty(get_dots, set_dots)

    def on__dots(self, _, new_dots):
        self.invalidate_render()

    _render: Optional[bytes] = ObjectProperty(None, allownone=True)
    has_data = AliasProperty(lambda self: bool(self.get_render()), bind=["_render"])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.render_pipeline = RenderPipeline()

    def on_active(self, _, active: bool):
        self.invalidate_render()
        self.renderer.set_patch_addresses()

    def invalidate_render(self):
        self._render = None

    def get_render(self):
        if self._render:
            return self._render
        if not self.active:
            return b""

        frame_count = self.renderer.xy_grid.size_x_getter()
        interpatch_spec = self.interpatch_spec
        if (interpatch_spec and
            self.patch is not interpatch_spec.master_patch and
            self.fixture_index in interpatch_spec.linked_shifts.keys()):
            master_row = self.renderer.get_row(interpatch_spec.master_patch, self.fixture_index)
            if master_row:
                render = master_row.get_render()
                shift_frames = round(self.renderer.get_interpatch_shift(self) * frame_count)
                render = apply_cycle_shift(render, shift_frames)
            else:
                render = b""
        elif self.row_phase_spec and self.fixture_index != min(self.row_phase_spec.indices):
            master_index = min(self.row_phase_spec.indices)
            master_row = self.renderer.get_row(self.patch, master_index)
            if master_row:
                render = master_row.get_render()
                shift_frames = round(self.renderer.get_row_phase_shift(self) * frame_count)
                render = apply_cycle_shift(render, shift_frames)
            else:
                render = b""
        else:
            render = self.render_pipeline.processing(
                self.dots,
                default_value=self.fixture_param.default_value,
                xy_grid=self.renderer.xy_grid
            )

        self._render = render
        return render
