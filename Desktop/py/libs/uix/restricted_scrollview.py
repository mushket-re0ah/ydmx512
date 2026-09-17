from kivy.clock import Clock
from kivy.properties import (
    BooleanProperty, AliasProperty, ObjectProperty,
    ListProperty, NumericProperty
)
from kivy.uix.stencilview import StencilView
from kivy.graphics import PushMatrix, Translate, PopMatrix, Canvas
from typing import Tuple, NamedTuple
from libs.properties import ClampedNumericProperty


class ScrollbarData(NamedTuple):
    pos_hint: float
    size_hint: float


class RestrictedScrollView(StencilView):
    _scrollable_widget_classes = []  # static
    @classmethod
    def register_scrollable_widget_class(cls, widget_cls):
        if widget_cls not in cls._scrollable_widget_classes:
            cls._scrollable_widget_classes.append(widget_cls)

    scroll_wheel_distance = NumericProperty('30dp')
    _scroll_x = ClampedNumericProperty(0.0, 0.0, 1.0)
    _scroll_y = ClampedNumericProperty(0.0, 0.0, 1.0)
    do_scroll_x = BooleanProperty(True)
    do_scroll_y = BooleanProperty(True)
    scroll_by_content = BooleanProperty(False)
    do_scroll_by_element = BooleanProperty(False)
    _scroll_element = NumericProperty(None)

    def set_scroll_element(self, scroll_element: int) -> bool:
        scroll_element = self.scroll_element_limiter(scroll_element)
        if self._scroll_element == scroll_element:
            return False
        self._scroll_element = scroll_element
        return True

    def scroll_element_limiter(self, scroll_element: int) -> int:
        raise NotImplementedError()

    scroll_element = AliasProperty(
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

    vbar = AliasProperty(_get_vbar,
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

    hbar = AliasProperty(_get_hbar,
                         bind=('_scroll_x', '_viewport', 'viewport_size',
                               'width', '_scroll_element', "do_scroll_x", "do_scroll_y"),
                         cache=True)

    viewport_size = ListProperty([0, 0])

    _viewport = ObjectProperty(None, allownone=True)

    def _set_viewport_size(self, instance, value):
        self.viewport_size = value

    def on__viewport(self, instance, value):
        if value:
            value.bind(size=self._set_viewport_size)
            self.viewport_size = value.size

    def __init__(self, **kwargs):
        self._start_pos = None
        self._start_scroll = None
        self._trigger_update_from_scroll = Clock.create_trigger(
            self.update_from_scroll, -1)
        self.trigger_do_scroll_by_element = Clock.create_trigger(
            self._do_scroll_by_element, -1)
        # create a specific canvas for the viewport
        self.canvas_viewport = Canvas()
        self.canvas = Canvas()
        with self.canvas_viewport.before:
            PushMatrix()
            self.g_translate = Translate(0, 0)
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

        self.on_do_scroll_by_element(None, self.do_scroll_by_element)

    def on_do_scroll_by_element(self, _, do_scroll_by_element: bool):
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

    scroll_element_block = False
    def _do_scroll_by_element(self, _):
        if self.do_scroll_by_element:
            self.scroll_element_block = True
            self.scroll_to(self.scroll_element)
            self.scroll_element_block = False
            self.update_from_scroll()

    block_set_scroll_x = False
    def set_scroll_x(self, scroll_x: float):
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
    scroll_x = AliasProperty(
        lambda self: self._scroll_x, set_scroll_x
    )

    def set_scroll_element_by_scroll_x(self, scroll_x: float) -> bool:
        raise NotImplementedError()

    block_set_scroll_y = False
    def set_scroll_y(self, scroll_y: float):
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
    scroll_y = AliasProperty(
        lambda self: self._scroll_y, set_scroll_y
    )

    def set_scroll_element_by_scroll_y(self, scroll_y: float) -> bool:
        raise NotImplementedError()

    def to_local(self, x, y, **k) -> Tuple[float, float]:
        tx, ty = self.g_translate.xy
        return x - tx, y - ty

    def to_parent(self, x, y, **k) -> Tuple[float, float]:
        tx, ty = self.g_translate.xy
        return x + tx, y + ty

    def _apply_transform(self, m, pos=None) -> Tuple[float, float]:
        tx, ty = self.g_translate.xy
        m.translate(tx, ty, 0)
        return super()._apply_transform(m, (0, 0))

    def simulate_touch_down(self, touch):
        # at this point the touch is in parent coords
        touch.push()
        touch.apply_transform_2d(self.to_local)
        ret = super().on_touch_down(touch)
        touch.pop()
        return ret

    def on_motion(self, etype, me):
        if me.type_id in self.motion_filter and 'pos' in me.profile:
            me.push()
            me.apply_transform_2d(self.to_local)
            ret = super().on_motion(etype, me)
            me.pop()
            return ret
        return super().on_motion(etype, me)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            scrollable_widget = self._get_scrollable_widget()
            if scrollable_widget and scrollable_widget is not self:
                if isinstance(self, type(scrollable_widget)):
                    touch.push()
                    touch.apply_transform_2d(self.to_local)
                    ret = scrollable_widget.on_touch_down(touch)
                    touch.pop()
                    return ret
                else:
                    return self.simulate_touch_down(touch)
            if touch.button == "middle" and self.scroll_by_content:
                self._start_pos = touch.pos
                self._start_scroll = [self.scroll_x, self.scroll_y]
            elif touch.button == "scrollup":
                self.scroll_y_down()
            elif touch.button == "scrolldown":
                self.scroll_y_up()
            else:
                return self.simulate_touch_down(touch)
        return False

    def _get_scrollable_widget(self):
        from libs.kivy_utils import walk_by_parents
        from libs.mouse_manager.hover import HoverBehavior

        hovered_widget = HoverBehavior.widget_under_cursor
        if hovered_widget is None:
            return None

        def is_scrollable(widget):
            return any(isinstance(widget, cls) for cls in self._scrollable_widget_classes)

        if is_scrollable(hovered_widget):
            return hovered_widget
        for parent in walk_by_parents(hovered_widget):
            if is_scrollable(parent):
                return parent
        return None

    def scroll_y_up(self):
        if self.do_scroll_y:
            if self.do_scroll_by_element and self.scroll_element:
                self.scroll_element -= 1
            else:
                dy = self.convert_distance_to_scroll_y(self.scroll_wheel_distance)
                self.scroll_y -= dy

    def scroll_y_down(self):
        if self.do_scroll_y:
            if self.do_scroll_by_element and self.scroll_element:
                self.scroll_element += 1
            else:
                dy = self.convert_distance_to_scroll_y(self.scroll_wheel_distance)
                self.scroll_y += dy

    def scroll_x_left(self):
        if self.do_scroll_x:
            if self.do_scroll_by_element and self.scroll_element:
                self.scroll_element -= 1
            else:
                dx = self.convert_distance_to_scroll_x(self.scroll_wheel_distance)
                self.scroll_x -= dx

    def scroll_x_right(self):
        if self.do_scroll_x:
            if self.do_scroll_by_element and self.scroll_element:
                self.scroll_element += 1
            else:
                dx = self.convert_distance_to_scroll_x(self.scroll_wheel_distance)
                self.scroll_x += dx

    def on_touch_move(self, touch):
        if self._start_scroll:
            if self.do_scroll_x:
                dx = self.convert_distance_to_scroll_x(touch.x - self._start_pos[0])
                self.scroll_x = self._start_scroll[0] - dx
            if self.do_scroll_y:
                dy = self.convert_distance_to_scroll_y(touch.y - self._start_pos[1])
                self.scroll_y = self._start_scroll[1] - dy
            return super().on_touch_move(touch)
        touch.push()
        touch.apply_transform_2d(self.to_local)
        ret = super().on_touch_move(touch)
        touch.pop()
        return ret

    def on_touch_up(self, touch):
        self._start_pos = None
        self._start_scroll = None
        touch.push()
        touch.apply_transform_2d(self.to_local)
        ret = super().on_touch_up(touch)
        touch.pop()
        return ret

    def scroll_to(self, widget):
        raise NotImplementedError()

    def convert_distance_to_scroll(self, dx: float, dy: float) -> Tuple[float, float]:
        '''Convert a distance in pixels to a scroll distance, depending on the
        content size and the RestrictedScrollView size.

        The result will be a tuple of scroll distance that can be added to
        :data:`scroll_x` and :data:`scroll_y`
        '''
        return (self.convert_distance_to_scroll_x(dx),
                self.convert_distance_to_scroll_y(dy))

    def convert_distance_to_scroll_x(self, dx: float):
        if not self._viewport:
            return 0
        vp = self._viewport
        if vp.width > self.width:
            sw = vp.width - self.width
            return dx / float(sw)
        else:
            return 0

    def convert_distance_to_scroll_y(self, dy: float):
        if not self._viewport:
            return 0
        vp = self._viewport
        if vp.height > self.height:
            sh = vp.height - self.height
            return dy / float(sh)
        else:
            return 0

    def update_from_scroll(self, *largs):
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

    def add_widget(self, widget, *args, **kwargs):
        if self._viewport:
            raise Exception('RestrictedScrollView accept only one widget')
        canvas = self.canvas
        self.canvas = self.canvas_viewport
        super().add_widget(widget, *args, **kwargs)
        self.canvas = canvas
        self._viewport = widget
        widget.bind(size=self._trigger_update_from_scroll,
                    size_hint=self._trigger_update_from_scroll,
                    size_hint_min=self._trigger_update_from_scroll)
        self._trigger_update_from_scroll()

    def remove_widget(self, widget, *args, **kwargs):
        canvas = self.canvas
        self.canvas = self.canvas_viewport
        super().remove_widget(widget, *args, **kwargs)
        self.canvas = canvas
        if widget is self._viewport:
            self._viewport = None

    def _get_uid(self, prefix='sv'):
        return '{0}.{1}'.format(prefix, self.uid)

    def _do_touch_up(self, touch, *largs):
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
