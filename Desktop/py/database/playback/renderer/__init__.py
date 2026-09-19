from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty, ObjectProperty, DictProperty
from database.patch import RowPatch
from libs.serialize import *
from typing import List, Tuple, Set, Union
from libs.properties import ClampedNumericProperty
from libs.kivy_utils import AutoUnbindBehavior
from libs.kivy_json_orm.fields import *
from libs.command import CommandHistory
from database.playback.renderer.render_data import (
    PlaybackRenderRow, RowPhaseSpec, InterpatchSpec, RenderDots
)
from libs.dmx512_render import (
    DMXRenderDot, InterpolationType, XYGrid, calc_phase_shift
)
from database.phase_curve_type import RowPhaseCurveType
from database.playback.renderer import render_utils
from database.playback.renderer.command import (
    PlaybackCommand,
    CommandSetActive, CommandAddDot, CommandRemoveDot, CommandMoveDot,
    CommandSetDotType,
    CommandCreateRowPhaseSpec, CommandUpdateRowPhaseSpec, CommandRemoveRowPhaseSpec,
    CommandCreateInterpatchSpec, CommandUpdateInterpatchSpec, CommandRemoveInterpatchSpec,
)
from misc import constants
from libs import logger


class PlaybackRenderer(AutoUnbindBehavior, CommandHistory, SerializableMixin):
    playback = ObjectProperty()
    _rows_by_patch = DictField(  # patch -> list[PlaybackRenderRow]
        serialize=lambda self, value: self._serialize_rows_by_patch(value),
        deserialize=lambda self, value: self._deserialize_rows_by_patch(value),
    )
    def _serialize_rows_by_patch(self, value):
        data = {}
        for patch, rows in value.items():
            data[str(patch._id)] = [row.serialize() for row in rows]
        return data

    def _deserialize_rows_by_patch(self, value):
        restored = {}
        for patch_id_str, rows_data in value.items():
            patch_id = int(patch_id_str)
            patch = self.playback.database.patch.get_row_by_id(patch_id)
            if patch is None:
                continue
            rows = []
            for i, row_data in enumerate(rows_data):
                render_row = PlaybackRenderRow(
                    renderer=self,
                    patch=patch,
                    fixture_index=i,
                )
                render_row.deserialize(row_data)
                rows.append(render_row)
            restored[patch] = rows
        return restored

    _row_phase_specs_by_patch = DictField(   # patch -> list[RowPhaseSpec]
        serialize=lambda self, value: self._serialize_row_phase_specs_by_patch(value),
        deserialize=lambda self, value: self._deserialize_row_phase_specs_by_patch(value)
    )

    def _serialize_row_phase_specs_by_patch(self, value):
        data = {}
        for patch, specs in value.items():
            data[str(patch._id)] = [spec.serialize() for spec in specs]
        return data

    def _deserialize_row_phase_specs_by_patch(self, value):
        restored = {}
        for patch_id_str, specs_data in value.items():
            patch_id = int(patch_id_str)
            patch = self.playback.database.patch.get_row_by_id(patch_id)
            if patch is None:
                continue
            specs = []
            for spec_data in specs_data:
                spec = RowPhaseSpec(patch=patch)
                spec.deserialize(spec_data)
                specs.append(spec)
            restored[patch] = specs
        return restored

    _interpatch_spec_by_patch = DictField(  # patch -> InterpatchSpec (одна группа на патч)
        serialize=lambda self, value: self._serialize_interpatch_specs(value),
        deserialize=lambda self, value: self._deserialize_interpatch_specs(value)
    )

    def _serialize_interpatch_specs(self, value):
        unique_specs = set(value.values())
        data = {}
        for spec in unique_specs:
            if not spec.ordered_patches:
                continue
            master_patch_id = str(spec.ordered_patches[0]._id)
            data[master_patch_id] = spec.serialize()
        return data

    def _deserialize_interpatch_specs(self, value):
        restored = {}
        for master_patch_id_str, spec_data in value.items():
            spec = InterpatchSpec()
            spec.deserialize(spec_data)
            for patch in spec.ordered_patches:
                restored[patch] = spec
        return restored

    patch_addresses = DictProperty()
    universe_addresses = DictProperty()

    intensive = ClampedNumericField(100, 0, 100)
    all_params_intensive = BooleanField(False)
    virtual_dimmer = BooleanField(True)
    correction_tilt = BooleanField(False)
    correction_pan = BooleanField(False)

    xy_grid = None

    __events__ = ("on_render_changed",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_patch_addresses()

    def after_deserialize(self):
        self.set_patch_addresses()
        # Синхронизируем точки мастер-строк с точками спецификаций
        for specs in self._row_phase_specs_by_patch.values():
            for spec in specs:
                if spec.indices:
                    master_index = min(spec.indices)
                    master_row = self.get_row(spec.patch, master_index)
                    if master_row:
                        master_row._dots = spec.dots
                        master_row.invalidate_render()
        for rows in self._rows_by_patch.values():
            for row in rows:
                row.invalidate_render()

    def edit(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
            self.property(key).dispatch(self)
        self.playback.save()

    def on_render_changed(self):
        self.playback.save()

    def on_playback(self, _, playback):
        self.xy_grid = XYGrid(lambda: playback.player.frame_count)
        self.bind(on_remove=self.on_remove_playback)
        self.bind_to(playback.player, frame_count=self.invalidate_all_render_cache)

    def on_remove_playback(self, playback):
        self.unbind_all()

    def add_patch(self, patch: RowPatch):
        if patch in self._rows_by_patch:
            return self._rows_by_patch[patch]
        rows = [
            PlaybackRenderRow(renderer=self, patch=patch, fixture_index=i)
            for i, _ in enumerate(patch.fixture.param_list_unpacked)
        ]
        self._rows_by_patch[patch] = rows
        self.set_patch_addresses()
        self._make_patch_binds(patch)
        return rows

    def patch_render_data_exist(self, patch: RowPatch) -> bool:
        rows = self._rows_by_patch.get(patch, [])
        return any(row.has_data for row in rows)

    def get_rows(self, patch: RowPatch) -> List[PlaybackRenderRow]:
        return self._rows_by_patch[patch]

    def _make_patch_binds(self, patch: RowPatch):
        patch.bind(start_address=self.set_patch_addresses)
        patch.fixture.bind(param_list_unpacked=self.set_patch_addresses)

    def get_patch_render(self, patch: RowPatch, fixture_index: int) -> bytes:
        row = self.get_row(patch, fixture_index)
        return row.get_render() if row else b""

    def get_row(self, patch: RowPatch, fixture_index: int) -> Optional[PlaybackRenderRow]:
        rows = self._rows_by_patch.get(patch, [])
        if fixture_index < len(rows):
            return rows[fixture_index]
        return None

    def set_patch_addresses(self, *args):
        patch_addresses = defaultdict(set)
        universe_addresses = defaultdict(set)
        for patch, rows in self._rows_by_patch.items():
            for fixture_index, row in enumerate(rows):
                if row.active:
                    address = min(patch.start_address + fixture_index, constants.DMX_ADDRESS_COUNT)
                    patch_addresses[patch].add(address)
                    universe_addresses[patch.universe].add(address)
        self.patch_addresses = patch_addresses
        self.universe_addresses = universe_addresses

    def end_session(self):
        super().end_session()
        self.dispatch("on_render_changed")

    def execute_command(self, command: PlaybackCommand) -> bool:
        success = super().execute_command(command)
        if success:
            self.invalidate_all_render_cache()
        return success

    def undo(self):
        super().undo()
        self.invalidate_all_render_cache()

    def redo(self):
        super().redo()
        self.invalidate_all_render_cache()

    def invalidate_all_render_cache(self, *args):
        for rows in self._rows_by_patch.values():
            for row in rows:
                row.invalidate_render()
        self.dispatch("on_render_changed")

    def set_row_active(self, active: bool, render_rows: List[PlaybackRenderRow]):
        self.execute_command(CommandSetActive(self, render_rows, {row: active for row in render_rows}))

    def add_dot_by_x(
            self,
            x: int, y: int, dot_type: InterpolationType,
            render_rows: List[PlaybackRenderRow]) -> Tuple[List[DMXRenderDot], bool]:
        self._activate_rows_if_needed(render_rows)
        source_rows = self._get_dots_source_rows(render_rows)
        command = CommandAddDot(self, source_rows, x, y, dot_type)
        success = self.execute_command(command)
        return command.added_dots, success

    def remove_dot_by_x(self, x: int, render_rows: List[PlaybackRenderRow]):
        self._activate_rows_if_needed(render_rows)
        source_rows = self._get_dots_source_rows(render_rows)
        rows_dots = render_utils.get_rows_to_dots_by_x(source_rows, x)
        self.execute_command(CommandRemoveDot(self, source_rows, rows_dots))

    def remove_dot(self, render_rows: List[PlaybackRenderRow], dots: List[DMXRenderDot]):
        self._activate_rows_if_needed(render_rows)
        source_rows = self._get_dots_source_rows(render_rows)
        rows_dots = self._filter_dots_for_rows(render_utils.get_rows_to_dots_all(source_rows), dots)
        self.execute_command(CommandRemoveDot(self, source_rows, rows_dots))

    def set_dot_type(
            self,
            dots: List[DMXRenderDot],
            dot_type: InterpolationType,
            render_rows: List[PlaybackRenderRow]) -> Optional[List[DMXRenderDot]]:
        self._activate_rows_if_needed(render_rows)
        source_rows = self._get_dots_source_rows(render_rows)
        rows_dots = self._filter_dots_for_rows(render_utils.get_rows_to_dots_all(source_rows), dots)
        command = CommandSetDotType(self, source_rows, rows_dots, dot_type)
        success = self.execute_command(command)
        return command.new_dots if success else None

    def move_dot(
            self,
            render_rows: List[PlaybackRenderRow],
            dots: List[DMXRenderDot],
            start_positions: Dict[DMXRenderDot, Tuple[float, float]],
            diff_x: float,
            diff_y: float) -> Optional[List[DMXRenderDot]]:
        self._activate_rows_if_needed(render_rows)
        source_rows = self._get_dots_source_rows(render_rows)
        rows_dots = self._filter_dots_for_rows(render_utils.get_rows_to_dots_all(source_rows), dots, reverse=not (diff_x <= 0))
        command = CommandMoveDot(self, source_rows, rows_dots, start_positions, diff_x, diff_y)
        success = self.execute_command(command)
        if not success:
            return None
        return [dot for row_dots in rows_dots.values() for dot in row_dots]

    def clear_dots(self, render_rows: List[PlaybackRenderRow]):
        dots_to_remove = []
        for row_dots in render_utils.get_rows_to_dots_all(render_rows).values():
            for dot in row_dots:
                if dot not in dots_to_remove:
                    dots_to_remove.append(dot)
        self.remove_dot(render_rows, dots_to_remove)

    def clear_rows(self, render_rows: List[PlaybackRenderRow], deactivate=False, clear_phases=False):
        if clear_phases:
            self.clear_row_phase(render_rows)
            self.remove_interpatch_linked_rows(render_rows)
        self.clear_dots(render_rows)
        if deactivate:
            self.set_row_active(False, render_rows)

    def apply_row_phase(self,
            render_rows: List[PlaybackRenderRow],
            phase_amount: float,
            phase_curve: RowPhaseCurveType,
            phase_inverted: bool):
        patch_render_rows = render_utils.get_patch_render_rows(render_rows)
        for patch, rows in patch_render_rows.items():
            group = self.get_interpatch_spec(patch)
            if group:
                # Ищем среди выбранных строк индексы, уже присутствующие в linked_shifts
                existing_in_rows = [row.fixture_index for row in rows if row.fixture_index in group.linked_shifts]
                if existing_in_rows:
                    ref_amount = group.linked_shifts[existing_in_rows[0]]
                    # Добавляем недостающие индексы с эталонным amount
                    missing = {row.fixture_index for row in rows} - set(group.linked_shifts.keys())
                    if missing:
                        new_shifts = group.linked_shifts.copy()
                        for idx in missing:
                            new_shifts[idx] = ref_amount
                        self.execute_command(CommandUpdateInterpatchSpec(
                            self, group, linked_shifts=new_shifts
                        ))
        patch_render_rows = self._expand_patches_via_interpatch(patch_render_rows)

        for patch, render_rows in patch_render_rows.items():
            self._activate_rows_if_needed(render_rows)
            if len(render_rows) < 2:
                continue
            indices = sorted({row.fixture_index for row in render_rows})
            cmd = self._prepare_row_phase_command(
                patch, indices, phase_amount, phase_curve, phase_inverted,
                dots=render_rows[0].dots if not self._get_existing_row_phase_spec(patch, indices) else None
            )
            if cmd:
                self.execute_command(cmd)

    def clear_row_phase(self, render_rows: List[PlaybackRenderRow]):
        patch_render_rows = render_utils.get_patch_render_rows(render_rows)
        patch_render_rows = self._expand_patches_via_interpatch(patch_render_rows)

        for patch, render_rows in patch_render_rows.items():
            if len(render_rows) < 2:
                continue
            indices = {row.fixture_index for row in render_rows}
            intersecting_specs = self._get_row_phase_specs_intersecting(patch, indices)
            for spec in intersecting_specs:
                remaining_indices = [idx for idx in spec.indices if idx not in indices]
                if len(remaining_indices) < 2:
                    command = CommandRemoveRowPhaseSpec(self, spec)
                else:
                    command = CommandUpdateRowPhaseSpec(self, spec, indices=remaining_indices)
                self.execute_command(command)

    def set_phase_interpatch_x(self, amount: float, render_rows: List[PlaybackRenderRow]):
        self._activate_rows_if_needed(render_rows)
        patches = list(dict.fromkeys(row.patch for row in render_rows))
        if len(patches) < 2:
            return False

        fixture = patches[0].fixture
        if any(patch.fixture != fixture for patch in patches):
            return False

        occupied_specs = {self.get_interpatch_spec(patch) for patch in patches}
        occupied_specs.discard(None)
        if len(occupied_specs) > 1:
            return False

        existing_spec = None
        if occupied_specs:
            existing_spec = occupied_specs.pop()
            if not all(patch in existing_spec.ordered_patches for patch in patches):
                return False

        # Расширяем linked_shifts с учётом row phase
        linked_shifts = self._get_expanded_interpatch_linked_shifts(render_rows, amount)

        self._sync_row_phase_for_interpatch(patches, render_rows)
        cmd = self._prepare_interpatch_command(
            existing_spec,
            patches,
            linked_shifts,
        )
        self.execute_command(cmd)

    def _get_expanded_interpatch_linked_shifts(self, render_rows: List[PlaybackRenderRow], amount: float) -> Dict[int, float]:
        """Возвращает расширенный список индексов с учётом row phase."""
        shifts = {}
        for row in render_rows:
            idx = row.fixture_index
            shifts[idx] = amount
            spec = self.get_row_phase_spec(row.patch, idx)
            if spec:
                for i in spec.indices:
                    shifts[i] = amount
        return shifts

    def clear_interpatch_phase(self, patch: RowPatch):
        spec = self.get_interpatch_spec(patch)
        if spec:
            cmd = CommandRemoveInterpatchSpec(self, spec)
            self.execute_command(cmd)

    def set_dots_for_row(self, row: PlaybackRenderRow, dots: RenderDots):
        spec = self.get_row_phase_spec(row.patch, row.fixture_index)
        if spec:
            spec.dots = dots
            self.invalidate_all_render_cache()
        else:
            row._dots = dots
            row.invalidate_render()

    def add_row_phase_spec(self, spec: RowPhaseSpec):
        patch = spec.patch
        self._row_phase_specs_by_patch.setdefault(patch, []).append(spec)

    def remove_row_phase_spec(self, spec: RowPhaseSpec):
        patch = spec.patch
        specs = self._row_phase_specs_by_patch.get(patch, [])
        if spec in specs:
            specs.remove(spec)
            if not specs:
                del self._row_phase_specs_by_patch[patch]

    def get_row_phase_spec(self, patch: RowPatch, fixture_index: int) -> Optional[RowPhaseSpec]:
        for spec in self._row_phase_specs_by_patch.get(patch, []):
            if fixture_index in spec.indices:
                return spec
        return None

    def add_interpatch_spec(self, spec: InterpatchSpec):
        for patch in spec.ordered_patches:
            self._interpatch_spec_by_patch[patch] = spec

    def remove_interpatch_spec(self, spec: InterpatchSpec):
        for patch in spec.ordered_patches:
            if self._interpatch_spec_by_patch.get(patch) is spec:
                del self._interpatch_spec_by_patch[patch]

    def get_interpatch_spec(self, patch: RowPatch, fixture_index=None) -> Optional[InterpatchSpec]:
        spec = self._interpatch_spec_by_patch.get(patch)
        if not spec:
            return None
        if fixture_index is not None:
            if fixture_index in spec.linked_shifts:
                return spec
            else:
                return None
        else:
            return spec

    def get_row_phase_shift(self, row: PlaybackRenderRow) -> float:
        spec = self.get_row_phase_spec(row.patch, row.fixture_index)
        if not spec:
            return 0.0
        try:
            index = spec.indices.index(row.fixture_index)
        except ValueError:
            return 0.0
        count = len(spec.indices)
        if count <= 1:
            return 0.0
        phase_amount = spec.amount * (-1 if spec.inverted else 1)
        return calc_phase_shift(index, count, phase_amount, spec.curve.dots)

    def get_interpatch_shift(self, row: PlaybackRenderRow) -> float:
        spec = self.get_interpatch_spec(row.patch, row.fixture_index)
        if not spec:
            return 0.0
        if row.patch is spec.master_patch:
            return 0.0
        try:
            patch_index = spec.ordered_patches.index(row.patch)
            amount = spec.linked_shifts.get(row.fixture_index, 0.0)
            return patch_index * amount
        except ValueError:
            return 0.0

    def _get_existing_row_phase_spec(self, patch: RowPatch, indices: List[int]):
        """Возвращает спецификацию, точно совпадающую по набору индексов."""
        for spec in self._row_phase_specs_by_patch.get(patch, []):
            if set(spec.indices) == set(indices):
                return spec
        return None

    def _get_row_phase_specs_intersecting(self, patch: RowPatch, indices: Set[int]) -> List[RowPhaseSpec]:
        """Возвращает спецификации, чьи индексы пересекаются с переданными."""
        return [
            spec for spec in self._row_phase_specs_by_patch.get(patch, [])
            if set(spec.indices) & indices
        ]

    def _expand_patches_via_interpatch(self, patch_render_rows: Dict[RowPatch, List[PlaybackRenderRow]]):
        """Расширяет набор патчей, если они входят в interpatch-группы."""
        expanded = defaultdict(list)
        for patch, rows in patch_render_rows.items():
            expanded[patch].extend(rows)

        affected_groups = set()
        for patch, rows in patch_render_rows.items():
            spec = self.get_interpatch_spec(patch)
            if spec:
                linked = set(spec.linked_shifts.keys())
                if any(row.fixture_index in linked for row in rows):
                    affected_groups.add(spec)
        for spec in affected_groups:
            linked = set(spec.linked_shifts.keys())
            for patch in spec.ordered_patches:
                all_rows = self.get_rows(patch)
                for row in all_rows:
                    if row.fixture_index in linked and row not in expanded[patch]:
                        expanded[patch].append(row)
        return dict(expanded)

    def _sync_row_phase_for_interpatch(self, patches: List[RowPatch], render_rows: List[PlaybackRenderRow]):
        """Копирует row phase с мастер-патча на slave-патчи перед созданием/обновлением interpatch."""
        master_patch = patches[0]
        master_specs = []
        for row in render_rows:
            if row.patch == master_patch:
                spec = self.get_row_phase_spec(row.patch, row.fixture_index)
                if spec and spec not in master_specs:
                    master_specs.append(spec)

        for master_spec in master_specs:
            indices = master_spec.indices
            for slave_patch in patches[1:]:
                slave_rows = self.get_rows(slave_patch)
                target_rows = [r for r in slave_rows if r.fixture_index in indices]
                if len(target_rows) < 2:
                    continue
                cmd = self._prepare_row_phase_command(
                    slave_patch,
                    indices,
                    master_spec.amount,
                    master_spec.curve,
                    master_spec.inverted,
                    dots=master_spec.dots,
                )
                if cmd:
                    self.execute_command(cmd)

    def remove_interpatch_linked_rows(self, render_rows: List[PlaybackRenderRow]):
        if not render_rows:
            return
        specs = {self.get_interpatch_spec(row.patch) for row in render_rows}
        specs.discard(None)
        for spec in specs:
            indices_to_remove = set()
            for row in render_rows:
                if self.get_interpatch_spec(row.patch) is spec:
                    indices_to_remove.add(row.fixture_index)
                    # Если строка в row phase, добавляем все индексы этой спецификации
                    rp_spec = self.get_row_phase_spec(row.patch, row.fixture_index)
                    if rp_spec:
                        indices_to_remove.update(rp_spec.indices)
            new_shifts = {idx: val for idx, val in spec.linked_shifts.items() if idx not in indices_to_remove}
            if not new_shifts:
                self.clear_interpatch_phase(spec.master_patch)
            else:
                cmd = CommandUpdateInterpatchSpec(self, spec, linked_shifts=new_shifts)
                self.execute_command(cmd)

    def _activate_rows_if_needed(self, render_rows: List[PlaybackRenderRow]):
        """Активирует неактивные строки, если они есть."""
        inactive = [row for row in render_rows if not row.active]
        if inactive:
            self.set_row_active(True, inactive)

    def _get_dots_source_rows(self, render_rows: List[PlaybackRenderRow]):
        sources = []
        seen = set()
        for row in render_rows:
            spec = self.get_row_phase_spec(row.patch, row.fixture_index)
            if spec:
                master_index = min(spec.indices)
                source = self.get_row(row.patch, master_index)
            else:
                source = row
            if source and id(source) not in seen:
                seen.add(id(source))
                sources.append(source)
        return sources

    def _filter_dots_for_rows(
            self,
            rows_dots: Dict[PlaybackRenderRow, List[DMXRenderDot]],
            dots: List[DMXRenderDot],
            reverse=False):
        filtered = {}
        for row, row_dots in rows_dots.items():
            intersection = set(dots) & set(row_dots)
            filtered[row] = sorted(intersection, key=lambda dot: dot.x, reverse=reverse)
        return filtered

    def _prepare_row_phase_command(
            self,
            patch: RowPatch,
            indices: List[int],
            amount: float,
            curve: RowPhaseCurveType,
            inverted: bool,
            dots=None
            ) -> Union[CommandUpdateRowPhaseSpec, CommandCreateRowPhaseSpec]:
        """Возвращает команду для создания/обновления row phase или None, если изменений нет."""
        existing_spec = self._get_existing_row_phase_spec(patch, indices)
        if existing_spec:
            return CommandUpdateRowPhaseSpec(
                self,
                existing_spec,
                amount=amount,
                curve=curve,
                inverted=inverted,
                dots=existing_spec.dots if dots is None else dots,
            )
        else:
            new_spec = RowPhaseSpec(
                patch=patch,
                indices=indices,
                amount=amount,
                curve=curve,
                inverted=inverted,
                dots=dots if dots is not None else RenderDots([]),
            )
            return CommandCreateRowPhaseSpec(self, new_spec)

    def _prepare_interpatch_command(
            self,
            existing_spec: InterpatchSpec,
            patches: List[RowPatch],
            linked_shifts: Dict[int, float]
            ) -> Union[CommandUpdateInterpatchSpec, CommandCreateInterpatchSpec]:
        """Возвращает команду для создания/обновления interpatch спецификации."""
        if existing_spec:
            new_shifts = existing_spec.linked_shifts.copy()
            new_shifts.update(linked_shifts)
            return CommandUpdateInterpatchSpec(
                self, existing_spec, linked_shifts=new_shifts
            )
        else:
            new_spec = InterpatchSpec(
                ordered_patches=patches,
                linked_shifts=linked_shifts,
            )
            return CommandCreateInterpatchSpec(self, new_spec)
