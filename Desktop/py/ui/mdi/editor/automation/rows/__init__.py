from collections import defaultdict
from typing import TYPE_CHECKING, Any, Callable, DefaultDict, Dict, FrozenSet, List, Optional, Set, Tuple, TypedDict, Union

from kivy.clock import Clock
from kivy.input.motionevent import MotionEvent
from kivy.lang import Builder
from kivy.properties import AliasProperty, BooleanProperty, ListProperty, ObjectProperty
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.widget import Widget

from database.fixture import RowFixture
from database.fixture_param import RowFixtureParam
from database.patch import RowPatch
from database.playback import PlaybackRenderRow
from database.playback.playback import RowPlayback
from database.playback.renderer import PlaybackRenderer, render_utils
from libs import logger
from libs.dmx512.misc import FullAddress
from libs.dmx512_render import DMXRenderDot
from libs.dmx512_render.misc import InterpolationType, XYGrid
from libs.sdl2_keyboard import manager as keyboard_manager
from libs.uix.recycle_restricted_scrollview import RecycleRestrictedScrollView
from libs.uix.scroll_layout import ScrollLayout
from misc import dmx_utils
from ui.mdi.editor.automation.rows.row import RowParam  # lazy kv import initialize
from ui.mdi.editor.automation.rows.row_data import RowParamData, RowsDataManager
from ui.mdi.editor.automation.tools import PasteTool, RemoveSelectedDotsTool

if TYPE_CHECKING:
    from ui.mdi.editor.automation import Automation

Builder.load_file("ui/mdi/editor/automation/rows/row_panel.kv")


class _ParamsMapEntry(TypedDict):
    patch_group: List[RowPatch]
    fixture_index: Dict[RowPatch, List[int]]
    fixture_param: Optional[RowFixtureParam]
_GroupKey = Union[
    Tuple[RowFixtureParam, RowFixture],
    Tuple[RowFixtureParam, None],
    Tuple[RowPatch, int],
    Tuple[RowFixtureParam, int],
]

class _RowParamDataDict(TypedDict):
    patch_group: Tuple[RowPatch, ...]
    fixture_index: Dict[RowPatch, Tuple[int, ...]]
    fixture_param: Optional[RowFixtureParam]
    address_list: Dict[FullAddress, bool]
    render_rows_by_address: Dict[FullAddress, Tuple[PlaybackRenderRow, ...]]
    render_rows: Tuple[PlaybackRenderRow, ...]


class RowPanel(ScrollLayout):
    box: RecycleBoxLayout = ObjectProperty()
    scrollview: RecycleRestrictedScrollView = ObjectProperty()

    automation: "Automation" = ObjectProperty(rebind=True)
    playback: Optional[RowPlayback] = ObjectProperty(None, allownone=True, rebind=True)
    renderer: Optional[PlaybackRenderer] = AliasProperty(
        lambda self: self.playback.renderer if self.playback else None,
        bind=("playback",)
    )
    xy_grid: Optional[XYGrid] = AliasProperty(
        lambda self: self.renderer.xy_grid if self.playback else None,
        bind=("playback",)
    )
    active_patch: Tuple[RowPatch, ...] = ListProperty()
    has_any_data: bool = BooleanProperty(False, rebind=True)

    def __init__(self, **kwargs: Any):
        self._update_rows_ev = Clock.create_trigger(self._update_rows, -1)
        self.bind(
            playback=self._update_rows_ev,
            active_patch=self._update_rows_ev,
        )
        super().__init__(**kwargs)

    def on_kv_post(self, base_widget: Widget):
        super().on_kv_post(base_widget)
        self.automation.editor_content.bind(on_render_changed=self._on_render_changed)
        self._sync_has_any_data()

    def _on_render_changed(self, _, renderer: PlaybackRenderer):
        self._sync_has_any_data()
        self._sync_selected_dots()

    def _register_active_patch(self):
        for patch in self.active_patch:
            self.renderer.add_patch(patch)

    def _build_params_map(self, agregate:bool=False) -> DefaultDict[_GroupKey, _ParamsMapEntry]:
        params_of_patches: DefaultDict[_GroupKey, _ParamsMapEntry] = defaultdict(
            lambda: {
                "patch_group": [],
                "fixture_index": defaultdict(list),
                "fixture_param": None,
            }
        )
        if agregate:
            logger.error("Агрегация пока не поддерживается")
            for patch in self.active_patch:
                fixture = patch.fixture
                for param_key, indices in fixture.param_map.items():
                    if param_key.is_linear:
                        group_key = (param_key.param, fixture)
                    else:
                        group_key = (param_key.param, None)

                    entry = params_of_patches[group_key]
                    entry["patch_group"].append(patch)
                    entry["fixture_index"][patch].extend(indices)
                    entry["fixture_param"] = param_key.param
        else:
            # Без агрегации
            for patch in self.active_patch:
                fixture = patch.fixture
                for param_key, indices in fixture.param_map.items():
                    for idx in indices:
                        if param_key.is_linear:
                            group_key = (patch, idx) # каждый канал отдельно
                        else:
                            group_key = (param_key.param, idx) # агрегация по патчам при одинаковом индексе
                        entry = params_of_patches[group_key]
                        entry["patch_group"].append(patch)
                        entry["fixture_index"][patch].append(idx)
                        entry["fixture_param"] = param_key.param

        return params_of_patches

    def _convert_to_rows_data(
            self,
            params_map: DefaultDict[_GroupKey, _ParamsMapEntry]
        ) -> Tuple[_RowParamDataDict, ...]:
        if self.renderer is None:
            raise RuntimeError()
        result: List[_RowParamDataDict] = []
        for row_data in params_map.values():
            render_rows: List[PlaybackRenderRow] = []
            address_list: Dict[FullAddress, bool] = {}
            render_rows_by_address: DefaultDict[FullAddress, List[PlaybackRenderRow]] = defaultdict(list)
            result_fixture_index: Dict[RowPatch, Tuple[int, ...]] = {}
            for patch, fixture_index_list in row_data["fixture_index"].items():
                for index in fixture_index_list:
                    render_row = self.renderer.get_row(patch, index)
                    if render_row is None:
                        raise RuntimeError()
                    render_rows.append(render_row)
                    fulladdress = FullAddress(patch.universe, patch.start_address + index)
                    address_list[fulladdress] = True
                    render_rows_by_address[fulladdress].append(render_row)
                result_fixture_index[patch] = tuple(fixture_index_list)

            result_render_rows_by_address: Dict[FullAddress, Tuple[PlaybackRenderRow, ...]] = {
                fulladdr: tuple(row_list) for fulladdr, row_list in render_rows_by_address.items()
            }
            result.append({
                "patch_group": tuple(row_data["patch_group"]),
                "fixture_index": result_fixture_index,
                "render_rows": tuple(render_rows),
                "address_list": address_list,
                "render_rows_by_address": result_render_rows_by_address,
                "fixture_param": row_data["fixture_param"],
            })
        return tuple(result)

    rows_data_manager = ObjectProperty(RowsDataManager([]))
    def _update_rows(self, _):
        if not self.playback:
            return
        self._register_active_patch()
        dmx_utils.update_dmx512_by_patch_list(self.renderer, self.active_patch)

        for row_data in self.rows_data_manager:
            row_data.unbind_all()

        manager = RowsDataManager()
        for row_data in self._convert_to_rows_data(self._build_params_map()):
            selected = any(row in self.selected_render_rows for row in row_data["render_rows"])
            data_row = RowParamData(
                row_panel=self,
                automation=self.automation,
                playback=self.playback,
                patch_group=row_data["patch_group"],
                fixture_index=row_data["fixture_index"],
                fixture_param=row_data["fixture_param"],
                render_rows=row_data["render_rows"],
                address_list=row_data["address_list"],
                render_rows_by_address=row_data["render_rows_by_address"],
                selected=selected,
            )
            manager.append(data_row)
        self.rows_data_manager = manager
        self.scrollview.data = manager

    def on_rows_data_manager(self, _, rows_data_manager: RowsDataManager):
        existing_rows: Set[PlaybackRenderRow] = set()
        for data_row in rows_data_manager:
            existing_rows.update(data_row.render_rows)

        self.selected_render_rows = [
            row for row in self.selected_render_rows if row in existing_rows
        ]
        self.property("master_selected_render_row").dispatch(self)
        self._sync_selected_dots()
        self._sync_has_any_data()

    def _sync_selected_dots(self):
        selected_rows_set = set(self.selected_render_rows)
        self.dots_selected = [
            dot for dot in self.dots_selected
            if any(dot in row.dots for row in selected_rows_set)
        ]

    def _sync_has_any_data(self):
        if not self.rows_data_manager:
            self.has_data = False
            return
        self.has_any_data = any(
            row.has_data
            for data_row in self.rows_data_manager
            for row in data_row.render_rows
        )

    def dispatch_row_change(self):
        if self.rows_data_manager:
            self.rows_data_manager.dispatch_row_change()

    def on_touch_up(self, touch: MotionEvent) -> bool:
        self.row_selection = False
        return super().on_touch_up(touch)

    def on_touch_move(self, touch: MotionEvent) -> bool:
        if self.row_selection:
            touch.push()
            touch.apply_transform_2d(self.scrollview.to_local)
            row = self.find_row_by_y(touch.y)
            if row:
                self.select_row_diaposone(self.row_selection_main_data_row, row.data_row)
            touch.pop()
            return False
        return super().on_touch_move(touch)

    def find_row_by_y(self, y: float) -> Optional[RowParam]:
        return next((row_param for row_param in self.box.children if row_param.y <= y <= row_param.top), None)

    def normalize_frame_x_with_row_phase(
            self,
            frame_x: int,
            data_row: RowParamData,
            allow_negative:bool=False
        ) -> float:
        master_row = data_row.master_render_row
        shift = self.renderer.get_row_phase_shift(master_row) if master_row.row_phase_spec else 0.0
        norm_x = self.xy_grid.to_normalized_x(frame_x, allow_negative=allow_negative)
        return (norm_x - shift) % 1.0

    def get_frame_row_shift(self, data_row: RowParamData) -> int:
        master_row = data_row.master_render_row
        shift = self.renderer.get_row_phase_shift(master_row) if master_row.row_phase_spec else 0.0
        return self.xy_grid.to_frame_x(shift, allow_negative=True)

    def create_hotkeys(self) -> Dict[FrozenSet[str], Callable[[], None]]:
        return {
            frozenset({"ctrl", "a"}): self.select_all,
            frozenset({"esc"}): self.unselect_all,
            frozenset({"delete"}): lambda: self.automation.set_tool(RemoveSelectedDotsTool),
            frozenset({"ctrl", "z"}): self.undo,
            frozenset({"ctrl", "shift", "z"}): self.redo,
            frozenset({"ctrl", "y"}): self.redo,
            frozenset({"ctrl", "c"}): self.copy,
            frozenset({"ctrl", "x"}): self.cut,
            frozenset({"ctrl", "v"}): self.paste,
        }

    clipboard_data: Tuple[Tuple[int, int, InterpolationType], ...] = tuple()
    def copy(self) -> bool:
        return self.copy_rows(self.selected_render_rows, False)

    def cut(self):
        if self.copy():
            self.automation.set_tool(RemoveSelectedDotsTool)

    def paste(self):
        self.paste_rows(self.selected_render_rows)

    def copy_rows(self, render_rows: List[PlaybackRenderRow], is_all_row_dots: bool) -> bool:
        if self.xy_grid is None:
            return False

        if not render_rows:
            return False

        if not any(row.has_data for row in render_rows):
            return False

        if is_all_row_dots:
            dots = render_rows[0].dots
        else:
            dots = self.dots_selected
            if not dots:
                return False
            first_row = render_rows[0]
            row_dots = render_utils.get_rows_to_dots_all([first_row])
            dots = set(dots) & set(row_dots[first_row])

        if not dots:
            return False

        min_x = min(dot.x for dot in dots)
        self.clipboard_data = tuple(
            (
                self.xy_grid.to_frame_x(dot.x - min_x),
                self.xy_grid.to_frame_y(dot.y),
                dot.dot_type
            )
            for dot in dots
        )
        return True

    def paste_rows(self, render_rows: List[PlaybackRenderRow]):
        if not self.clipboard_data:
            return
        if not self.playback or not render_rows:
            return
        self.automation.set_tool(PasteTool, render_rows)

    def start_area_selection(self, frame_pos: Tuple[int, int], data_row: RowParamData):
        if self.xy_grid is None:
            return
        master_shift = self.get_frame_row_shift(data_row)

        selected_data_rows = self.rows_data_manager.get_selected_data_rows()
        for row_param in self.box.children:
            if row_param.data_row in selected_data_rows:
                shift = self.get_frame_row_shift(row_param.data_row)
                frame_x = (frame_pos[0] - master_shift + shift) % self.xy_grid.size_x_getter()
                row_param.tact_box.start_selector((frame_x, frame_pos[1]))

    def update_area_selection(
            self,
            frame_pos: Tuple[int, int],
            frame_size: Tuple[int, int],
            data_row: RowParamData):
        if self.xy_grid is None:
            return
        for row_param in self.box.children:
            if row_param.tact_box.selector:
                row_param.tact_box.set_selector_size(frame_size)
        shift = self.get_frame_row_shift(data_row)
        frame_x = (frame_pos[0] - shift) % self.xy_grid.size_x_getter()
        self.select_dots_by_selector((frame_x, frame_pos[1]), frame_size)

    def stop_area_selection(self):
        for row_param in self.box.children:
            if row_param.tact_box.selector:
                row_param.tact_box.stop_selector()

    def select_dots_by_selector(
            self,
            frame_pos: Tuple[int, int],
            frame_size: Tuple[int, int]):
        if self.xy_grid is None:
            return
        render_rows = self.selected_render_rows
        norm_start_x = self.xy_grid.to_normalized_x(min(frame_pos[0], frame_pos[0] + frame_size[0]))
        norm_width = self.xy_grid.to_normalized_x(abs(frame_size[0]))
        norm_start_y = self.xy_grid.to_normalized_y(min(frame_pos[1], frame_pos[1] + frame_size[1]))
        norm_height = self.xy_grid.to_normalized_y(abs(frame_size[1]))
        self.dots_selected = render_utils.get_dots_by_area(
            render_rows,
            norm_start_x, norm_start_y, norm_width, norm_height
        )

    dots_selected: Tuple[DMXRenderDot, ...] = ObjectProperty(tuple())

    selection_main_x: Optional[int] = None

    def select_all(self):
        self.dots_selected = self.get_rows_all_dots(self.selected_render_rows)

    def unselect_all(self):
        self.dots_selected = tuple()

    def select_dots_by_x(self, frame_x: int, data_row: RowParamData) -> Tuple[DMXRenderDot, ...]:
        if self.selection_main_x is not None and keyboard_manager.check_shift():
            precision_x = 1

            start = min(self.selection_main_x, frame_x)
            end = max(self.selection_main_x, frame_x)
            norm_area_x = self.normalize_frame_x_with_row_phase(start - precision_x, data_row)
            norm_area_width = self.normalize_frame_x_with_row_phase((end - start) + 2 * precision_x, data_row)

            self.dots_selected = render_utils.get_dots_by_area(
                self.selected_render_rows,
                norm_area_x, 0.0, norm_area_width, 1.0
            )
        else:
            self.selection_main_x = frame_x
            norm_x = self.normalize_frame_x_with_row_phase(frame_x, data_row)
            dots = render_utils.get_dots_by_x(
                self.selected_render_rows, norm_x
            )
            if keyboard_manager.check_ctrl():
                selected = set(self.dots_selected)
                dots_selected = [
                    dot for dot in self.dots_selected
                    if dot not in dots
                ]
                dots_selected.extend(
                    dot for dot in dots
                    if dot not in selected
                )
                self.dots_selected = tuple(dots_selected)
            elif not set(self.dots_selected) & set(dots):
                self.dots_selected = dots
        return self.dots_selected

    def get_rows_all_dots(self, render_rows: List[PlaybackRenderRow]) -> Tuple[DMXRenderDot, ...]:
        dots: List[DMXRenderDot] = []
        for row in render_rows:
            for dot in row.dots:
                if dot not in dots:
                    dots.append(dot)
        return tuple(dots)

    def set_dots_under_cursor(self, data_row: RowParamData, frame_x: int):
        norm_x = self.normalize_frame_x_with_row_phase(frame_x, data_row)
        dots = render_utils.get_dots_by_x(data_row.render_rows, norm_x)

        group = self._get_row_group(data_row)
        for row_param in self.box.children:
            row_param.tact_box.set_dots_under_cursor(
                dots if row_param.data_row in group else []
            )

    row_selection = BooleanProperty(False)
    row_selection_main_data_row = ObjectProperty(None, allownone=True)

    selected_render_rows: Tuple[PlaybackRenderRow, ...] = ListProperty(rebind=True)
    master_selected_render_row: Optional[PlaybackRenderRow] = AliasProperty(
        lambda self: self.selected_render_rows[0] if self.selected_render_rows else None,
        bind=("selected_render_rows",),
        rebind=True,
        cache=True
    )
    selected_patch_render_rows: Dict[RowPatch, List[PlaybackRenderRow]] = AliasProperty(
        lambda self: render_utils.get_patch_render_rows(self.selected_render_rows),
        bind=("selected_render_rows",),
        rebind=True
    )
    allow_row_phase: bool = AliasProperty(
        lambda self: any(len(v) >= 2 for v in self.selected_patch_render_rows.values()),
        bind=("selected_patch_render_rows",),
        rebind=True
    )
    def _get_row_group(self, data_row: Optional[RowParamData]) -> Set[RowParamData]:
        """Возвращает множество RowParamData, которые должны выделяться вместе с data_row если есть фаза"""
        if data_row is None:
            return set()
        row_phase_spec = data_row.row_phase_spec
        if not row_phase_spec:
            return {data_row}
        group: Set[RowParamData] = set()
        for index in row_phase_spec.indices:
            row = self.renderer.get_row(row_phase_spec.patch, index)
            if row is not None:
                for i_data_row in self.rows_data_manager:
                    if row in i_data_row.render_rows:
                        group.add(i_data_row)
        return group

    def _set_row_select(self, data_row: RowParamData, selected: bool):
        data_row.selected = selected

    def select_one_row(self, data_row: RowParamData, force:bool=False):
        if not force and data_row in self.rows_data_manager.get_selected_data_rows():
            return
        group = self._get_row_group(data_row)
        for i_data_row in self.rows_data_manager:
            self._set_row_select(i_data_row, i_data_row in group)
        self.row_selection_main_data_row = data_row
        self.set_selected_render_rows()

    def select_row_diaposone(self, row_start_data_row: RowParamData, row_end_data_row: RowParamData):
        start_index = self.rows_data_manager.index(row_start_data_row)
        end_index = self.rows_data_manager.index(row_end_data_row)

        min_index = min(start_index, end_index)
        max_index = max(start_index, end_index)

        group: Set[RowParamData] = set()
        for i, data_row in enumerate(self.rows_data_manager):
            if min_index <= i <= max_index:
                group.update(self._get_row_group(data_row))
        for i_data_row in self.rows_data_manager:
            self._set_row_select(i_data_row, i_data_row in group)
        self.set_selected_render_rows()

    def start_row_selection(self, row: RowParamData):
        if keyboard_manager.check_ctrl():
            group = self._get_row_group(row)
            should_select = not any(data_row.selected for data_row in group)
            for data_row in group:
                self._set_row_select(data_row, should_select)
        elif keyboard_manager.check_shift():
            if not self.row_selection_main_data_row:
                self.row_selection_main_data_row = row
                return
            self.select_row_diaposone(self.row_selection_main_data_row, row)
        else:
            self.select_one_row(row, force=True)
            self.row_selection = True
        self.set_selected_render_rows()

    def set_selected_render_rows(self):
        if self.rows_data_manager:
            self.selected_render_rows = self.rows_data_manager.get_selected_render_rows()
        else:
            self.selected_render_rows = tuple()

    def undo(self):
        if self.playback:
            self.renderer.undo()

    def redo(self):
        if self.playback:
            self.renderer.redo()
