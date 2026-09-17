from kivy.properties import (
    ObjectProperty, NumericProperty, BooleanProperty,
    ListProperty, ColorProperty
)
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.relativelayout import RelativeLayout
from kivy.utils import boundary
from libs.uix.workspace_manager import WorkspaceBehavior
from ui.components.scroll_layout import ScrollLayout
from libs.mouse_manager.hover import HoverBehavior, NestedHoverBehavior
from libs.animation import AnimationBehavior
from ui.components.context_menu import ContextMenu
from misc import constants
from misc import colorscheme as cs
from enum import Enum
from typing import List, Tuple, Optional, Union
from libs.animation import StatefulColorProperty
from libs.kivy_utils import walk_by_parents
from operator import attrgetter
from kivy.lang import Builder


Builder.load_file("ui/components/scroll_layout_map.kv")


class MapSelectorTouchUD(Enum):
    START_CELL = "start_cell"
    CURRENT_CELL = "current_cell"
    START_SELF = "start_uid_cell"


def check_collision(gx1, gy1, gw1, gh1, gx2, gy2, gw2, gh2):
    return not (gx1 + gw1 <= gx2 or gx1 >= gx2 + gw2 or
                gy1 + gh1 <= gy2 or gy1 >= gy2 + gh2)


class GridBehavior:
    map_layout = ObjectProperty()
    grid_size = constants.MAP_LAYOUT_GRID_SIZE

    grid_x = NumericProperty(0)
    grid_y = NumericProperty(0)
    grid_width = NumericProperty(1)
    grid_height = NumericProperty(1)

    is_limiters = BooleanProperty(True)

    _trigger_update_pos = None
    _trigger_update_size = None
    def __init__(self, **kwargs):
        trigger_update_pos = Clock.create_trigger(self._update_pos, -1)
        trigger_update_size = Clock.create_trigger(self._update_size, -1)
        self._trigger_update_pos = trigger_update_pos
        self._trigger_update_size = trigger_update_size
        super().__init__(**kwargs)
        self.bind(
            grid_x=trigger_update_pos,
            grid_y=trigger_update_pos,
            grid_width=trigger_update_size,
            grid_height=trigger_update_size,
        )

    def on_map_layout(self, _, _map_layout: "MapLayout"):
        self.pos = self.cell_to_pixel(self.grid_x, self.grid_y)
        self.size = self.cell_to_pixel(self.grid_width, self.grid_height)
        _map_layout.bind(height=self._trigger_update_pos)

    def _update_pos(self, *args):
        if not self.map_layout:
            return
        if self.is_limiters:
            self.grid_x = self._limiter_x(self.grid_x)
            self.grid_y = self._limiter_y(self.grid_y)
        # self.pos = self.cell_to_pixel(self.grid_x, self.grid_y)
        if self.map_layout.invert_grid:
            self.pos = (self.grid_x * self.grid_size, self.grid_y * self.grid_size + self.map_layout.height % self.grid_size)
        else:
            self.pos = (self.grid_x * self.grid_size, self.grid_y * self.grid_size)

    def _update_size(self, _):
        self.size = self.cell_to_pixel(self.grid_width, self.grid_height)

    def cell_to_pixel(self, cell_x: int, cell_y: int) -> Tuple[int, int]:
        if self.map_layout.invert_grid:
            return (cell_x * self.grid_size, cell_y * self.grid_size)
        else:
            return (cell_x * self.grid_size, cell_y * self.grid_size)

    def _limiter_x(self, x: int) -> int:
        grid_size = self.map_layout.grid_size
        # right_limit = (self.map_layout.right - self.width) // grid_size
        right_limit = constants.MAP_LAYOUT_MAX_SIZE * constants.MAP_LAYOUT_GRID_SIZE
        return int(boundary(x, 0, right_limit))

    def _limiter_y(self, y: int) -> int:
        grid_size = self.map_layout.grid_size
        # top_limit = (self.map_layout.top - self.height) // grid_size
        top_limit = constants.MAP_LAYOUT_MAX_SIZE * constants.MAP_LAYOUT_GRID_SIZE
        return int(boundary(y, 0, top_limit))

    def collide_widget(self, wid):
        return self.check_collide_grid_pos(
            wid.grid_x, wid.grid_y,
            wid.grid_x + wid.grid_width, wid.grid_y + wid.grid_height
        )

    def check_collide_grid_pos(self,
                               grid_x: int, grid_y: int,
                               grid_right: int, grid_top: int):
        if self.grid_x + self.grid_width <= grid_x:
            return False
        if self.grid_x >= grid_right:
            return False
        if self.grid_y + self.grid_height <= grid_y:
            return False
        if self.grid_y >= grid_top:
            return False
        return True

    def _if_allow_move(self, widget: Widget) -> bool:
        return widget is not self.map_layout and widget is self or self._check_allow_move_widget(widget)

    def _check_allow_move_widget(self, widget: Widget) -> bool:
        # Надо в наследнике переопределять
        return widget is self


class SelectableBehavior(AnimationBehavior, NestedHoverBehavior, GridBehavior):
    animation_time = 0.0
    border_color = StatefulColorProperty(
        normal=cs.SelectableBehavior.border_color_normal,
        states={
            "is_select": cs.SelectableBehavior.border_color_is_select,
            "real_hover": cs.SelectableBehavior.border_color_hover,
        }
    )
    is_select = BooleanProperty(False)

    def on_map_layout(self, _, map_layout: "MapLayout"):
        super().on_map_layout(_, map_layout)
        self.bind(is_select=map_layout.trigger_set_selected)
        self.bind(pos=map_layout._trigger_calc_resize)

    def do_select(self):
        for widget in self.map_layout.selected:
            widget.is_select = False
        self.is_select = True

    def unselect(self):
        self.is_select = False

    def move(self, touch, delta_x: int, delta_y: int) -> bool:
        """
            Возвращает, был ли виджет перемещен
        """
        start_self_x, start_self_y = self._get_self_start_cell(touch)

        proposed_grid_x = start_self_x + delta_x
        proposed_grid_y = start_self_y + delta_y

        # Применяем ограничители
        proposed_grid_x = self._limiter_x(proposed_grid_x)
        proposed_grid_y = self._limiter_y(proposed_grid_y)

        # Проверяем коллизии
        for widget in self.map_layout._get_map_widgets():
            if widget == self:
                continue
            if check_collision(
                proposed_grid_x, proposed_grid_y, self.grid_width, self.grid_height,
                widget.grid_x, widget.grid_y, widget.grid_width, widget.grid_height
            ):
                return False
        self.grid_x = proposed_grid_x
        self.grid_y = proposed_grid_y
        return True

    def _get_self_start_cell(self, touch) -> List[float]:
        key = f"{MapSelectorTouchUD.START_SELF}_{self.uid}"
        if key not in touch.ud:
            touch.ud[key] = (self.grid_x, self.grid_y)
        return touch.ud[key]


class MapSelector(GridBehavior, Widget):
    _set_collide_trigger = None
    def __init__(self, **kwargs):
        self._set_collide_trigger = Clock.create_trigger(self.set_collide, 0)
        super().__init__(**kwargs)
        self.bind(
            grid_x=self._set_collide_trigger,
            grid_y=self._set_collide_trigger,
            grid_width=self._set_collide_trigger,
            grid_height=self._set_collide_trigger,
        )
        self._set_collide_trigger()

    def move(self, touch):
        start_x, start_y = touch.ud[MapSelectorTouchUD.START_CELL]
        current_x, current_y = touch.ud[MapSelectorTouchUD.CURRENT_CELL]

        min_x = min(start_x, current_x)
        min_y = min(start_y, current_y)
        max_x = max(start_x, current_x)
        max_y = max(start_y, current_y)

        grid_size = self.grid_size
        # max_cell_x = max(0, (self.map_layout.width // grid_size) - 1)
        # max_cell_y = max(0, (self.map_layout.height // grid_size) - 1)
        max_cell_x = constants.MAP_LAYOUT_MAX_SIZE * constants.MAP_LAYOUT_GRID_SIZE
        max_cell_y = constants.MAP_LAYOUT_MAX_SIZE * constants.MAP_LAYOUT_GRID_SIZE

        min_x = max(0, min(min_x, max_cell_x))
        max_x = min(max_x, max_cell_x)
        min_y = max(0, min(min_y, max_cell_y))
        max_y = min(max_y, max_cell_y)

        if min_x > max_x:
            min_x, max_x = max_x, min_x
        if min_y > max_y:
            min_y, max_y = max_y, min_y

        self.grid_width = max_x - min_x + 1
        self.grid_height = max_y - min_y + 1
        self.grid_x = min_x
        self.grid_y = min_y
        self.map_layout._trigger_calc_resize()

    def set_collide(self, _):
        for i in self.map_layout._get_map_widgets():
            i.is_select = self.collide_widget(i)


class MapLayout(RelativeLayout):
    scrollview = ObjectProperty()

    selector: MapSelector = None
    selected = ListProperty([])
    grid_points = ListProperty([])
    grid_size = constants.MAP_LAYOUT_GRID_SIZE

    selectable = BooleanProperty(True)
    resize_by_children = BooleanProperty(False)
    invert_grid = BooleanProperty(False)

    _trigger_set_map_selected = None
    _trigger_update_grid = None
    _touched_widget = None
    # _trigger_calc_resize = None
    def __init__(self, **kwargs):
        self.trigger_set_selected = Clock.create_trigger(
                                            self._set_map_selected, -1)
        self._trigger_update_grid = Clock.create_trigger(self.update_grid, -1)
        self._touched_widget = None
        self._widget_touched_by_cursor = None
        self.prev_delta_x = None
        self.prev_delta_y = None
        self._trigger_calc_resize = Clock.create_trigger(self._calc_resize, 0)
        super().__init__(**kwargs)
        self.bind(
            size=self._trigger_update_grid,
            invert_grid=self._trigger_update_grid,
        )
        self.bind(
            size=self._trigger_calc_resize,
            invert_grid=self._trigger_calc_resize,
            children=self._trigger_calc_resize,
        )

    def on_kv_post(self, _):
        self.scrollview.bind(size=self._calc_resize)
        self._calc_resize()

    def _calc_resize(self, *args):
        if self.resize_by_children:
            self._calc_resize_by_children()
        else:
            self._calc_resize_default()

    def _calc_resize_default(self):
        sv_size = self.scrollview.size
        if not self.children:
            self.size = sv_size
        else:
            max_size = self.grid_size * constants.MAP_LAYOUT_MAX_SIZE
            child_max_right = max((i.right for i in self.children))
            child_max_top = max((i.top for i in self.children))
            max_x = boundary(child_max_right, sv_size[0], max_size)
            max_y = boundary(child_max_top, sv_size[1], max_size)
            self.size = [max_x, max_y]

    child_grid_pos_attrgetter = attrgetter("grid_pos")
    def _calc_resize_by_children(self):
        """
            Рассчитывает, насколько надо сместить по [x;y] все PatchEditUi для
        того, чтобы они стояли у лево-верхней границы без нарушения их положения
        относительно друг друга.
        """
        sv_size = self.scrollview.size
        children = self.children
        if not children:
            self.size = sv_size
            return

        get_grid_pos = self.child_grid_pos_attrgetter
        min_x = min(get_grid_pos(c)[0] for c in children)
        min_y = min(get_grid_pos(c)[1] for c in children)

        max_right = max(get_grid_pos(c)[0] - min_x + c.grid_width for c in children)
        max_bottom = max(get_grid_pos(c)[1] - min_y + c.grid_height for c in children)

        grid_size = constants.MAP_LAYOUT_GRID_SIZE
        max_size = self.grid_size * constants.MAP_LAYOUT_MAX_SIZE
        width = boundary(max_right * grid_size, sv_size[0], max_size)
        height = boundary(max_bottom * grid_size, sv_size[1], max_size)
        self.size = [width, height]
        for c in children:
            c.grid_x = get_grid_pos(c)[0] - min_x
            c.grid_y = (get_grid_pos(c)[1] - min_y) + ((height // grid_size) - max_bottom)

    def _set_map_selected(self, _):
        self.selected = [i for i in self._get_map_widgets() if i.is_select]

    def _get_map_widgets(self) -> List[Widget]:
        return [i for i in self.children if isinstance(i, SelectableBehavior)]

    def pixel_to_cell(self, x: float, y: float):
        return (int(x // self.grid_size), int(y // self.grid_size))

    def cell_to_pixel(self, cell_x: int, cell_y: int):
        return (cell_x * self.grid_size, cell_y * self.grid_size)

    def update_grid(self, _):
        grid_points = []
        width, height = self.size
        grid_size = self.grid_size
        invert_grid = self.invert_grid

        # Генерация горизонтальных линий (змейкой снизу вверх)
        current_x = 0
        current_y = height if invert_grid else 0  # Начинаем снизу
        direction = 1  # 1 - вправо, -1 - влево

        draw_x_condition = (lambda: current_y >= 0) if invert_grid else (lambda: current_y <= height)
        while draw_x_condition():
            end_x = width if direction == 1 else 0
            grid_points.extend([current_x, current_y, end_x, current_y])

            # Сдвигаемся вверх
            prev_y = current_y
            current_y += grid_size * (-1 if invert_grid else 1)

            # Вертикальный сегмент между горизонтальными линиями
            if current_y <= height:
                grid_points.extend([end_x, prev_y, end_x, current_y])

            current_x = end_x
            direction *= -1

        # Генерация вертикальных линий (змейкой слева направо)
        current_x = 0
        current_y = 0
        direction = 1  # 1 - вверх, -1 - вниз

        grid_points.extend([float('nan'), float('nan')])
        while current_x <= width:
            end_y = height if direction == 1 else 0
            grid_points.extend([current_x, current_y, current_x, end_y])

            # Сдвигаемся вправо
            prev_x = current_x
            current_x += grid_size

            # Горизонтальный сегмент между вертикальными линиями
            if current_x <= width:
                grid_points.extend([prev_x, end_y, current_x, end_y])

            direction *= -1

        self.grid_points = grid_points

    def on_touch_down(self, touch):
        if touch.grab_current is not None:
            return False

        if not self.collide_point(*touch.pos):
            return False

        if self.disabled:
            return True

        self._touched_widget = self._get_touched_widget()
        if self.selectable:
            self._do_select_touched_widget()
        if touch.button == "right":
            if self._touched_widget and hasattr(self._touched_widget, "open_context_menu"):
                self._touched_widget.open_context_menu(touch.pos)
            else:
                self.open_context_menu(touch.pos)
            return True

        if self.selectable:
            if self.selector:
                self._stop_select(touch)
            touch.grab(self)
            touch.ud[MapSelectorTouchUD.START_CELL] = self.pixel_to_cell(*touch.pos)
            touch.ud[MapSelectorTouchUD.CURRENT_CELL] = self.pixel_to_cell(*touch.pos)
            if self._touched_widget is None:
                self._start_select(touch)
            self._do_move(touch)
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self._do_move(touch)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            if self.selector:
                self._stop_select(touch)
            self.prev_delta_x = None
            self.prev_delta_y = None
            return True
        return super().on_touch_up(touch)

    def _do_select_touched_widget(self):
        tw = self._touched_widget
        if (tw is not None) and isinstance(tw, SelectableBehavior) and (tw not in self.selected):
            tw.do_select()

    def _get_touched_widget(self) -> Optional[SelectableBehavior]:
        hovered_widget = HoverBehavior.widget_under_cursor
        self._widget_touched_by_cursor = hovered_widget
        if hovered_widget is None:
            return None
        if isinstance(hovered_widget, GridBehavior) and\
           not isinstance(hovered_widget, MapSelector):
            return hovered_widget
        for widget in walk_by_parents(hovered_widget):
            if isinstance(widget, GridBehavior) and not isinstance(widget, MapSelector):
                return widget
        return None

    def _start_select(self, touch):
        self.selector = MapSelector(
            grid_x=touch.ud[MapSelectorTouchUD.START_CELL][0],
            grid_y=touch.ud[MapSelectorTouchUD.START_CELL][1],
            map_layout=self,
        )
        self.add_widget(self.selector)

    def _do_move(self, touch):
        if self._touched_widget and self._widget_touched_by_cursor:
            if not self._touched_widget._if_allow_move(self._widget_touched_by_cursor):
                return
        touch.ud[MapSelectorTouchUD.CURRENT_CELL] = self.pixel_to_cell(*touch.pos)
        if self.selector:
            self._move_select(touch)
        else:
            start_x, start_y = touch.ud[MapSelectorTouchUD.START_CELL]
            current_x, current_y = self.pixel_to_cell(*touch.pos)
            delta_x = current_x - start_x
            delta_y = current_y - start_y
            if self.prev_delta_x == delta_x and self.prev_delta_y == delta_y:
                return
            self.prev_delta_x = delta_x
            self.prev_delta_y = delta_y

            selected_set = set(self.get_movement_order(self.selected, delta_x, delta_y))
            moved_set = set()
            for _ in range(10):
                for widget in selected_set - moved_set:
                    if widget.move(touch, delta_x, delta_y):
                        moved_set.add(widget)
                if moved_set == selected_set:
                    break
            self._trigger_calc_resize()

    def get_movement_order(self, selected_widgets: list, delta_x: int, delta_y: int) -> list:
        if not selected_widgets:
            return []
        
        if delta_x == 0 and delta_y == 0:
            return selected_widgets
        
        def get_front_projection(widget):
            # Получаем координаты всех углов виджета
            corners = [
                (widget.grid_x, widget.grid_y),  # левый-верхний
                (widget.grid_x + widget.grid_width, widget.grid_y),  # правый-верхний  
                (widget.grid_x, widget.grid_y + widget.grid_height),  # левый-нижний
                (widget.grid_x + widget.grid_width, widget.grid_y + widget.grid_height)  # правый-нижний
            ]
            
            # Вычисляем проекции всех углов на вектор движения
            projections = [x * delta_x + y * delta_y for x, y in corners]
            
            # Возвращаем максимальную проекцию - это будет "передний" край
            return max(projections)
        
        # Сортируем по убыванию проекции - сначала идут виджеты с наибольшей проекцией
        # (те, что находятся "впереди" по направлению движения)
        return sorted(selected_widgets, key=get_front_projection, reverse=True)

    def _move_select(self, touch):
        self.selector.move(touch)

    def _stop_select(self, touch):
        self.remove_widget(self.selector)
        self.selector = None
        touch.ungrab(self)
        self._trigger_calc_resize()

    def open_context_menu(self, pos: tuple):
        if self.disabled:
            return
        self._create_context_menu().open(self, pos=pos)

    def _create_context_menu(self) -> ContextMenu:
        raise NotImplementedError()


class MapScrollLayout(ScrollLayout):
    scrollview = ObjectProperty()
    box = ObjectProperty()
    selectable = BooleanProperty(True)
    resize_by_children = BooleanProperty(False)
    invert_grid = BooleanProperty(False)

    def on_selectable(self, _, selectable: bool):
        self.box.selectable = selectable

    def on_resize_by_children(self, _, resize_by_children: bool):
        self.box.resize_by_children = resize_by_children

    def on_invert_grid(self, _, invert_grid: bool):
        self.box.invert_grid = invert_grid

    def on_scrollview(self, _, scrollview):
        super().on_scrollview(_, scrollview)
        self._save_add_widget = self.add_widget
        self.add_widget = self.patch2_add_widget

    def patch2_add_widget(self, widget, index=0, canvas=None):
        if isinstance(widget, SelectableBehavior) or isinstance(widget, GridBehavior):
            widget.map_layout = self.box
            self.box.add_widget(widget, index, canvas)
        else:
            self._save_add_widget(widget, index, canvas)

    def find_empty_pos(self, widget: Union[GridBehavior, SelectableBehavior]):
        layout = self.box

        step = constants.MAP_LAYOUT_GRID_SIZE
        layout_width = layout.width // step
        layout_height = layout.height // step
        widget_width = widget.grid_width
        widget_height = widget.grid_height

        # Начальная позиция Y сверху
        start_y = (layout.top // step) - widget_height - 1

        # Перебираем координаты Y сверху вниз
        for y in range(int(start_y) + 1, -1, -1):
            # Перебираем координаты X слева направо
            for x in range(0, int(layout_width), 1):
                # Проверяем, что область не выходит за границы layout
                if x + widget_width > layout_width or y < 0:
                    continue

                # Проверяем пересечение с каждым дочерним виджетом
                if not any(child.check_collide_grid_pos(x, y, x + widget_width, y + widget_height) 
                           for child in layout.children):
                    return (x, y)
        return (0, start_y)


class WorkspaceMapScrollLayout(WorkspaceBehavior, MapScrollLayout):
    pass
