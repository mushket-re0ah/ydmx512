from collections import defaultdict
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from database.playback.renderer.render_data import InterpatchSpec, PlaybackRenderRow, RowPhaseSpec
from libs.command import Command
from libs.dmx512_render.misc import DMXRenderDot, InterpolationType

if TYPE_CHECKING:
    from database.playback.renderer import PlaybackRenderer


class PlaybackCommand(Command):
    def __init__(self, renderer: "PlaybackRenderer"):
        self.renderer = renderer
        self.playback = self.renderer.playback
        super().__init__()


class PlaybackRowCommand(PlaybackCommand):
    def __init__(
            self,
            renderer: "PlaybackRenderer",
            render_rows: List[PlaybackRenderRow],
        ):
        self.render_rows: List[PlaybackRenderRow] = render_rows
        super().__init__(renderer)

    def _do_execute(self) -> bool:
        for row in self.render_rows:
            if not self._do_execute_row(row):
                return False
        return True

    def _do_execute_row(self, row: PlaybackRenderRow) -> bool:
        raise NotImplementedError()

    def _do_undo(self):
        for row in self.render_rows:
            self._do_undo_row(row)

    def _do_undo_row(self, row: PlaybackRenderRow) -> None:
        raise NotImplementedError()

    def _do_redo(self):
        for row in self.render_rows:
            self._do_redo_row(row)

    def _do_redo_row(self, row: PlaybackRenderRow) -> None:
        raise NotImplementedError()

    def merge_render_rows(self, command: "PlaybackRowCommand"):
        self.render_rows = list(set(self.render_rows) | set(command.render_rows))


class PlaybackRowDotsCommand(PlaybackRowCommand):
    def __init__(
            self,
            renderer: "PlaybackRenderer",
            render_rows: List[PlaybackRenderRow],
            rows_dots: Dict[PlaybackRenderRow, List[DMXRenderDot]]
        ):
        super().__init__(renderer, render_rows)
        self.rows_dots = rows_dots

    def merge_rows_dots(self, command: "PlaybackRowDotsCommand"):
        for row, dots in command.rows_dots.items():
            if row in self.rows_dots:
                for dot in dots:
                    if dot not in self.rows_dots[row]:
                        self.rows_dots[row].append(dot)
            else:
                self.rows_dots[row] = dots[:]


class CommandSetActive(PlaybackRowCommand):
    def __init__(
            self,
            renderer: "PlaybackRenderer",
            render_rows: List[PlaybackRenderRow],
            rows_active: Dict[PlaybackRenderRow, bool]
        ):
        self.undo_data: Dict[PlaybackRenderRow, bool] = {}
        super().__init__(renderer, render_rows)
        self.rows_active = rows_active

    def _do_execute_row(self, row: PlaybackRenderRow) -> bool:
        self.undo_data[row] = row.active
        row.active = self.rows_active[row]
        return True

    def _do_undo_row(self, row: PlaybackRenderRow):
        row.active = self.undo_data[row]

    def _do_redo_row(self, row: PlaybackRenderRow):
        row.active = self.rows_active[row]

    def merge(self, command: "CommandSetActive") -> bool:
        self.rows_active.update(command.rows_active)
        for row, active in command.undo_data.items():
            if row not in self.undo_data:
                self.undo_data[row] = active
        self.merge_render_rows(command)
        return True


class CommandSetDotType(PlaybackRowDotsCommand):
    def __init__(
            self,
            renderer: "PlaybackRenderer",
            render_rows: List[PlaybackRenderRow],
            rows_dots: Dict[PlaybackRenderRow, List[DMXRenderDot]],
            dot_type: InterpolationType
        ):
        super().__init__(renderer, render_rows, rows_dots)
        self.dot_type = dot_type
        self.old_types: Dict[DMXRenderDot, InterpolationType] = {}
        self.new_dots: List[DMXRenderDot] = []

    def _do_execute_row(self, row: PlaybackRenderRow) -> bool:
        for dot in self.rows_dots[row]:
            if dot not in self.old_types:
                self.old_types[dot] = dot.dot_type
            if not row.dots.set_dot_type(dot, self.dot_type):
                return False
            self.new_dots.append(dot)
        return True

    def _do_undo_row(self, row: PlaybackRenderRow):
        for dot in self.rows_dots[row]:
            row.dots.set_dot_type(dot, self.old_types[dot])

    def _do_redo_row(self, row: PlaybackRenderRow):
        for dot in self.rows_dots[row]:
            row.dots.set_dot_type(dot, self.dot_type)

    def merge(self, command: "CommandSetDotType") -> bool:
        self.merge_rows_dots(command)

        # сохраняем только первый исходный тип для каждой точки
        for dot, old_type in command.old_types.items():
            self.old_types.setdefault(dot, old_type)

        self.new_dots.extend([dot for dot in command.new_dots if dot not in self.new_dots])
        self.merge_render_rows(command)
        return True


class CommandAddDot(PlaybackRowCommand):
    def __init__(
            self,
            renderer: "PlaybackRenderer",
            render_rows: List[PlaybackRenderRow],
            x: int,
            y: int,
            dot_type: InterpolationType
        ):
        super().__init__(renderer, render_rows)
        self.x = x
        self.y = y
        self.dot_type = dot_type
        self.added_dots_by_row: Dict[PlaybackRenderRow, List[DMXRenderDot]] = {}
        self.added_dots: List[DMXRenderDot] = []

    def _do_execute_row(self, row: PlaybackRenderRow) -> bool:
        new_dot = row.dots.add_dot(self.x, self.y, self.dot_type, self.renderer.xy_grid)
        if new_dot is None:
            return False
        self.added_dots_by_row.setdefault(row, []).append(new_dot)
        self.added_dots.append(new_dot)
        return True

    def _do_undo_row(self, row: PlaybackRenderRow):
        for dot in self.added_dots_by_row.get(row, []):
            row.dots.remove_dot(dot)

    def _do_redo_row(self, row: PlaybackRenderRow):
        for dot in self.added_dots_by_row.get(row, []):
            row.dots.insert_dot_by_x(dot)

    def merge(self, command: "CommandAddDot") -> bool:
        self.merge_render_rows(command)
        for row, dots in command.added_dots_by_row.items():
            self.added_dots_by_row.setdefault(row, []).extend(dots)
        for dot in command.added_dots:
            if dot not in self.added_dots:
                self.added_dots.append(dot)
        return True


class CommandRemoveDot(PlaybackRowDotsCommand):
    def __init__(
            self,
            renderer: "PlaybackRenderer",
            render_rows: List[PlaybackRenderRow],
            rows_dots: Dict[PlaybackRenderRow, List[DMXRenderDot]]
        ):
        super().__init__(renderer, render_rows, rows_dots)
        self.removed_dots_by_row: Dict[PlaybackRenderRow, List[DMXRenderDot]] = defaultdict(list)

    def _do_execute_row(self, row: PlaybackRenderRow) -> bool:
        dots_to_remove = self.rows_dots[row]
        # Проверяем, что все точки существуют в строке
        if not all(dot in row.dots for dot in dots_to_remove):
            return False

        for dot in dots_to_remove:
            row.dots.remove_dot(dot)
            self.removed_dots_by_row[row].append(dot)
        return True

    def _do_undo_row(self, row: PlaybackRenderRow):
        for dot in self.removed_dots_by_row.get(row, []):
            row.dots.insert_dot_by_x(dot)

    def _do_redo_row(self, row: PlaybackRenderRow):
        for dot in self.removed_dots_by_row.get(row, []):
            row.dots.remove_dot(dot)

    def merge(self, command: "CommandRemoveDot") -> bool:
        self.merge_rows_dots(command)

        # Объединяем removed_dots_by_row (удалённые точки)
        for row, dots in command.removed_dots_by_row.items():
            existing = self.removed_dots_by_row.setdefault(row, [])
            for dot in dots:
                if dot not in existing:
                    existing.append(dot)

        self.merge_render_rows(command)
        return True


class CommandMoveDot(PlaybackRowDotsCommand):
    def __init__(
            self,
            renderer: "PlaybackRenderer",
            render_rows: List[PlaybackRenderRow],
            rows_dots: Dict[PlaybackRenderRow, List[DMXRenderDot]],
            start_positions: Dict[DMXRenderDot, Tuple[float, float]],
            diff_x: float,
            diff_y: float
        ):
        super().__init__(renderer, render_rows, rows_dots)
        self.start_positions: Dict[DMXRenderDot, Tuple[float, float]] = start_positions
        self.target_positions: Dict[DMXRenderDot, Tuple[float, float]] = {
            dot: (x + diff_x, y + diff_y)
            for dot, (x, y) in start_positions.items()
        }
        self.end_positions: Dict[DMXRenderDot, Tuple[float, float]] = {}

    def _do_execute_row(self, row: PlaybackRenderRow) -> bool:
        for dot in self.rows_dots[row]:
            target_x, target_y = self.target_positions[dot]
            if not row.dots.move_dot_to(dot, target_x, target_y, self.renderer.xy_grid):
                return False
            self.end_positions[dot] = (dot.x, dot.y)
        return True

    def _do_undo_row(self, row: PlaybackRenderRow):
        for dot in self.rows_dots[row]:
            start_x, start_y = self.start_positions[dot]
            row.dots.move_dot_to(dot, start_x, start_y, self.renderer.xy_grid)

    def _do_redo_row(self, row: PlaybackRenderRow):
        for dot in self.rows_dots[row]:
            end_x, end_y = self.end_positions[dot]
            row.dots.move_dot_to(dot, end_x, end_y, self.renderer.xy_grid)

    def merge(self, command: "CommandMoveDot") -> bool:
        self.merge_rows_dots(command)
        for dot, pos in command.start_positions.items():
            if dot not in self.start_positions:
                self.start_positions[dot] = pos
        self.target_positions.update(command.target_positions)
        self.end_positions.update(command.end_positions)
        self.merge_render_rows(command)
        return True


class CommandCreateRowPhaseSpec(PlaybackCommand):
    def __init__(
            self,
            renderer: "PlaybackRenderer",
            spec: RowPhaseSpec
        ):
        super().__init__(renderer)
        self.spec = spec

    def _do_execute(self) -> bool:
        self.renderer.add_row_phase_spec(self.spec)
        return True

    def _do_undo(self):
        self.renderer.remove_row_phase_spec(self.spec)

    def _do_redo(self):
        self.renderer.add_row_phase_spec(self.spec)

    def merge(self, command: "CommandCreateRowPhaseSpec") -> bool:
        return False


class CommandUpdateRowPhaseSpec(PlaybackCommand):
    def __init__(
            self,
            renderer: "PlaybackRenderer",
            spec: RowPhaseSpec,
            **kwargs: Any
        ):
        super().__init__(renderer)
        self.spec = spec
        self.new_values: Dict[str, Any] = kwargs
        self.old_values: Dict[str, Any] = {}

    def _do_execute(self) -> bool:
        # Сохраняем старые значения только при первом выполнении
        if not self.old_values:
            for field in self.new_values.keys():
                self.old_values[field] = getattr(self.spec, field)
        for field, value in self.new_values.items():
            setattr(self.spec, field, value)
        return True

    def _do_undo(self):
        for field, value in self.old_values.items():
            setattr(self.spec, field, value)

    def _do_redo(self):
        for field, value in self.new_values.items():
            setattr(self.spec, field, value)

    def merge(self, command: "CommandUpdateRowPhaseSpec") -> bool:
        if command.spec is self.spec:
            self.new_values.update(command.new_values)
            return True
        return False


class CommandRemoveRowPhaseSpec(PlaybackCommand):
    def __init__(
            self,
            renderer: "PlaybackRenderer",
            spec: RowPhaseSpec
        ):
        super().__init__(renderer)
        self.spec = spec

    def _do_execute(self) -> bool:
        self.renderer.remove_row_phase_spec(self.spec)
        return True

    def _do_undo(self):
        self.renderer.add_row_phase_spec(self.spec)

    def _do_redo(self):
        self.renderer.remove_row_phase_spec(self.spec)

    def merge(self, command: "CommandRemoveRowPhaseSpec") -> bool:
        return False


class CommandCreateInterpatchSpec(PlaybackCommand):
    def __init__(
            self,
            renderer: "PlaybackRenderer",
            spec: InterpatchSpec
        ):
        super().__init__(renderer)
        self.spec = spec

    def _do_execute(self) -> bool:
        self.renderer.add_interpatch_spec(self.spec)
        return True

    def _do_undo(self):
        self.renderer.remove_interpatch_spec(self.spec)

    def _do_redo(self):
        self.renderer.add_interpatch_spec(self.spec)

    def merge(self, command: "CommandCreateInterpatchSpec") -> bool:
        return False


class CommandUpdateInterpatchSpec(PlaybackCommand):
    def __init__(
            self,
            renderer: "PlaybackRenderer",
            spec: InterpatchSpec,
            **kwargs: Any
        ):
        super().__init__(renderer)
        self.spec = spec
        self.new_values: Dict[str, Any] = kwargs
        self.old_values: Dict[str, Any] = {}

    def _do_execute(self) -> bool:
        if not self.old_values:
            for field in self.new_values.keys():
                self.old_values[field] = getattr(self.spec, field)
        for field, value in self.new_values.items():
            setattr(self.spec, field, value)
        return True

    def _do_undo(self):
        for field, value in self.old_values.items():
            setattr(self.spec, field, value)

    def _do_redo(self):
        for field, value in self.new_values.items():
            setattr(self.spec, field, value)

    def merge(self, command: "CommandUpdateInterpatchSpec") -> bool:
        if command.spec is self.spec:
            self.new_values.update(command.new_values)
            return True
        return False


class CommandRemoveInterpatchSpec(PlaybackCommand):
    def __init__(
            self,
            renderer: "PlaybackRenderer",
            spec: InterpatchSpec
        ):
        super().__init__(renderer)
        self.spec = spec

    def _do_execute(self) -> bool:
        self.renderer.remove_interpatch_spec(self.spec)
        return True

    def _do_undo(self):
        self.renderer.add_interpatch_spec(self.spec)

    def _do_redo(self):
        self.renderer.remove_interpatch_spec(self.spec)

    def merge(self, command: "CommandRemoveInterpatchSpec") -> bool:
        return False
