from kivy.utils import boundary
from libs.dmx512_render import DMXRenderDot, InterpolationType
from libs.sdl2_keyboard import manager as keyboard_manager
from database.playback import PlaybackRenderRow
from database.playback.renderer import render_utils
from database.playback.renderer.render_data import RowPhaseSpec, RenderDots
from database.patch import RowPatch
from database.phase_curve_type import RowPhaseCurveType
from presets.param_presets import ParamPresetData
from presets.fixture_presets import FixturePresetData
from misc import dmx_utils
from typing import List
from misc import logger


class EditorTool:
    requires_session = True
    auto_execute = False

    def __init__(self, automation):
        self.automation = automation
        self.renderer = automation.playback.renderer
        self.xy_grid = self.renderer.xy_grid
        self.row_panel = automation.row_panel

    def finish(self):
        self.automation.set_tool(None)

    def execute(self):
        self.finish()


class AddDotTool(EditorTool):
    def on_touch_down(self, touch, source_widget):
        frame_x, value_y = source_widget.to_quant_coords(*touch.pos, ignore_dot_radius=False)
        self._start_quant = (frame_x, value_y)

        dot_type = InterpolationType.SPLINE if keyboard_manager.check_shift() else InterpolationType.LINEAR

        selected_rows = self.row_panel.selected_render_rows
        if not selected_rows:
            self.finish()
            return

        norm_x = self.row_panel.normalize_frame_x_with_row_phase(frame_x, source_widget.data_row)
        norm_y = self.xy_grid.to_normalized_y(value_y)

        created_dots, success = self.renderer.add_dot_by_x(norm_x, norm_y, dot_type, selected_rows)
        if success:
            self.row_panel.dots_selected = created_dots

    def on_touch_move(self, touch, source_widget):
        self.automation.set_tool(MoveDotsTool, self._start_quant)

    def on_touch_up(self, touch, source_widget):
        self.finish()


class SetDotTypeTool(EditorTool):
    def on_touch_down(self, touch, source_widget):
        selected_dots = self.row_panel.dots_selected
        if not selected_dots:
            self.finish()
            return

        sorted_dots = sorted(selected_dots, key=lambda d: d.x)
        current_type = sorted_dots[0].dot_type
        new_type = InterpolationType.get_next_type(current_type)

        selected_rows = self.row_panel.selected_render_rows
        if not selected_rows:
            self.finish()
            return

        new_dots = self.renderer.set_dot_type(selected_dots, new_type, selected_rows)
        if new_dots is not None:
            self.row_panel.dots_selected = new_dots

        self.finish()


class RemoveDotTool(EditorTool):
    def on_touch_down(self, touch, source_widget):
        frame_x, _ = source_widget.to_quant_coords(*touch.pos, ignore_dot_radius=False)

        selected_rows = self.row_panel.selected_render_rows
        if not selected_rows:
            self.finish()
            return

        norm_x = self.row_panel.normalize_frame_x_with_row_phase(frame_x, source_widget.data_row)
        self.renderer.remove_dot_by_x(norm_x, selected_rows)
        self.finish()


class MoveDotsTool(EditorTool):
    start_quant = None
    start_positions = None
    def __init__(self, automation, start_quant=None):
        super().__init__(automation)
        self.start_quant = start_quant
        self.start_positions = {
            dot: (dot.x, dot.y)
            for dot in self.row_panel.dots_selected
        }

    def on_touch_down(self, touch, source_widget):
        self.start_quant = source_widget.to_quant_coords(*touch.pos, ignore_dot_radius=False)

    def on_touch_move(self, touch, source_widget):
        current_quant = source_widget.to_quant_coords(*touch.pos, ignore_dot_radius=True)
        diff_x = current_quant[0] - self.start_quant[0]
        diff_y = current_quant[1] - self.start_quant[1]

        if diff_x == 0 and diff_y == 0:
            return

        selected_rows = self.row_panel.selected_render_rows
        selected_dots = self.row_panel.dots_selected
        if not selected_rows or not selected_dots:
            return

        norm_diff_x = self.xy_grid.to_normalized_x(diff_x, allow_negative=True)
        norm_diff_y = self.xy_grid.to_normalized_y(diff_y, allow_negative=True)

        self.renderer.move_dot(
            selected_rows, selected_dots, self.start_positions,
            norm_diff_x, norm_diff_y
        )

    def on_touch_up(self, touch, source_widget):
        self.finish()


class MoveDotsByNumericInputTool(EditorTool):
    def __init__(self, automation):
        super().__init__(automation)
        self.selected_rows = self.row_panel.selected_render_rows
        self.selected_dots = self.row_panel.dots_selected
        if not self.selected_dots:
            self.finish()
            return
        reference_dot = min(self.selected_dots, key=lambda d: d.x)
        self.initial_x = self.xy_grid.to_frame_x(reference_dot.x)
        self.initial_y = self.xy_grid.to_frame_y(reference_dot.y)
        self.start_positions = {
            dot: (dot.x, dot.y) for dot in self.selected_dots
        }

    def update_pos(self, new_x: int, new_y: int):
        diff_x = new_x - self.initial_x
        diff_y = new_y - self.initial_y

        if diff_x == 0 and diff_y == 0:
            return

        norm_diff_x = self.xy_grid.to_normalized_x(diff_x, allow_negative=True)
        norm_diff_y = self.xy_grid.to_normalized_y(diff_y, allow_negative=True)

        self.renderer.move_dot(
            self.selected_rows, self.selected_dots, self.start_positions,
            norm_diff_x, norm_diff_y
        )


class SelectAreaTool(EditorTool):
    requires_session = False

    def on_touch_down(self, touch, source_widget):
        self.start_quant = source_widget.to_quant_coords(*touch.pos)
        self.last_quant = self.start_quant
        self.row_panel.unselect_all()
        self.row_panel.start_area_selection(self.start_quant, source_widget.data_row)

    def on_touch_move(self, touch, source_widget):
        current = source_widget.to_quant_coords(*touch.pos, ignore_dot_radius=True)
        area_width = boundary(current[0] - self.start_quant[0],
                              -self.start_quant[0],
                              self.xy_grid.last_x_frame - self.start_quant[0])

        area_height = boundary(current[1] - self.start_quant[1],
                               -self.start_quant[1],
                               255 - self.start_quant[1])
        self.row_panel.update_area_selection(self.start_quant, (area_width, area_height), source_widget.data_row)
        self.last_quant = current

    def on_touch_up(self, touch, source_widget):
        self.row_panel.stop_area_selection()
        self.finish()


class RowPhaseTool(EditorTool):
    def __init__(self, automation, curve: RowPhaseCurveType, inverted: bool):
        super().__init__(automation)
        self.curve = curve
        self.inverted = inverted

    def on_value_change(self, amount: float):
        selected_rows = self.row_panel.selected_render_rows
        if not selected_rows:
            return
        self.renderer.apply_row_phase(
            selected_rows,
            amount,
            self.curve,
            self.inverted
        )

    def clear_phase(self):
        selected_rows = self.row_panel.selected_render_rows
        if not selected_rows:
            return
        self.renderer.clear_row_phase(selected_rows)


class InterpatchPhaseTool(EditorTool):
    def __init__(self, automation, render_rows: List[PlaybackRenderRow]):
        super().__init__(automation)
        self.render_rows = render_rows

    def on_value_change(self, amount: float):
        if not self.render_rows:
            return
        self.renderer.set_phase_interpatch_x(amount, self.render_rows)

    def clear_phase(self):
        if not self.render_rows:
            return
        self.renderer.remove_interpatch_linked_rows(self.render_rows)


class PasteTool(EditorTool):
    auto_execute = True

    def __init__(self, automation, render_rows: List[PlaybackRenderRow]):
        super().__init__(automation)
        self.render_rows = render_rows

    def execute(self):
        cursor_frame = self.automation.cursor_frame
        dots = []
        for dot_info in self.row_panel.clipboard_data:
            x, y, dot_type = dot_info
            norm_x = self.xy_grid.to_normalized_x(x + cursor_frame)
            norm_y = self.xy_grid.to_normalized_y(y)
            created_dots, success = self.renderer.add_dot_by_x(norm_x, norm_y, dot_type, self.render_rows)
            if success:
                for dot in created_dots:
                    if dot not in dots:
                        dots.append(dot)
        if dots:
            self.row_panel.dots_selected = dots
        self.finish()


class RemoveSelectedDotsTool(EditorTool):
    auto_execute = True

    def execute(self):
        dots_selected = self.row_panel.dots_selected
        render_rows = self.row_panel.selected_render_rows
        self.renderer.remove_dot(render_rows, dots_selected)
        self.finish()


class DiscardRowTool(EditorTool):
    auto_execute = True

    def __init__(self, automation, render_rows: List[PlaybackRenderRow]):
        super().__init__(automation)
        self.render_rows = render_rows

    def execute(self):
        render_rows = self.render_rows

        spec = next((row.row_phase_spec for row in render_rows if row.row_phase_spec), None)
        if spec:
            master_index = min(spec.indices)
            master_row = self.renderer.get_row(spec.patch, master_index)
            group_rows = [self.renderer.get_row(spec.patch, index) for index in spec.indices]

            self.renderer.clear_rows([master_row], deactivate=False)
            self.renderer.set_row_active(False, group_rows)
            dmx_utils.set_dmx_by_rows({row: None for row in group_rows})
        else:
            self.renderer.clear_rows(render_rows, deactivate=True)
            dmx_utils.set_dmx_by_rows({row: None for row in render_rows})
        self.finish()


class DiscardAllTool(EditorTool):
    auto_execute = True

    def execute(self):
        render_rows = self.row_panel.rows_data_manager.get_all_render_rows()
        self.renderer.clear_rows(render_rows, deactivate=True, clear_phases=True)
        dmx_utils.set_dmx_by_rows({row: None for row in render_rows})
        self.finish()


class SetRowActiveTool(EditorTool):
    auto_execute = True

    def __init__(self, automation, active: bool, render_rows: List[PlaybackRenderRow]):
        super().__init__(automation)
        self.active = active
        self.render_rows = render_rows

    def execute(self):
        self.renderer.set_row_active(self.active, self.render_rows)
        self.finish()


class LoadParamPresetTool(EditorTool):
    auto_execute = True

    def __init__(self, automation, preset: ParamPresetData, render_rows: List[PlaybackRenderRow]):
        super().__init__(automation)
        self.preset = preset
        self.render_rows = render_rows

    def execute(self):
        dots = self.preset.dots

        self.renderer.clear_rows(self.render_rows)
        for x, y, dot_type in dots:
            self.renderer.add_dot_by_x(x, y, InterpolationType(dot_type), self.render_rows)
        self.renderer.set_row_active(True, self.render_rows)

        self.finish()


class LoadFixturePresetTool(EditorTool):
    auto_execute = True

    def __init__(self, automation, preset: FixturePresetData, patch: RowPatch):
        super().__init__(automation)
        self.preset = preset
        self.patch = patch

    def execute(self):
        rows = self.renderer.get_rows(self.patch)

        self.renderer.clear_rows(rows, deactivate=False, clear_phases=True)

        for row, row_data in zip(rows, self.preset.rows):
            for x, y, dot_type_value in row_data.dots:
                dot_type = InterpolationType(dot_type_value)
                self.renderer.add_dot_by_x(x, y, dot_type, [row])
            self.renderer.set_row_active(row_data.active, [row])

        for phase_data in self.preset.phases:
            spec = RowPhaseSpec(
                patch=self.patch,
                indices=phase_data.indices,
                amount=phase_data.amount,
                curve=phase_data.curve,
                inverted=phase_data.inverted,
                dots=RenderDots([
                    DMXRenderDot(x, y, InterpolationType(t)) for (x, y, t) in phase_data.dots
                ])
            )
            self.renderer.add_row_phase_spec(spec)

        self.finish()
