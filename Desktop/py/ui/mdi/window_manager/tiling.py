from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from ui.components.mdi_window import MDIWindow
from libs.kivy_utils import WidgetSide, TOP_WIDGET_SIDES, BOTTOM_WIDGET_SIDES 
from typing import Tuple, Union, Optional, List
from enum import Enum, auto
from ui.mdi.window_manager.interface import IWindowManager
from database import db
from kivy.properties import OptionProperty
from libs.properties import EnumProperty
from kivy.clock import Clock


class MDITilingBox(BoxLayout):
    """Удаляется сам, если не осталось дочерних элементов"""

    def remove_widget(self, widget):
        autoremove = len(self.children) == 1
        super().remove_widget(widget)
        if autoremove:
            self.parent.parent.layout_mode.sync_mdi_list_showed()
            self.parent.remove_widget(self)

    def swap_mdi(self, mdi: MDIWindow, index: int):
        self.remove_widget(mdi)
        self.add_widget(mdi, index)
        self.parent.parent.layout_mode.sync_mdi_list_showed()

    def move_mdi(self, mdi: MDIWindow, step: int):
        index = self.mdi_index(mdi) + step
        if index >= 0:
            self.swap_mdi(mdi, index)
        self.parent.parent.layout_mode.sync_mdi_list_showed()

    def mdi_index(self, mdi: MDIWindow) -> int:
        return self.children.index(mdi)


class MDITilingBoxContainer(BoxLayout):
    pass


class TilingOrientation(Enum):
    HORIZONTAL = auto()
    VERTICAL = auto()


class TilingWindowManager(IWindowManager):
    title = "Тайлинг"
    container: MDITilingBoxContainer = None
    tiling_orientation = EnumProperty(TilingOrientation, TilingOrientation.HORIZONTAL)

    def __init__(self, mdi_container, from_wm):
        self.mdi_container = mdi_container
        self.container = MDITilingBoxContainer()
        super().__init__(mdi_container, from_wm)
        mdi_container.add_widget(self.container)

    def get_title_buttons(self) -> List[str]:
        return ["lock", "close"]

    def _can_start_resize(self, touch, mdi, side) -> bool:
        return side != WidgetSide.VOID and not mdi.locked

    def _can_start_move(self, touch, mdi, side) -> bool:
        return mdi.title_bar_label.collide_point(*touch.pos) and side == WidgetSide.VOID

    def db_sync(self):
        layout = self.mdi_container.db_row.layout
        if not layout:
            return
        get_mdi_by_title_id = App.get_running_app().get_mdi_by_title_id
        for mdi_box in layout[:]:
            mdi_list = mdi_box[:]
            mdi_id = mdi_list.pop(0)
            self.tiling_orientation = TilingOrientation.HORIZONTAL
            mdi = get_mdi_by_title_id(mdi_id)
            mdi.open(workspace_index=self.mdi_container.index)
            self.tiling_orientation = TilingOrientation.VERTICAL
            for mdi_id in mdi_box:
                mdi = get_mdi_by_title_id(mdi_id)
                mdi.open(workspace_index=self.mdi_container.index)

    def sync_mdi_list_showed(self):
        mdi_list = self.mdi_container.mdi_list_showed
        mdi_id_list = []
        for c in reversed(self.container.children):
            mdi_id_list.append([i._db_title_id for i in reversed(c.children)])
        self.mdi_container.db_row.edit(layout=mdi_id_list)

    def show_mdi(self, mdi: MDIWindow):
        db.mdi_manager.mdi_data.set_mdi_state(mdi)
        if mdi.size_hint[0] is None or mdi.size_hint[1] is None:
            mdi.size_hint = (1, 1)
        if self.container.children:
            if self.tiling_orientation is TilingOrientation.HORIZONTAL:
                mdi_box = self._focused_mdi_box()
                if mdi_box is None:
                    mdi_box_index = 0
                else:
                    mdi_box_index = self.container.children.index(mdi_box)
                self.__add_mdi_tiling_mdi_box(mdi, mdi_box_index)
            else:
                mdi_box = self._focused_mdi_box()
                if mdi_box is None:
                    self.__add_mdi_tiling_mdi_box(mdi)
                else:
                    mdi_index = mdi_box.children.index(self._focused_mdi())
                    mdi_box.add_widget(mdi, mdi_index)
                    self.sync_mdi_list_showed()
        else:
            self.__add_mdi_tiling_mdi_box(mdi)
        self._mdi_bind(mdi)

    def _mdi_bind(self, mdi: MDIWindow):
        self.bind_to(mdi, size_hint=lambda m, v: db.mdi_manager.mdi_data.set_size_hint(m._db_title_id, v))

    def hide_mdi(self, mdi: MDIWindow):
        if mdi is None:
            return
        mdi_box = mdi.parent
        if not mdi_box:
            return

        if self._focused_mdi() is mdi:
            self.__hide_mdi_focused()

        mdi_box.remove_widget(mdi)
        self.unbind_from(mdi)

    def on_start_move(self, mdi: MDIWindow):
        mdi.opacity = 0.3

    def on_stop_move(self, mdi: MDIWindow):
        mdi.opacity = 1.0

    def move_mdi(self, mdi, start_mdi_pos, start_mouse_pos, now_mouse_pos):
        """Перемещает mdi в позицию под курсором now_mouse_pos."""
        drop = self._find_drop_location(mdi, *now_mouse_pos)
        if drop is None:
            return
        target_box, target_index = drop

        current_box = mdi.parent
        if current_box is target_box and current_box.mdi_index(mdi) == target_index:
            return  # окно уже на нужном месте

        current_box.remove_widget(mdi)
        target_box.add_widget(mdi, target_index)
        self.sync_mdi_list_showed()

    def _find_drop_location(self, mdi, mouse_x, mouse_y):
        """
        Определяет, в какой MDITilingBox и на какую позицию нужно переместить mdi
        при перетаскивании в точку (mouse_x, mouse_y).
        Возвращает (target_box, target_index) или None, если перемещение невозможно.
        """
        container = self.container
        # 1. Найти бокс, над которым находится курсор (по горизонтали)
        collided_box = next((box for box in container.children if box.x <= mouse_x <= box.right), None)

        if collided_box is None:
            parent_box = mdi.parent
            current_index = container.children.index(parent_box)
            parent_box.remove_widget(mdi)
            self.sync_mdi_list_showed()

            if mouse_x > container.children[0].x:
                new_index = 0
            elif mouse_x < container.children[-1].x:
                new_index = len(container.children)
            elif mouse_x > mdi.x:
                new_index = current_index
            else:
                new_index = current_index + (1 if len(parent_box.children) == 1 else 0)

            return self.__add_mdi_tiling_mdi_box(mdi, new_index), 0

        # 2. Курсор над существующим боксом
        if collided_box is not mdi.parent:
            # Перемещение в другой бокс
            collided_mdi = next(
                (w for w in collided_box.children if w.collide_point(mouse_x, mouse_y)),
                None
            )
            if collided_mdi is None:
                # Не над конкретным окном — вставляем в начало или конец бокса
                if mouse_y > collided_box.children[0].y:
                    return collided_box, len(collided_box.children)
                elif mouse_y < collided_box.children[-1].y:
                    return collided_box, 0
                return None  # на границе бокса, но не над окнами — игнорируем

            # Вставка перед/после collided_mdi
            index = collided_box.children.index(collided_mdi)
            if collided_mdi.center_y <= mouse_y:
                index += 1
            return collided_box, index

        # 3. В том же боксе — меняем порядок
        collided_mdi = next(
            (w for w in collided_box.children if w.collide_point(mouse_x, mouse_y)),
            None
        )
        if collided_mdi is None or collided_mdi is mdi:
            return None  # не над другим окном или над собой — без изменений

        target_index = collided_box.children.index(collided_mdi)
        return collided_box, target_index

    def resize_mdi(self, side: WidgetSide, mdi_now: MDIWindow,
                   mouse_pos: Tuple[float, float]):
        if mdi_now.locked:
            return
        mouse_x, mouse_y = mouse_pos
        if side in (WidgetSide.LEFT, WidgetSide.RIGHT):
            self.__change_mdi_width(side, mdi_now, mouse_x)
        elif (side in TOP_WIDGET_SIDES) or (side in BOTTOM_WIDGET_SIDES):
            self.__change_mdi_height(side, mdi_now, mouse_y)

    def create_hotkeys(self) -> Optional[dict]:
        return {
            frozenset({"tab"}): self.switch_focus,
            frozenset({"v"}): self._handle_vertical_layout,
            frozenset({"h"}): self._handle_horizontal_layout,
            frozenset({"j"}): lambda: self._move_focus_horizontal(-1),
            frozenset({";"}): lambda: self._move_focus_horizontal(1),
            frozenset({"k"}): lambda: self._move_focus_vertical(-1),
            frozenset({"l"}): lambda: self._move_focus_vertical(1),
            frozenset({"shift", "j"}): lambda: self._move_horizontal(1),
            frozenset({"shift", ";"}): lambda: self._move_horizontal(-1),
            frozenset({"shift", "k"}): lambda: self._move_vertical(-1),
            frozenset({"shift", "l"}): lambda: self._move_vertical(1),
        }

    def _handle_vertical_layout(self):
        self.tiling_orientation = TilingOrientation.VERTICAL

    def _handle_horizontal_layout(self):
        self.tiling_orientation = TilingOrientation.HORIZONTAL

    def __change_mdi_width(self, side: WidgetSide, mdi_now: MDIWindow,
                           mouse_x: float):
        mdi_box_now = mdi_now.parent
        index_mdi_box_now = self.container.children.index(mdi_box_now)
        if side is WidgetSide.LEFT:
            if index_mdi_box_now == (len(self.container.children) - 1):
                return
            neighbor_mdi_box = self.container.children[index_mdi_box_now + 1]
            master_mdi_box, slave_mdi_box = mdi_box_now, neighbor_mdi_box
        else:
            if index_mdi_box_now == 0:
                return
            neighbor_mdi_box = self.container.children[index_mdi_box_now - 1]
            master_mdi_box, slave_mdi_box = neighbor_mdi_box, mdi_box_now

        master_mdi_box.size_hint_x, slave_mdi_box.size_hint_x = self.__calc_hints(
            sum_hint=master_mdi_box.size_hint_x + slave_mdi_box.size_hint_x,
            sum_size=master_mdi_box.width + slave_mdi_box.width,
            mouse_local=mouse_x - slave_mdi_box.x
        )

    def __change_mdi_height(self, side: WidgetSide, mdi_now: MDIWindow,
                            mouse_y: float):
        mdi_box_now = mdi_now.parent
        index_mdi_now = mdi_box_now.mdi_index(mdi_now)
        if side in TOP_WIDGET_SIDES:
            if index_mdi_now == (len(mdi_box_now.children) - 1):
                return
            neighbor_mdi = mdi_box_now.children[index_mdi_now + 1]
            master_mdi, slave_mdi = neighbor_mdi, mdi_now
        else:
            if index_mdi_now == 0:
                return
            neighbor_mdi = mdi_box_now.children[index_mdi_now - 1]
            master_mdi, slave_mdi = mdi_now, neighbor_mdi

        master_mdi.size_hint_y, slave_mdi.size_hint_y = self.__calc_hints(
            sum_hint=master_mdi.size_hint_y + slave_mdi.size_hint_y,
            sum_size=master_mdi.height + slave_mdi.height,
            mouse_local=mouse_y - slave_mdi.y
        )

    def __calc_hints(self,
                     sum_hint: float,
                     sum_size: float,
                     mouse_local: float) -> Tuple[float, float]:
        size_hint_min = MDIWindow.SIZE_HINT_MINIMUM

        ratio = mouse_local / sum_size
        slave_hint = max(
            size_hint_min, min(
                ratio * sum_hint, sum_hint - size_hint_min))
        master_hint = max(size_hint_min, sum_hint - slave_hint)
        return (master_hint, slave_hint)

    def _move_focus_horizontal(self, step: int):
        mdi_box = self._focused_mdi_box()
        if mdi_box is None:
            return
        mdi_box_index = self.container.children.index(mdi_box)
        new_index = mdi_box_index + step
        if 0 <= new_index < len(self.container.children):
            new_mdi_box = self.container.children[new_index]
            self._move_focus_to_another_mdi_box(new_mdi_box)

    def _move_focus_vertical(self, step: int):
        mdi_box = self._focused_mdi_box()
        if mdi_box is None:
            return
        index = mdi_box.mdi_index(self._focused_mdi())
        new_index = index + step
        if 0 <= new_index < len(mdi_box.children):
            self._set_focus(mdi_box.children[new_index])

    def _move_horizontal(self, step):
        mdi_box = self._focused_mdi_box()
        if mdi_box is None:
            return
        mdi_focused = self._focused_mdi()
        mdi_box_index = self.container.children.index(mdi_box)
        index = mdi_box_index + step
        if 0 <= index < len(self.container.children):
            right_mdi_box = self.container.children[index]
            mdi = self.__get_must_overlapped_mdi(right_mdi_box)
            mdi_index = right_mdi_box.mdi_index(mdi)
            mdi_box.remove_widget(mdi_focused)
            right_mdi_box.add_widget(mdi_focused, mdi_index)
            self.sync_mdi_list_showed()
        else:
            mdi_box.remove_widget(mdi_focused)
            index = len(self.container.children) if step > 0 else 0
            self.__add_mdi_tiling_mdi_box(mdi_focused, index)

    def _move_vertical(self, step: int):
        mdi_box = self._focused_mdi_box()
        if (mdi_box is None) or len(mdi_box.children) == 1:
            return
        mdi_box.move_mdi(self._focused_mdi(), step)

    def _move_focus_to_another_mdi_box(self, mdi_box: MDITilingBox):
        """Переносит фокус на окно в другом гриде, наиболее близкое по
        вертикали."""
        self._set_focus(self.__get_must_overlapped_mdi(mdi_box))

    def __get_must_overlapped_mdi(self, mdi_box: MDITilingBox) -> MDIWindow:
        """Возвращает mdi, наиболее пересекающийся с другим MDI из параметра
        mdi_box."""
        current_y, current_top = self._focused_mdi().y, self._focused_mdi().top

        must_overlapped_mdi = None
        max_overlap = 0
        for widget in mdi_box.children:
            widgets_intersect = current_y <= widget.top and current_top >= widget.y
            if not widgets_intersect:
                continue

            overlap_height = current_top - \
                widget.y if current_top < widget.top else widget.top - current_y

            if overlap_height > max_overlap:
                must_overlapped_mdi = widget
                max_overlap = overlap_height
        return must_overlapped_mdi

    def __add_mdi_tiling_mdi_box(
            self,
            mdi: MDIWindow,
            index=0) -> MDITilingBox:
        mdi_box = MDITilingBox()
        mdi_box.add_widget(mdi)
        self.container.add_widget(mdi_box, index)
        self.sync_mdi_list_showed()
        return mdi_box

    def __hide_mdi_focused(self):
        mdi_box = self._focused_mdi_box()
        if mdi_box is not None:
            new_focus = self._find_new_focus(mdi_box, self._focused_mdi())
            self._set_focus(new_focus)

    def _find_new_focus(self, mdi_box: MDITilingBox,
                        mdi: MDIWindow) -> Union[None, MDIWindow]:
        if len(mdi_box.children) > 1:
            index = mdi_box.mdi_index(mdi)
            return mdi_box.children[(index + 1) % len(mdi_box.children)]

        if len(self.container.children) == 1:
            return None
        mdi_box_index = self.container.children.index(mdi_box)
        if mdi_box_index == 0:
            return self.container.children[1].children[-1]
        else:
            return self.container.children[mdi_box_index - 1].children[-1]

    def _set_focus(self, mdi: MDIWindow):
        self.mdi_container.set_focus(mdi)

    def _focused_mdi_box(self) -> Union[None, MDITilingBox]:
        mdi_focused = self._focused_mdi()
        return mdi_focused.parent if mdi_focused else None

    def _transform_to_that_window_manager(self, from_wm: IWindowManager):
        from ui.mdi.window_manager.floating import FloatingWindowManager
        if isinstance(from_wm, FloatingWindowManager):
            container = self.mdi_container
            focused = self._focused_mdi()
            self.mdi_container.mdi_focused = None
            for mdi in container.mdi_list_showed:
                from_wm.unbind_from(mdi)
                container.remove_widget(mdi)
                self._mdi_bind(mdi)
                self.show_mdi(mdi)
                mdi.size_hint = (1, 1)
            self.mdi_container.mdi_focused = focused
            self.sync_mdi_list_showed()
