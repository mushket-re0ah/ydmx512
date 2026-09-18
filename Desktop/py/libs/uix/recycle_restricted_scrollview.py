from kivy.uix.recycleview import RecycleViewBehavior
from kivy.properties import AliasProperty
from kivy.utils import boundary
from kivy.uix.recycleview.layout import RecycleLayoutManagerBehavior
from kivy.uix.recycleview.views import RecycleDataAdapter
from kivy.uix.recycleview.datamodel import RecycleDataModel
from libs.uix.restricted_scrollview import RestrictedScrollView


class RecycleRestrictedScrollView(RecycleViewBehavior, RestrictedScrollView):
    def __init__(self, **kwargs):
        if self.data_model is None:
            kwargs.setdefault('data_model', RecycleDataModel())
        if self.view_adapter is None:
            kwargs.setdefault('view_adapter', RecycleDataAdapter())
        super().__init__(**kwargs)

        fbind = self.fbind
        self.bind(
            _scroll_x=self.refresh_from_viewport,
            _scroll_y=self.refresh_from_viewport,
            size=self.refresh_from_viewport
        )
        self.refresh_from_data()

    def on_kv_post(self, _):
        super().on_kv_post(_)
        self.initialize_scroll_element()

    def initialize_scroll_element(self, *args):
        if not self.do_scroll_by_element:
            return

        if not self.layout_manager:
            return

        if self.do_scroll_x:
            self.set_scroll_element_by_scroll_x(self.scroll_x)
        elif self.do_scroll_y:
            self.set_scroll_element_by_scroll_y(self.scroll_y)
        self.unbind(layout_manager=self.initialize_scroll_element)

    def refresh_views(self, *largs):
        lm = self.layout_manager
        flags = self._refresh_flags
        if lm is None or self.view_adapter is None or self.data_model is None:
            return

        data = self.data
        f = flags['data']
        if f:
            self.save_viewport()
            # lm.clear_layout()
            flags['data'] = []
            flags['layout'] = [{}]
            lm.compute_sizes_from_data(data, f)

        while flags['layout']:
            # if `data` we were re-triggered so finish in the next call.
            # Otherwise go until fully laid out.
            self.save_viewport()
            if flags['data']:
                return
            flags['viewport'] = True
            f = flags['layout']
            flags['layout'] = []

            try:
                lm.compute_layout(data, f)
            except LayoutChangeException:
                flags['layout'].append({})
                continue

        if flags['data']:  # in case that happened meanwhile
            return

        # make sure if we were re-triggered in the loop that we won't be
        # called needlessly later.
        self._refresh_trigger.cancel()

        self.restore_viewport()

        if flags['viewport']:
            # TODO: make this also listen to LayoutChangeException
            flags['viewport'] = False
            viewport = self.get_viewport()
            indices = lm.compute_visible_views(data, viewport)
            self._last_indices = indices
            lm.set_visible_views(indices, data, viewport)

    def _convert_sv_to_lm(self, x, y):
        lm = self.layout_manager
        tree = [lm]
        parent = lm.parent
        while parent is not None and parent is not self:
            tree.append(parent)
            parent = parent.parent

        if parent is not self:
            raise Exception(
                'The layout manager must be a sub child of the recycleview. '
                'Could not find {} in the parent tree of {}'.format(self, lm))

        for widget in reversed(tree):
            x, y = widget.to_local(x, y)

        return x, y

    def get_viewport(self):
        lm = self.layout_manager
        lm_w, lm_h = lm.size
        w, h = self.size

        # Инверсия scroll_y для расчета viewport
        if lm_h > h:
            available_height = lm_h - h
            bottom = available_height * (1 - self.scroll_y)
        else:
            bottom = 0

        left = max(0, (lm_w - w) * self.scroll_x)
        width = min(w, lm_w)
        height = min(h, lm_h)

        return left, bottom, width, height

    def save_viewport(self):
        pass

    def restore_viewport(self):
        pass

    def add_widget(self, widget, *args, **kwargs):
        super().add_widget(widget, *args, **kwargs)
        if (isinstance(widget, RecycleLayoutManagerBehavior) and
                not self.layout_manager):
            self.layout_manager = widget

    def remove_widget(self, widget, *args, **kwargs):
        super().remove_widget(widget, *args, **kwargs)
        if self.layout_manager == widget:
            self.layout_manager = None

    def set_scroll_element_by_scroll_x(self, scroll_x: float) -> bool:
        if not self.layout_manager:
            return False

        rv_positions = self.layout_manager._rv_positions
        if not rv_positions:
            return False

        scroll_x *= 1 - self.hbar.size_hint
        x = self.viewport_size[0] * scroll_x
        scroll_element = None
        for i, rv_x in enumerate(rv_positions):
            rv_x = max(rv_x, 0)
            if rv_x >= x:
                scroll_element = i
                break

        if scroll_element is None:
            return False

        self.scroll_element = scroll_element
        return True

    def set_scroll_element_by_scroll_y(self, scroll_y: float) -> bool:
        if not self.layout_manager:
            return False

        rv_positions = self.layout_manager._rv_positions
        if not rv_positions:
            return False

        scroll_y *= 1 - self.vbar.size_hint
        y = self.viewport_size[1] * scroll_y
        scroll_element = None
        for i, rv_y in enumerate(rv_positions):
            rv_y = max(rv_y, 0)
            if rv_y >= y:
                scroll_element = i
                break

        if scroll_element is None:
            return False

        self.scroll_element = scroll_element
        return True

    def scroll_element_limiter(self, scroll_element: int) -> int:
        lm = self.layout_manager
        if not lm or not lm._rv_positions:
            return scroll_element

        if self.do_scroll_x:
            available = lm.width - self.width
        elif self.do_scroll_y:
            available = lm.height - self.height
        else:
            return scroll_element

        if available <= 0:
            return 0

        max_scroll_element = len(lm._rv_positions) - 1
        for index, pos in enumerate(lm._rv_positions):
            if pos >= available:
                max_scroll_element = index
                break

        return boundary(scroll_element, 0, max_scroll_element)

    def scroll_to(self, index: int):
        lm = self.layout_manager
        if not lm:
            return False
        if not lm._rv_positions:
            return False
        rv_positions = lm._rv_positions
        if index is None:
            if self.do_scroll_x:
                self.set_scroll_element_by_scroll_x(self.scroll_x)
            elif self.do_scroll_y:
                self.set_scroll_element_by_scroll_y(self.scroll_y)
            index = self.scroll_element
        if index is None:
            self.scroll_element = 0
            return False
        if (index < 0) or (index >= len(rv_positions)):
            return False

        if self.do_scroll_x:
            available_width = lm.width - self.width
            if available_width <= 0:
                return False
            self._scroll_x = lm._rv_positions[index] / available_width
        elif self.do_scroll_y:
            available_height = lm.height - self.height
            if available_height <= 0:
                return False
            self._scroll_y = lm._rv_positions[index] / available_height
        self.update_from_scroll()

    # or easier way to use
    def _get_data(self):
        d = self.data_model
        return d and d.data

    def _set_data(self, value):
        d = self.data_model
        if d is not None:
            d.data = value

    data = AliasProperty(_get_data, _set_data, bind=["data_model"])
    """
    The data used by the current view adapter. This is a list of dicts whose
    keys map to the corresponding property names of the
    :attr:`~RecycleView.viewclass`.

    data is an :class:`~kivy.properties.AliasProperty` that gets and sets the
    data used to generate the views.
    """

    def _get_viewclass(self):
        a = self.layout_manager
        return a and a.viewclass

    def _set_viewclass(self, value):
        a = self.layout_manager
        if a:
            a.viewclass = value

    viewclass = AliasProperty(_get_viewclass, _set_viewclass,
                              bind=["layout_manager"])
    """
    The viewclass used by the current layout_manager.

    viewclass is an :class:`~kivy.properties.AliasProperty` that gets and sets
    the class used to generate the individual items presented in the view.
    """

    def _get_key_viewclass(self):
        a = self.layout_manager
        return a and a.key_viewclass

    def _set_key_viewclass(self, value):
        a = self.layout_manager
        if a:
            a.key_viewclass = value

    key_viewclass = AliasProperty(_get_key_viewclass, _set_key_viewclass,
                                  bind=["layout_manager"])
    """
    key_viewclass is an :class:`~kivy.properties.AliasProperty` that gets and
    sets the key viewclass for the current
    :attr:`~kivy.uix.recycleview.layout_manager`.
    """
