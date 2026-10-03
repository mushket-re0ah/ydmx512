from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type

from kivy.input.motionevent import MotionEvent
from kivy.lang import Builder
from kivy.properties import (
    AliasProperty,
    BooleanProperty,
    ColorProperty,
    NumericProperty,
    ObjectProperty,
    OptionProperty,
    ReferenceListProperty,
    StringProperty,
)
from kivy.uix.behaviors import ButtonBehavior, ToggleButtonBehavior
from kivy.uix.widget import Widget

from libs.animation import AnimationBehavior, StatefulColorProperty
from libs.mouse_manager import cursor_manager
from libs.mouse_manager.hover import HoverBehavior
from libs.typecheck import RGBA, WidgetProtocol
from libs.uix import colorscheme as uix_cs
from libs.uix.behaviors.tooltip import TooltipBehavior
from libs.uix.label import RestrictedLabel
from libs.uix.layouts import ModalBoxLayout
from misc import imgs_path

if TYPE_CHECKING:
    from libs.uix.recycle_restricted_scrollview import RecycleRestrictedScrollView
    from libs.uix.scroll_layout import ScrollLayout


Builder.load_string("""
#:import uix_cs libs.uix.colorscheme

<-ImageButton>:
    state_image: self.background_down if self.is_down else self.background_normal
    canvas:
        Color:
            rgba: self.background_color
        Rectangle:
            size: self.size
            pos: self.pos
            source: self.state_image


<-ImageToggleButton>:
    state_image: self.background_down if self.is_down else self.background_normal
    canvas:
        Color:
            rgba: self.background_color
        Rectangle:
            size: self.size
            pos: self.pos
            source: self.state_image


<-HoverButton>:
    state_image: self.background_down if self.is_down else self.background_normal
    canvas:
        Color:
            rgba: self.background_color
        Rectangle:
            size: self.size
            pos: self.pos
            source: self.state_image
        Color:
            rgba: uix_cs.Label.fg_disabled if self.disabled else uix_cs.Label.fg
        Rectangle:
            texture: self.texture
            size: self.texture_size
            pos: (\
                int(self.center_x - self.texture_size[0] / 2.0),\
                int(self.center_y - self.texture_size[1] / 2.0)\
            )


<-HoverToggleButton>:
    state_image: self.background_down if self.is_down else self.background_normal
    canvas:
        Color:
            rgba: self.background_color
        Rectangle:
            size: self.size
            pos: self.pos
            source: self.state_image
        Color:
            rgba: uix_cs.Label.fg_disabled if self.disabled else uix_cs.Label.fg
        Rectangle:
            texture: self.texture
            size: self.texture_size
            pos: (\
                int(self.center_x - self.texture_size[0] / 2.0),\
                int(self.center_y - self.texture_size[1] / 2.0)\
            )


<OptionToggleButtonContextMenu>:
    scroll_layout: scroll_layout
    scrollview: scrollview

    size: ("150dp", "200dp")

    RestrictedLabel:
        text: root.title
        font_size: "14sp"
        size_hint: (1, None)
        size: self.texture_size
    ScrollLayout:
        id: scroll_layout
        scrollview: scrollview
        RecycleRestrictedScrollView:
            id: scrollview
            viewclass: root.option_cls
            scroll_by_content: True
            do_scroll_x: False
            do_scroll_by_element: True
            RecycleBoxLayout:
                size_hint: (1, None)
                orientation: "vertical"
                default_size_hint: (1, None)
                height: self.minimum_height
                default_size: (None, "30dp")



<-ImageOptionToggleButton>:
    state_image: self.background_down if self.pressed else self.background_normal
    canvas:
        Color:
            rgba: self.background_color
        Rectangle:
            size: self.size
            pos: self.pos
            source: self.state_image


<-OptionToggleButton>:
    state_image: self.background_down if self.pressed else self.background_normal
    canvas:
        Color:
            rgba: self.background_color
        Rectangle:
            size: self.size
            pos: self.pos
            source: self.state_image
        Color:
            rgba: uix_cs.Label.fg_disabled if self.disabled else uix_cs.Label.fg
        Rectangle:
            texture: self.texture
            size: self.texture_size
            pos: (\
                int(self.center_x - self.texture_size[0] / 2.0),\
                int(self.center_y - self.texture_size[1] / 2.0)\
            )



<ColorToggleButton>:  # Widget
    canvas:
        Color:
            rgba: self.color
        Rectangle:
            size: self.size
            pos: self.pos
            source: self.source
        Color:
            rgba: self.border_color
        Line:
            rectangle: (self.x + 1, self.y + 1, self.width - 1, self.height - 1)
            width: 1


<ArrowBehavior>:
    canvas.after:
        Color:
            rgba: self.arrow_color if self.do_show_arrow else [0, 0, 0, 0]
        Triangle:
            points: self.arrow_points
"""
)

class ExpansiveButtonBehavior(ButtonBehavior, WidgetProtocol):
    is_down: bool = AliasProperty(
        lambda self: self.state == "down",
        lambda self, value: setattr(self, "state", "down" if value else "normal"),
        bind=("state",),
    )
    pressed: bool = BooleanProperty(False)

    def on_touch_down(self, touch: MotionEvent) -> bool:
        pressed = super().on_touch_down(touch)
        if pressed:
            self.pressed = True
            self.is_down = True
        return pressed

    def on_touch_up(self, touch: MotionEvent) -> bool:
        self.is_down = False
        self.pressed = False
        if not self.collide_point(*touch.pos):
            return False
        return super().on_touch_up(touch)


class ExpansiveToggleButtonBehavior(ToggleButtonBehavior, WidgetProtocol):
    is_down: bool = AliasProperty(
        lambda self: self.state == "down",
        lambda self, value: setattr(self, "state", "down" if value else "normal"),
        bind=("state",),
    )
    always_release: bool = BooleanProperty(False)
    pressed: bool = BooleanProperty(False)
    discard_state_release: bool = BooleanProperty(True)
    _toggle_committed: bool = BooleanProperty(False)

    def _do_press(self):
        self.pressed = True
        if (not self.allow_no_selection and
                self.group and self.is_down):
            return

        self._release_group(self)
        self.is_down = not self.is_down
        self._toggle_committed = True

    def _do_release(self, *args: Any):
        self.pressed = False
        self._toggle_committed = False

    def on_touch_up(self, touch: MotionEvent) -> bool:
        self.pressed = False
        if self.collide_point(*touch.pos):
            # Бля да хуй знает на самом деле в чем был мой замысел с return False
            return super().on_touch_up(touch)
            return False
        return super().on_touch_up(touch)


class ButtonBase(AnimationBehavior, TooltipBehavior):
    background_color: RGBA = StatefulColorProperty(
        normal=uix_cs.HoverButton.background_color_normal,
        states={
            "disabled": uix_cs.HoverButton.background_color_disabled,
            ("is_down", "hover"): uix_cs.HoverButton.background_color_hover,
            "is_down": uix_cs.HoverButton.background_color_down,
            ("pressed", "hover"): uix_cs.HoverButton.background_color_hover,
            "pressed": uix_cs.HoverButton.background_color_down,
            "hover": uix_cs.HoverButton.background_color_hover,
        }
    )
    background_normal: str = StringProperty(imgs_path.button_background_normal)
    background_down: str = StringProperty(imgs_path.button_background_down)

    def on_mouse_move(self, _):
        if self.hover and not self.disabled:
            cursor_manager.set_cursor("hand")


class ImageButton(ButtonBase, ExpansiveButtonBehavior, Widget):
    pass


class HoverButton(ButtonBase, ExpansiveButtonBehavior, RestrictedLabel):
    pass


class ImageToggleButton(ButtonBase, ExpansiveToggleButtonBehavior, Widget):
    pass


class HoverToggleButton(ButtonBase, ExpansiveToggleButtonBehavior, RestrictedLabel):
    pass


class OptionToggleButtonContextMenu(ModalBoxLayout):
    option_cls: Type[ButtonBase] = ObjectProperty()
    scroll_layout: "ScrollLayout" = ObjectProperty()
    scrollview: "RecycleRestrictedScrollView" = ObjectProperty()
    title: str = StringProperty("")


class OptionToggleButtonContextMenuOption(HoverButton):
    modal: OptionToggleButtonContextMenu = ObjectProperty()
    state_button: "OptionToggleButton" = ObjectProperty()
    state_button_state: Any = ObjectProperty()

    def on_release(self):
        self.state_button.state = self.state_button_state
        self.modal.dismiss()


class OptionToggleButton(ButtonBase, ExpansiveToggleButtonBehavior, RestrictedLabel):
    modal_cls: Type[OptionToggleButtonContextMenu] = ObjectProperty(OptionToggleButtonContextMenu)
    option_cls: Type[OptionToggleButtonContextMenuOption] = ObjectProperty(
        OptionToggleButtonContextMenuOption
    )
    state: Any = OptionProperty(None, options=[None])  # переопределять в предке
    state_to_str: Dict[Any, str]

    def on_kv_post(self, base_widget: Widget):
        self.property("state").dispatch(self)

    last_touch: Optional[MotionEvent] = None
    def on_touch_down(self, touch: MotionEvent) -> bool:
        self.last_touch = touch
        if self.collide_point(*touch.pos) and not self.disabled:
            if touch.button == "scrollup":
                self.state = self.get_state_step(-1)
                return True
            if touch.button == "scrolldown":
                self.state = self.get_state_step(1)
                return True
            if touch.button == "middle":
                self._open_state_menu()
                return True
        return super().on_touch_down(touch)

    def on_state(self, _, state: str):
        self.text = self.state_to_str[state]

    def _do_press(self):
        self.pressed = True
        if (not self.allow_no_selection and
                self.group and self.is_down):
            return

        self._release_group(self)

        direction = 1
        if self.last_touch.button == "right":  # pyright: ignore[reportOptionalMemberAccess]
            direction = -direction
        self.state = self.get_state_step(direction)

    def _do_release(self, *args: Any):
        self.pressed = False
        if (not self.allow_no_selection and
                self.group and self.is_down):
            return

        self._release_group(self)
        if self.discard_state_release:
            direction = -1
            if self.last_touch.button == "right":  # pyright: ignore[reportOptionalMemberAccess]
                direction = -direction
            self.state = self.get_state_step(direction)

    def get_state_step(self, direction: int) -> Any:
        lst: List[Any] = self.property("state").options
        i = lst.index(self.state)
        i = (i + direction) % len(lst)
        return lst[i]

    def _open_state_menu(self):
        modal = self.modal_cls(option_cls=self.option_cls)
        modal.open(self)
        modal.scrollview.data = self._make_state_menu_data(modal)

    def _make_state_menu_data(self, modal: OptionToggleButtonContextMenu) -> List[Dict[str, Any]]:
        return []


class ImageOptionToggleButtonBehavior(ButtonBase, ExpansiveToggleButtonBehavior, Widget):
    state: Any = OptionProperty(None, options=[None])  # переопределять в предке


class ColorToggleButton(AnimationBehavior, HoverBehavior, ExpansiveToggleButtonBehavior, Widget):
    color: RGBA = ColorProperty()
    source: str = StringProperty("")

    border_color: RGBA = StatefulColorProperty(
        normal=uix_cs.ColorToggleButton.border_color_normal,
        states={
            ("is_down", "hover"): uix_cs.ColorToggleButton.border_color_hover,
            "is_down": uix_cs.ColorToggleButton.border_color_is_select,
            "hover": uix_cs.ColorToggleButton.border_color_hover,
        }
    )


class ArrowBehavior(WidgetProtocol):
    arrow_color: RGBA = StatefulColorProperty(
        normal=uix_cs.ArrowToggleButton.arrow_color_normal,
        states={
            "disabled": uix_cs.ArrowToggleButton.arrow_color_disabled,
            ("is_down", "hover"): uix_cs.ArrowToggleButton.arrow_color_hover,
            "is_down": uix_cs.ArrowToggleButton.arrow_color_down,
            "hover": uix_cs.ArrowToggleButton.arrow_color_hover,
        }
    )

    reverse_arrow: bool = BooleanProperty(False)
    vertical_arrow: bool = BooleanProperty(True)
    do_show_arrow: bool = BooleanProperty(True)

    arrow_height: float = NumericProperty("8dp")
    arrow_width: float = NumericProperty("8dp")
    arrow_size: Tuple[float, float] = ReferenceListProperty(arrow_width, arrow_height)
    arrow_offset_right: float = NumericProperty("4dp")

    def _get_arrow_points(self) -> Tuple[float, float, float, float, float, float]:
        y_padding = (self.height - self.arrow_height) / 2
        top = self.top - y_padding
        y = self.y + y_padding
        right = self.right - self.arrow_offset_right
        left = right - self.arrow_width

        if self.vertical_arrow:
            center_x = right - (self.arrow_width / 2)
            if self.reverse_arrow:
                return (left, y, center_x, top, right, y)
            return (left, top, right, top, center_x, y)
        center_y = self.center_y
        if self.reverse_arrow:
            return (left, center_y, right, top, right, y)
        return (right, center_y, left, top, left, y)

    arrow_points: Tuple[float, float, float, float, float, float] = AliasProperty(
        _get_arrow_points,
        bind=(
            "vertical_arrow", "reverse_arrow",
            "arrow_size", "arrow_offset_right",
            "pos", "size", "x", "y", "center_x",
            "center_y", "right", "top", "width", "height"
        ),
        cache=True
    )


class ArrowImageButton(ArrowBehavior, ImageButton):
    pass


class ArrowToggleButton(ArrowBehavior, HoverToggleButton):
    pass
