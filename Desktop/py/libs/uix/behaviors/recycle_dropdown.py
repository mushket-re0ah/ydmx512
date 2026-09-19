from kivy.properties import (
    ObjectProperty, BooleanProperty, NumericProperty, StringProperty
)
from kivy.clock import Clock
from libs.kivy_utils import AutoUnbindBehavior
from libs.uix.recycle_dropdown import RecycleDropdown
from libs.uix.button import HoverButton


class RecycleDropdownBehavior(AutoUnbindBehavior):
    values = ObjectProperty(allownone=True)
    host_attr = StringProperty(None)
    viewclass = ObjectProperty(HoverButton)
    dropdown_cls = ObjectProperty(RecycleDropdown)
    max_height = NumericProperty("400dp")
    min_height = NumericProperty("120dp")
    cls_height = NumericProperty("30dp")
    selected = ObjectProperty(allownone=True)
    auto_width = BooleanProperty(True)
    dropdown_width = NumericProperty("200dp")
    auto_height = BooleanProperty(True)
    dropdown_height = NumericProperty("300dp")
    force_host_value = ObjectProperty(None, allownone=True)

    opened = BooleanProperty(False)
    auto_select = BooleanProperty(True)

    __events__ = ("on_select",)

    _dropdown = None
    _trigger_set_host_value = None
    def __init__(self, **kwargs):
        self._trigger_set_host_value = Clock.create_trigger(self._set_host_value, 0)
        self.bind(selected=self._trigger_set_host_value)
        super().__init__(**kwargs)

    def on_kv_post(self, _):
        if self.values_getter is None:
            self.values_getter = self.dropdown_cls._default_values_getter
        if self.value_to_dict is None:
            self.value_to_dict = self.dropdown_cls._default_value_to_dict
        if self.value_to_host is None:
            self.value_to_host = self.dropdown_cls._default_value_to_host

        if self.auto_select and self.selected is None and self.values:
            self.selected = self.filter_values_getter(self)[0]

    values_getter = ObjectProperty(None, allownone=True)
    value_to_dict = ObjectProperty(None, allownone=True)
    value_to_host  = ObjectProperty(None, allownone=True)
    def _default_filter_values_getter(self):
        return self.values_getter(self)
    filter_values_getter = ObjectProperty(_default_filter_values_getter)

    def _set_host_value(self, _):
        host_value = self.force_host_value if self.force_host_value is not None\
                     else self.value_to_host(self.selected)
        setattr(self, self.host_attr, host_value)

    def _update_filtered_values(self):
        if self._dropdown:
            self._dropdown.update_values()

    def on_opened(self, instance, value):
        if value:
            self._dropdown.open(self)
        else:
            if self._dropdown.attach_to:
                self._dropdown.dismiss()

    def on_select(self, value: any):
        pass

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        if self._do_mouse_scroll(touch):
            return True
        return super().on_touch_down(touch)

    def _do_mouse_scroll(self, touch) -> bool:
        if touch.button == "scrollup":
            self._do_scroll(1)
            return True
        elif touch.button == "scrolldown":
            self._do_scroll(-1)
            return True
        return False

    def _do_scroll(self, step: int):
        values = self.values_getter(self)
        new_index = values.index(self.selected) + step
        if (new_index < 0) or (new_index >= len(values)):
            return
        self.selected = values[new_index]
        self.dispatch("on_select", self.selected)

    def __build_dropdown(self):
        self._dropdown = self.dropdown_cls(
            viewclass=self.viewclass,
            auto_width=self.auto_width,
            force_width=self.dropdown_width,
            auto_height=self.auto_height,
            force_height=self.dropdown_height,
            values=self.values,
            values_getter=lambda this: self.filter_values_getter(self),
            value_to_dict=self.value_to_dict,
            value_to_host=self.value_to_host,
            max_height=self.max_height,
            min_height=self.min_height,
            cls_height=self.cls_height
        )
        self.bind_to(self._dropdown,
                     on_select=self._on_dropdown_select,
                     on_dismiss=self._close_dropdown)
        Clock.schedule_once(self.scroll_to_selected, 0)

    def scroll_to_selected(self, *args):
        sv = self._dropdown.scrollview
        values = self.filter_values_getter(self)
        if self.selected in values:
            sv.scroll_to(values.index(self.selected))

    def _open_dropdown(self):
        self.__build_dropdown()
        self.opened = True

    def _close_dropdown(self, *largs):
        if self._dropdown:
            self.unbind_from(self._dropdown)
        self.opened = False
        self._dropdown = None

    def _on_dropdown_select(self, instance, data, *largs):
        self.selected = data
        self.dispatch("on_select", data)
        self._trigger_set_host_value()
        self.opened = False
