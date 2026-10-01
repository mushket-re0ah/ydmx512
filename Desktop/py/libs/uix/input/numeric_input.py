from typing import Callable, Dict, FrozenSet, List, Union

from kivy.input.motionevent import MotionEvent
from kivy.lang import Builder
from kivy.properties import AliasProperty, BooleanProperty, NumericProperty
from kivy.uix.widget import Widget
from kivy.utils import boundary

from libs.typecheck import Number, OptionalNumber
from libs.uix.context_menu import ContextMenu, ContextMenuItem, ContextMenuTemplates
from libs.uix.input import HoverInput
from libs.uix.restricted_scrollview import RestrictedScrollView

Builder.load_string("""
<NumericInput>:  # HoverInput
    input_filter: "int"
    input_type: "number"
    multiline: False
"""
)


class NumericInput(HoverInput):
    _value: OptionalNumber = NumericProperty(0, allownone=True, force_dispatch=True)
    default_value: OptionalNumber = NumericProperty(0, allownone=True)
    minimum: Number = NumericProperty(0)
    maximum: Number = NumericProperty(100)
    allow_empty: bool = BooleanProperty(False)
    step_mouse_scroll: Number = NumericProperty(1)
    decimals: int = NumericProperty(2)

    # Для изменения значений смещением курсора
    sensitive: Number = NumericProperty(2)
    THRESHOLD_Y: float = 35

    def on_kv_post(self, base_widget: Widget):
        self._set_text_by_value()
        self.default_value = self.value

    def on_minimum(self, *_):
        self.property("value").dispatch(self)

    def on_maximum(self, *_):
        self.property("value").dispatch(self)

    def on_text(self, _, text: str):
        self.value = self._str_to_value(text)

    value_start_focus = None

    def on_focus(self, _, focus: bool):
        if focus:
            self.value_start_focus = self.value
        if not focus:
            self._set_unredo_value(
                self.value_start_focus,
                self.value,
                from_undo=False)
            self._set_text_by_value()
        super().on_focus(_, focus)

    def set_value(self, value: OptionalNumber):
        if value is None:
            if self.allow_empty:
                self._value = value
                self._set_text_by_value()
                self.property("value").dispatch(self)
                return
            raise ValueError(
                "Поле ввода не поддерживает None. Если должно,"
                " установите allow_empty: True")
        value = self._value_bounds(value)
        if value != self._value:
            self._value = value
        if not self.focus:
            self._set_text_by_value()

    value: OptionalNumber = AliasProperty(
        lambda self: self._value,
        set_value,
        bind=("_value", "minimum", "maximum")
    )

    def _set_text_by_value(self):
        self.text = self._value_to_str(self.value)

    def _value_to_str(self, value: OptionalNumber) -> str:
        if value is None:
            return ""
        return str(value)

    def _str_to_value(self, text: str) -> OptionalNumber:
        if text in ("", "-"):
            if self.allow_empty:
                return None
            return self.default_value
        value = float(text) if self.input_filter == "float" else int(
            float(text))
        return self._value_bounds(value)

    def _value_bounds(self, value: Number) -> Number:
        if self.input_filter == "float":
            value = round(value, self.decimals)
        else:
            value = int(value)
        return boundary(value, self.minimum, self.maximum)

    def on_touch_down(self, touch: MotionEvent) -> bool:
        if touch.grab_current is not None:
            return False

        if not self.collide_point(*touch.pos):
            return False

        if self.disabled:
            return True

        if self._do_mouse_scroll(touch):
            return True
        touch.ud["start_pos_y"] = touch.y
        touch.ud["start_value"] = self.value
        touch.grab(self)
        return super().on_touch_down(touch)

    def on_touch_move(self, touch: MotionEvent) -> bool:
        if touch.grab_current is self and self._do_move_value(touch):
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch: MotionEvent) -> bool:
        if touch.grab_current is self:
            touch.ungrab(self)
            return True
        return super().on_touch_up(touch)

    def _do_move_value(self, touch: MotionEvent) -> bool:
        if self._threshold_check(touch):
            y_offset = self._get_y_offset(touch)
            value = touch.ud["start_value"]
            value = self.default_value if value is None else value
            value = self.minimum if value is None else value
            self.value = value + y_offset / self.sensitive
            self._set_text_by_value()
            return True
        return False

    def _get_y_offset(self, touch: MotionEvent) -> float:
        if touch.ud["start_pos_y"] > touch.y:
            return touch.y - touch.ud["start_pos_y"] + self.THRESHOLD_Y
        return touch.y - touch.ud["start_pos_y"] - self.THRESHOLD_Y

    def _threshold_check(self, touch: MotionEvent) -> bool:
        return abs(touch.y - touch.ud["start_pos_y"]) > self.THRESHOLD_Y

    def _do_mouse_scroll(self, touch: MotionEvent) -> bool:
        if touch.button == "scrollup":
            self._inc_value(-self.step_mouse_scroll)
            return True
        if touch.button == "scrolldown":
            self._inc_value(self.step_mouse_scroll)
            return True
        return False

    def create_hotkeys(self) -> Dict[FrozenSet[str], Callable[[], None]]:
        return {
            **super().create_hotkeys(),
            frozenset({"up"}): self._do_arrows_scroll_up,
            frozenset({"down"}): self._do_arrows_scroll_down,
        }

    def _do_arrows_scroll_up(self):
        self._inc_value(self.step_mouse_scroll)

    def _do_arrows_scroll_down(self):
        self._inc_value(-self.step_mouse_scroll)

    def _inc_value(self, step: Number):
        cursor = self.cursor
        value = self.default_value if self.value is None else self.value
        if value is None:
            self.value = self.minimum
        else:
            self.value = value + step
        self._set_text_by_value()
        self.cursor = cursor

    def _create_context_menu(self) -> ContextMenu:
        return ContextMenu(items=self._create_context_menu_items(clean_btn=False))

    def _create_context_menu_items(self, clean_btn: bool=False) -> List[ContextMenuItem]:
        items = super()._create_context_menu_items()
        items.append(ContextMenuTemplates.separator())
        items.append(
            ContextMenuTemplates.button(
                text="Установить по-умолчанию",
                on_release=lambda x: self.set_default(),
            ))
        items.append(
            ContextMenuTemplates.button(
                text="Установить минимум",
                on_release=lambda x: self.set_minimum(),
            ))
        items.append(
            ContextMenuTemplates.button(
                text="Установить максимум",
                on_release=lambda x: self.set_maximum(),
            ))
        items.append(
            ContextMenuTemplates.button(
                text="Установить пустое",
                on_release=lambda x: self.set_empty(),
                disabled=not self.allow_empty
            ))
        return items

    def set_default(self):
        self.value = self.default_value

    def set_minimum(self):
        self.value = self.minimum

    def set_maximum(self):
        self.value = self.maximum

    def set_empty(self):
        self.value = None

    def _set_unredo_bkspc(self, ol_index, new_index, substring, from_undo,
                          mode):
        return

    def _set_unredo_delsel(self, a, b, substring, from_undo):
        return

    def _set_unredo_insert(self, ci, sci, substring, from_undo):
        return

    # custom
    def _set_unredo_value(self, old_value: Union[int, float],
                          new_value: Union[int, float], from_undo: bool):
        if from_undo:
            return
        self._undo.append({
            "undo_command": ("set_value", old_value, new_value),
            "redo_command": old_value})
        self._redo = []

    def do_redo(self):
        try:
            x_item = self._redo.pop()
            undo_type = x_item['undo_command'][0]

            if undo_type == "set_value":
                old_value, new_value = x_item['undo_command'][1:]
                self.value = new_value
                self._set_text_by_value()
            self._undo.append(x_item)
        except IndexError:
            pass

    def do_undo(self):
        try:
            x_item = self._undo.pop()
            undo_type = x_item['undo_command'][0]
            if undo_type == "set_value":
                old_value, new_value = x_item['undo_command'][1:]
                self.value = old_value
                self._set_text_by_value()
            self._redo.append(x_item)
        except IndexError:
            pass

RestrictedScrollView.register_scrollable_widget_class(NumericInput)
