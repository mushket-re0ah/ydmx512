from kivy.app import App
from ..mdi_window import MDIWindow
from libs.kivy_utils import (
    WidgetSide, LEFT_WIDGET_SIDES, RIGHT_WIDGET_SIDES, TOP_WIDGET_SIDES,
    BOTTOM_WIDGET_SIDES, WIDGET_SIDE_CURSOR, get_cursor_zone
)
from typing import Tuple, Union, Optional
from .interface import ILayoutMode
from kivy.clock import Clock
from enum import Enum, auto
from libs.uix.context_menu import ContextMenu, ContextMenuTemplates


class FlexMode(Enum):
    LEFT = auto()
    RIGHT = auto()
    VERTICAL = auto()


class FloatingLayoutMode(ILayoutMode):
    layout_state_key = "floating"
    title = "Плавающие окна"
    FLEX_OPACITY = 0.4

    def __init__(self, mdi_container, from_layout_mode):
        self._save_lock = False
        super().__init__(mdi_container, from_layout_mode)

    def _can_start_resize(self, touch, mdi, side) -> bool:
        return side != WidgetSide.VOID

    def _can_start_move(self, touch, mdi, side) -> bool:
        return mdi.title_bar_label.collide_point(*touch.pos) and side == WidgetSide.VOID

    def show_mdi(self, mdi: MDIWindow):
        super().show_mdi(mdi)
        self.mdi_container._layout_add_widget(mdi)
        mdi.size_hint = (None, None)
        self._mdi_bind(mdi)
        self.setup_title_buttons(mdi)

    def _on_mdi_state(self, mdi, state: dict):
        self.apply_mdi_expand(mdi, mdi.get_layout_state("expanded", False))

    def _mdi_bind(self, mdi: MDIWindow):
        if mdi.get_layout_state("size", None) is None:
            mdi.set_layout_state(size=mdi.size[:])
        if mdi.get_layout_state("pos", None) is None:
            mdi.set_layout_state(pos=mdi.pos[:])
        if mdi.get_layout_state("size_hint", None) is None:
            mdi.set_layout_state(size_hint=mdi.size_hint[:])

        self.bind_to(
            mdi,
            state=self._on_mdi_state,
            size_hint=self._save_mdi_state,
            size=self._save_mdi_state,
            pos=self._save_mdi_state,
        )
        self._on_mdi_state(mdi, mdi.state)

    def _save_mdi_state(self, mdi, *args):
        expanded = mdi.get_layout_state("expanded", False)
        flex = mdi.get_layout_state("flex", None) is not None
        if expanded or flex or self._save_lock:
            return
        mdi.set_layout_state(
            size_hint=mdi.size_hint[:],
            size=mdi.size[:],
            pos=mdi.pos[:]
        )

    def do_mdi_unexpand(self, mdi: MDIWindow):
        locked = mdi.get_layout_state("locked", False)
        if locked:
            return
        mdi.set_layout_state(expanded=False)

    def apply_mdi_expand(self, mdi: MDIWindow, expanded: bool):
        self._save_lock = True
        if expanded:
            mdi.size_hint = (1, 1)
            mdi.pos = (0, 0)
        else:
            mdi.size_hint = (None, None)
            mdi.size = mdi.get_layout_state("size", mdi.size[:])
            mdi.pos = mdi.get_layout_state("pos", mdi.pos[:])
        self._save_lock = False

    def get_title_buttons(self) -> List[str]:
        return ["lock", "expand", "close"]

    def hide_mdi(self, mdi: MDIWindow):
        if mdi is None:
            return

        if self._focused_mdi() is mdi:
            self._hide_mdi_focused()

        self.mdi_container._layout_remove_widget(mdi)
        self.unbind_from(mdi)

    def on_start_move(self, mdi: MDIWindow):
        locked = mdi.get_layout_state("locked", False)
        expanded = mdi.get_layout_state("expanded", False)
        if not locked and expanded:
            self.do_mdi_unexpand(mdi)
            mdi.center_x = self._start_mouse_pos[0]
            mdi.top = self._start_mouse_pos[1]
            mdi.x = self._limiter_x(mdi.x)
            mdi.y = self._limiter_y(mdi.y)
            self._start_mdi_pos = mdi.pos[:]

    def on_stop_move(self, mdi: MDIWindow):
        mdi.opacity = 1.0

    def move_mdi(self,
                 mdi: MDIWindow,
                 start_mdi_pos: Tuple[float, float],
                 start_mouse_pos: Tuple[float, float],
                 now_mouse_pos: Tuple[float, float]):
        if mdi.get_layout_state("locked", False):
            return
        start_mdi_x, start_mdi_y = start_mdi_pos
        start_mouse_x, start_mouse_y = start_mouse_pos
        now_mouse_x, now_mouse_y = now_mouse_pos
        mdi.x = self._limiter_x(start_mdi_x + now_mouse_x - start_mouse_x)
        mdi.y = self._limiter_y(start_mdi_y + now_mouse_y - start_mouse_y)
        self._flex_manager(mdi, now_mouse_x, now_mouse_y)

    def create_hotkeys(self) -> Optional[dict]:
        return {
            **super().create_hotkeys(),
            frozenset({"ctrl", "shift", "l"}): self.mdi_invert_locked,
            frozenset({"ctrl", "shift", "e"}): self.mdi_close,
            frozenset({"ctrl", "shift", "u"}): self.mdi_invert_expanded,
            frozenset({"ctrl", "shift", "up"}): self.mdi_do_expand,
            frozenset({"ctrl", "shift", "down"}): self.mdi_do_unexpand,
        }

    def _flex_manager(self, mdi, mouse_x, mouse_y):
        mdc = self.mdi_container
        mouse_hint_x = mouse_x / mdc.width
        mouse_hint_y = mouse_y / mdc.height

        if mouse_hint_x < 0.1:
            width = mdc.width / 6 if mouse_hint_x < 0.05 else mdc.width / 3
            flex_type = FlexMode.LEFT
            x = 0

        elif mouse_hint_x > 0.9:
            width = mdc.width / 6 if mouse_hint_x > 0.95 else mdc.width / 3
            flex_type = FlexMode.RIGHT
            x = mdc.width - width

        elif mouse_hint_y < 0.2:
            width = mdc.width / 3
            flex_type = FlexMode.VERTICAL
            x = self._limiter_x(mouse_x - width / 2)

        else:
            self._reset_flex(mdi)
            return

        if self._get_mdi_flex_state(mdi) is None:
            self._start_flex(mdi, flex_type)

        self._apply_flex_style(mdi, width, x)

    def _apply_flex_style(self, mdi, width, x):
        mdi.opacity = self.FLEX_OPACITY
        mdi.size_hint = (None, 1.0)
        mdi.width = width
        mdi.pos = (x, 0)

    def _start_flex(self, mdi: MDIWindow, flex_type: FlexMode):
        mdi.set_layout_state(
            size_hint=mdi.size_hint[:],
            size=mdi.size[:],
            pos=mdi.pos[:],
            flex=flex_type,
        )

    def _reset_flex(self, mdi):
        if self._get_mdi_flex_state(mdi) is not None:
            mdi.size_hint = mdi.get_layout_state("size_hint", (None, None))
            mdi.size = mdi.get_layout_state("size", mdi.size[:])
            mdi.pos = mdi.get_layout_state("pos", mdi.pos[:])
            mdi.set_layout_state(flex=None)
            mdi.opacity = 1

    def _get_mdi_flex_state(self, mdi: MDIWindow):
        return mdi.get_layout_state("flex", None)

    def resize_mdi(self, side: WidgetSide, mdi: MDIWindow,
                   mouse_pos: Tuple[float, float]):
        locked = mdi.get_layout_state("locked", False)
        expanded = mdi.get_layout_state("expanded", False)
        if locked or expanded:
            return

        mouse_x, mouse_y = mouse_pos
        container = self.mdi_container
        flex_state = self._get_mdi_flex_state(mdi)

        new_width = mdi.width
        new_height = mdi.height
        x = mdi.x
        y = mdi.y

        # Правый край
        if side in RIGHT_WIDGET_SIDES and flex_state is not FlexMode.RIGHT:
            new_width = min(mouse_x - mdi.x, container.width - mdi.x)
        # Левый край
        elif side in LEFT_WIDGET_SIDES and flex_state is not FlexMode.LEFT:
            new_x = max(0, mouse_x)
            new_width = mdi.right - new_x
            if new_width >= mdi.window_minimum_width:
                x = new_x
                new_width = min(new_width, container.width - x)
            else:
                new_width = mdi.window_minimum_width
                x = mdi.right - new_width

        # Верхний/нижний край
        if flex_state is None:
            if side in TOP_WIDGET_SIDES:
                new_height = min(mouse_y - mdi.y, container.height - mdi.y)
            elif side in BOTTOM_WIDGET_SIDES:
                new_y = max(0, mouse_y)
                new_height = mdi.top - new_y
                if new_height >= mdi.window_minimum_height:
                    y = new_y
                    new_height = min(new_height, container.height - y)
                else:
                    new_height = mdi.window_minimum_height
                    y = mdi.top - new_height

        mdi.width = max(new_width, mdi.window_minimum_width)
        mdi.height = max(new_height, mdi.window_minimum_height)
        mdi.x = max(0, min(x, container.width - mdi.width))
        mdi.y = max(0, min(y, container.height - mdi.height))

    def on_mdi_focus(self, mdi: MDIWindow):
        self._move_widget_on_top(mdi)

    def _move_widget_on_top(self, mdi: MDIWindow):
        if mdi.parent is not None:
            self.mdi_container._layout_remove_widget(mdi)
        self.mdi_container._layout_add_widget(mdi)
        for locked_mdi in (i for i in self.mdi_container.mdi_list_showed if i.get_layout_state("locked", False)):
            self.mdi_container._layout_remove_widget(locked_mdi)
            self.mdi_container._layout_add_widget(locked_mdi)

    def _on_double_tap(self, touch, mdi: MDIWindow) -> bool:
        mdi.set_layout_state(expanded=not mdi.get_layout_state("expanded", False))
        return True

    def _limiter_x(self, x: float):
        mdi = self._focused_mdi()
        return max(0, min(x, self.mdi_container.width - mdi.width))

    def _limiter_y(self, y: float) -> float:
        mdi = self._focused_mdi()
        return max(0, min(y, self.mdi_container.height - mdi.height))

    def _hide_mdi_focused(self):
        showed = self.mdi_container.mdi_list_showed
        if len(showed) == 1:
            return
        self.mdi_container.switch_focus()

    def _set_focus(self, mdi: MDIWindow):
        self.mdi_container.set_focus(mdi)

    def find_mdi_at_pos(self, pos: Tuple[float, float]):
        return next(
            (mdi for mdi in self.mdi_container.children
             if mdi.collide_point(*pos)),
            None,
        )

    def _transform_to_that_layout_mode(self, from_layout_mode: ILayoutMode):
        from .tiling import TilingLayoutMode
        if isinstance(from_layout_mode, TilingLayoutMode):
            container = self.mdi_container
            for mdi in container.mdi_list_showed:
                mdi.parent.remove_widget(mdi)
            container._clear_layout_widgets()
            for mdi in container.mdi_list_showed:
                from_layout_mode.unbind_from(mdi)
                self._mdi_bind(mdi)
                size = mdi.size[:]
                mdi.size_hint = (None, None)
                mdi.size = size
                mdi.pos = mdi.pos[:]
                self.setup_title_buttons(mdi)
                self.mdi_container._layout_add_widget(mdi)
