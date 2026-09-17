# https://github.com/kivy/kivy/issues/9378

def apply_patch():
    from kivy.uix.recycleview import views
    def get_view(self, index, data_item, viewclass):
        dirty_views = self.dirty_views
        if viewclass is None:
            return
        stale = False
        view = None

        if viewclass in dirty_views:
            dirty_class = dirty_views[viewclass]
            if index in dirty_class:
                view = dirty_class.pop(index)
            elif views._cached_views[viewclass]:
                # there: pop() -> pop(0)
                view, stale = views._cached_views[viewclass].pop(0), True
            elif dirty_class:
                view, stale = dirty_class.popitem()[1], True
        elif views._cached_views[viewclass]:
            # there: pop() -> pop(0)
            view, stale = views._cached_views[viewclass].pop(0), True

        if view is None:
            view = self.create_view(index, data_item, viewclass)
            if view is None:
                return

        if stale:
            self.refresh_view_attrs(index, data_item, view)
        return view
    views.RecycleDataAdapter.get_view = get_view

    from kivy.uix.recyclelayout import RecycleLayout

    def _catch(self, instance=None, value=None):
        rv = self.recycleview
        if rv is None:
            return
        idx = self.view_indices.get(instance)
        if idx is not None:
            if self._size_needs_update:
                return
            opt = self.view_opts[idx]
            sh = opt['size_hint']
            size_ok = (
                (sh[0] is not None or instance.size[0] == opt['size'][0]) and
                (sh[1] is not None or instance.size[1] == opt['size'][1])
            )
            if (size_ok and
                  instance.size_hint == opt['size_hint'] and
                  instance.size_hint_min == opt['size_hint_min'] and
                  instance.size_hint_max == opt['size_hint_max'] and
                  instance.pos_hint == opt['pos_hint']):
                return
            self._size_needs_update = True
            rv.refresh_from_layout(view_size=True)
        elif instance is self:
            prev = getattr(self, '_prev_catch_size', None)
            cur = tuple(self.size)
            self._prev_catch_size = cur
            if prev is not None:
                horizontal = getattr(self, 'orientation', 'vertical') == 'horizontal'
                width_changed = prev[0] != cur[0]
                height_changed = prev[1] != cur[1]
                if not horizontal and width_changed and not height_changed:
                    pad_l, pad_t, pad_r, pad_b = self.padding
                    inner_w = cur[0] - pad_l - pad_r
                    for widget, index in self.view_indices.items():
                        opt = self.view_opts[index]
                        sh = opt['size_hint']
                        if sh[0] is not None:
                            widget.width = sh[0] * inner_w
                        else:
                            widget.width = opt['size'][0]
                    return
                if horizontal and height_changed and not width_changed:
                    pad_l, pad_t, pad_r, pad_b = self.padding
                    inner_h = cur[1] - pad_t - pad_b
                    for widget, index in self.view_indices.items():
                        opt = self.view_opts[index]
                        sh = opt['size_hint']
                        if sh[1] is not None:
                            widget.height = sh[1] * inner_h
                        else:
                            widget.height = opt['size'][1]
                    return
            rv.refresh_from_layout()
        else:
            rv.refresh_from_layout()

    RecycleLayout._catch_layout_trigger = _catch

    def _refresh_view_layout(self, index, layout, view, viewport):
        opt = self.view_opts[index].copy()
        width_none = opt.pop('width_none')
        height_none = opt.pop('height_none')
        opt.update(layout)

        w, h = opt['size']
        shw, shh = opt['size_hint']

        pad_l, pad_t, pad_r, pad_b = self.padding

        if shw is None and width_none:
            w = None
        elif shw is not None:
            w = shw * (self.width - pad_l - pad_r)

        if shh is None and height_none:
            h = None
        elif shh is not None:
            h = shh * (self.height - pad_t - pad_b)

        opt['size'] = w, h
        super(RecycleLayout, self).refresh_view_layout(index, opt, view, viewport)

    RecycleLayout.refresh_view_layout = _refresh_view_layout

    def _set_visible(self, indices, data, viewport):
        view_opts = self.view_opts
        new, remaining, old = self.recycleview.view_adapter.set_visible_views(
            indices, data, view_opts)

        view_indices = self.view_indices
        for _, widget in old:
            self.remove_widget(widget)
            del view_indices[widget]

        refresh_view_layout = self.refresh_view_layout

        # refresh new (as in original)
        for index, widget in new:
            opt = view_opts[index].copy()
            del opt['width_none']
            del opt['height_none']
            refresh_view_layout(index, opt, widget, viewport)

        # NEW: refresh remaining too, so their size follows the container
        for index, widget in remaining:
            opt = view_opts[index].copy()
            del opt['width_none']
            del opt['height_none']
            refresh_view_layout(index, opt, widget, viewport)

        add = self.add_widget
        for index, widget in new:
            view_indices[widget] = index
            if widget.parent is None:
                add(widget)

        changed = False
        for index, widget in new + remaining:
            opt = view_opts[index]
            sh = opt['size_hint']
            size_ok = (
                (sh[0] is not None or widget.size[0] == opt['size'][0]) and
                (sh[1] is not None or widget.size[1] == opt['size'][1])
            )
            ok = (size_ok and
                  widget.size_hint == opt['size_hint'] and
                  widget.size_hint_min == opt['size_hint_min'] and
                  widget.size_hint_max == opt['size_hint_max'] and
                  widget.pos_hint == opt['pos_hint'])
            if not ok:
                changed = True

        if changed:
            self._size_needs_update = True
            self.recycleview.refresh_from_layout(view_size=True)

    RecycleLayout.set_visible_views = _set_visible
