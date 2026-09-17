from kivy.app import App
from kivy.properties import (
    ObjectProperty, NumericProperty, BooleanProperty, ListProperty,
    AliasProperty, ColorProperty, VariableListProperty
)
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.graphics import *
from kivy.uix.widget import Widget
from misc import colorscheme as cs
from libs.dmx512_render import DMXRenderDot, InterpolationType
from database.playback import RowPlayback
from database.patch import RowPatch
from kivy.lang import Builder
from ui.components.button import HoverToggleButton
from typing import NamedTuple, List, Tuple, Optional, Set, Dict
from libs.uix.recycle_restricted_scrollview import RecycleRestrictedScrollView
from collections import defaultdict
from libs.mouse_manager.hover import HoverBehavior
from libs.animation import AnimationBehavior
from ui.mdi.editor.automation.rows.row_data import RowParamData, RowsDataManager
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from libs.dmx512.misc import FullAddress
from libs.kivy_utils import AutoUnbindBehavior
from libs.animation import StatefulColorProperty
from libs.uix.layouts import ModalBoxLayout
from libs.mouse_manager import cursor_manager
from libs.sdl2_keyboard import manager as keyboard_manager
from enum import Enum, auto
from database.playback import PlaybackRenderRow
from typing import Tuple, Set, List
from kivy.utils import boundary
from ui.mdi.editor.automation.tools import (
    AddDotTool, SetDotTypeTool, RemoveDotTool, MoveDotsTool, SelectAreaTool,
    InterpatchPhaseTool, SetRowActiveTool
)
from misc import logger
Builder.load_file("ui/mdi/editor/automation/rows/row_param.kv")


class RowDotsSelector(Widget):
    rect_1_size = VariableListProperty([0, 0], length=2)
    rect_1_pos = VariableListProperty([0, 0], length=2)

    rect_2_size = VariableListProperty([0, 0], length=2)
    rect_2_pos = VariableListProperty([0, 0], length=2)

    def set_pixel_rect(self, pos, size):
        self.pos = pos
        self.size = size

        left = self.parent.x + self.parent.padding_x
        right = self.parent.right - self.parent.padding_x

        start = min(self.x, self.right)
        end = max(self.x, self.right)

        vis_start = max(start, left)
        vis_end = min(end, right)
        self.rect_1_pos = [vis_start, self.y]
        self.rect_1_size = [vis_end - vis_start, self.height]

        # выход за левую границу
        if start < left:
            overflow = left - start
            self.rect_2_pos = [right - overflow, self.y]
            self.rect_2_size = [overflow, self.height]
        # выход за правую границу
        elif end > right:
            overflow = end - right
            self.rect_2_pos = [left, self.y]
            self.rect_2_size = [overflow, self.height]
        else:
            self.rect_2_pos = [0, 0]
            self.rect_2_size = [0, 0]


class RowParamTactBox(AnimationBehavior, HoverBehavior, Widget):
    automation = ObjectProperty()
    row_panel = ObjectProperty()
    row_param = ObjectProperty()

    def get_data_row(self):
        return self.row_param.data_row
    data_row = AliasProperty(lambda self: self.row_param.data_row)

    selector: RowDotsSelector = ObjectProperty(None, allownone=True)

    playback = ObjectProperty(None, allownone=True, rebind=True)
    beat_line_points = ListProperty()
    halfbeat_line_points = ListProperty()

    active = BooleanProperty(False)
    row_phase_spec = ObjectProperty(allownone=True)

    draw_ev = None
    dots_under_cursor = ObjectProperty(None, allownone=True)
    focus = BooleanProperty(False)

    background_color = StatefulColorProperty(
        normal=cs.AutomationTactBox.bg,
        states={
            ("focus", "row_phase_spec"): cs.AutomationTactBox.bg_row_phase_focused,
            ("hover", "row_phase_spec"): cs.AutomationTactBox.bg_row_phase_hovered,
            ("active", "row_phase_spec"): cs.AutomationTactBox.bg_row_phase_active,
            "row_phase_spec": cs.AutomationTactBox.bg_row_phase,
            "disabled": cs.AutomationTactBox.bg_disabled,
            "focus": cs.AutomationTactBox.bg_focused,
            "hover": cs.AutomationTactBox.bg_hovered,
            "active": cs.AutomationTactBox.bg_active,
        }
    )

    padding_x = AliasProperty(lambda self: self.automation.TACT_BOX_PADDING_X)
    padding_y = AliasProperty(lambda self: self.automation.TACT_BOX_PADDING_Y)

    LINE_DETECTION_PRECISION = 10
    last_touch_quant_pos = None
    line_under_cursor = False
    selection_start_quant = None

    def on_kv_post(self, _):
        draw_ev = Clock.create_trigger(self.draw, -1)
        self.draw_ev = draw_ev
        self.bind(
            playback=self.draw_ev,
            dots_under_cursor=self.draw_ev,
            size=self.draw_ev,
            pos=self.draw_ev,
        )

    def on_row_panel(self, _, row_panel):
        row_panel.bind(dots_selected=self.draw_ev)

    def on_automation(self, _, automation):
        automation.bind(
            beats_x_pos=self.draw_ev,
            xy_grid=self.draw_ev,
            quant_width=self.draw_ev
        )

    def to_pixel_coords(self, quant_x, quant_y):
        """Конвертирует квантованные координаты (кадр, значение 0-255) в пиксели внутри такт-бокса."""
        x_pixel = self.x + self.padding_x + quant_x * self.automation.quant_width
        y_pixel = self.y + self.padding_y + (quant_y / 255) * (self.height - 2 * self.padding_y)
        return (x_pixel, y_pixel)

    def to_quant_coords(self, x_pixel, y_pixel, ignore_dot_radius=False):
        """Обратное преобразование из пикселей в квантованные координаты."""
        dot_radius = 0 if ignore_dot_radius else self.dot_radius
        quant_x = int((x_pixel - self.x - self.padding_x + dot_radius) / self.automation.quant_width)
        quant_y = int((y_pixel - self.y - self.padding_y + dot_radius) * 255 / (self.height - 2 * self.padding_y))
        return (quant_x, quant_y)

    def to_pixel_size(self, quant_size):
        quant_w, quant_h = quant_size
        qw, qh = self.quant_size
        return (quant_w * qw, quant_h * qh)

    def draw(self, _):
        if not self.parent:
            return
        self.canvas.before.remove_group("render_lines")
        self.canvas.before.remove_group("dots")
        self.draw_beats_lines()
        self.draw_render_lines()
        self.draw_dots()

    BEAT_LINE_WIDTH = NumericProperty(1)
    HALFBEAT_HEIGHT = NumericProperty("4dp")
    def draw_beats_lines(self):
        y = self.y
        with self.canvas.after:
            beat_line_points = []
            halfbeat_line_points = []
            for x_beat, x_halfbeat in self.automation.beats_x_pos:
                x_beat = self.to_widget(x_beat, 0)[0]
                x_halfbeat = self.to_widget(x_halfbeat, 0)[0]
                beat_line_points.extend([x_beat, y, x_beat, self.top, float("nan"), float("nan")])
                halfbeat_line_points.extend([x_halfbeat, y, x_halfbeat, y + self.HALFBEAT_HEIGHT, float("nan"), float("nan")])
            x_beat = self.right - self.padding_x
            beat_line_points.extend([x_beat, self.y, x_beat, self.top, float("nan"), float("nan")])
        self.beat_line_points = beat_line_points
        self.halfbeat_line_points = halfbeat_line_points

    RENDER_MASTER_LINE_WIDTH = NumericProperty("2dp")
    RENDER_SLAVE_LINE_WIDTH = NumericProperty("1dp")
    def _get_patch_render_line_width(self, patch: RowPatch) -> int:
        if patch is self.data_row.master_patch:
            return self.RENDER_MASTER_LINE_WIDTH
        else:
            return self.RENDER_SLAVE_LINE_WIDTH

    def _get_patch_render(self, patch: RowPatch, index: int, frame: int) -> Optional[int]:
        if self.automation.toolbar.clear_render_mode:
            return self.playback.player.get_patch_render(patch, index, frame)
        else:
            render = self.playback.renderer.get_patch_render(patch, index)
            if frame >= len(render):
                return None
            return render[frame] if render else None

    def draw_render_lines(self):
        if not self.playback or not self.row_param or not self.row_param.render_rows or not self.data_row.active:
            return
        quant_width, quant_height = self.quant_size
        x = self.x + self.padding_x
        y = self.y + self.padding_y

        data_row = self.data_row
        for patch in data_row.patch_group:
            line_width = self._get_patch_render_line_width(patch)
            for index in data_row.fixture_index[patch]:
                color = patch.fixture.param_list_unpacked[index].color
                points = []
                for frame in range(self.playback.renderer.xy_grid.size_x_getter() - 1):
                    y0 = self._get_patch_render(patch, index, frame)
                    y1 = self._get_patch_render(patch, index, frame + 1)
                    if y0 is None or y1 is None:
                        continue
                    x0 = frame * quant_width
                    x1 = (frame + 1) * quant_width
                    points.extend([
                        x + x0, y + y0 * quant_height,
                        x + x1, y + y1 * quant_height,
                    ])
                with self.canvas.before:
                    Color(*color, group="render_lines")
                    SmoothLine(width=line_width, points=points, group="render_lines")

    # Словарь для выбора цвета
    dot_color_map = {  # (selected, hovered, type): color
        (False, False, InterpolationType.LINEAR): cs.RowParam.dot_color_linear,
        (True, False, InterpolationType.LINEAR): cs.RowParam.dot_color_linear_selected,
        (False, True, InterpolationType.LINEAR): cs.RowParam.dot_color_linear_hovered,
        (True, True, InterpolationType.LINEAR): cs.RowParam.dot_color_linear_selected_hovered,
        (False, False, InterpolationType.SPLINE): cs.RowParam.dot_color_spline,
        (True, False, InterpolationType.SPLINE): cs.RowParam.dot_color_spline_selected,
        (False, True, InterpolationType.SPLINE): cs.RowParam.dot_color_spline_hovered,
        (True, True, InterpolationType.SPLINE): cs.RowParam.dot_color_spline_selected_hovered,
    }
    def draw_dots(self):
        row_param = self.row_param
        render_rows = row_param.render_rows
        if not render_rows:
            return

        data_row = row_param.data_row

        quant_width, quant_height = self.quant_size
        dot_radius = self.dot_radius
        dot_size = self.dot_size

        x = self.x - dot_radius + self.padding_x
        y = self.y - dot_radius + self.padding_y

        color_map = RowParamTactBox.dot_color_map
        dots_selected = self.row_panel.dots_selected
        dots_hovered = self.dots_under_cursor if self.dots_under_cursor else []
        dots_by_color = defaultdict(list)
        for render_row in render_rows:
            row_phase = self.playback.renderer.get_row_phase_shift(render_row)
            size_x = self.row_panel.xy_grid.size_x_getter()
            row_phase = round(row_phase * size_x)
            dots = render_row.dots
            if not dots:
                continue
            for dot in dots:
                x_dot, y_dot, dot_type = dot
                x_dot = self.row_panel.xy_grid.to_frame_x(x_dot)
                x_dot = (x_dot + row_phase) % self.row_panel.xy_grid.size_x_getter()
                y_dot = self.row_panel.xy_grid.to_frame_y(y_dot)
                x_pos = x + x_dot * quant_width
                y_pos = y + y_dot * quant_height
                base_color = color_map[dot in dots_selected, dot in dots_hovered, dot_type]
                if render_row.patch is data_row.master_patch:
                    color = base_color
                else:
                    color = (*base_color[:3], 0.65)
                dots_by_color[color].append((x_pos, y_pos))
        with self.canvas.before:
            for color, positions in dots_by_color.items():
                Color(*color, group="dots")
                for pos in positions:
                    SmoothEllipse(pos=pos, size=dot_size, group="dots")

    def set_dots_under_cursor(self, dots: Set[DMXRenderDot]):
        self.dots_under_cursor = dots

    def get_quant_size(self) -> Tuple[float, float]:
        quant_width = self.automation.quant_width
        quant_height = (self.height - self.padding_y * 2) / 255
        return (quant_width, quant_height)
    quant_size = AliasProperty(
        get_quant_size, None, bind=["size"]
    )

    def get_dot_size(self) -> Tuple[float, float]:
        quant_width, _ = self.quant_size
        return (quant_width, quant_width)
    dot_size = AliasProperty(
        get_dot_size, None, bind=["quant_size"]
    )

    def get_dot_radius(self) -> float:
        quant_width, _ = self.quant_size
        return max(quant_width / 2, 1)
    dot_radius = AliasProperty(
        get_dot_radius, None, bind=["quant_size"]
    )

    def start_selector(self, quant_pos):
        px_pos = self.to_pixel_coords(*quant_pos)
        self.selector = RowDotsSelector()
        self.add_widget(self.selector)
        self.selector.set_pixel_rect(px_pos, (0, 0))

    def set_selector_size(self, quant_size):
        if self.selector:
            px_size = self.to_pixel_size(quant_size)
            self.selector.set_pixel_rect(self.selector.pos, px_size)

    def stop_selector(self):
        if self.selector:
            self.remove_widget(self.selector)
            self.selector = None

    def on_touch_down(self, touch):
        quant_x, quant_y = self.to_quant_coords(*touch.pos, ignore_dot_radius=False)
        self.last_quant_pos = self.to_quant_coords(*touch.pos, ignore_dot_radius=False)
        if self.collide_point(*touch.pos):
            self.focus = True
            self.row_panel.select_one_row(self.row_param.data_row)
            if touch.button == "left":
                dots = self.row_param.master_render_row.dots
                if self.dots_under_cursor:
                    x, y = self.to_quant_coords(*touch.pos)
                    self.row_panel.select_dots_by_x(x, self.data_row)
                    if not keyboard_manager.check_ctrl():
                        if touch.is_double_tap:
                            if self.row_panel.dots_selected:
                                self.automation.set_tool(SetDotTypeTool)
                        else:
                            self.automation.set_tool(MoveDotsTool)
                elif keyboard_manager.check_ctrl() or self.line_under_cursor or (not dots):
                    self.automation.set_tool(AddDotTool)
                else:
                    self.automation.set_tool(SelectAreaTool)
            elif touch.button == "right":
                if self.dots_under_cursor:
                    self.automation.set_tool(RemoveDotTool)
            self.automation.tool_action("on_touch_down", touch, self)
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.focus:
            self.automation.tool_action("on_touch_move", touch, self)
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.focus:
            self.focus = False
            self.automation.tool_action("on_touch_up", touch, self)
        return super().on_touch_up(touch)

    def on_mouse_move(self, mouse_pos: Tuple[float, float]):
        if self.collide_point(*mouse_pos):
            x, y = self.to_quant_coords(*mouse_pos)
            self.row_panel.set_dots_under_cursor(self.data_row, x)
            self.line_under_cursor = self.check_if_line_under_cursor(x, y)
            if self.dots_under_cursor:
                cursor_manager.set_cursor("hand")
            elif self.line_under_cursor:
                cursor_manager.set_cursor("hand")

    def check_if_line_under_cursor(self, quant_x: int, quant_y: int) -> bool:
        master_patch = self.data_row.master_patch
        index = self.data_row.fixture_index[master_patch][0]
        render_y = self._get_patch_render(master_patch, index, quant_x)
        if not render_y:
            return False
        bottom_y = render_y - self.LINE_DETECTION_PRECISION
        top_y = render_y + self.LINE_DETECTION_PRECISION
        return bottom_y <= quant_y <= top_y


class FixtureParamToggle(HoverToggleButton):
    fixture_param = ObjectProperty()
    render_rows = ObjectProperty()
    row_panel = ObjectProperty()

    def _do_press(self, *args):
        return

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.button == "right":
            self.open_context_menu()
            return False
        return super().on_touch_down(touch)

    def open_context_menu(self):
        from ui.mdi.editor.automation.rows.menu_preset_param_fixture import MenuPresetParamFixture
        MenuPresetParamFixture(
            category_key=self.fixture_param,
            render_rows=self.render_rows,
            row_panel=self.row_panel
        ).open(self)


class RowParamActiveToggle(HoverToggleButton):
    row_param = ObjectProperty()

    def _do_press(self, *args):
        return

    def set_row_active(self):
        self.row_param.automation.set_tool(
            SetRowActiveTool,
            not self.row_param.data_row.active,
            self.row_param.render_rows
        )


class RowParamAddressToggle(HoverToggleButton):
    row_param = ObjectProperty()
    address_list = ObjectProperty()
    fulladdress = ObjectProperty()

    universe = AliasProperty(
        lambda self: self.fulladdress.universe if self.fulladdress else 0,
        bind=["fulladdress"]
    )
    address = AliasProperty(
        lambda self: self.fulladdress.address if self.fulladdress else 0,
        bind=["fulladdress"]
    )

    def on_is_down(self, _, is_down: bool):
        if self.fulladdress:
            self.address_list[self.fulladdress] = is_down


class AddressListBoxContextMenu(ModalBoxLayout):
    row_param = ObjectProperty()
    address_list = ObjectProperty()

    def on_kv_post(self, _):
        for fulladdress in self.address_list:
            toggle = RowParamAddressToggle(
                row_param=self.row_param,
                fulladdress=fulladdress,
                address_list=self.address_list
            )
            self.box.add_widget(toggle)


class AddressListBox(RecycleRestrictedScrollView):
    address_list = ObjectProperty()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.button == "right" and not self.disabled:
            self.open_context_menu()
            return False
        return super().on_touch_down(touch)

    def open_context_menu(self):
        AddressListBoxContextMenu(
            row_param=self.row_param,
            address_list=self.address_list
        ).open(self)


class CheckboxPhaseInterpatchX(HoverToggleButton):
    data_row = ObjectProperty(rebind=True)
    phase_active = BooleanProperty(False)

    def on_data_row(self, _, data_row: RowParamData):
        self.phase_active = data_row.phase_interpatch_x is not None
        data_row.bind(phase_interpatch_x=self.set_phase_active)

    def set_phase_active(self, _, phase_interpatch_x: Optional[int]):
        self.phase_active = phase_interpatch_x is not None

    color = StatefulColorProperty(
        normal=cs.CheckboxPhaseInterpatchX.fg_normal,
        states={
            ("phase_active", "disabled"): cs.CheckboxPhaseInterpatchX.fg_active_disabled,
            "disabled": cs.CheckboxPhaseInterpatchX.fg_disabled,
            "phase_active": cs.CheckboxPhaseInterpatchX.fg_active,
        }
    )


class RowParam(RecycleDataViewBehavior, AutoUnbindBehavior, BoxLayout):
    automation = ObjectProperty()
    row_panel = ObjectProperty()

    address_list_box = ObjectProperty()
    scrollview_address_list_box = ObjectProperty()
    tact_box = ObjectProperty()
    phase_interpatch_input_x = ObjectProperty()

    data_row = ObjectProperty(rebind=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._update_trigger = Clock.create_trigger(self.update, -1)

    def refresh_view_attrs(self, rv, index, data_row):
        if self.data_row is not data_row:
            if self.data_row:
                self.unbind_from(self.data_row)
            self.data_row = data_row
            self.bind_to(
                data_row,
                address_list=self.on_address_list,
                on_data_changed=self._update_trigger
            )
            self.on_address_list(None, data_row.address_list)
            super().refresh_view_attrs(rv, index, data_row)

    def on_address_list(self, _, address_list: Dict[FullAddress, bool]):
        self.address_list_box.data = [
            {
                "row_param": self,
                "fulladdress": fulladdress,
                "address_list": address_list
            }
            for fulladdress in address_list
        ]

    def update(self, *args):
        self.tact_box.draw_ev()
        self.property("data_row").dispatch(self.data_row)

    def _input_set_interpatch_x(self, active: bool=True):
        if not self.data_row.allow_interpatch_phase:
            return
        if not self.row_panel:
            return

        automation = self.automation
        if not automation.check_tool(InterpatchPhaseTool):
            automation.set_tool(InterpatchPhaseTool, self.data_row.get_master_render_rows())
        if active:
            automation.tool_action("on_value_change", self.phase_interpatch_input_x.value)
        else:
            automation.tool_action("clear_phase")

    def on_press_btn_interpatch_phase(self):
        if self.checkbox_phase.is_down:
            self._input_set_interpatch_x()
        else:
            self._input_set_interpatch_x(False)

    def on_touch_up(self, touch):
        if self.automation.check_tool(InterpatchPhaseTool):
            self.automation.tool_action("finish")
        return super().on_touch_up(touch)
