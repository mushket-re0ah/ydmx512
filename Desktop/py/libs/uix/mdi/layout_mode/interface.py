from typing import TYPE_CHECKING, Callable, Dict, FrozenSet, List, Optional, Tuple

from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.input.motionevent import MotionEvent

from libs.kivy_mixins import AutoUnbindBehavior
from libs.kivy_utils import WIDGET_SIDE_CURSOR, WidgetSide, get_cursor_zone
from libs.mouse_manager import cursor_manager
from libs.sdl2_keyboard import KeyboardBehavior
from libs.uix.context_menu import ContextMenu, ContextMenuItem, ContextMenuTemplates
from libs.uix.mdi.mdi_button import MDIButtonClose, MDIButtonExpand, MDIButtonLock
from libs.uix.mdi.mdi_window import MDIWindow

if TYPE_CHECKING:
    from libs.uix.mdi.mdi_container import MDIContainer


class ILayoutMode(AutoUnbindBehavior, KeyboardBehavior, EventDispatcher):
    layout_state_key: str
    title: str
    mdi_container: "MDIContainer"

    def __init__(
            self,
            mdi_container: "MDIContainer",
            from_layout_mode: Optional["ILayoutMode"]
        ):
        super().__init__()
        self.register_event_type("on_layout_changed")
        self.mdi_container = mdi_container

        self._resizing: bool = False
        self._moving: bool = False
        self._resize_side: Optional[WidgetSide] = None
        self._start_mdi_pos: Tuple[float, float] = (0, 0)
        self._start_mouse_pos: Tuple[float, float] = (0, 0)
        self._last_mouse_pos: Tuple[float, float] = (0, 0)
        self._trigger_resize = Clock.create_trigger(self._apply_resize, -1)
        self._trigger_move = Clock.create_trigger(self._apply_move, -1)

        self._mdi_on_cursor: Optional[MDIWindow] = None
        self._widget_side_now: WidgetSide = WidgetSide.VOID
        self._prev_mdi_on_cursor: Optional[MDIWindow] = None

        if from_layout_mode:
            self._transform_to_that_layout_mode(from_layout_mode)

    def sync_mdi_list_showed(self, mdi_list_showed: List[MDIWindow]):
        self.dispatch("on_layout_changed", self.get_layout())

    def on_layout_changed(self, layout: List[MDIWindow]):
        pass

    def get_layout(self) -> List[MDIWindow]:
        return list(reversed(self.mdi_container.mdi_list_showed))

    def load_layout(self, layout: List[MDIWindow]):
        self.mdi_container.clear_widgets()
        for mdi in layout:
            self.mdi_container.add_widget(mdi)

    def create_hotkeys(self) -> Dict[FrozenSet[str], Callable[[], None]]:
        return {
            frozenset({"tab"}): self.mdi_container.switch_focus,
        }

    def setup_title_buttons(self, mdi: MDIWindow):
        title_bar = mdi.title_bar
        title_bar.clear_widgets()
        title_bar.add_widget(mdi.title_bar_label)

        buttons = self.get_title_buttons()

        if "lock" in buttons:
            title_bar.add_widget(MDIButtonLock(mdi=mdi))
        if "expand" in buttons:
            title_bar.add_widget(MDIButtonExpand(mdi=mdi))
        if "close" in buttons:
            title_bar.add_widget(MDIButtonClose(mdi=mdi))

    def get_title_buttons(self) -> List[str]:
        return []

    def mdi_invert_locked(self, mdi: Optional[MDIWindow]=None):
        if not mdi:
            mdi = self._focused_mdi()
        if mdi is None:
            return
        locked = mdi.get_layout_state("locked", False)
        mdi.set_layout_state(locked=not locked)
        if not locked:
            self.on_mdi_focus(mdi)

    def mdi_close(self, mdi: Optional[MDIWindow]=None):
        if not mdi:
            mdi = self._focused_mdi()
        if mdi is not None:
            self.mdi_container.remove_widget(mdi)

    def mdi_invert_expanded(self, mdi: Optional[MDIWindow]=None):
        if not mdi:
            mdi = self._focused_mdi()
        if mdi is None:
            return
        if mdi.get_layout_state("locked", False):
            return
        mdi.set_layout_state(
            expanded=not mdi.get_layout_state("expanded", False)
        )

    def mdi_do_expand(self, mdi: Optional[MDIWindow]=None):
        if not mdi:
            mdi = self._focused_mdi()
        if mdi is None:
            return
        if mdi.get_layout_state("locked", False):
            return
        mdi.set_layout_state(expanded=True)

    def mdi_do_unexpand(self, mdi: Optional[MDIWindow]=None):
        if not mdi:
            mdi = self._focused_mdi()
        if mdi is None:
            return
        if mdi.get_layout_state("locked", False):
            return
        mdi.set_layout_state(expanded=False)

    def is_busy(self) -> bool:
        return self._resizing or self._moving

    def handle_touch_down(self, touch: MotionEvent) -> bool:
        self._update_cursor_zone(touch.pos)
        mdi = self._mdi_on_cursor

        if not mdi or not mdi.collide_point(*touch.pos):
            return False

        self.mdi_container.set_focus(mdi)

        if touch.is_double_tap and self._is_double_tap_target(touch, mdi):
            return self._on_double_tap(touch, mdi)

        if self._is_title_bar_clicked(touch) and touch.button == "right":
            self._on_title_right_click(touch, mdi)
            return True

        if self._try_start_resize_or_move(touch, mdi):
            return True

        return mdi.dispatch("on_touch_down", touch)

    def handle_touch_move(self, touch: MotionEvent) -> bool:
        if self._resizing or self._moving:
            self._last_mouse_pos = touch.pos
            if self._resizing:
                self._trigger_resize()
            elif self._moving:
                self._trigger_move()
            return True
        if self._mdi_on_cursor:
            return self._mdi_on_cursor.dispatch("on_touch_move", touch)
        return False

    def handle_touch_up(self, touch: MotionEvent) -> bool:
        if self._resizing:
            self._resizing = False
            self._resize_side = None
            self.on_stop_resize(self._focused_mdi())
            self._update_cursor_zone(touch.pos)
            self._set_cursor()
            cursor_manager.set_force(False)
            return True
        if self._moving:
            self._moving = False
            self.on_stop_move(self._focused_mdi())
            self._update_cursor_zone(touch.pos)
            self._set_cursor()
            cursor_manager.set_force(False)
            return True
        if self._mdi_on_cursor:
            return self._mdi_on_cursor.dispatch("on_touch_up", touch)
        return False

    def handle_mouse_move(self, pos: Tuple[float, float]):
        self._update_cursor_zone(pos)
        self._set_cursor()

    def _update_cursor_zone(self, pos: Tuple[float, float]):
        if self.is_busy():
            return
        self._mdi_on_cursor = self.find_mdi_at_pos(pos)
        if self._mdi_on_cursor:
            self._widget_side_now = get_cursor_zone(self._mdi_on_cursor, pos)
        else:
            self._widget_side_now = WidgetSide.VOID
        if self._prev_mdi_on_cursor is not self._mdi_on_cursor:
            if self._prev_mdi_on_cursor:
                self._prev_mdi_on_cursor.focus_selected = False
            if self._mdi_on_cursor:
                self._mdi_on_cursor.focus_selected = True
            self._prev_mdi_on_cursor = self._mdi_on_cursor

    def find_mdi_at_pos(self, pos: Tuple[float, float]) -> Optional[MDIWindow]:
        return next(
            (mdi for mdi in reversed(self.mdi_container.mdi_list_showed)
                 if mdi.collide_point(*pos)),
            None
        )

    def _set_cursor(self):
        if self.is_busy():
            return
        cursor_manager.set_cursor(WIDGET_SIDE_CURSOR[self._widget_side_now])

    def _is_title_bar_clicked(self, touch: MotionEvent) -> bool:
        mdi = self._mdi_on_cursor
        return mdi and mdi.title_bar_label.collide_point(*touch.pos)

    def _is_double_tap_target(self, touch: MotionEvent, mdi: MDIWindow) -> bool:
        return (mdi.title_bar_label.collide_point(*touch.pos) or
                self._widget_side_now != WidgetSide.VOID)

    def _on_double_tap(self, touch: MotionEvent, mdi: MDIWindow) -> bool:
        return True

    def _on_title_right_click(self, touch: MotionEvent, mdi: MDIWindow) -> bool:
        self._mdi_open_context_menu(mdi, touch.pos)
        return True

    def _mdi_open_context_menu(self, mdi: MDIWindow, pos: Tuple[float, float]):
        buttons = self.get_title_buttons()
        items: List[ContextMenuItem] = []

        if "lock" in buttons:
            items.append(self._create_context_menu_lock_btn(mdi))
        if "expand" in buttons:
            items.append(self._create_context_menu_expand_btn(mdi))
        if "close" in buttons:
            items.append(self._create_context_menu_close_btn(mdi))

        ContextMenu(items=items).open(mdi, pos=pos)

    def _create_context_menu_lock_btn(self, mdi: MDIWindow) -> ContextMenuItem:
        return ContextMenuTemplates.button(
            text="Разблокировать" if mdi.get_layout_state("locked", False) else "Заблокировать",
            on_release=lambda _: self.mdi_invert_locked(mdi),
            hotkey=frozenset({"ctrl", "shift", "l"}),
        )

    def _create_context_menu_expand_btn(self, mdi: MDIWindow) -> ContextMenuItem:
        return ContextMenuTemplates.button(
            text="Свернуть" if mdi.get_layout_state("expanded", False) else "Развернуть",
            on_release=lambda _: self.mdi_invert_expanded(mdi),
            hotkey=frozenset({"ctrl", "shift", "u"}),
            disabled=mdi.get_layout_state("locked", False)
        )

    def _create_context_menu_close_btn(self, mdi: MDIWindow) -> ContextMenuItem:
        return ContextMenuTemplates.button(
            text="Закрыть",
            on_release=lambda _: self.mdi_close(mdi),
            hotkey=frozenset({"ctrl", "shift", "e"}),
        )

    def _try_start_resize_or_move(self, touch: MotionEvent, mdi: MDIWindow) -> bool:
        side = self._widget_side_now
        if self._can_start_resize(touch, mdi, side):
            return self._start_resize(touch, mdi, side)
        if self._can_start_move(touch, mdi, side):
            return self._start_move(touch, mdi, side)
        return False

    def _start_resize(self, touch: MotionEvent, mdi: MDIWindow, side: WidgetSide) -> bool:
        self._resizing = True
        self._resize_side = side
        self._last_mouse_pos = touch.pos
        self.on_start_resize(mdi)
        cursor_manager.set_cursor(WIDGET_SIDE_CURSOR[side])
        cursor_manager.set_force(True)
        return True

    def _start_move(self, touch: MotionEvent, mdi: MDIWindow, side: WidgetSide) -> bool:
        self._moving = True
        self._start_mouse_pos = touch.pos
        self._start_mdi_pos = mdi.pos[:]
        self._last_mouse_pos = touch.pos
        self.on_start_move(mdi)
        cursor_manager.set_cursor("size_all")
        cursor_manager.set_force(True)
        return True

    def _can_start_resize(self, touch: MotionEvent, mdi: MDIWindow, side: WidgetSide) -> bool:
        return False

    def _can_start_move(self, touch: MotionEvent, mdi: MDIWindow, side: WidgetSide) -> bool:
        return False

    def _apply_resize(self, _):
        mdi = self._focused_mdi()
        if mdi and self._resize_side is not None:
            self.resize_mdi(self._resize_side, mdi, self._last_mouse_pos)

    def _apply_move(self, _):
        mdi = self._focused_mdi()
        if mdi and self._moving:
            self.move_mdi(mdi, self._start_mdi_pos, self._start_mouse_pos, self._last_mouse_pos)

    def on_start_resize(self, mdi: MDIWindow): return
    def on_stop_resize(self, mdi: MDIWindow): return
    def on_start_move(self, mdi: MDIWindow): return
    def on_stop_move(self, mdi: MDIWindow): return

    def show_mdi(self, mdi: MDIWindow):
        state = mdi.state.get("layout_state", {})

        if state.get("layout") != self.layout_state_key:
            mdi.clear_layout_state()
            mdi.set_layout_state(layout=self.layout_state_key)

    def hide_mdi(self, mdi: Optional[MDIWindow]): return
    def move_mdi(self, mdi: MDIWindow, start_mdi_pos: Tuple[float, float],
                 start_mouse_pos: Tuple[float, float], now_mouse_pos: Tuple[float, float]): return
    def resize_mdi(self, side: WidgetSide, mdi: MDIWindow, mouse_pos: Tuple[float, float]): return
    def on_mdi_focus(self, mdi: MDIWindow): return

    def _transform_to_that_layout_mode(self, from_layout_mode: "ILayoutMode"):
        self.mdi_container.clear_widgets()

    def _focused_mdi(self) -> Optional[MDIWindow]:
        return self.mdi_container.mdi_focused
