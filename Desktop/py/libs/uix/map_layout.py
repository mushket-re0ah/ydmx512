from kivy.properties import (
    ObjectProperty, NumericProperty, BooleanProperty,
    ListProperty, ColorProperty, ReferenceListProperty,
    VariableListProperty, AliasProperty
)
from kivy.clock import Clock
from kivy.uix.widget import Widget
from libs.uix.workspace_manager import WorkspaceBehavior
from libs.uix.scroll_layout import ScrollLayout
from libs.mouse_manager.hover import NestedHoverBehavior
from libs.animation import AnimationBehavior
from typing import Tuple, Optional, Dict, Set, Iterator
from libs.animation import StatefulColorProperty
from kivy.lang import Builder
from math import ceil, floor
from kivy.graphics.texture import Texture
from libs.kivy_utils import AutoUnbindBehavior, walk_by_children
from libs.sdl2_keyboard import manager as keyboard_manager
from libs.uix import colorscheme as uix_cs
from libs.uix.context_menu import ContextMenu, ContextMenuTemplates
from weakref import WeakKeyDictionary
from libs import logger


Builder.load_string("""
<MapGridItemBehavior>:
    canvas.after:
        Color:
            rgba: self.border_color
        Line:
            width: dp(1)
            rectangle: (self.x, self.y, self.width, self.height)


<_MapLayoutSelector>:
    size_hint: (None, None)
    canvas:
        Color:
            rgba: self.bg_color
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: self.border_color
        Line:
            width: dp(1)
            rectangle: (self.x, self.y, self.width, self.height)


<MapLayout>:  # ScrollLayout
    scrollview: scrollview
    layout: layout
    wrap_layout: wrap_layout

    size_hint: (1, 1)
    scroll_by_content: True
    RestrictedScrollView:
        id: scrollview
        size_hint: (1, 1)
        scroll_by_content: True
        BoxLayout:
            id: wrap_layout
            size_hint: (None, None)
            padding: root.grid_padding
            canvas.before:
                Color:
                    rgba: root.bg_color
                Rectangle:
                    pos: self.pos
                    size: self.size
            RelativeLayout:
                id: layout
                size_hint: (1, 1)
                scrollview: scrollview
                map_layout: root
                canvas.before:
                    Color:
                        rgba: root.grid_color if root.grid_show else (1, 1, 1, 0)
                    Rectangle:
                        texture: root._grid_texture
                        pos: root._grid_render_pos
                        size: root._grid_render_size

<WorkspaceMapLayout>:
    if_contain: False if self.layout is None else len(self.grid_items) > 0
""")


class _GridGeometryItemBehavior(AutoUnbindBehavior):
    map_layout = ObjectProperty(allownone=True)

    grid_x = NumericProperty()
    grid_y = NumericProperty()
    grid_pos = ReferenceListProperty(grid_x, grid_y)

    grid_width = NumericProperty()
    grid_height = NumericProperty()
    grid_size = ReferenceListProperty(grid_width, grid_height)

    def __init__(self, **kwargs):
        self._trigger_update_geometry = Clock.create_trigger(
            self._update_geometry, -1
        )
        super().__init__(**kwargs)
        self.bind(
            grid_pos=self._trigger_update_geometry,
            grid_size=self._trigger_update_geometry,
            map_layout=self._trigger_update_geometry
        )

    def on_kv_post(self, _):
        self._trigger_update_geometry()

    _prev_map_layout = None
    def on_map_layout(self, _, map_layout):
        if self._prev_map_layout:
            self.unbind_from(self._prev_map_layout.layout)
        if map_layout:
            self.bind_to(
                map_layout.layout,
                size=self._trigger_update_geometry
            )
        self._prev_map_layout = map_layout

    def _update_geometry(self, *_):
        if self.map_layout is None:
            return

        self.pos = self.map_layout.cell_to_pixel(self.grid_x, self.grid_y)
        self.size = self.map_layout.grid_size_to_pixel(self.grid_width, self.grid_height)


class MapGridItemBehavior(AnimationBehavior, NestedHoverBehavior, _GridGeometryItemBehavior):
    selectable = BooleanProperty(False)
    selected = BooleanProperty(False)

    _not_selectable = AliasProperty(lambda self: not self.selectable, bind=["selectable"])
    animation_time = 0.0
    border_color = StatefulColorProperty(
        normal=uix_cs.MapGridItemBehavior.border_color_normal,
        states={
            "_not_selectable": (0, 0, 0, 0),
            "selected": uix_cs.MapGridItemBehavior.border_color_is_select,
            "hover": uix_cs.MapGridItemBehavior.border_color_hover
        }
    )


class _MapLayoutSelector(_GridGeometryItemBehavior, Widget):
    bg_color = ColorProperty(uix_cs.MapSelector.bg)
    border_color = ColorProperty(uix_cs.MapSelector.border)


class MapLayout(ScrollLayout, AutoUnbindBehavior):
    scrollview = ObjectProperty()
    layout = ObjectProperty()

    cell_width = NumericProperty("16dp")
    cell_height = NumericProperty("16dp")
    cell_size = ReferenceListProperty(cell_width, cell_height)

    bg_color = ColorProperty(uix_cs.MapLayout.bg)
    grid_padding = VariableListProperty([0, 0, 0, 0], length=4)
    grid_show = BooleanProperty(True)
    grid_color = ColorProperty(uix_cs.MapLayout.grid_color)
    grid_line_width = NumericProperty("1dp")

    grid_spacing_width = NumericProperty(0)
    grid_spacing_height = NumericProperty(0)
    grid_spacing = ReferenceListProperty(grid_spacing_width, grid_spacing_height)

    max_columns = NumericProperty(24)
    max_rows = NumericProperty(24)
    max_grid_size = ReferenceListProperty(max_columns, max_rows)

    selectable = BooleanProperty(True)

    selected = ListProperty()
    grid_items = ListProperty()

    _columns = NumericProperty()
    _rows = NumericProperty()
    _grid_size = ReferenceListProperty(_columns, _rows)

    _grid_texture = ObjectProperty(None, allownone=True)
    _grid_render_pos = VariableListProperty([0, 0], length=2)
    _grid_render_size = VariableListProperty([0, 0], length=2)

    @property
    def _step_x(self) -> float:
        return self.cell_width + self.grid_spacing_width

    @property
    def _step_y(self) -> float:
        return self.cell_height + self.grid_spacing_height

    def __init__(self, *args, **kwargs):
        self._trigger_draw_grid = Clock.create_trigger(self._draw_grid, -1)
        self._trigger_calc_grid_size = Clock.create_trigger(self._calc_grid_size, -1)
        super().__init__(*args, **kwargs)

        self._grid_occupancy = {}
        self._grid_item_geometry = {}

        self._grid_texture_cache_key = None
        self._grid_texture_size = None
        self._grid_texture_buf = None

        self._touched_widget = None
        self._touch_start_cell = None
        self._touch_start_pos = None
        self._touch_selected_start_positions = {}
        self._touch_last_cell = None
        self._touch_delta_cell = (0, 0)

        self._selector = None

    def on_kv_post(self, _):
        super().on_kv_post(_)
        self.bind(
            pos=self._trigger_draw_grid,
            size=self._trigger_draw_grid,
            cell_size=self._trigger_draw_grid,
            grid_show=self._trigger_draw_grid,
            grid_color=self._trigger_draw_grid,
            grid_line_width=self._trigger_draw_grid,
            grid_spacing=self._trigger_draw_grid,
            max_grid_size=self._trigger_draw_grid,
            _grid_size=self._trigger_draw_grid
        )
        self.layout.bind(
            size=self._trigger_draw_grid,
            children=self._trigger_calc_grid_size
        )
        self.scrollview.bind(
            size=self._trigger_draw_grid,
            scroll_x=self._trigger_draw_grid,
            scroll_y=self._trigger_draw_grid,
        )
        self.scrollview.bind(
            size=self._trigger_calc_grid_size
        )
        self._trigger_draw_grid()

    def on_touch_down(self, touch):
        if self.disabled:
            return super().on_touch_down(touch)

        # Сначала дети. Кто первый вернёт True - тот и обработал
        if super().on_touch_down(touch):
            return True

        # Никто из детей не взял, работаем сами
        mouse_pos = self.layout.to_widget(*touch.pos)

        if touch.button == "right":
            self._open_context_menu(touch.pos)
            return True

        touch.grab(self)
        self._touch_start_pos = mouse_pos
        self._touch_start_cell = self.pixel_to_cell(*mouse_pos, ignore_spaces=True)

        widget = self.hit_test(*mouse_pos)
        self._touched_widget = widget
        if widget is not None:
            if not widget.selectable:
                return True

            if keyboard_manager.check_ctrl():
                if widget in self.selected:
                    self.unselect(widget)
                else:
                    self.select(widget, clear=False)
            else:
                if widget not in self.selected:
                    self.select(widget, clear=True)

            self._touch_selected_start_positions = {
                widget: widget.grid_pos[:]
                for widget in self.selected
            }
        else:
            self.clear_selected()
            if self._touch_start_cell is not None:
                self._update_selector(self._touch_start_cell)
        return True

    def on_touch_move(self, touch):
        if self._touch_start_pos is None:
            return super().on_touch_move(touch)
        if self._touch_start_cell is None:
            return True

        mouse_pos = self.layout.to_widget(*touch.pos)
        current_cell = self.pixel_to_cell(*mouse_pos, ignore_spaces=True, allow_outbound=True)
        if current_cell is None:
            return True
        current_x, current_y = current_cell
        if self._touch_last_cell is None:
            self._touch_last_cell = (current_x, current_y)

        prev_x, prev_y = self._touch_last_cell
        if (current_x != prev_x) or (current_y != prev_y):
            if self._selector:
                self._update_selector(current_cell)
            elif self._touched_widget is not None:
                start_x, start_y = self._touch_start_cell
                delta_x = current_x - start_x
                delta_y = current_y - start_y
                self.move_selected(delta_x, delta_y)

        self._touch_last_cell = (current_x, current_y)
        return True

    def on_touch_up(self, touch):
        touch.ungrab(self)
        self._touched_widget = None
        self._touch_start_cell = None
        self._touch_start_pos = None
        self._touch_selected_start_positions = {}
        self._touch_last_cell = None
        if self._selector:
            self.layout.remove_widget(self._selector)
            self._selector = None
        return super().on_touch_up(touch)

    def patch_add_widget(self, widget, index=0, canvas=None):
        if isinstance(widget, MapGridItemBehavior):
            ret = self.layout.add_widget(widget, index, canvas)
            self._bind_grid_item(widget)
            return ret
        return super().patch_add_widget(widget, index, canvas)

    def remove_widget(self, widget, *args, **kwargs):
        if isinstance(widget, MapGridItemBehavior):
            self._unbind_grid_item(widget)
            return self.layout.remove_widget(widget, *args, **kwargs)
        return super().remove_widget(widget, *args, **kwargs)

    def clear_widgets(self, children=None):
        for child in self.layout.children[:]:
            self.remove_widget(child)

    def cell_to_pixel(self, cell_x: int, cell_y: int) -> Tuple[float, float]:
        return (cell_x * self._step_x, cell_y * self._step_y)

    def pixel_to_cell(
            self,
            x: float,
            y: float,
            ignore_spaces: bool=False,
            allow_outbound: bool=False) -> Optional[Tuple[int, int]]:
        """
        Возвращает клетку только если точка находится именно внутри
        клетки, а не в spacing/padding.
        """
        if not allow_outbound and x < 0:
            return None

        cell_x = floor(x / self._step_x)
        inside_x = x - cell_x * self._step_x

        if not allow_outbound and (cell_x < 0 or cell_x >= self._columns):
            return None

        if not ignore_spaces and inside_x >= self.cell_width:
            return None

        local_y = y

        if not allow_outbound and local_y < 0:
            return None

        cell_y = floor(local_y / self._step_y)
        inside_y = local_y - cell_y * self._step_y

        if not allow_outbound and (cell_y < 0 or cell_y >= self._rows):
            return None

        if not ignore_spaces and inside_y >= self.cell_height:
            return None

        return (cell_x, cell_y)

    def grid_size_to_pixel(self, columns: int, rows: int) -> Tuple[float, float]:
        width = (
            columns * self.cell_width
            + max(columns - 1, 0) * self.grid_spacing_width
        )
        height = (
            rows * self.cell_height
            + max(rows - 1, 0) * self.grid_spacing_height
        )
        return (width, height)

    def pixel_to_map_size(self, width: float, height: float) -> Tuple[int, int]:
        available_width = width
        available_height = height

        if available_width <= 0:
            columns = 0
        else:
            columns = floor((available_width + self.grid_spacing_width) / self._step_x)

        if available_height <= 0:
            rows = 0
        else:
            rows = floor((available_height + self.grid_spacing_height) / self._step_y)
        return (columns, rows)

    def get_grid_collisions(
        self,
        grid_x: int,
        grid_y: int,
        grid_width: int,
        grid_height: int,
        exclude=None,
    ):
        selected = set() if exclude is None else {exclude.__self__}
        collisions = set()
        for cell in self._cells_of(grid_x, grid_y, grid_width, grid_height):
            for widget in self._grid_occupancy.get(cell, ()):
                if widget not in selected:
                    collisions.add(widget)
        return collisions

    def can_place(
        self,
        grid_x: int,
        grid_y: int,
        grid_width: int,
        grid_height: int,
        exclude=None,
    ) -> bool:
        if not self._within_bounds(grid_x, grid_y, grid_width, grid_height):
            return False

        selected = set() if exclude is None else {exclude.__self__}
        return self._cells_free(grid_x, grid_y, grid_width, grid_height, selected)

    def find_empty_pos(self, grid_width: int, grid_height: int) -> Optional[Tuple[int, int]]:
        if grid_width > self.max_columns or grid_height > self.max_rows:
            return None

        left, bottom, right, top = self._visible_cell_range()

        # Проход 1: виджет целиком внутри видимой области.
        # Сверху вниз, слева направо, начиная с верхне-левого угла viewport'а.
        y_hi = top - grid_height
        y_lo = bottom
        x_lo = left
        x_hi = right - grid_width + 1

        for grid_y in range(y_hi, y_lo - 1, -1):
            for x in range(x_lo, x_hi + 1):
                if self.can_place(x, grid_y, grid_width, grid_height):
                    return (x, grid_y)

        # Проход 2: наружу от видимой области.
        # Строки чередуются: чуть выше видимой, чуть ниже, ещё выше, ещё ниже...
        max_y = self.max_rows - grid_height
        y_above, y_below = top, bottom - grid_height

        while y_above <= max_y or y_below >= 0:
            for y in (y_above, y_below):
                if 0 <= y <= max_y:
                    for x in range(self.max_columns - grid_width + 1):
                        if self.can_place(x, y, grid_width, grid_height):
                            return (x, y)
            y_above += 1
            y_below -= 1

        return None

    def _visible_cell_range(self) -> Tuple[int, int, int, int]:
        """(left, bottom, right, top) - клетки, пересекающиеся с viewport'ом."""
        sw = max(0, self.wrap_layout.width  - self.scrollview.width)
        sh = max(0, self.wrap_layout.height - self.scrollview.height)

        vx0 = self.scrollview.scroll_x * sw
        vy0 = (1.0 - self.scrollview.scroll_y) * sh
        vx1 = vx0 + self.scrollview.width
        vy1 = vy0 + self.scrollview.height

        eps = 1e-6  # чтобы не захватить лишнюю клетку, если край попал точно в границу
        left   = max(0, int(floor(vx0 / self._step_x)))
        right  = min(self.max_columns - 1, int(floor((vx1 - eps) / self._step_x)))
        bottom = max(0, int(floor(vy0 / self._step_y)))
        top    = min(self.max_rows - 1, int(floor((vy1 - eps) / self._step_y)))
        return left, bottom, right, top

    def clear_selected(self):
        for widget in self.selected:
            widget.selected = False
        self.selected = []

    def unselect(self, widget):
        widget.selected = False
        self.selected = [x for x in self.selected if x is not widget]

    def select(self, widget, clear=True):
        if not self.selectable:
            return

        if not widget.selectable:
            return

        if clear:
            self.clear_selected()
        if widget.selected:
            return
        widget.selected = True
        self.selected = [*self.selected, widget]

    def hit_test(self, x: float, y: float) -> Optional[MapGridItemBehavior]:
        cell = self.pixel_to_cell(x, y, ignore_spaces=True)
        if cell is None:
            return None

        items = self._grid_occupancy.get(cell)
        if not items:
            return None

        for item in items:
            return item
        return None

    def move_selected(self, delta_x: float, delta_y: float):
        positions = self._resolve_drag(self._touch_selected_start_positions, delta_x, delta_y)

        for widget, pos in positions.items():
            widget.grid_pos = pos

    def _resolve_drag(
        self,
        positions: Dict[Widget, Tuple[int, int]],
        delta_x: int,
        delta_y: int,
    ) -> Dict[Widget, Tuple[int, int]]:
        if not positions or (delta_x == 0 and delta_y == 0):
            return positions

        # 1. Fallback: per-widget, с docking и slip-through.
        if delta_x != 0 and delta_y != 0:
            p1 = self._resolve_drag_y(self._resolve_drag_x(positions, delta_x), delta_y)
            p2 = self._resolve_drag_x(self._resolve_drag_y(positions, delta_y), delta_x)
            fallback = min(
                (p1, p2),
                key=lambda p: self._drag_score(positions, p, delta_x, delta_y),
            )
        elif delta_x != 0:
            fallback = self._resolve_drag_x(positions, delta_x)
        else:
            fallback = self._resolve_drag_y(positions, delta_y)

        # 2. Combined jump с клампом - спасает от застревания на промежуточном
        #    препятствии, когда целевая позиция свободна, но per-axis до неё
        #    не доходит.
        cx, cy = self._clamp_delta(positions, delta_x, delta_y)
        if (cx, cy) == (0, 0):
            return fallback
        if not self._combined_target_free(positions, cx, cy):
            return fallback

        jump = {w: (p[0] + cx, p[1] + cy) for w, p in positions.items()}

        # 3. Из двух - что ближе к желаемой дельте.
        #    При равенстве предпочитаем fallback: docking и пристыковка к стенам.
        fallback_score = self._drag_score(positions, fallback, delta_x, delta_y)
        jump_score = self._drag_score(positions, jump, delta_x, delta_y)
        if jump_score < fallback_score:
            return jump
        return fallback

    def _clamp_delta(
            self,
            positions: Dict[Widget, Tuple[int, int]],
            dx: int,
            dy: int) -> Tuple[int, int]:
        if dx > 0:
            limit = min(self.max_columns - (x + w.grid_width)
                        for w, (x, y) in positions.items())
            dx = max(0, min(dx, limit))
        elif dx < 0:
            limit = max(-x for w, (x, y) in positions.items())
            dx = min(0, max(dx, limit))

        if dy > 0:
            limit = min(self.max_rows - (y + w.grid_height)
                        for w, (x, y) in positions.items())
            dy = max(0, min(dy, limit))
        elif dy < 0:
            limit = max(-y for w, (x, y) in positions.items())
            dy = min(0, max(dy, limit))

        return (dx, dy)

    def _combined_target_free(
            self,
            positions: Dict[Widget, Tuple[int, int]],
            dx: int,
            dy: int) -> bool:
        selected = set(positions)
        reserved = set()

        for widget, (x, y) in positions.items():
            nx, ny = x + dx, y + dy
            w, h = widget.grid_width, widget.grid_height

            if not self._cells_free(nx, ny, w, h, selected, reserved):
                return False
            reserved.update(self._cells_of(nx, ny, w, h))

        return True

    def _cells_of(self, x: int, y: int, w: int, h: int) -> Iterator[Tuple[int, int]]:
        """Все клетки, которые занимает прямоугольник."""
        for cy in range(y, y + h):
            for cx in range(x, x + w):
                yield (cx, cy)

    def _within_bounds(self, x: int, y: int, w: int, h: int) -> bool:
        return (x >= 0 and y >= 0
                and x + w <= self.max_columns
                and y + h <= self.max_rows)

    def _cells_free(
            self,
            x: int,
            y: int,
            w: int,
            h: int,
            selected: Set[MapGridItemBehavior],
            reserved: Optional[Set[Tuple[int, int]]]=None) -> bool:
        """Свободны ли все клетки прямоугольника от не-выделенных
        и от уже зарезервированных (для группового разрешения)."""
        for cell in self._cells_of(x, y, w, h):
            if reserved is not None and cell in reserved:
                return False
            for other in self._grid_occupancy.get(cell, ()):
                if other not in selected:
                    return False
        return True

    def _drag_score(
            self,
            start: Dict[Widget, Tuple[int, int]],
            end: Dict[Widget, Tuple[int, int]],
            dx: int,
            dy: int) -> int:
        score = 0
        for widget, sp in start.items():
            ep = end[widget]
            score += (ep[0] - sp[0] - dx) ** 2
            score += (ep[1] - sp[1] - dy) ** 2
        return score

    def _resolve_drag_x(
            self,
            positions: Dict[Widget, Tuple[int, int]],
            delta_x: int) -> Dict[Widget, Tuple[int, int]]:
        return self._resolve_axis(positions, delta_x, axis=0)

    def _resolve_drag_y(
            self,
            positions: Dict[Widget, Tuple[int, int]],
            delta_y: int) -> Dict[Widget, Tuple[int, int]]:
        return self._resolve_axis(positions, delta_y, axis=1)

    def _resolve_axis(
            self,
            positions: Dict[Widget, Tuple[int, int]],
            delta: int,
            axis: int) -> Dict[Widget, Tuple[int, int]]:
        direction = 1 if delta > 0 else -1
        desired = abs(delta)
        max_grid = self.max_columns if axis == 0 else self.max_rows

        ordered = sorted(
            positions,
            key=lambda w: positions[w][axis],
            reverse=direction > 0,
        )

        selected = set(positions)
        resolved = {}

        for widget in ordered:
            pos = positions[widget]
            w, h = widget.grid_width, widget.grid_height
            size = w if axis == 0 else h

            # стены
            if direction < 0:
                allowed = min(desired, pos[axis])
            else:
                allowed = min(desired, max_grid - (pos[axis] + size))

            # уже разрешенные selected через прямое расстояние
            for other, other_pos in resolved.items():
                other_size = other.grid_width if axis == 0 else other.grid_height

                if axis == 0:
                    perp_a = (pos[1], pos[1] + h)
                    perp_b = (other_pos[1], other_pos[1] + other.grid_height)
                else:
                    perp_a = (pos[0], pos[0] + w)
                    perp_b = (other_pos[0], other_pos[0] + other.grid_width)

                if not self._ranges_overlap(*perp_a, *perp_b):
                    continue

                if direction < 0:
                    distance = pos[axis] - (other_pos[axis] + other_size)
                else:
                    distance = other_pos[axis] - (pos[axis] + size)
                allowed = min(allowed, max(0, distance))

            # неподвижные препятствия: только целевая клетка
            d = allowed
            while d > 0 and not self._target_free(pos, d * direction, axis, w, h, selected):
                d -= 1
            allowed = d

            resolved[widget] = self._shift(pos, allowed * direction, axis)

        return resolved

    def _target_free(
            self,
            pos: Tuple[int, int],
            delta: int,
            axis: int,
            w: int,
            h: int,
            selected: Set[MapGridItemBehavior]):
        x, y = pos
        if axis == 0:
            x += delta
        else:
            y += delta
        return self._cells_free(x, y, w, h, selected)

    @staticmethod
    def _shift(pos: Tuple[int, int], delta: int, axis: int) -> Tuple[int, int]:
        x, y = pos
        return (x + delta, y) if axis == 0 else (x, y + delta)

    @staticmethod
    def _ranges_overlap(a0: int, a1: int, b0: int, b1: int) -> bool:
        return a0 < b1 and a1 > b0

    def _open_context_menu(self, pos: Tuple[float, float]) -> Optional[ContextMenu]:
        if self.disabled:
            return None
        menu = self._create_context_menu()
        if menu is None:
            return None
        menu.open(self, pos=pos)
        return menu

    def _create_context_menu(self) -> Optional[ContextMenu]:
        return None

    def _update_selector(self, cell_pos: Tuple[int, int]):
        if not self.selectable:
            return

        if self._selector is None:
            self._selector = _MapLayoutSelector(map_layout=self)
            self.layout.add_widget(self._selector, index=0)
        start_x, start_y = self._touch_start_cell
        current_x, current_y = cell_pos

        grid_x, grid_width = self._clamp_axis(start_x, current_x, self.max_columns)
        grid_y, grid_height = self._clamp_axis(start_y, current_y, self.max_rows)

        self._selector.grid_size = (grid_width, grid_height)
        self._selector.grid_pos = (grid_x, grid_y)

        self.clear_selected()
        for widget in self.get_grid_collisions(grid_x, grid_y, grid_width, grid_height):
            self.select(widget, clear=False)

    @staticmethod
    def _clamp_axis(start: int, current: int, max_size: int) -> Tuple[int, int]:
        # Сырые границы интервала между якорем и текущей клеткой
        left = min(start, current)
        right = max(start, current)

        # Обрезаем по допустимому диапазону
        left = max(0, left)
        right = min(max_size - 1, right)

        # Если start валиден, left <= right гарантировано.
        # На случай, если start всё же вне границ, подстрахуемся:
        if left > right:
            left = right = max(0, min(max_size - 1, start))

        width = right - left + 1
        return left, width

    def _bind_grid_item(self, widget):
        widget.map_layout = self
        self.bind_to(
            widget,
            grid_pos=self._trigger_calc_grid_size,
            grid_size=self._trigger_calc_grid_size,
        )
        self.bind_to(
            widget,
            grid_pos=self._on_grid_item_geometry_change,
            grid_size=self._on_grid_item_geometry_change,
        )
        self._sync_grid_item(widget)
        self.grid_items = [*self.grid_items, widget]

    def _unbind_grid_item(self, widget):
        self.unselect(widget)
        self.unbind_from(widget)
        geometry = self._grid_item_geometry.pop(widget, None)
        if geometry is not None:
            self._release_grid_item(widget, geometry)
        widget.map_layout = None
        self.grid_items = [x for x in self.grid_items if x is not widget]

    def _on_grid_item_geometry_change(self, widget, _):
        self._sync_grid_item(widget)
        self._trigger_calc_grid_size()

    def _occupy_grid_item(self, widget, geometry: Tuple[int, int, int, int]):
        x, y, width, height = geometry

        for cell_y in range(y, y + height):
            for cell_x in range(x, x + width):
                self._grid_occupancy.setdefault((cell_x, cell_y), set()).add(widget)

    def _release_grid_item(self, widget, geometry: Tuple[int, int, int, int]):
        x, y, width, height = geometry

        for cell_y in range(y, y + height):
            for cell_x in range(x, x + width):
                cell = (cell_x, cell_y)
                items = self._grid_occupancy.get(cell)

                if items is None:
                    continue

                items.discard(widget)

                if not items:
                    del self._grid_occupancy[cell]

    def _sync_grid_item(self, widget):
        new_geometry = self._get_grid_item_geometry(widget)
        old_geometry = self._grid_item_geometry.get(widget)

        if old_geometry == new_geometry:
            return

        if old_geometry is not None:
            self._release_grid_item(widget, old_geometry)

        self._occupy_grid_item(widget, new_geometry)
        self._grid_item_geometry[widget] = new_geometry

    @staticmethod
    def _get_grid_item_geometry(widget) -> Tuple[int, int, int, int]:
        return (
            widget.grid_x,
            widget.grid_y,
            widget.grid_width,
            widget.grid_height,
        )

    def _calc_grid_size(self, _):
        padding_w = self.grid_padding[0] + self.grid_padding[2]
        padding_h = self.grid_padding[1] + self.grid_padding[3]

        available_w = max(0, self.scrollview.width - padding_w)
        available_h = max(0, self.scrollview.height - padding_h)

        viewport_columns, viewport_rows = self.pixel_to_map_size(available_w, available_h)

        required_columns = 0
        required_rows = 0
        for widget in self.layout.children:
            if not isinstance(widget, MapGridItemBehavior):
                continue
            required_columns = max(required_columns, widget.grid_x + widget.grid_width)
            required_rows = max(required_rows, widget.grid_y + widget.grid_height)

        columns = min(max(viewport_columns, required_columns), self.max_columns)
        rows = min(max(viewport_rows, required_rows), self.max_rows)

        self._grid_size = (columns, rows)
        grid_w, grid_h = self.grid_size_to_pixel(columns, rows)
        self.wrap_layout.size = (
            max(grid_w + padding_w, self.scrollview.width),
            max(grid_h + padding_h, self.scrollview.height),
        )

    def _get_grid_texture(self) -> Texture:
        texture_cache_key = (
            self.cell_width, self.cell_height,
            self.grid_spacing_width, self.grid_spacing_height,
            self.grid_line_width,
        )
        if self._grid_texture_cache_key != texture_cache_key:
            width = max(1, ceil(self._step_x))
            height = max(1, ceil(self._step_y))

            buf = bytearray(width * height * 4)
            line_width = max(1, ceil(self.grid_line_width))

            half_left = line_width // 2
            half_right = line_width - half_left

            cell_w = int(round(self.cell_width))
            cell_h = int(round(self.cell_height))

            # Вертикальная линия должна заходить в горизонтальную на её толщину,
            # и наоборот - иначе угол клетки не закрашивается.
            y_extent = cell_h + half_right
            x_extent = cell_w + half_right

            def set_pixel(x, y):
                if 0 <= x < width and 0 <= y < height:
                    offset = (y * width + x) * 4
                    buf[offset:offset + 4] = b"\xff\xff\xff\xff"

            def horizontal_line(y, x_start, x_end):
                y = round(y)
                for yy in range(y - half_left, y + half_right):
                    for xx in range(x_start, x_end):
                        set_pixel(xx, yy)

            def vertical_line(x, y_start, y_end):
                x = round(x)
                for xx in range(x - half_left, x + half_right):
                    for yy in range(y_start, y_end):
                        set_pixel(xx, yy)

            # Левая граница
            vertical_line(0, 0, y_extent)

            # Правая граница - только если есть spacing
            if self.grid_spacing_width > 0:
                vertical_line(cell_w, 0, y_extent)

            # Нижняя граница
            horizontal_line(0, 0, x_extent)

            # Верхняя граница - только если есть spacing
            if self.grid_spacing_height > 0:
                horizontal_line(cell_h, 0, x_extent)

            self._grid_texture_cache_key = texture_cache_key
            self._grid_texture_size = (width, height)
            self._grid_texture_buf = bytes(buf)

            texture = Texture.create(
                size=(width, height),
                colorfmt="rgba",
                bufferfmt="ubyte",
            )
            texture.wrap = "repeat"
            texture.mag_filter = "nearest"
            texture.min_filter = "nearest"
            texture.blit_buffer(
                self._grid_texture_buf,
                colorfmt="rgba",
                bufferfmt="ubyte",
            )
            self._grid_texture = texture

        return self._grid_texture

    def _draw_grid(self, _):
        if not self.layout:
            return

        if not self.grid_show:
            self._grid_render_size = (0, 0)
            return

        step_x = self._step_x
        step_y = self._step_y

        if step_x <= 0 or step_y <= 0:
            self._grid_render_size = (0, 0)
            return

        # Пиксельная позиция viewport внутри content.
        scrollable_width = max(0, self.layout.width - self.scrollview.width)
        scrollable_height = max(0, self.layout.height - self.scrollview.height)

        max_grid_w, max_grid_h = self.grid_size_to_pixel(self.max_columns, self.max_rows)

        visible_x0 = self.scrollview.scroll_x * scrollable_width
        visible_x1 = min(max_grid_w, visible_x0 + self.scrollview.width)

        visible_y0 = (1.0 - self.scrollview.scroll_y) * scrollable_height
        visible_y1 = min(max_grid_h, visible_y0 + self.scrollview.height)

        rect_left = floor(visible_x0 / step_x) * step_x
        rect_bottom = floor(visible_y0 / step_y) * step_y

        render_size = (
            max(0, ceil((visible_x1 - rect_left) / step_x)) * step_x,
            max(0, ceil((visible_y1 - rect_bottom) / step_y)) * step_y,
        )

        texture = self._get_grid_texture()
        if render_size[0] > 0 and render_size[1] > 0:
            texture.uvsize = (
                render_size[0] / step_x,
                render_size[1] / step_y,
            )

        self._grid_texture = texture
        self._grid_render_pos = (rect_left, rect_bottom)
        self._grid_render_size = render_size
        self.property("_grid_texture").dispatch(self)


class WorkspaceMapLayout(MapLayout, WorkspaceBehavior):
    pass


class DesignScaledContainer:
    """Mixin для MapGridItemBehavior, чтобы виджеты умели подгонять размер
    детей под произвольный размер клетки и spacing, и в том числе если
    проектировались под один grid_size, то чтобы можно было задать другой.
    Да, зачастую это повлечет искажение соотношения изначальной геометрии, но...
    НЕ ЗАДАВАЙТЕ ЗНАЧЕНИЯ В DP И SP ДЛЯ ДЕТЕЙ!
    ЗНАЧЕНИЯ В KV - БЕЗРАЗМЕРНЫЕ ЧИСЛА!
    """
    design_grid_size = VariableListProperty([0, 0], length=2)  # MUST BE OVERRIDE
    _design_cell_width = 16
    _design_cell_height = 16
    _design = None  # {widget: (pos, size)}
    _design_pixel_width = None
    _design_pixel_height = None

    @staticmethod
    def _walk(widget):
        for child in widget.children:
            yield child
            yield from DesignScaledContainer._walk(child)

    def on_kv_post(self, _):
        super().on_kv_post(_)
        self._capture_design()
        self.bind(size=self._apply_design)
        self._apply_design()

    def _capture_design(self):
        # Пиксельный размер, под который рисовался дизайн в kv.
        self._design_pixel_width = self.design_grid_size[0] * self._design_cell_width
        self._design_pixel_height = self.design_grid_size[1] * self._design_cell_height

        design = WeakKeyDictionary()
        for child in self._walk(self):
            font_size = None
            if hasattr(child, "font_size"):
                font_size = child.font_size
            design[child] = (tuple(child.pos), tuple(child.size), font_size)
        self._design = design

    def _apply_design(self, *_):
        if not self._design or not self.map_layout:
            return

        sx = self.width  / self._design_pixel_width
        sy = self.height / self._design_pixel_height
        s_min = min(sx, sy)
        for widget, (pos, size, font_size) in list(self._design.items()):
            x, y = pos
            w, h = size
            # не надо писать dp/sp строки, т.к. metrics учтены в self.width/height
            widget.pos  = (x * sx, y * sy)
            widget.size = (w * sx, h * sy)
            if font_size:
                widget.font_size = font_size * s_min


if __name__ == "__main__":
    from kivy.app import App
    from kivy.lang import Builder
    from kivy.properties import ObjectProperty
    from kivy.uix.boxlayout import BoxLayout
    from libs import sdl2_keyboard
    from libs.uix.map_layout import *
    from libs.mouse_manager import cursor_manager


    class TestGridWidget(MapGridItemBehavior, BoxLayout):
        pass


    Builder.load_string("""
    <TestGridWidget>:
        size_hint: (None, None)
        canvas:
            Color:
                rgba: (1, 0, 0, 1)
            Rectangle:
                size: self.size
                pos: self.pos

    <Root>:
        map_layout: map_layout
        w1: w1
        w2: w2
        padding: (40, 40, 40, 40)
        MapLayout:
            id: map_layout
            grid_padding: [8, 8, 8, 8]
            grid_spacing_size: [4, 4]
            cell_size: [16, 16]
            # grid_inversion_y: True
            max_grid_size: [24, 24]
            selectable: True
            TestGridWidget:
                id: w1
                grid_size: [3, 3]
                grid_pos: [0, 0]
                selectable: True
            TestGridWidget:
                id: w2
                grid_size: [3, 3]
                grid_pos: [0, 3]
                selectable: True
            TestGridWidget:
                id: w3
                grid_size: [3, 3]
                grid_pos: [3, 0]
                selectable: True
    """
    )


    class Root(BoxLayout):
        w1 = ObjectProperty()
        map_layout = ObjectProperty()

        def on_kv_post(self, _):
            # self.map_layout.move_grid_item(self.w1, 2, 2)
            # self.map_layout.remove_widget(self.w2)
            pass

    class Test(App):
        def build(self):
            return Root()

        sdl2_keyboard.init()
        cursor_manager.init()
        from libs.mouse_manager.hover import HoverBehavior
        Test().run()
