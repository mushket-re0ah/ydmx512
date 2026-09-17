from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import BooleanProperty, ObjectProperty
from typing import Tuple, List
from libs.kivy_utils import walk_by_parents
from . import register_mouse_observer


class HoverBehavior:
    hover = BooleanProperty(False)
    widget_under_cursor = ObjectProperty(None, rebind=True, allownone=True)

    __events__ = ("on_enter", "on_leave")

    _initialized = False
    def __init__(self, *args, **kwargs):
        if not HoverBehavior._initialized:
            register_mouse_observer(HoverBehavior._check_hover)
            HoverBehavior._initialized = True
        super().__init__(*args, **kwargs)

    def on_hover(self, instance, value):
        if value:
            self.dispatch("on_enter")
        else:
            self.dispatch("on_leave")
        for parent in walk_by_parents(self):
            if hasattr(parent, "nested_hover"):
                parent.nested_hover = value

    def on_enter(self):
        pass

    def on_leave(self):
        pass

    @staticmethod
    def _check_hover(mouse_pos: Tuple[int, int], window_childs=None):
        if window_childs is None:
            window_childs = Window.children

        if len(window_childs) > 0:
            window_widget = next((
                child for child in window_childs
                if not (hasattr(child, "window_hover_ignore") and child.window_hover_ignore))
            )

            hovered = HoverBehavior.find_widget_under_cursor(window_widget, mouse_pos)

            if hovered is None and hasattr(window_widget, "allow_hover_outside") and window_widget.allow_hover_outside:
                HoverBehavior._check_hover(mouse_pos, window_childs[1:])
                return
        else:
            hovered = None

        old_hovered = HoverBehavior.widget_under_cursor
        if hovered is old_hovered:
            return
        if old_hovered and isinstance(old_hovered, HoverBehavior):
            old_hovered.hover = False
        if hovered and isinstance(hovered, HoverBehavior):
            hovered.hover = True
        HoverBehavior.widget_under_cursor = hovered

    @staticmethod
    def find_widget_under_cursor(widget, pos: Tuple[int, int]):
        if widget.collide_point(*pos):
            if hasattr(widget, "on_mouse_move"):
                widget.on_mouse_move(pos)
            if hasattr(widget, "to_local"):
                pos = widget.to_local(*pos)
            for child in widget.children:
                hovered_widget = HoverBehavior.find_widget_under_cursor(
                    child, pos)
                if hovered_widget:
                    return hovered_widget
            return widget
        return None


class NestedHoverBehavior(HoverBehavior):
    real_hover = BooleanProperty(False)
    nested_hover = BooleanProperty(False)
    __events__ = HoverBehavior.__events__ + ("on_real_hover_enter", "on_real_hover_leave")

    def __init__(self, **kwargs):
        trigger_set_real_hover = Clock.create_trigger(self.set_real_hover, -1)
        self.trigger_set_real_hover = trigger_set_real_hover
        self.bind(hover=trigger_set_real_hover, nested_hover=trigger_set_real_hover)
        super().__init__(**kwargs)

    def set_real_hover(self, _):
        self.real_hover = self.hover or self.nested_hover

    def on_real_hover(self, instance, value):
        if value:
            self.dispatch("on_real_hover_enter")
        else:
            self.dispatch("on_real_hover_leave")

    def on_real_hover_enter(self):
        pass

    def on_real_hover_leave(self):
        pass
