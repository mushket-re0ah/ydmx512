from kivy.clock import Clock
from kivy.properties import (
    ObjectProperty, NumericProperty, AliasProperty, BooleanProperty
)
from kivy.uix.boxlayout import BoxLayout
from typing import Tuple
from kivy.lang import Builder
from kivy.metrics import dp


Builder.load_string("""
#:import uix_cs libs.uix.colorscheme

<ScrollBar>:  # BoxLayout
    layout_cursor: layout_cursor
    cursor: cursor

    size_hint: (None, 1) if self.orientation == "vertical" else (1, None)
    size: (self._default_width, self._default_height)
    canvas.before:
        Color:
            rgba: uix_cs.general.menu_bg
        Rectangle:
            pos: self.pos
            size: self.size

    ArrowImageButton:
        reverse_arrow: True
        vertical_arrow: root.orientation == "vertical"
        arrow_size: ["10dp", "6dp"] if self.vertical_arrow else ["6dp", "10dp"]
        arrow_offset_right: "5dp" if self.vertical_arrow else "8dp"
        size_hint: (1, None) if root.orientation == "vertical" else (None, 1)
        height: root.width
        width: root.height
        on_press: root.on_press_btn_scroll(1)
        disabled: root.scroll_at_start

    RelativeLayout:
        id: layout_cursor
        ImageButton:
            id: cursor

    ArrowImageButton:
        vertical_arrow: root.orientation == "vertical"
        arrow_size: ["10dp", "6dp"] if self.vertical_arrow else ["6dp", "10dp"]
        arrow_offset_right: "5dp" if self.vertical_arrow else "6dp"
        size_hint: (1, None) if root.orientation == "vertical" else (None, 1)
        height: root.width
        width: root.height
        on_press: root.on_press_btn_scroll(-1)
        disabled: root.scroll_at_end


<ScrollLayout>:  # BoxLayout
    box_vertical: box_vertical

    orientation: "vertical"
    BoxLayout:
        id: box_vertical
"""
)


class ScrollBar(BoxLayout):
    layout_cursor = ObjectProperty()
    cursor = ObjectProperty()
    scrollview = ObjectProperty()

    btn_scroll = NumericProperty("100dp")
    scroll_at_start = BooleanProperty(False)
    scroll_at_end = BooleanProperty(False)

    _clock_btn_press = None
    _start_pos = None
    _start_scroll = None
    _scroll_by_cursor_layout = False

    _scrollview_bar_attr = None
    _size_hint_attr = None
    _size_attr = None
    _pos_attr = None
    _scroll_attr = None
    _btn_scroll_dimension_orientation = None
    _convert_distance_to_scroll = None
    _processing_scrollup = None
    _processing_scrolldown = None

    _btn_scroll_start = 0
    _btn_scroll_diff = 0

    _DEFAULT_WIDTH_NUMERIC = 20
    _DEFAULT_HEIGHT_NUMERIC = 20
    _default_width  = NumericProperty(f"{_DEFAULT_WIDTH_NUMERIC}dp")
    _default_height = NumericProperty(f"{_DEFAULT_HEIGHT_NUMERIC}dp")

    def on_kv_post(self, _):
        sv = self.scrollview
        if_vertical = self.orientation == "vertical"
        self.if_vertical = if_vertical
        self._scrollview_bar_attr = "vbar" if if_vertical else "hbar"
        self._size_hint_attr = "size_hint_y" if if_vertical else "size_hint_x"
        self._size_attr = "height" if if_vertical else "width"
        self._pos_attr = "y" if if_vertical else "x"
        self._scroll_attr = "scroll_y" if if_vertical else "scroll_x"
        self._btn_scroll_dimension_orientation = 1 if if_vertical else -1
        self._convert_distance_to_scroll = sv.convert_distance_to_scroll_y if\
                        if_vertical else sv.convert_distance_to_scroll_x
        self._processing_scrollup = self.scrollview.scroll_y_down if\
                        if_vertical else self.scrollview.scroll_x_left
        self._processing_scrolldown = self.scrollview.scroll_y_up if\
                        if_vertical else self.scrollview.scroll_x_right

        sv.bind(**{self._scrollview_bar_attr: self.on_scrollview_bar})
        self.layout_cursor.bind(size=self.on_scrollview_bar)
        self.scroll_at_start = self.get_scroll_at_start()
        self.scroll_at_end = self.get_scroll_at_end()

    def on_scrollview_bar(self, *args):
        pos, size_hint = self.__get_bar()
        pos *= getattr(self.layout_cursor, self._size_attr)
        self.__set_cursor(size_hint, pos)
        self.scroll_at_start = self.get_scroll_at_start()
        self.scroll_at_end = self.get_scroll_at_end()

    def on_press_btn_scroll(self, dimension: int):
        self._btn_scroll_start = self.__get_scroll()

        if self.scrollview.do_scroll_by_element:
            self._btn_scroll_diff = dimension
            self._scroll_by_diff(dimension)
        else:
            self._btn_scroll_diff = self._convert_distance_to_scroll(
                self._btn_scroll_dimension_orientation * dimension * self.btn_scroll
            )
            self.__inc_scroll(self._btn_scroll_diff)

        self._clock_btn_press = Clock.schedule_once(
            self._create_clock_btn_scroll, 0.3
        )

    def _create_clock_btn_scroll(self, _):
        self._clock_btn_press = Clock.schedule_interval(
            self._btn_scroll, 1 / 30)

    def _btn_scroll(self, _):
        self._btn_scroll_diff *= 1.065
        if self.scrollview.do_scroll_by_element:
            self._scroll_by_diff(self._btn_scroll_diff)
        else:
            self.__inc_scroll(self._btn_scroll_diff / 10)

    def _scroll_by_diff(self, diff):
        if self.orientation == "vertical":
            if diff > 0:
                self.scrollview.scroll_y_up(abs(diff))
            else:
                self.scrollview.scroll_y_down(abs(diff))
        else:
            if diff > 0:
                self.scrollview.scroll_x_left(abs(diff))
            else:
                self.scrollview.scroll_x_right(abs(diff))

    def on_touch_down(self, touch):
        if self._do_mouse_scroll(touch):
            return True
        if self._do_cursor(touch):
            # чтобы передать кнопке событие. Хотя наверное стоило сделать это лучшим образом
            touch.grab(self)
            return super().on_touch_down(touch)
        if self._check_scroll_by_cursor_layout(touch):
            touch.grab(self)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._start_pos:
            self.__do_scroll_by_cursor(touch)
            return True
        elif self._scroll_by_cursor_layout:
            self.__do_scroll_by_cursor_layout(touch)
            return True
        else:
            return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
        self._start_pos = None
        self._scroll_by_cursor_layout = False
        if self._clock_btn_press:
            self._clock_btn_press.cancel()
        return super().on_touch_up(touch)

    def _do_mouse_scroll(self, touch) -> bool:
        if self.collide_point(*touch.pos):
            if touch.button == "scrollup":
                self._processing_scrollup()
                return True
            elif touch.button == "scrolldown":
                self._processing_scrolldown()
                return True
        return False

    def _do_cursor(self, touch) -> bool:
        locale_touch = self.layout_cursor.to_local(*touch.pos)
        if self.cursor.collide_point(*locale_touch):
            self._start_pos = locale_touch[1 if self.orientation ==
                                           "vertical" else 0]
            self._start_scroll = self.__get_scroll()
            return True
        return False

    def _check_scroll_by_cursor_layout(self, touch) -> bool:
        scroll_by_cursor_layout = self.layout_cursor.collide_point(*touch.pos)
        self._scroll_by_cursor_layout = scroll_by_cursor_layout
        if scroll_by_cursor_layout:
            self.__do_scroll_by_cursor_layout(touch)
        return scroll_by_cursor_layout

    def __do_scroll_by_cursor(self, touch):
        touch.push()
        touch.apply_transform_2d(self.layout_cursor.to_local)
        dy = self.__get_touch_pos(touch) - self._start_pos
        diff = dy / self.__get_empty_layout_space()
        if self.orientation == "vertical":
            diff = -diff
        self.__set_scroll(self._start_scroll + diff)
        touch.pop()

    def __do_scroll_by_cursor_layout(self, touch):
        touch.push()
        touch.apply_transform_2d(self.layout_cursor.to_local)
        dy = self.__get_touch_pos(touch)
        if self.orientation == "vertical":
            self.__set_scroll(1 - (dy / self.__get_empty_layout_space()))
        else:
            self.__set_scroll(dy / self.__get_empty_layout_space())
        touch.pop()

    def __get_empty_layout_space(self) -> float:
        value = getattr(self.layout_cursor, self._size_attr) -\
            getattr(self.cursor, self._size_attr)
        return max(value, 1)

    def __get_bar(self) -> Tuple[float, float]:
        return getattr(self.scrollview, self._scrollview_bar_attr)

    def __get_scroll(self) -> float:
        return getattr(self.scrollview, self._scroll_attr)

    def __get_touch_pos(self, touch) -> float:
        return getattr(touch, self._pos_attr)

    def __set_scroll(self, value: float):
        setattr(self.scrollview, self._scroll_attr, value)

    def __set_cursor(self, size_hint: float, pos: float):
        setattr(self.cursor, self._size_hint_attr, size_hint)
        setattr(self.cursor, self._pos_attr, pos)

    def __inc_scroll(self, value: float):
        if self.orientation == "vertical":
            self.__set_scroll(self._btn_scroll_start - self._btn_scroll_diff)
        else:
            self.__set_scroll(self._btn_scroll_start + self._btn_scroll_diff)

    def get_scroll_at_start(self):
        sv = self.scrollview
        if not sv:
            return True

        if sv.do_scroll_by_element:
            return sv.scroll_element is not None and sv.scroll_element == 0

        if self.orientation == "vertical":
            return sv._scroll_y <= 0.0
        return sv._scroll_x <= 0.0

    def get_scroll_at_end(self):
        sv = self.scrollview
        if not sv:
            return True

        if sv.do_scroll_by_element:
            if sv.scroll_element is None:
                return False

            lm = sv.layout_manager
            if not lm or not lm._rv_positions:
                return True

            max_element = sv.scroll_element_limiter(
                len(lm._rv_positions) - 1
            )
            return sv.scroll_element >= max_element

        if self.orientation == "vertical":
            return sv._scroll_y >= 1.0
        return sv._scroll_x >= 1.0


class ScrollLayout(BoxLayout):
    scrollview = ObjectProperty()
    scrollbar_vertical = ObjectProperty(allownone=True)
    scrollbar_horizontal = ObjectProperty(allownone=True)
    box_vertical = ObjectProperty()

    trigger_on_scrollview_hbar = None
    trigger_on_scrollview_vbar = None
    def __init__(self, **kwargs):
        self.trigger_on_scrollview_bar = Clock.create_trigger(self.on_scrollview_bar, -1)
        self._setter_scrollview_attrs_list = []
        super().__init__(**kwargs)

    # Параметры scrollview
    def _alias_get_scrollview_attr(self, attr: str) -> any:
        return getattr(self.scrollview, attr)

    def _alias_set_scrollview_attr(self, attr: str, value: any):
        sv = self.scrollview
        if sv is None:
            self._setter_scrollview_attrs_list.append((attr, value))
            return False
        if getattr(sv, attr) == value:
            return False
        setattr(sv, attr, value)
        return True

    viewclass = AliasProperty(
        lambda x: x._alias_get_scrollview_attr("viewclass"),
        lambda x, value: x._alias_set_scrollview_attr("viewclass", value),
    )
    scroll_by_content = AliasProperty(
        lambda x: x._alias_get_scrollview_attr("scroll_by_content"),
        lambda x, value: x._alias_set_scrollview_attr("scroll_by_content", value),
    )
    do_scroll_by_element = AliasProperty(
        lambda x: x._alias_get_scrollview_attr("do_scroll_by_element"),
        lambda x, value: x._alias_set_scrollview_attr("do_scroll_by_element", value),
    )
    scroll_element = AliasProperty(
        lambda x: x._alias_get_scrollview_attr("scroll_element"),
        lambda x, value: x._alias_set_scrollview_attr("scroll_element", value),
    )
    scroll_wheel_distance = AliasProperty(
        lambda x: x._alias_get_scrollview_attr("scroll_wheel_distance"),
        lambda x, value: x._alias_set_scrollview_attr("scroll_wheel_distance", value),
    )
    scroll_x = AliasProperty(
        lambda x: x._alias_get_scrollview_attr("scroll_x"),
        lambda x, value: x._alias_set_scrollview_attr("scroll_x", value),
    )
    scroll_y = AliasProperty(
        lambda x: x._alias_get_scrollview_attr("scroll_y"),
        lambda x, value: x._alias_set_scrollview_attr("scroll_y", value),
    )
    do_scroll_x = AliasProperty(
        lambda x: x._alias_get_scrollview_attr("do_scroll_x"),
        lambda x, value: x._alias_set_scrollview_attr("do_scroll_x", value),
    )
    do_scroll_y = AliasProperty(
        lambda x: x._alias_get_scrollview_attr("do_scroll_y"),
        lambda x, value: x._alias_set_scrollview_attr("do_scroll_y", value),
    )

    def on_kv_post(self, _):
        self.remove_widget(self.scrollview)
        self.box_vertical.add_widget(self.scrollview)

    def on_scrollview(self, _, scrollview):
        self.original_add_widget = self.add_widget
        self.add_widget = self.patch_add_widget
        for attr, value in self._setter_scrollview_attrs_list:
            setattr(scrollview, attr, value)
        self._setter_scrollview_attrs_list = None
        scrollview.bind(
            vbar=self.trigger_on_scrollview_bar,
            hbar=self.trigger_on_scrollview_bar,
            size=self.trigger_on_scrollview_bar,
        )
        self.trigger_on_scrollview_bar()

    def patch_add_widget(self, widget, index=0, canvas=None):
        if isinstance(widget, ScrollBar) and (
                widget.orientation == "horizontal"):
            self.original_add_widget(widget)
        elif isinstance(widget, ScrollBar) and (
                widget.orientation == "vertical"):
            self.box_vertical.add_widget(self.scrollbar_vertical)
        else:
            self.scrollview.add_widget(widget)

    def on_scrollview_bar(self, *args):
        sv = self.scrollview
        if not sv:
            return
        vp = sv._viewport

        need_h = self.do_scroll_x and (vp.width > sv.width)
        need_v = self.do_scroll_y and (vp.height > sv.height)
        if need_h and not need_v:
            if (vp.height != sv.height) and vp.height > sv.height - self._get_hbar_thickness() and self.do_scroll_y:
                need_v = True

        self._set_scrollbar_horizontal(need_h)
        self._set_scrollbar_vertical(need_v)

    def _get_hbar_thickness(self):
        if self.scrollbar_horizontal:
            return self.scrollbar_horizontal.height
        return dp(ScrollBar._DEFAULT_HEIGHT_NUMERIC)

    def _set_scrollbar_horizontal(self, needed):
        if needed:
            if self.scrollbar_horizontal is None and self.do_scroll_x:
                self.scrollbar_horizontal = ScrollBar(
                    scrollview=self.scrollview, orientation="horizontal"
                )
                self.add_widget(self.scrollbar_horizontal)
        else:
            if self.scrollbar_horizontal is not None:
                self.remove_widget(self.scrollbar_horizontal)
                self.scrollbar_horizontal = None

    def _set_scrollbar_vertical(self, needed):
        if needed:
            if self.scrollbar_vertical is None and self.do_scroll_y:
                self.scrollbar_vertical = ScrollBar(
                    scrollview=self.scrollview, orientation="vertical"
                )
                self.add_widget(self.scrollbar_vertical)
        else:
            if self.scrollbar_vertical is not None:
                self.box_vertical.remove_widget(self.scrollbar_vertical)
                self.scrollbar_vertical = None
