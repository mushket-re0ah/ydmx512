from kivy.app import App
from ui.components.mdi_window import MDIWindow
from libs.kivy_utils import (
    WidgetSide, LEFT_WIDGET_SIDES, RIGHT_WIDGET_SIDES, TOP_WIDGET_SIDES,
    BOTTOM_WIDGET_SIDES, WIDGET_SIDE_CURSOR, get_cursor_zone
)
from typing import Tuple, Union, Optional
from ui.mdi.window_manager.interface import IWindowManager
from database import db
from database.mdi_manager import FlexManager
from kivy.clock import Clock


class FloatingWindowManager(IWindowManager):
    title = "Плавающие окна"
    FLEX_OPACITY = 0.4

    def _can_start_resize(self, touch, mdi, side) -> bool:
        return side != WidgetSide.VOID

    def _can_start_move(self, touch, mdi, side) -> bool:
        return mdi.title_bar_label.collide_point(*touch.pos) and side == WidgetSide.VOID

    def db_sync(self):
        layout = self.mdi_container.db_row.layout
        if not layout:
            return
        for mdi_title_id in layout[:]:
            mdi = App.get_running_app().get_mdi_by_title_id(mdi_title_id)
            mdi.open(workspace_index=self.mdi_container.index)

    def sync_mdi_list_showed(self):
        mdi_list = self.mdi_container.mdi_list_showed
        self.mdi_container.db_row.edit(layout=[
            mdi._db_title_id for mdi in mdi_list
        ])

    def show_mdi(self, mdi: MDIWindow):
        self.mdi_container.add_widget(mdi)
        db.mdi_manager.mdi_data.set_mdi_state(mdi)
        self._ensure_floating_size_hint(mdi)
        self._mdi_bind(mdi)

    def _save_mdi_state(self, mdi, *_):
        db.mdi_manager.mdi_data.set_size_hint(mdi._db_title_id, mdi.size_hint)
        db.mdi_manager.mdi_data.set_size(mdi._db_title_id, mdi.size)
        db.mdi_manager.mdi_data.set_pos(mdi._db_title_id, mdi.pos)

    def _mdi_bind(self, mdi: MDIWindow):
        self.bind_to(mdi,
            size_hint=self._save_mdi_state,
            size=self._save_mdi_state,
            pos=self._save_mdi_state,
            expanded=self.on_mdi_expand
        )

    def hide_mdi(self, mdi: MDIWindow):
        if mdi is None:
            return

        if self._focused_mdi() is mdi:
            self.__hide_mdi_focused()

        self.mdi_container.remove_widget(mdi)
        self.unbind_from(mdi)

    def on_start_move(self, mdi: MDIWindow):
        if not mdi.locked and mdi.expanded:
            mdi.do_unexpand()
            mdi.center_x = self._start_mouse_pos[0]
            mdi.top = self._start_mouse_pos[1]
            mdi.x = self.__limiter_x(mdi.x)
            mdi.y = self.__limiter_y(mdi.y)
            self._start_mdi_pos = mdi.pos[:]

    def on_stop_move(self, mdi: MDIWindow):
        mdi.opacity = 1.0

    def move_mdi(self, mdi: MDIWindow,
                 start_mdi_pos: Tuple[float, float],
                 start_mouse_pos: Tuple[float, float],
                 now_mouse_pos: Tuple[float, float]):
        start_mdi_x, start_mdi_y = start_mdi_pos
        start_mouse_x, start_mouse_y = start_mouse_pos
        now_mouse_x, now_mouse_y = now_mouse_pos
        mdi.x = self.__limiter_x(start_mdi_x + now_mouse_x - start_mouse_x)
        mdi.y = self.__limiter_y(start_mdi_y + now_mouse_y - start_mouse_y)
        self.__flex_manager(mdi, now_mouse_x, now_mouse_y)

    def on_mdi_expand(self, mdi: MDIWindow, expanded: bool):
        if expanded:
            db.mdi_manager.mdi_data.save_mdi_state(mdi)
            mdi.size_hint = (1, 1)
            mdi.pos = (0, 0)
        else:
            mdi.size_hint = (None, None)
            db.mdi_manager.mdi_data.load_mdi_state(mdi)

    def create_hotkeys(self) -> Optional[dict]:
        return {
            frozenset({"tab"}): self.switch_focus,
        }

    def __flex_manager(self, mdi, mouse_x, mouse_y):
        mdc = self.mdi_container
        mouse_hint_x = mouse_x / mdc.width
        mouse_hint_y = mouse_y / mdc.height

        if mouse_hint_x < 0.1:
            width = mdc.width / 6 if mouse_hint_x < 0.05 else mdc.width / 3
            flex_type = FlexManager.LEFT
            x = 0

        elif mouse_hint_x > 0.9:
            width = mdc.width / 6 if mouse_hint_x > 0.95 else mdc.width / 3
            flex_type = FlexManager.RIGHT
            x = mdc.width - width

        elif mouse_hint_y < 0.2:
            width = mdc.width / 3
            flex_type = FlexManager.VERTICAL
            x = self.__limiter_x(mouse_x - width / 2)

        else:
            self.__reset_flex(mdi)
            return

        if self.__get_mdi_flex_state(mdi) is None:
            self.__start_flex(mdi, flex_type)

        self.__apply_flex_style(mdi, width, x)

    def __apply_flex_style(self, mdi, width, x):
        mdi.opacity = self.FLEX_OPACITY
        mdi.size_hint = (None, 1.0)
        mdi.width = width
        mdi.pos = (x, 0)

    def __start_flex(self, mdi: MDIWindow, flex_type: FlexManager):
        db.mdi_manager.mdi_data.save_mdi_state(mdi)
        db.mdi_manager.mdi_data.set_flex(mdi._db_title_id, flex_type)

    def __reset_flex(self, mdi):
        if self.__get_mdi_flex_state(mdi) is not None:
            db.mdi_manager.mdi_data.set_flex(mdi._db_title_id, None)
            db.mdi_manager.mdi_data.load_mdi_state(mdi)
            mdi.opacity = 1

    def __get_mdi_flex_state(self, mdi: MDIWindow):
        return db.mdi_manager.mdi_data.get_mdi_state(mdi._db_title_id).flex

    def resize_mdi(self, side: WidgetSide, mdi: MDIWindow,
                   mouse_pos: Tuple[float, float]):
        if mdi.locked or mdi.expanded:
            return

        mouse_x, mouse_y = mouse_pos
        new_width = mdi.width
        new_height = mdi.height
        x = mdi.x
        y = mdi.y
        container = self.mdi_container
        flex_state = self.__get_mdi_flex_state(mdi)

        # Обработка горизонтального ресайза
        if side in RIGHT_WIDGET_SIDES and flex_state is not FlexManager.RIGHT:
            new_width = min(mouse_x - mdi.x, container.width - mdi.x)
        elif side in LEFT_WIDGET_SIDES and flex_state is not FlexManager.LEFT:
            new_x = max(container.x, mouse_x)
            new_width = mdi.right - new_x
            if new_width >= mdi.real_minimum_width:
                x = new_x
                new_width = min(new_width, container.width - x)
            else:
                new_width = mdi.real_minimum_width
                x = mdi.right - new_width

        # Обработка вертикального ресайза
        if flex_state is None:
            if side in TOP_WIDGET_SIDES:
                new_height = min(mouse_y - mdi.y, container.height - mdi.y)
            elif side in BOTTOM_WIDGET_SIDES:
                new_y = max(container.y, mouse_y)
                new_height = mdi.top - new_y
                if new_height >= mdi.real_minimum_height:
                    y = new_y
                    new_height = min(new_height, container.height - y)
                else:
                    new_height = mdi.real_minimum_height
                    y = mdi.top - new_height

        mdi.width = max(new_width, mdi.real_minimum_width)
        mdi.height = max(new_height, mdi.real_minimum_height)
        mdi.x = max(container.x, min(x, container.width - mdi.width))
        mdi.y = max(container.y, min(y, container.height - mdi.height))

    def on_mdi_focus(self, mdi: MDIWindow):
        self.__move_widget_on_top(mdi)

    def __move_widget_on_top(self, mdi: MDIWindow):
        if mdi.parent is not None:
            mdi.parent.remove_widget(mdi)
        self.mdi_container.add_widget(mdi)
        for locked_mdi in (i for i in self.mdi_container.mdi_list_showed if i.locked):
            self.mdi_container.remove_widget(locked_mdi)
            self.mdi_container.add_widget(locked_mdi)

    def __limiter_x(self, x: float):
        mdi = self._focused_mdi()
        return max(mdi.parent.x, min(x, mdi.parent.width - mdi.width))

    def __limiter_y(self, y: float) -> float:
        mdi = self._focused_mdi()
        return max(mdi.parent.y, min(y, mdi.parent.height - mdi.height))

    def __hide_mdi_focused(self):
        showed = self.mdi_container.mdi_list_showed
        if len(showed) == 1:
            return
        self.mdi_container.switch_focus()

    def _set_focus(self, mdi: MDIWindow):
        self.mdi_container.set_focus(mdi)

    def _ensure_floating_size_hint(self, mdi):
        """Гарантируем, что окно не имеет тайлового size_hint."""
        if mdi.size_hint != (None, None):
            mdi.size_hint = (None, None)
            db.mdi_manager.mdi_data.set_size_hint(mdi._db_title_id, (None, None))

    def _transform_to_that_window_manager(self, from_wm: IWindowManager):
        from ui.mdi.window_manager.tiling import TilingWindowManager
        if isinstance(from_wm, TilingWindowManager):
            container = self.mdi_container
            for mdi in container.mdi_list_showed:
                mdi.parent.remove_widget(mdi)
            container.clear_widgets()
            for mdi in container.mdi_list_showed:
                from_wm.unbind_from(mdi)
                self._mdi_bind(mdi)
                size = mdi.size[:]
                mdi.size_hint = (None, None)
                mdi.size = size
                mdi.pos = mdi.pos[:]
                container.add_widget(mdi)
                self._ensure_floating_size_hint(mdi)
            self.sync_mdi_list_showed()
