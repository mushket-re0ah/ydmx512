from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from libs.uix.mdi.mdi_window import MDIWindow
from kivy.properties import ObjectProperty
from libs.kivy_utils import WidgetSide, TOP_WIDGET_SIDES, BOTTOM_WIDGET_SIDES 
from typing import Tuple, Union, Optional, List
from enum import Enum, auto
from .interface import ILayoutMode
from kivy.properties import OptionProperty
from libs.properties import EnumProperty
from kivy.clock import Clock
from kivy.lang import Builder
from libs.uix.context_menu import ContextMenu, ContextMenuTemplates

Builder.load_string("""
#:set mdi_tiling_spacing "4dp"


<MDITilingBox>:  # BoxLayout
    spacing: mdi_tiling_spacing
    orientation: "vertical"


<MDITilingBoxContainer>:  # BoxLayout
    spacing: mdi_tiling_spacing
"""
)


class MDITilingBox(BoxLayout):
    """Удаляется сам, если не осталось дочерних элементов"""
    layout_mode = ObjectProperty()

    def remove_widget(self, widget):
        autoremove = len(self.children) == 1
        super().remove_widget(widget)
        if autoremove:
            self.parent.remove_widget(self)

    def swap_mdi(self, mdi: MDIWindow, index: int):
        self.remove_widget(mdi)
        self.add_widget(mdi, index)

    def move_mdi(self, mdi: MDIWindow, step: int):
        index = self.mdi_index(mdi) + step
        if index >= 0:
            self.swap_mdi(mdi, index)

    def mdi_index(self, mdi: MDIWindow) -> int:
        return self.children.index(mdi)

    def on_children(self, _, children):
        self.layout_mode.dispatch("on_layout_changed", self.layout_mode.get_layout())


class MDITilingBoxContainer(BoxLayout):
    layout_mode = ObjectProperty()

    def on_children(self, _, children):
        self.layout_mode.dispatch("on_layout_changed", self.layout_mode.get_layout())


class TilingOrientation(Enum):
    HORIZONTAL = auto()
    VERTICAL = auto()


class TilingLayoutMode(ILayoutMode):
    SIZE_HINT_MINIMUM = 0.1
    EDGE_DROP_ZONE = 30

    layout_state_key = "tiling"
    title = "Тайлинг"
    container: MDITilingBoxContainer = None
    tiling_orientation = EnumProperty(TilingOrientation, TilingOrientation.HORIZONTAL)

    def __init__(self, mdi_container, from_layout_mode):
        self.mdi_container = mdi_container
        self.container = MDITilingBoxContainer(layout_mode=self)
        super().__init__(mdi_container, from_layout_mode)
        mdi_container._layout_add_widget(self.container)

    def get_layout(self):
        return [
            [mdi for mdi in reversed(mdi_box.children)]
            for mdi_box in reversed(self.container.children)
        ]

    def load_layout(self, layout):
        mdi_list = [
            mdi
            for mdi_group in layout
            for mdi in mdi_group
        ]

        for mdi in mdi_list:
            self.mdi_container.add_widget(mdi)
        for child in self.container.children[:]:
            child.clear_widgets()
        self.container.clear_widgets()

        for mdi_group in layout:
            mdi_box = MDITilingBox(layout_mode=self)
            for mdi in mdi_group:
                mdi_box.add_widget(mdi)
            self.container.add_widget(mdi_box)

    def _can_start_resize(self, touch, mdi, side) -> bool:
        return side != WidgetSide.VOID and not mdi.get_layout_state("locked", False)

    def _can_start_move(self, touch, mdi, side) -> bool:
        return mdi.title_bar_label.collide_point(*touch.pos) and side == WidgetSide.VOID

    def show_mdi(self, mdi: MDIWindow):
        super().show_mdi(mdi)
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
        else:
            self.__add_mdi_tiling_mdi_box(mdi)
        self.setup_title_buttons(mdi)

    def get_title_buttons(self) -> List[str]:
        return ["lock", "close"]

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
        locked = mdi.get_layout_state("locked", False)
        if locked:
            return

        drop = self._find_drop_location(mdi, *now_mouse_pos)
        if drop is None:
            return

        target_box, target_index = drop
        current_box = mdi.parent

        # Новый box слева
        if target_box is None and target_index == "left":
            current_box.remove_widget(mdi)
            self.__add_mdi_tiling_mdi_box(
                mdi,
                len(self.container.children),
            )
            return

        # Новый box справа
        if target_box is None and target_index == "right":
            current_box.remove_widget(mdi)
            self.__add_mdi_tiling_mdi_box(mdi, 0)
            return

        if current_box is target_box and current_box.mdi_index(mdi) == target_index:
            return

        current_box.remove_widget(mdi)
        target_box.add_widget(mdi, target_index)

    def _find_drop_location(self, mdi, mouse_x, mouse_y):
        """
        Определяет, в какой MDITilingBox и на какую позицию нужно переместить mdi
        при перетаскивании в точку (mouse_x, mouse_y).
        Возвращает (target_box, target_index) или None, если перемещение невозможно.
        """
        container = self.container

        if mouse_x < container.x + self.EDGE_DROP_ZONE:
            return None, "left"

        if mouse_x > container.right - self.EDGE_DROP_ZONE:
            return None, "right"

        collided_box = next((box for box in container.children if box.x <= mouse_x <= box.right), None)

        if collided_box is None:
            return None

        if collided_box is not mdi.parent:
            collided_mdi = next((w for w in collided_box.children if w.collide_point(mouse_x, mouse_y)), None)

            if collided_mdi is None:
                if mouse_y > collided_box.children[0].y:
                    return collided_box, len(collided_box.children)
                if mouse_y < collided_box.children[-1].y:
                    return collided_box, 0
                return None

            index = collided_box.children.index(collided_mdi)
            if collided_mdi.center_y <= mouse_y:
                index += 1

            return collided_box, index

        collided_mdi = next((w for w in collided_box.children if w.collide_point(mouse_x, mouse_y)), None)

        if collided_mdi is None or collided_mdi is mdi:
            return None

        return collided_box, collided_box.children.index(collided_mdi)

    def resize_mdi(self, side: WidgetSide, mdi_now: MDIWindow,
                   mouse_pos: Tuple[float, float]):
        if mdi_now.get_layout_state("locked", False):
            return
        mouse_x, mouse_y = mouse_pos
        if side in (WidgetSide.LEFT, WidgetSide.RIGHT):
            self.__change_mdi_width(side, mdi_now, mouse_x)
        elif (side in TOP_WIDGET_SIDES) or (side in BOTTOM_WIDGET_SIDES):
            self.__change_mdi_height(side, mdi_now, mouse_y)

    def create_hotkeys(self) -> Optional[dict]:
        return {
            **super().create_hotkeys(),
            frozenset({"ctrl", "shift", "l"}): self.mdi_invert_locked,
            frozenset({"ctrl", "shift", "e"}): self.mdi_close,
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
        size_hint_min = self.SIZE_HINT_MINIMUM

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
        mdi_box = MDITilingBox(layout_mode=self)
        mdi_box.add_widget(mdi)
        self.container.add_widget(mdi_box, index)
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

    def _transform_to_that_layout_mode(self, from_layout_mode: ILayoutMode):
        from .floating import FloatingLayoutMode
        if isinstance(from_layout_mode, FloatingLayoutMode):
            container = self.mdi_container
            focused = self._focused_mdi()
            self.mdi_container.mdi_focused = None
            for mdi in container.mdi_list_showed:
                from_layout_mode.unbind_from(mdi)
                container._layout_remove_widget(mdi)
                self.show_mdi(mdi)
                mdi.size_hint = (1, 1)
            self.mdi_container.mdi_focused = focused
