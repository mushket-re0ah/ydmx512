from typing import Tuple, Union

from kivy.lang import Builder
from kivy.properties import AliasProperty, BooleanProperty, NumericProperty
from kivy.uix.widget import Widget
from typing_extensions import Self

from libs.animation import AnimationBehavior, StatefulColorProperty
from libs.mouse_manager import cursor_manager
from libs.properties import ContextualNumericProperty
from libs.typecheck import RGBA, Number
from libs.uix import colorscheme as uix_cs
from libs.uix.behaviors.mouse import TouchMouseBehavior
from libs.uix.behaviors.tooltip import TooltipBehavior
from libs.uix.context_menu import ContextMenu, ContextMenuTemplates
from libs.uix.restricted_scrollview import RestrictedScrollView

Builder.load_string("""
<RotaryButton>:
    size_hint: (None, None)
    size: ("64dp", "64dp")
    canvas.before:
        Color:
            rgba: self.rotary_passive_color
        SmoothEllipse:
            pos: self.pos
            size: self.size
        Color:
            rgba: self.rotary_active_color
        SmoothEllipse:
            pos: self.pos
            size: self.size
            angle_start: self.angle_start
            angle_end: self.angle
        PushMatrix
        Rotate:
            angle: -self.angle
            origin: self.center
        Color:
            rgb: self.texture_color
        SmoothEllipse:
            pos: (self.x + (self.width * 0.072), self.y + (self.height * 0.072))
            size: (self.width * 0.86, self.height * 0.86)
            source: imgs_path.rotary_button
    canvas.after:
        PopMatrix
""")


class RotaryButton(TouchMouseBehavior, AnimationBehavior, TooltipBehavior, Widget):
    TEXTURE_PADDING_POS: float = 0.07
    TEXTURE_PADDING_SIZE: float = 1 - TEXTURE_PADDING_POS * 2

    texture_color: RGBA = StatefulColorProperty(
        normal=uix_cs.RotaryButton.texture_color_normal,
        states={
            "disabled": uix_cs.RotaryButton.texture_color_disabled_diff,
            "focus": uix_cs.RotaryButton.texture_color_focused_diff,
            "hover": uix_cs.RotaryButton.texture_color_hover_diff,
        }
    )
    rotary_active_color: RGBA = StatefulColorProperty(
        normal=uix_cs.RotaryButton.rotary_active_color_normal,
        states={
            "disabled": uix_cs.RotaryButton.rotary_active_color_disabled_diff,
            "focus": uix_cs.RotaryButton.rotary_active_color_focused_diff,
            "hover": uix_cs.RotaryButton.rotary_active_color_hover_diff,
        }
    )
    rotary_passive_color: RGBA = StatefulColorProperty(
        normal=uix_cs.RotaryButton.rotary_passive_color_normal,
        states={
            "disabled": uix_cs.RotaryButton.rotary_passive_color_disabled_diff,
            "focus": uix_cs.RotaryButton.rotary_passive_color_focused_diff,
            "hover": uix_cs.RotaryButton.rotary_passive_color_hover_diff,
        }
    )

    angle_start: float = NumericProperty(-135)
    angle_end: float = NumericProperty(135)

    minimum: Number = NumericProperty(0)
    maximum: Number = NumericProperty(100)
    default_value: Number = NumericProperty(0, allownone=True)
    step_mouse_scroll: Number = NumericProperty(5)
    drag_sensitivity: Number = NumericProperty(150)
    decimals: int = NumericProperty(2)

    focus: bool = BooleanProperty(False)

    value: Number = ContextualNumericProperty(
        default=0,
        min_getter=lambda self: self.minimum,
        max_getter=lambda self: self.maximum,
        decimals_getter=lambda self: self.decimals,
        dependencies=("minimum", "maximum", "decimals")
    )

    drag_enabled: bool = BooleanProperty(True)

    def on_drag_start(self, touch) -> bool:
        self.focus = True
        touch.ud["start_value"] = self.value
        return True

    def on_drag(self, touch, delta_x: float, delta_y: float) -> bool:
        y_offset = delta_y / self.drag_sensitivity
        y_offset *= self._get_full_value()
        self.value = touch.ud["start_value"] + y_offset
        return True

    def on_drag_end(self, touch) -> bool:
        self.focus = False
        return True

    def on_scroll_up(self, touch) -> bool:
        self.value -= self.step_mouse_scroll
        return True

    def on_scroll_down(self, touch) -> bool:
        self.value += self.step_mouse_scroll
        return True

    def on_right_click(self, touch) -> bool:
        self.open_context_menu(touch.pos)
        return True

    def on_mouse_move(self, _):
        if self.hover and not self.disabled:
            cursor_manager.set_cursor("hand")

    def _get_full_angle(self) -> Union[int, float]:
        return abs(self.angle_start) + abs(self.angle_end)

    def _get_full_value(self) -> Union[int, float]:
        return max(self.maximum - self.minimum, 1)

    def open_context_menu(self, pos: Tuple[float, float]):
        if self.disabled:
            return
        self._create_context_menu().open(self, pos=pos)

    def _create_context_menu(self) -> ContextMenu:
        return ContextMenu(items=[
            ContextMenuTemplates.button(
                text="Установить по-умолчанию",
                on_release=lambda _: setattr(self, "value", self.default_value),
            ),
            ContextMenuTemplates.button(
                text="Установить минимум",
                on_release=lambda _: setattr(self, "value", self.minimum),
            ),
            ContextMenuTemplates.button(
                text="Установить максимум",
                on_release=lambda _: setattr(self, "value", self.maximum),
            ),
            ]
        )

    def _get_angle(self) -> float:
        # Вычисляем угол пропорционально значению
        if self._get_full_value() != 0:
            angle_per_value = self._get_full_angle() / self._get_full_value()
            angle = self.angle_start + (self.value - self.minimum) * angle_per_value
        else:
            angle = self.angle_start
        return min(max(angle, self.angle_start), self.angle_end)

    angle: float = AliasProperty(
        _get_angle,
        bind=["value", "angle_start", "angle_end", "minimum", "maximum"],
        cache=True
    )


class PanRotaryButton(RotaryButton):
    angle_start: float = NumericProperty(-180)
    angle_end: float = NumericProperty(180)

    color_left = uix_cs.PanRotaryButton.rotary_active_color_left_normal
    color_right = uix_cs.PanRotaryButton.rotary_active_color_right_normal

    def on_kv_post(self, base_widget: Self):
        super().on_kv_post(base_widget)
        self._update_color()

    def on_angle(self, _, _angle: float):
        self._update_color()

    def _update_color(self):
        prop = self.property("rotary_active_color")
        if self.angle > 0:
            prop.set_normal(self, self.color_right)
        else:
            prop.set_normal(self, self.color_left)

RestrictedScrollView.register_scrollable_widget_class(RotaryButton)
