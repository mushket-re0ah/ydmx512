from kivy.properties import (
    ObjectProperty, NumericProperty, ListProperty, BooleanProperty, AliasProperty
)
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.graphics import *
from kivy.utils import boundary
from kivy.clock import Clock
from libs.uix.layouts import StencilBoxLayout
from ui.components.rotary_button import PanRotaryButton
from ui.components.button import OptionToggleButton, OptionToggleButtonContextMenu
from ui.components.input.numeric_input import NumericInput
from libs.uix.layouts import WindowModalBoxLayout
from database.playback import RowPlayback
from database.playback.renderer import render_utils
from database.patch import RowPatch
from database.playback.renderer.render_data import PlaybackRenderRow
from database import db
from ui.mdi.editor.automation.tools import RowPhaseTool, DiscardAllTool, MoveDotsByNumericInputTool
from database.phase_curve_type import RowPhaseCurveType
from libs.dmx512_render import DMXRenderDot
from typing import List, Optional, Set
from misc import colorscheme as cs
from libs.properties import EnumProperty


Builder.load_file("ui/mdi/editor/automation/toolbar/toolbar.kv")


class PhaseCurveTypeCreateMenuCanvas(Widget):
    dots = ListProperty()

    def __init__(self, **kwargs):
        self.draw_ev = Clock.create_trigger(self.draw, -1)
        super().__init__(**kwargs)

    def draw(self, _):
        if not self.parent:
            return
        self.canvas.after.remove_group("render_lines")
        self.canvas.after.remove_group("dots")
        self.draw_render_lines()
        self.draw_dots()

    RENDER_MASTER_LINE_WIDTH = NumericProperty("2dp")
    def draw_render_lines(self):
        x = self.x
        y = self.y

        points = []
        dots = list(sorted(self.dots, key=lambda x: x[0]))
        for i in range(len(dots) - 1):
            next_x_dot = i + 1
            points.append(x + dots[i][0] * self.width)
            points.append(y + dots[i][1] * self.height)
            points.append(x + dots[next_x_dot][0] * self.width)
            points.append(y + dots[next_x_dot][1] * self.height)
        with self.canvas.after:
            Color(1, 1, 1, 1, group="render_lines")
            SmoothLine(width=2, points=points, group="render_lines")

    def draw_dots(self):
        dot_radius = 5
        dot_size = (10, 10)

        x = self.x - dot_radius
        y = self.y - dot_radius

        with self.canvas.after:
            Color(1, 1, 1, 1, group="dots")
        for x_dot, y_dot in self.dots:
            x_pos = x + x_dot * self.width
            y_pos = y + y_dot * self.height
            with self.canvas.after:
                SmoothEllipse(pos=(x_pos, y_pos), size=dot_size, group="dots")

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self.add_dot(touch)
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self.add_dot(touch)
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            return True
        return super().on_touch_up(touch)

    def add_dot(self, touch):
        x, y = touch.pos
        x, y = x - self.x, y - self.y
        x, y = x / self.width, y / self.height
        x = round(round(boundary(x, 0.0, 1.0) / 0.05) * 0.05, 2)
        y = round(round(boundary(y, 0.0, 1.0) / 0.05) * 0.05, 2)
        for xy in self.dots[:]:
            if xy[0] == x:
                self.dots.remove(xy)
        if (x, y) not in self.dots:
            self.dots.append((x, y))

    def on_dots(self, _, dots: list):
        self.draw_ev()


class PhaseCurveTypeCreateMenu(WindowModalBoxLayout):
    pass


class PhaseCurveTypeMenu(OptionToggleButtonContextMenu):
    def open_create_menu(self):
        modal = PhaseCurveTypeCreateMenu()
        modal.open(None)


class PhaseCurveTypeOptionButton(OptionToggleButton):
    modal_cls = ObjectProperty(PhaseCurveTypeMenu)
    state = ObjectProperty(db.phase_curve_type.get_default_row())

    def on_state(self, _, state: RowPhaseCurveType):
        self.text = state.title

    def get_state_step(self, direction):
        keys = tuple(db.phase_curve_type.rows.keys())
        values = tuple(db.phase_curve_type.rows.values())
        i = values.index(self.state)
        i = (i + direction) % len(keys)
        return db.phase_curve_type.rows[keys[i]]

    def _make_state_menu_data(self, modal) -> list:
        return [{
            "text": curve.title,
            "modal": modal,
            "state_button": self,
            "state_button_state": curve,
        } for curve in db.phase_curve_type.rows.values()]


class NumericInputDotX(NumericInput):
    def set_value(self, value: int):
        if value is not None:
            value = value - 1
        super().set_value(value)

    def _value_to_str(self, value: int):
        if value is None:
            return ""
        return str(value + 1)

    def _str_to_value(self, text: str):
        if text in ("", "-"):
            if self.allow_empty:
                return None
            return self.default_value - 1 if self.default_value else None
        value = float(text) if self.input_filter == "float" else int(float(text))
        value -= 1
        return self._value_bounds(value)


class AutomationToolbar(StencilBoxLayout):
    playback = ObjectProperty(None, allownone=True, rebind=True)
    active_patch: List[RowPatch] = ListProperty([])

    automation = ObjectProperty(rebind=True)

    fixture_selected_count = NumericProperty(0)
    clear_render_mode = BooleanProperty(False)

    toggle_fixture_presets = ObjectProperty()
    btn_phase = ObjectProperty()
    toggle_phase_curve = ObjectProperty()
    input_phase_amount = ObjectProperty()
    btn_phase_direction = ObjectProperty()
    input_zoom_y = ObjectProperty()
    input_dot_x = ObjectProperty()
    input_dot_y = ObjectProperty()

    selected_master_row_phase_spec = ObjectProperty(None, allownone=True, rebind=True)

    def _set_master_row_phase_spec(self, _, master_selected_render_row: Optional[PlaybackRenderRow]):
        if master_selected_render_row:
            self.selected_master_row_phase_spec = master_selected_render_row.row_phase_spec
        else:
            self.selected_master_row_phase_spec = None

    def on_kv_post(self, _):
        self.automation.row_panel.bind(
            dots_selected=self.update_dots_data,
            master_selected_render_row=self._set_master_row_phase_spec
        )
        self.automation.editor_content.bind(on_render_changed=self._on_render_changed)

    def on_active_patch(self, _, active_patch: List[RowPatch]):
        self.fixture_selected_count = len(set(patch.fixture for patch in active_patch))

    def on_clear_render_mode(self, *args):
        self.automation.row_panel.dispatch_row_change()

    def _on_render_changed(self, _, renderer):
        self.update_dots_data()

    menu_preset_fixture = None
    def open_menu_preset_fixture(self):
        if self.menu_preset_fixture:
            return
        fixture_count = self.fixture_selected_count
        if not(0 < fixture_count <= 1):
            return
        from ui.mdi.editor.automation.toolbar.menu_preset_fixture import MenuPresetFixture
        row_panel = self.automation.row_panel
        menu = MenuPresetFixture(
            row_panel=row_panel,
            patch=self.active_patch[0],
            category_key=self.active_patch[0].fixture
        )
        menu.bind(
            on_open=self.set_toggle_fixture_presets_down,
            on_dismiss=self.set_toggle_fixture_presets_normal,
        )
        menu.open(self.toggle_fixture_presets)
        self.menu_preset_fixture = menu

    def close_menu_preset_fixture(self):
        if self.menu_preset_fixture:
            self.menu_preset_fixture.dismiss()
            self.menu_preset_fixture = None

    def set_toggle_fixture_presets_down(self, _):
        self.toggle_fixture_presets.is_down = True

    def set_toggle_fixture_presets_normal(self, _):
        self.toggle_fixture_presets.is_down = False

    def set_row_phase(self, active: bool=True):
        row_panel = self.automation.row_panel
        if not row_panel.allow_row_phase:
            return

        automation = self.automation
        if not automation.check_tool(RowPhaseTool):
            automation.set_tool(RowPhaseTool,
                                curve=self.toggle_phase_curve.state,
                                inverted=self.btn_phase_direction.is_down)
        if active:
            automation.tool_action("on_value_change", self.input_phase_amount.value)
            self.btn_phase.is_down = True
        else:
            automation.tool_action("clear_phase")

    def on_press_btn_row_phase(self):
        if self.btn_phase.is_down:
            self.set_row_phase()
        else:
            self.set_row_phase(False)

    def discard_all(self):
        self.automation.set_tool(DiscardAllTool)

    def on_touch_up(self, touch):
        if self.automation.check_tool(RowPhaseTool):
            self.automation.tool_action("finish")
        return super().on_touch_up(touch)

    processing_sync_data = BooleanProperty(False)
    def update_dots_data(self, *args):
        self.processing_sync_data = True
        dots = self.automation.row_panel.dots_selected
        if not dots:
            self.input_dot_x.value = None
            self.input_dot_y.value = None
            self.processing_sync_data = False
            return
        first_dot = min(dots, key=lambda d: d.x)
        self.input_dot_x.value = self.automation.row_panel.xy_grid.to_frame_x(first_dot.x)
        self.input_dot_y.value = self.automation.row_panel.xy_grid.to_frame_y(first_dot.y)
        self.processing_sync_data = False

    def set_dot_pos_by_input(self) -> bool:
        if not self.automation.row_panel.dots_selected:
            return False
        if self.processing_sync_data:
            return False
        x = self.input_dot_x.value
        y = self.input_dot_y.value
        if x is None:
            x = 0
        if y is None:
            y = 0
        if self.automation.check_tool(None):
            self.automation.set_tool(MoveDotsByNumericInputTool)
        if self.automation.check_tool(MoveDotsByNumericInputTool):
            self.automation.tool_action("update_pos", x, y)
            return True
        return False

    def set_dot_x_by_input(self):
        if self.set_dot_pos_by_input() and not self.input_dot_x.focus:
            self.cancel_input_session()

    def set_dot_y_by_input(self):
        if self.set_dot_pos_by_input() and not self.input_dot_y.focus:
            self.cancel_input_session()

    def cancel_input_session(self):
        if self.automation.check_tool(MoveDotsByNumericInputTool):
            self.automation.tool_action("finish")
