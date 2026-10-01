from typing import Any, List, Literal, NamedTuple, Optional, Tuple, Type

from kivy.clock import Clock
from kivy.graphics import Canvas, PopMatrix, PushMatrix, Translate
from kivy.graphics.transformation import Matrix
from kivy.input.motionevent import MotionEvent
from kivy.properties import (
    AliasProperty,
    BooleanProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
)
from kivy.uix.stencilview import StencilView
from kivy.uix.widget import Widget
from typing_extensions import Self

from libs.properties import ClampedNumericProperty


class ScrollbarData(NamedTuple):
    pos_hint: float
    size_hint: float


class RestrictedScrollView(StencilView):
    _scrollable_widget_classes: List[Type[Widget]] = []  # static
    @classmethod
    def register_scrollable_widget_class(cls, widget_cls: Type[Widget]):
        if widget_cls not in cls._scrollable_widget_classes:
            cls._scrollable_widget_classes.append(widget_cls)

    scroll_wheel_distance: float = NumericProperty('30dp')
    _scroll_x: float = ClampedNumericProperty(0.0, 0.0, 1.0)
    _scroll_y: float = ClampedNumericProperty(0.0, 0.0, 1.0)
    do_scroll_x: bool = BooleanProperty(True)
    do_scroll_y: bool = BooleanProperty(True)
    scroll_by_content: bool = BooleanProperty(False)
    do_scroll_by_element: bool = BooleanProperty(False)
    _scroll_element: int = NumericProperty(0)

    def set_scroll_element(self, scroll_element: int) -> bool:
        scroll_element = self.scroll_element_limiter(scroll_element)
        if self._scroll_element == scroll_element:
            return False
        self._scroll_element = scroll_element
        return True

    def scroll_element_limiter(self, scroll_element: int) -> int:
        raise NotImplementedError()

    scroll_element: int = AliasProperty(
        lambda self: self._scroll_element, set_scroll_element
    )

    def _get_vbar(self) -> ScrollbarData:
        # must return (y, height) in %
        # calculate the viewport size / RestrictedScrollView size %
        if self._viewport is None:
            return ScrollbarData(0.0, 1.0)
        vh = self._viewport.height
        h = self.height
        if vh < h or vh == 0:
            return ScrollbarData(0.0, 1.0)
        ph = max(0.01, h / float(vh))
        sy = min(1.0, max(0.0, self.scroll_y))
        py = (1.0 - ph) * (1.0 - sy)
        return ScrollbarData(py, ph)

    vbar: ScrollbarData = AliasProperty(_get_vbar,
                         bind=('_scroll_y', '_viewport', 'viewport_size',
                               'height', '_scroll_element', "do_scroll_x", "do_scroll_y"),
                         cache=True)

    def _get_hbar(self) -> ScrollbarData:
        # must return (x, width) in %
        # calculate the viewport size / RestrictedScrollView size %
        if self._viewport is None:
            return ScrollbarData(0.0, 1.0)
        vw = self._viewport.width
        w = self.width
        if vw < w or vw == 0:
            return ScrollbarData(0.0, 1.0)
        pw = max(0.01, w / float(vw))
        sx = min(1.0, max(0.0, self.scroll_x))
        px = (1.0 - pw) * sx
        return ScrollbarData(px, pw)

    hbar: ScrollbarData = AliasProperty(_get_hbar,
                         bind=('_scroll_x', '_viewport', 'viewport_size',
                               'width', '_scroll_element', "do_scroll_x", "do_scroll_y"),
                         cache=True)

    viewport_size: Tuple[float, float] = ListProperty([0, 0])

    _viewport: Optional[Widget] = ObjectProperty(None, allownone=True)

    def _set_viewport_size(self, instance: Optional[Widget], size: Tuple[float, float]):
        self.viewport_size = size

    def on__viewport(self, instance: Self, viewport: Optional[Widget]):
        if viewport:
            viewport.bind(size=self._set_viewport_size)
            self.viewport_size = viewport.size

    def __init__(self, **kwargs: Any):
        self._start_pos: Optional[Tuple[float, float]] = None
        self._start_scroll: Optional[Tuple[float, float]] = None
        self._trigger_update_from_scroll = Clock.create_trigger(
            self.update_from_scroll, -1)
        self.trigger_do_scroll_by_element = Clock.create_trigger(
            self._do_scroll_by_element, -1)
        # create a specific canvas for the viewport
        self.canvas_viewport = Canvas()
        self.canvas = Canvas()
        with self.canvas_viewport.before:
            PushMatrix()
            self.g_translate: Translate = Translate(0, 0)
        with self.canvas_viewport.after:
            PopMatrix()
        super().__init__(**kwargs)
        # now add the viewport canvas to our canvas
        self.canvas.add(self.canvas_viewport)

        trigger_update_from_scroll = self._trigger_update_from_scroll
        self.bind(
            _scroll_x=trigger_update_from_scroll,
            _scroll_y=trigger_update_from_scroll,
            pos=trigger_update_from_scroll,
        )

        trigger_update_from_scroll()

        self.on_do_scroll_by_element(self, self.do_scroll_by_element)

    def on_do_scroll_by_element(self, instance: Self, do_scroll_by_element: bool):
        if do_scroll_by_element:
            self.bind(
                size=self.trigger_do_scroll_by_element,
                scroll_element=self.trigger_do_scroll_by_element
            )
            self.unbind(
                size=self._trigger_update_from_scroll
            )
        else:
            self.bind(
                size=self._trigger_update_from_scroll
            )
            self.unbind(
                size=self.trigger_do_scroll_by_element,
                scroll_element=self.trigger_do_scroll_by_element
            )

    scroll_element_block: bool = False
    def _do_scroll_by_element(self, _: Any):
        if self.do_scroll_by_element:
            self.scroll_element_block = True
            self.scroll_to(self.scroll_element)
            self.scroll_element_block = False
            self.update_from_scroll()

    block_set_scroll_x: bool = False
    def set_scroll_x(self, scroll_x: float) -> bool:
        if (scroll_x == self._scroll_x) or self.block_set_scroll_x:
            return False
        self.block_set_scroll_x = True
        if self.do_scroll_by_element:
            if not self.set_scroll_element_by_scroll_x(scroll_x):
                self._scroll_x = scroll_x
        else:
            self._scroll_x = scroll_x
        self.block_set_scroll_x = False
        return True
    scroll_x: float = AliasProperty(
        lambda self: self._scroll_x, set_scroll_x
    )

    def set_scroll_element_by_scroll_x(self, scroll_x: float) -> bool:
        raise NotImplementedError()

    block_set_scroll_y: bool = False
    def set_scroll_y(self, scroll_y: float) -> bool:
        if (scroll_y == self._scroll_y) or self.block_set_scroll_y:
            return False
        self.block_set_scroll_y = True
        if self.do_scroll_by_element:
            if not self.set_scroll_element_by_scroll_y(scroll_y):
                self._scroll_y = scroll_y
        else:
            self._scroll_y = scroll_y
        self.block_set_scroll_y = False
        return True
    scroll_y: float = AliasProperty(
        lambda self: self._scroll_y, set_scroll_y
    )

    def set_scroll_element_by_scroll_y(self, scroll_y: float) -> bool:
        raise NotImplementedError()

    def to_local(self, x: float, y: float, relative:bool=False) -> Tuple[float, float]:
        tx, ty = self.g_translate.xy
        return x - tx, y - ty

    def to_parent(self, x: float, y: float, relative:bool=False) -> Tuple[float, float]:
        tx, ty = self.g_translate.xy
        return x + tx, y + ty

    def _apply_transform(self, m: Matrix, pos:Optional[Tuple[float, float]]=None) -> Matrix:
        tx, ty = self.g_translate.xy
        m.translate(tx, ty, 0)
        return super()._apply_transform(m, (0, 0))

    def simulate_touch_down(self, touch: MotionEvent) -> bool:
        # at this point the touch is in parent coords
        touch.push()
        touch.apply_transform_2d(self.to_local)
        ret = super().on_touch_down(touch)
        touch.pop()
        return ret

    def on_motion(self, etype: Literal["begin", "update", "end"], me: MotionEvent) -> bool:
        if me.type_id in self.motion_filter and 'pos' in me.profile:
            me.push()
            me.apply_transform_2d(self.to_local)
            ret = super().on_motion(etype, me)
            me.pop()
            return ret
        return super().on_motion(etype, me)

    def on_touch_down(self, touch: MotionEvent) -> bool:
        if self.collide_point(*touch.pos):
            scrollable_widget = self._get_scrollable_widget()
            if scrollable_widget and scrollable_widget is not self:
                if isinstance(self, type(scrollable_widget)):
                    touch.push()
                    touch.apply_transform_2d(self.to_local)
                    ret = scrollable_widget.on_touch_down(touch)
                    touch.pop()
                    return ret
                return self.simulate_touch_down(touch)
            if touch.button == "middle" and self.scroll_by_content:
                self._start_pos = touch.pos
                self._start_scroll = (self.scroll_x, self.scroll_y)
                touch.grab(self)
                return True
            if touch.button == "scrollup" and self._can_scroll_by_y():
                self.scroll_y_down()
                return True
            if touch.button == "scrolldown" and self._can_scroll_by_y():
                self.scroll_y_up()
                return True
            return self.simulate_touch_down(touch)
        return False

    def _can_scroll_by_y(self) -> bool:
        if not self.do_scroll_y:
            return False
        vp = self._viewport
        return vp is not None and vp.height > self.height

    def _can_scroll_by_x(self) -> bool:
        if not self.do_scroll_x:
            return False
        vp = self._viewport
        return vp is not None and vp.width > self.width

    def _get_scrollable_widget(self) -> Optional[Widget]:
        from libs.kivy_utils import walk_by_parents
        from libs.mouse_manager.hover import HoverBehavior

        hovered_widget = HoverBehavior.widget_under_cursor
        if hovered_widget is None:
            return None

        def is_scrollable(widget: Widget) -> bool:
            return any(isinstance(widget, cls) for cls in self._scrollable_widget_classes)

        if is_scrollable(hovered_widget):
            return hovered_widget
        for parent in walk_by_parents(hovered_widget):
            if is_scrollable(parent):
                return parent
        return None

    def scroll_y_up(self, diff:float=1):
        if self.do_scroll_y:
            if self.do_scroll_by_element:
                self.scroll_element -= int(diff)
            else:
                dy = self.convert_distance_to_scroll_y(self.scroll_wheel_distance)
                self.scroll_y -= dy * diff

    def scroll_y_down(self, diff:float=1):
        if self.do_scroll_y:
            if self.do_scroll_by_element:
                self.scroll_element += int(diff)
            else:
                dy = self.convert_distance_to_scroll_y(self.scroll_wheel_distance)
                self.scroll_y += dy * diff

    def scroll_x_left(self, diff:float=1):
        if self.do_scroll_x:
            if self.do_scroll_by_element:
                self.scroll_element -= int(diff)
            else:
                dx = self.convert_distance_to_scroll_x(self.scroll_wheel_distance)
                self.scroll_x -= dx * diff

    def scroll_x_right(self, diff:float=1):
        if self.do_scroll_x:
            if self.do_scroll_by_element:
                self.scroll_element += int(diff)
            else:
                dx = self.convert_distance_to_scroll_x(self.scroll_wheel_distance)
                self.scroll_x += dx * diff

    def on_touch_move(self, touch: MotionEvent) -> bool:
        if self._start_scroll:
            if self._start_pos is None:
                raise ValueError()
            if self.do_scroll_x:
                dx = self.convert_distance_to_scroll_x(touch.x - self._start_pos[0])
                self.scroll_x = self._start_scroll[0] + dx
            if self.do_scroll_y:
                dy = self.convert_distance_to_scroll_y(touch.y - self._start_pos[1])
                self.scroll_y = self._start_scroll[1] - dy
            return True
        touch.push()
        touch.apply_transform_2d(self.to_local)
        ret = super().on_touch_move(touch)
        touch.pop()
        return ret

    def on_touch_up(self, touch: MotionEvent) -> bool:
        if self._start_scroll:
            touch.ungrab(self)
        self._start_pos = None
        self._start_scroll = None
        touch.push()
        touch.apply_transform_2d(self.to_local)
        ret = super().on_touch_up(touch)
        touch.pop()
        return ret

    def scroll_to(self, index: int) -> None:
        raise NotImplementedError()

    def convert_distance_to_scroll(self, dx: float, dy: float) -> Tuple[float, float]:
        '''Convert a distance in pixels to a scroll distance, depending on the
        content size and the RestrictedScrollView size.

        The result will be a tuple of scroll distance that can be added to
        :data:`scroll_x` and :data:`scroll_y`
        '''
        return (self.convert_distance_to_scroll_x(dx),
                self.convert_distance_to_scroll_y(dy))

    def convert_distance_to_scroll_x(self, dx: float) -> float:
        if not self._viewport:
            return 0
        vp = self._viewport
        if vp.width > self.width:
            sw = vp.width - self.width
            return dx / float(sw)
        return 0

    def convert_distance_to_scroll_y(self, dy: float) -> float:
        if not self._viewport:
            return 0
        vp = self._viewport
        if vp.height > self.height:
            sh = vp.height - self.height
            return dy / float(sh)
        return 0

    def update_from_scroll(self, *_:Any):
        if self.scroll_element_block:
            return
        if not self._viewport:
            self.g_translate.xy = self.pos
            return
        vp = self._viewport

        if vp.size_hint_x is not None:
            w = vp.size_hint_x * self.width
            if vp.size_hint_min_x is not None:
                w = max(w, vp.size_hint_min_x)
            if vp.size_hint_max_x is not None:
                w = min(w, vp.size_hint_max_x)
            vp.width = w

        if vp.size_hint_y is not None:
            h = vp.size_hint_y * self.height
            if vp.size_hint_min_y is not None:
                h = max(h, vp.size_hint_min_y)
            if vp.size_hint_max_y is not None:
                h = min(h, vp.size_hint_max_y)
            vp.height = h

        if vp.width > self.width:
            sw = vp.width - self.width
            x = self.x - self.scroll_x * sw
        else:
            x = self.x

        if vp.height > self.height:
            sh = vp.height - self.height
            y = self.y - (1 - self.scroll_y) * sh
        else:
            y = self.top - vp.height

        vp.pos = 0, 0

        self.g_translate.xy = x, y

    def add_widget(self, widget: Widget, *args:Any, **kwargs:Any):
        if self._viewport:
            raise RuntimeError('RestrictedScrollView accept only one widget')
        canvas = self.canvas
        self.canvas = self.canvas_viewport
        super().add_widget(widget, *args, **kwargs)
        self.canvas = canvas
        self._viewport = widget
        widget.bind(size=self._trigger_update_from_scroll,
                    size_hint=self._trigger_update_from_scroll,
                    size_hint_min=self._trigger_update_from_scroll)
        self._trigger_update_from_scroll()

    def remove_widget(self, widget: Widget, *args: Any, **kwargs: Any):
        canvas = self.canvas
        self.canvas = self.canvas_viewport
        super().remove_widget(widget, *args, **kwargs)
        self.canvas = canvas
        if widget is self._viewport:
            self._viewport = None

    def _get_uid(self, prefix:str='sv') -> str:
        return f'{prefix}.{self.uid}'

    def _do_touch_up(self, touch: MotionEvent, *_):
        # touch is in window coords
        touch.push()
        touch.apply_transform_2d(self.to_widget)
        super().on_touch_up(touch)
        touch.pop()
        # don't forget about grab event!
        for x in touch.grab_list[:]:
            touch.grab_list.remove(x)
            x = x()
            if not x:
                continue
            touch.grab_current = x
            # touch is in window coords
            touch.push()
            touch.apply_transform_2d(self.to_widget)
            super().on_touch_up(touch)
            touch.pop()
        touch.grab_current = None

RestrictedScrollView.register_scrollable_widget_class(RestrictedScrollView)
