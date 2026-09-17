from kivy.event import EventDispatcher
from kivy.clock import Clock
from ui.components.mdi_window import MDIWindow
from libs.kivy_utils import WidgetSide, AutoUnbindBehavior, WIDGET_SIDE_CURSOR, get_cursor_zone
from libs.sdl2_keyboard import KeyboardBehavior
from libs.mouse_manager import cursor_manager
from typing import Optional, List, Tuple


class IWindowManager(AutoUnbindBehavior, KeyboardBehavior, EventDispatcher):
    title = None
    mdi_container = None

    def __init__(self, mdi_container: "MDIContainer",
                 from_wm: Optional["IWindowManager"]):
        super().__init__()
        self.mdi_container = mdi_container

        self._resizing = False
        self._moving = False
        self._resize_side = None
        self._start_mdi_pos = (0, 0)
        self._start_mouse_pos = (0, 0)
        self._last_mouse_pos = (0, 0)
        self._trigger_resize = Clock.create_trigger(self._apply_resize, -1)
        self._trigger_move = Clock.create_trigger(self._apply_move, -1)

        self._mdi_on_cursor: Optional[MDIWindow] = None
        self._widget_side_now = WidgetSide.VOID
        self._prev_mdi_on_cursor: Optional[MDIWindow] = None

        if from_wm:
            self._transform_to_that_window_manager(from_wm)

    def get_title_buttons(self) -> List[str]:
        return ["lock", "expand", "close"]

    def is_busy(self) -> bool:
        return self._resizing or self._moving

    def handle_touch_down(self, touch) -> bool:
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

    def handle_touch_move(self, touch) -> bool:
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

    def handle_touch_up(self, touch) -> bool:
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

    def handle_mouse_move(self, pos: Tuple[float, float]) -> None:
        self._update_cursor_zone(pos)
        self._set_cursor()

    def _update_cursor_zone(self, pos: Tuple[float, float]):
        if self.is_busy():
            return
        self._mdi_on_cursor = self.find_mdi_at_pos(pos)
        self._widget_side_now = get_cursor_zone(self._mdi_on_cursor, pos) if self._mdi_on_cursor else WidgetSide.VOID
        if self._prev_mdi_on_cursor is not self._mdi_on_cursor:
            if self._prev_mdi_on_cursor:
                self._prev_mdi_on_cursor.focus_selected = False
            if self._mdi_on_cursor:
                self._mdi_on_cursor.focus_selected = True
            self._prev_mdi_on_cursor = self._mdi_on_cursor

    def find_mdi_at_pos(self, pos):
        return next((mdi for mdi in reversed(self.mdi_container.mdi_list_showed) if mdi.collide_point(*pos)), None)

    def _set_cursor(self):
        if self.is_busy():
            return
        cursor_manager.set_cursor(WIDGET_SIDE_CURSOR[self._widget_side_now])

    def _is_title_bar_clicked(self, touch) -> bool:
        mdi = self._mdi_on_cursor
        return mdi and mdi.title_bar_label.collide_point(*touch.pos)

    def _is_double_tap_target(self, touch, mdi) -> bool:
        return (mdi.title_bar_label.collide_point(*touch.pos) or
                self._widget_side_now != WidgetSide.VOID)

    def _on_double_tap(self, touch, mdi) -> bool:
        mdi.invert_expanded()
        return True

    def _on_title_right_click(self, touch, mdi) -> bool:
        mdi.open_context_menu(touch.pos)
        return True

    def _try_start_resize_or_move(self, touch, mdi) -> bool:
        side = self._widget_side_now
        if self._can_start_resize(touch, mdi, side):
            return self._start_resize(touch, mdi, side)
        if self._can_start_move(touch, mdi, side):
            return self._start_move(touch, mdi, side)
        return False

    def _start_resize(self, touch, mdi, side) -> bool:
        self._resizing = True
        self._resize_side = side
        self._last_mouse_pos = touch.pos
        self.on_start_resize(mdi)
        cursor_manager.set_cursor(WIDGET_SIDE_CURSOR[side])
        cursor_manager.set_force(True)
        return True

    def _start_move(self, touch, mdi, side) -> bool:
        self._moving = True
        self._start_mouse_pos = touch.pos
        self._start_mdi_pos = mdi.pos[:]
        self._last_mouse_pos = touch.pos
        self.on_start_move(mdi)
        cursor_manager.set_cursor("size_all")
        cursor_manager.set_force(True)
        return True

    def _can_start_resize(self, touch, mdi, side) -> bool:
        return False

    def _can_start_move(self, touch, mdi, side) -> bool:
        return False

    def on_start_resize(self, mdi): pass
    def on_stop_resize(self, mdi): pass
    def on_start_move(self, mdi): pass
    def on_stop_move(self, mdi): pass

    def _apply_resize(self, dt):
        mdi = self._focused_mdi()
        if mdi and self._resize_side is not None:
            self.resize_mdi(self._resize_side, mdi, self._last_mouse_pos)

    def _apply_move(self, dt):
        mdi = self._focused_mdi()
        if mdi and not mdi.locked:
            self.move_mdi(mdi, self._start_mdi_pos, self._start_mouse_pos, self._last_mouse_pos)

    def _handle_hide_focused_mdi(self):
        self.mdi_container.hide_focused_mdi()

    def switch_focus(self):
        self.mdi_container.switch_focus()

    def _handle_expand(self):
        self.mdi_container.expand_focused_mdi()

    def _handle_unexpand(self):
        self.mdi_container.unexpand_focused_mdi()

    def db_sync(self): pass
    def show_mdi(self, mdi): pass
    def hide_mdi(self, mdi): pass
    def move_mdi(self, mdi, start_mdi_pos, start_mouse_pos, now_mouse_pos): pass
    def resize_mdi(self, side, mdi_now, mouse_pos): pass
    def on_mdi_expand(self, mdi): pass
    def on_mdi_list_showed(self, mdi_list): pass
    def on_mdi_focus(self, mdi): pass

    def _transform_to_that_window_manager(self, from_wm):
        self.mdi_container.clear_widgets()

    def _focused_mdi(self) -> Optional[MDIWindow]:
        return self.mdi_container.mdi_focused
