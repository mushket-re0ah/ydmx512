from libs.uix.label import RestrictedLabel
from kivy.uix.widget import Widget
from kivy.event import EventDispatcher
from kivy.uix.behaviors import ButtonBehavior, ToggleButtonBehavior
from kivy.properties import (
    ColorProperty, StringProperty, BooleanProperty, NumericProperty,
    ReferenceListProperty, AliasProperty, OptionProperty, ObjectProperty
)
from libs.mouse_manager.hover import HoverBehavior
from libs.animation import AnimationBehavior
from libs.uix.behaviors.tooltip import TooltipBehavior
from misc import colorscheme as cs
from misc import imgs_path
from libs.mouse_manager import cursor_manager
from libs.uix.layouts import ModalBoxLayout
from kivy.lang import Builder
from libs.animation import StatefulColorProperty

Builder.load_file("ui/components/button.kv")


class ExpansiveButtonBehavior(ButtonBehavior):
    is_down = AliasProperty(
        lambda self: self.state == "down",
        lambda self, value: setattr(self, "state", "down" if value else "normal"),
        bind=["state"],
    )
    pressed = BooleanProperty(False)

    def on_touch_down(self, touch):
        pressed = super().on_touch_down(touch)
        if pressed:
            self.pressed = True
            self.is_down = True
            return pressed

    def on_touch_up(self, touch):
        self.is_down = False
        self.pressed = False
        if not self.collide_point(*touch.pos):
            return False
        return super().on_touch_up(touch)


class ExpansiveToggleButtonBehavior(ToggleButtonBehavior):
    is_down = AliasProperty(
        lambda self: self.state == "down",
        lambda self, value: setattr(self, "state", "down" if value else "normal"),
        bind=["state"],
    )
    always_release = BooleanProperty(False)
    pressed = BooleanProperty(False)
    discard_state_release = BooleanProperty(True)
    _toggle_committed = BooleanProperty(False)

    def _do_press(self):
        self.pressed = True
        if (not self.allow_no_selection and
                self.group and self.is_down):
            return

        self._release_group(self)
        self.is_down = not self.is_down
        self._toggle_committed = True

    def _do_release(self, *args):
        self.pressed = False
        self._toggle_committed = False

    def on_touch_up(self, touch):
        self.pressed = False
        if self.collide_point(*touch.pos):
            # Бля да хуй знает на самом деле в чем был мой замысел с return False
            return super().on_touch_up(touch)
            return False
        return super().on_touch_up(touch)


class _ButtonBase(AnimationBehavior, TooltipBehavior):
    background_color = StatefulColorProperty(
        normal=cs.HoverButton.background_color_normal,
        states={
            "disabled": cs.HoverButton.background_color_disabled,
            ("is_down", "hover"): cs.HoverButton.background_color_hover,
            "is_down": cs.HoverButton.background_color_down,
            ("pressed", "hover"): cs.HoverButton.background_color_hover,
            "pressed": cs.HoverButton.background_color_down,
            "hover": cs.HoverButton.background_color_hover,
        }
    )
    background_normal = StringProperty(imgs_path.button_background_normal)
    background_down = StringProperty(imgs_path.button_background_down)

    def on_mouse_move(self, _):
        if self.hover and not self.disabled:
            cursor_manager.set_cursor("hand")


class ImageButton(_ButtonBase, ExpansiveButtonBehavior, Widget):
    pass


class HoverButton(_ButtonBase, ExpansiveButtonBehavior, RestrictedLabel):
    pass


class ImageToggleButton(_ButtonBase, ExpansiveToggleButtonBehavior, Widget):
    pass


class HoverToggleButton(_ButtonBase, ExpansiveToggleButtonBehavior, RestrictedLabel):
    pass


class OptionToggleButtonContextMenu(ModalBoxLayout):
    option_cls = ObjectProperty()
    scroll_layout = ObjectProperty()
    scrollview = ObjectProperty()
    title = StringProperty("")


class OptionToggleButtonContextMenuOption(HoverButton):
    modal = ObjectProperty()
    state_button = ObjectProperty()
    state_button_state = ObjectProperty()

    def on_release(self):
        self.state_button.state = self.state_button_state
        self.modal.dismiss()


class OptionToggleButton(_ButtonBase, ExpansiveToggleButtonBehavior, RestrictedLabel):
    modal_cls = ObjectProperty(OptionToggleButtonContextMenu)
    option_cls = ObjectProperty(OptionToggleButtonContextMenuOption)
    state = OptionProperty(None, options=[None])  # переопределять в предке
    state_to_str = None  # переопределять в предке
    modal_state_text = None  # переопределять в предке

    # clock_open_state_menu = None
    # TIME_OPEN_STATE_MENU = 0.5

    def on_kv_post(self, _):
        self.property("state").dispatch(self)

    last_touch = None
    def on_touch_down(self, touch):
        self.last_touch = touch
        if self.collide_point(*touch.pos) and not self.disabled:
            if touch.button == "scrollup":
                self.state = self.get_state_step(-1)
                return True
            elif touch.button == "scrolldown":
                self.state = self.get_state_step(1)
                return True
            elif touch.button == "middle":
                self._open_state_menu()
                return True

        return super().on_touch_down(touch)

    # def on_touch_up(self, touch):
    #     if self.clock_open_state_menu:
    #         self.clock_open_state_menu.cancel()
    #         self.clock_open_state_menu = None
    #     return super().on_touch_up(touch)

    def on_state(self, _, state: str):
        self.text = self.state_to_str[state]

    def _do_press(self):
        self.pressed = True
        if (not self.allow_no_selection and
                self.group and self.is_down):
            return

        self._release_group(self)

        direction = 1
        # if self.last_touch.button == "middle":
        #     self.clock_open_state_menu = Clock.schedule_once(self._open_state_menu, self.TIME_OPEN_STATE_MENU)
        if self.last_touch.button == "right":
            direction = -direction
        self.state = self.get_state_step(direction)

    def _do_release(self, *args):
        self.pressed = False
        if (not self.allow_no_selection and
                self.group and self.is_down):
            return

        self._release_group(self)
        if self.discard_state_release:
            direction = -1
            if self.last_touch.button == "right":
                direction = -direction
            self.state = self.get_state_step(direction)

    def get_state_step(self, direction):
        lst = self.property("state").options
        i = lst.index(self.state)
        i = (i + direction) % len(lst)
        return lst[i]

    def _open_state_menu(self):
        # if self.clock_open_state_menu:
        #     self.clock_open_state_menu.cancel()
        #     self.clock_open_state_menu = None
        modal = self.modal_cls(option_cls=self.option_cls)
        modal.open(self)
        modal.scrollview.data = self._make_state_menu_data(modal)

    def _make_state_menu_data(self, modal) -> list:
        return {}


class ImageOptionToggleButtonBehavior(_ButtonBase, ExpansiveToggleButtonBehavior, Widget):
    state = OptionProperty(None, options=[None])  # переопределять в предке


class ColorToggleButton(AnimationBehavior, HoverBehavior, ExpansiveToggleButtonBehavior, Widget):
    color = ColorProperty()
    source = StringProperty("")

    border_color = StatefulColorProperty(
        normal=cs.ColorToggleButton.border_color_normal,
        states={
            ("is_down", "hover"): cs.ColorToggleButton.border_color_hover,
            "is_down": cs.ColorToggleButton.border_color_is_select,
            "hover": cs.ColorToggleButton.border_color_hover,
        }
    )


class ArrowBehavior(EventDispatcher):
    arrow_color = StatefulColorProperty(
        normal=cs.ArrowToggleButton.arrow_color_normal,
        states={
            "disabled": cs.ArrowToggleButton.arrow_color_disabled,
            ("is_down", "hover"): cs.ArrowToggleButton.arrow_color_hover,
            "is_down": cs.ArrowToggleButton.arrow_color_down,
            "hover": cs.ArrowToggleButton.arrow_color_hover,
        }
    )

    reverse_arrow = BooleanProperty(False)
    vertical_arrow = BooleanProperty(True)
    do_show_arrow = BooleanProperty(True)

    arrow_height = NumericProperty("8dp")
    arrow_width = NumericProperty("8dp")
    arrow_size = ReferenceListProperty(arrow_width, arrow_height)
    arrow_offset_right = NumericProperty("4dp")

    def _get_arrow_points(self):
        y_padding = (self.height - self.arrow_height) / 2
        top = self.top - y_padding
        y = self.y + y_padding
        right = self.right - self.arrow_offset_right
        left = right - self.arrow_width

        if self.vertical_arrow:
            center_x = right - (self.arrow_width / 2)
            if self.reverse_arrow:
                return [left, y, center_x, top, right, y]
            else:
                return [left, top, right, top, center_x, y]
        else:
            center_y = self.center_y
            if self.reverse_arrow:
                return [left, center_y, right, top, right, y]
            else:
                return [right, center_y, left, top, left, y]
    arrow_points = AliasProperty(
        _get_arrow_points,
        bind=[
            "vertical_arrow", "reverse_arrow",
            "arrow_size", "arrow_offset_right",
            "pos", "size", "x", "y", "center_x",
            "center_y", "right", "top", "width", "height"
        ],
        cache=True
    )


class ArrowImageButton(ArrowBehavior, ImageButton):
    pass


class ArrowToggleButton(ArrowBehavior, HoverToggleButton):
    pass
