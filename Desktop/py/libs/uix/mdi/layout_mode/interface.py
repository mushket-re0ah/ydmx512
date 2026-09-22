from kivy.event import EventDispatcher
from kivy.clock import Clock
from libs.uix.mdi.mdi_window import MDIWindow
from libs.kivy_utils import WidgetSide, AutoUnbindBehavior, WIDGET_SIDE_CURSOR, get_cursor_zone
from libs.sdl2_keyboard import KeyboardBehavior
from libs.mouse_manager import cursor_manager
from typing import Optional, List, Tuple
from libs.uix.context_menu import ContextMenu, ContextMenuTemplates
from ..mdi_button import MDIButtonLock, MDIButtonExpand, MDIButtonClose


class ILayoutMode(AutoUnbindBehavior, KeyboardBehavior, EventDispatcher):
    layout_state_key = None
    title = None
    mdi_container = None

    def __init__(self, mdi_container: "MDIContainer",
                 from_layout_mode: Optional["ILayoutMode"]):
        super().__init__()
        self.register_event_type("on_layout_changed")
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

        if from_layout_mode:
            self._transform_to_that_layout_mode(from_layout_mode)

    def sync_mdi_list_showed(self, mdi_list_showed: List[MDIWindow]):
        self.dispatch("on_layout_changed", self.get_layout())

    def on_layout_changed(self, layout):
        pass

    def get_layout(self):
        return [mdi for mdi in reversed(self.mdi_container.mdi_list_showed)]

    def load_layout(self, layout):
        self.mdi_container.clear_widgets()
        for mdi in layout:
            self.mdi_container.add_widget(mdi)

    def create_hotkeys(self) -> Optional[dict]:
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

    def mdi_invert_locked(self, mdi=None):
        if not mdi:
            mdi = self._focused_mdi()
        if mdi is None:
            return
        locked = mdi.get_layout_state("locked", False)
        mdi.set_layout_state(locked=not locked)
        if not locked:
            self.on_mdi_focus(mdi)

    def mdi_close(self, mdi=None):
        if not mdi:
            mdi = self._focused_mdi()
        if mdi is not None:
            self.mdi_container.remove_widget(mdi)

    def mdi_invert_expanded(self, mdi=None):
        if not mdi:
            mdi = self._focused_mdi()
        if mdi is None:
            return
        if mdi.get_layout_state("locked", False):
            return
        mdi.set_layout_state(
            expanded=not mdi.get_layout_state("expanded", False)
        )

    def mdi_do_expand(self, mdi=None):
        if not mdi:
            mdi = self._focused_mdi()
        if mdi is None:
            return
        if mdi.get_layout_state("locked", False):
            return
        mdi.set_layout_state(expanded=True)

    def mdi_do_unexpand(self, mdi=None):
        if not mdi:
            mdi = self._focused_mdi()
        if mdi is None:
            return
        if mdi.get_layout_state("locked", False):
            return
        mdi.set_layout_state(expanded=False)

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

    def find_mdi_at_pos(self, pos: Tuple[float, float]):
        return next((mdi for mdi in reversed(self.mdi_container.mdi_list_showed) if mdi.collide_point(*pos)), None)

    def _set_cursor(self):
        if self.is_busy():
            return
        cursor_manager.set_cursor(WIDGET_SIDE_CURSOR[self._widget_side_now])

    def _is_title_bar_clicked(self, touch) -> bool:
        mdi = self._mdi_on_cursor
        return mdi and mdi.title_bar_label.collide_point(*touch.pos)

    def _is_double_tap_target(self, touch, mdi: MDIWindow) -> bool:
        return (mdi.title_bar_label.collide_point(*touch.pos) or
                self._widget_side_now != WidgetSide.VOID)

    def _on_double_tap(self, touch, mdi: MDIWindow) -> bool:
        return True

    def _on_title_right_click(self, touch, mdi: MDIWindow) -> bool:
        self._mdi_open_context_menu(mdi, touch.pos)
        return True

    def _mdi_open_context_menu(self, mdi, pos: Tuple[float, float]):
        buttons = self.get_title_buttons()
        items = []

        if "lock" in buttons:
            items.append(self._create_context_menu_lock_btn(mdi))
        if "expand" in buttons:
            items.append(self._create_context_menu_expand_btn(mdi))
        if "close" in buttons:
            items.append(self._create_context_menu_close_btn(mdi))

        ContextMenu(items=items).open(mdi, pos=pos)

    def _create_context_menu_lock_btn(self, mdi: MDIWindow):
        return ContextMenuTemplates.button(
            text="Разблокировать" if mdi.get_layout_state("locked", False) else "Заблокировать",
            on_release=lambda _: self.mdi_invert_locked(mdi),
            hotkey=frozenset({"ctrl", "shift", "l"}),
        )

    def _create_context_menu_expand_btn(self, mdi: MDIWindow):
        return ContextMenuTemplates.button(
            text="Свернуть" if mdi.get_layout_state("expanded", False) else "Развернуть",
            on_release=lambda _: self.mdi_invert_expanded(mdi),
            hotkey=frozenset({"ctrl", "shift", "u"}),
            disabled=mdi.get_layout_state("locked", False)
        )

    def _create_context_menu_close_btn(self, mdi: MDIWindow):
        return ContextMenuTemplates.button(
            text="Закрыть",
            on_release=lambda _: self.mdi_close(mdi),
            hotkey=frozenset({"ctrl", "shift", "e"}),
        )

    def _try_start_resize_or_move(self, touch, mdi: MDIWindow) -> bool:
        side = self._widget_side_now
        if self._can_start_resize(touch, mdi, side):
            return self._start_resize(touch, mdi, side)
        if self._can_start_move(touch, mdi, side):
            return self._start_move(touch, mdi, side)
        return False

    def _start_resize(self, touch, mdi: MDIWindow, side) -> bool:
        self._resizing = True
        self._resize_side = side
        self._last_mouse_pos = touch.pos
        self.on_start_resize(mdi)
        cursor_manager.set_cursor(WIDGET_SIDE_CURSOR[side])
        cursor_manager.set_force(True)
        return True

    def _start_move(self, touch, mdi: MDIWindow, side) -> bool:
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

    def _apply_resize(self, dt):
        mdi = self._focused_mdi()
        if mdi and self._resize_side is not None:
            self.resize_mdi(self._resize_side, mdi, self._last_mouse_pos)

    def _apply_move(self, dt):
        mdi = self._focused_mdi()
        if mdi and self._moving:
            self.move_mdi(mdi, self._start_mdi_pos, self._start_mouse_pos, self._last_mouse_pos)

    def on_start_resize(self, mdi): pass
    def on_stop_resize(self, mdi): pass
    def on_start_move(self, mdi): pass
    def on_stop_move(self, mdi): pass

    def show_mdi(self, mdi):
        state = mdi.state.get("layout_state", {})

        if state.get("layout") != self.layout_state_key:
            mdi.clear_layout_state()
            mdi.set_layout_state(layout=self.layout_state_key)

    def hide_mdi(self, mdi): pass
    def move_mdi(self, mdi, start_mdi_pos, start_mouse_pos, now_mouse_pos): pass
    def resize_mdi(self, side, mdi_now, mouse_pos): pass
    def on_mdi_focus(self, mdi): pass

    def _transform_to_that_layout_mode(self, from_layout_mode):
        self.mdi_container.clear_widgets()

    def _focused_mdi(self) -> Optional[MDIWindow]:
        return self.mdi_container.mdi_focused
