from libs.command import Command
from typing import List, Dict
from database.playback.renderer.render_data import RowPhaseSpec, InterpatchSpec
from collections import defaultdict
from libs import logger


class PlaybackCommand(Command):
    def __init__(
            self,
            renderer: "PlaybackRenderer",
            render_rows: List["PlaybackRenderRow"],
        ):
        self.renderer = renderer
        self.render_rows = render_rows
        self.playback = self.renderer.playback
        self.undo_data = {}  # ключ - строка, значение - значение
        super().__init__()

    def _do_execute(self) -> bool:
        for row in self.render_rows:
            if not self._do_execute_row(row):
                return False
        return True

    def _do_execute_row(self, row: "PlaybackRenderRow") -> bool:
        raise NotImplementedError()

    def _do_undo(self):
        for row in self.render_rows:
            self._do_undo_row(row)

    def _do_undo_row(self, row: "PlaybackRenderRow"):
        raise NotImplementedError()

    def _do_redo(self):
        for row in self.render_rows:
            self._do_redo_row(row)

    def _do_redo_row(self, row: "PlaybackRenderRow"):
        raise NotImplementedError()

    def merge_render_rows(self, command: "PlaybackCommand"):
        self.render_rows = list(set(self.render_rows) | set(command.render_rows))

    def merge_rows_dots(self, command: "PlaybackCommand"):
        for row, dots in command.rows_dots.items():
            if row in self.rows_dots:
                for dot in dots:
                    if dot not in self.rows_dots[row]:
                        self.rows_dots[row].append(dot)
            else:
                self.rows_dots[row] = dots[:]


class CommandSetActive(PlaybackCommand):
    def __init__(
            self,
            renderer: "PlaybackRenderer",
            render_rows: List["PlaybackRenderRow"],
            rows_active: Dict["PlaybackRenderRow", bool]
        ):
        super().__init__(renderer, render_rows)
        self.rows_active = rows_active

    def _do_execute_row(self, row: "PlaybackRenderRow") -> bool:
        self.undo_data[row] = row.active
        row.active = self.rows_active[row]
        return True

    def _do_undo_row(self, row: "PlaybackRenderRow"):
        row.active = self.undo_data[row]

    def _do_redo_row(self, row: "PlaybackRenderRow"):
        row.active = self.rows_active[row]

    def merge(self, command: "CommandSetActive"):
        self.rows_active.update(command.rows_active)
        for row, active in command.undo_data.items():
            if row not in self.undo_data:
                self.undo_data[row] = active
        self.merge_render_rows(command)


class CommandSetDotType(PlaybackCommand):
    def __init__(self, renderer, render_rows, rows_dots, dot_type):
        super().__init__(renderer, render_rows)
        self.rows_dots = rows_dots
        self.dot_type = dot_type
        self.old_types = {}      # точка -> исходный тип
        self.new_dots = []

    def _do_execute_row(self, row):
        for dot in self.rows_dots[row]:
            if dot not in self.old_types:
                self.old_types[dot] = dot.dot_type
            if not row.dots.set_dot_type(dot, self.dot_type):
                return False
            self.new_dots.append(dot)
        return True

    def _do_undo_row(self, row):
        for dot in self.rows_dots[row]:
            row.dots.set_dot_type(dot, self.old_types[dot])

    def _do_redo_row(self, row):
        for dot in self.rows_dots[row]:
            row.dots.set_dot_type(dot, self.dot_type)

    def merge(self, command):
        self.merge_rows_dots(command)

        # сохраняем только первый исходный тип для каждой точки
        for dot, old_type in command.old_types.items():
            self.old_types.setdefault(dot, old_type)

        self.new_dots.extend([dot for dot in command.new_dots if dot not in self.new_dots])
        self.merge_render_rows(command)


class CommandAddDot(PlaybackCommand):
    def __init__(self, renderer, render_rows, x, y, dot_type):
        super().__init__(renderer, render_rows)
        self.x = x
        self.y = y
        self.dot_type = dot_type
        self.added_dots_by_row = {}  # row -> list[DMXRenderDot]
        self.added_dots = []

    def _do_execute_row(self, row):
        new_dot = row.dots.add_dot(self.x, self.y, self.dot_type, self.renderer.xy_grid)
        if new_dot is None:
            return False
        self.added_dots_by_row.setdefault(row, []).append(new_dot)
        self.added_dots.append(new_dot)
        return True

    def _do_undo_row(self, row):
        for dot in self.added_dots_by_row.get(row, []):
            row.dots.remove_dot(dot)

    def _do_redo_row(self, row):
        for dot in self.added_dots_by_row.get(row, []):
            row.dots.insert_dot_by_x(dot)

    def merge(self, command):
        self.merge_render_rows(command)
        for row, dots in command.added_dots_by_row.items():
            self.added_dots_by_row.setdefault(row, []).extend(dots)
        for dot in command.added_dots:
            if dot not in self.added_dots:
                self.added_dots.append(dot)


class CommandRemoveDot(PlaybackCommand):
    def __init__(self, renderer, render_rows, rows_dots):
        super().__init__(renderer, render_rows)
        self.rows_dots = rows_dots   # Dict[PlaybackRenderRow, List[DMXRenderDot]]
        self.removed_dots_by_row = defaultdict(list)  # row -> list точек, удалённых при execute

    def _do_execute_row(self, row):
        dots_to_remove = self.rows_dots[row]
        # Проверяем, что все точки существуют в строке
        if not all(dot in row.dots for dot in dots_to_remove):
            return False

        for dot in dots_to_remove:
            row.dots.remove_dot(dot)
            self.removed_dots_by_row[row].append(dot)
        return True

    def _do_undo_row(self, row):
        for dot in self.removed_dots_by_row.get(row, []):
            row.dots.insert_dot_by_x(dot)

    def _do_redo_row(self, row):
        for dot in self.removed_dots_by_row.get(row, []):
            row.dots.remove_dot(dot)

    def merge(self, command):
        self.merge_rows_dots(command)

        # Объединяем removed_dots_by_row (удалённые точки)
        for row, dots in command.removed_dots_by_row.items():
            existing = self.removed_dots_by_row.setdefault(row, [])
            for dot in dots:
                if dot not in existing:
                    existing.append(dot)

        self.merge_render_rows(command)


class CommandMoveDot(PlaybackCommand):
    def __init__(self, renderer, render_rows, rows_dots, start_positions, diff_x, diff_y):
        super().__init__(renderer, render_rows)
        self.rows_dots = rows_dots
        self.start_positions = start_positions
        self.target_positions = {
            dot: (x + diff_x, y + diff_y)
            for dot, (x, y) in start_positions.items()
        }
        self.end_positions = {}

    def _do_execute_row(self, row):
        for dot in self.rows_dots[row]:
            target_x, target_y = self.target_positions[dot]
            if not row.dots.move_dot_to(dot, target_x, target_y, self.renderer.xy_grid):
                return False
            self.end_positions[dot] = (dot.x, dot.y)
        return True

    def _do_undo_row(self, row):
        for dot in self.rows_dots[row]:
            start_x, start_y = self.start_positions[dot]
            row.dots.move_dot_to(dot, start_x, start_y, self.renderer.xy_grid)

    def _do_redo_row(self, row):
        for dot in self.rows_dots[row]:
            end_x, end_y = self.end_positions[dot]
            row.dots.move_dot_to(dot, end_x, end_y, self.renderer.xy_grid)

    def merge(self, command):
        self.merge_rows_dots(command)
        for dot, pos in command.start_positions.items():
            if dot not in self.start_positions:
                self.start_positions[dot] = pos
        self.target_positions.update(command.target_positions)
        self.end_positions.update(command.end_positions)
        self.merge_render_rows(command)


class CommandCreateRowPhaseSpec(PlaybackCommand):
    def __init__(self, renderer, spec):
        super().__init__(renderer, [])
        self.spec = spec

    def _do_execute(self):
        self.renderer.add_row_phase_spec(self.spec)
        return True

    def _do_undo(self):
        self.renderer.remove_row_phase_spec(self.spec)

    def _do_redo(self):
        self.renderer.add_row_phase_spec(self.spec)

    def merge(self, command):
        return False


class CommandUpdateRowPhaseSpec(PlaybackCommand):
    def __init__(self, renderer, spec, **kwargs):
        super().__init__(renderer, [])
        self.spec = spec
        self.new_values = kwargs
        self.old_values = {}

    def _do_execute(self):
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

    def merge(self, command):
        if command.spec is self.spec:
            self.new_values.update(command.new_values)
            return True
        return False


class CommandRemoveRowPhaseSpec(PlaybackCommand):
    def __init__(self, renderer, spec):
        super().__init__(renderer, [])
        self.spec = spec

    def _do_execute(self):
        self.renderer.remove_row_phase_spec(self.spec)
        return True

    def _do_undo(self):
        self.renderer.add_row_phase_spec(self.spec)

    def _do_redo(self):
        self.renderer.remove_row_phase_spec(self.spec)

    def merge(self, command):
        return False


class CommandCreateInterpatchSpec(PlaybackCommand):
    def __init__(self, renderer, spec):
        super().__init__(renderer, [])
        self.spec = spec

    def _do_execute(self):
        self.renderer.add_interpatch_spec(self.spec)
        return True

    def _do_undo(self):
        self.renderer.remove_interpatch_spec(self.spec)

    def _do_redo(self):
        self.renderer.add_interpatch_spec(self.spec)

    def merge(self, command):
        return False


class CommandUpdateInterpatchSpec(PlaybackCommand):
    def __init__(self, renderer, spec, **kwargs):
        super().__init__(renderer, [])
        self.spec = spec
        self.new_values = kwargs
        self.old_values = {}

    def _do_execute(self):
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

    def merge(self, command):
        if command.spec is self.spec:
            self.new_values.update(command.new_values)
            return True
        return False


class CommandRemoveInterpatchSpec(PlaybackCommand):
    def __init__(self, renderer, spec):
        super().__init__(renderer, [])
        self.spec = spec

    def _do_execute(self):
        self.renderer.remove_interpatch_spec(self.spec)
        return True

    def _do_undo(self):
        self.renderer.add_interpatch_spec(self.spec)

    def _do_redo(self):
        self.renderer.remove_interpatch_spec(self.spec)

    def merge(self, command):
        return False
