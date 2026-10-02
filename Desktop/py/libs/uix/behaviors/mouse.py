from kivy.input.motionevent import MotionEvent
from kivy.properties import BooleanProperty

from libs.typecheck import WidgetProtocol


class TouchMouseBehavior(WidgetProtocol):
    drag_enabled: bool = BooleanProperty(False)

    def on_touch_down(self, touch: MotionEvent) -> bool:
        if self.disabled:
            return False
        if touch.grab_current is not None:
            return False
        if self.collide_point(*touch.pos):
            touch.ud["start_mouse_pos"] = touch.pos[:]
            if touch.button == "scrollup":
                if self.on_scroll_up(touch):
                    return True
            elif touch.button == "scrolldown":
                if self.on_scroll_down(touch):
                    return True
            elif touch.button == "left":
                if self.drag_enabled:
                    if self.on_drag_start(touch):
                        touch.grab(self)
                        return True
                if self.on_left_click(touch):
                    return True
            elif touch.button == "right":
                if self.on_right_click(touch):
                    return True
            elif touch.button == "middle":
                if self.on_middle_click(touch):
                    return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch: MotionEvent) -> bool:
        if self.drag_enabled and touch.grab_current is self:
            dx = touch.pos[0] - touch.ud["start_mouse_pos"][0]
            dy = touch.pos[1] - touch.ud["start_mouse_pos"][1]
            if self.on_drag(touch, dx, dy):
                return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch: MotionEvent) -> bool:
        if self.drag_enabled and touch.grab_current is self:
            touch.ungrab(self)
            if self.on_drag_end(touch):
                return True
        return super().on_touch_up(touch)

    def on_left_click(self, touch: MotionEvent) -> bool: return False
    def on_right_click(self, touch: MotionEvent) -> bool: return False
    def on_middle_click(self, touch: MotionEvent) -> bool: return False
    def on_scroll_up(self, touch: MotionEvent) -> bool: return False
    def on_scroll_down(self, touch: MotionEvent) -> bool: return False
    def on_drag_start(self, touch: MotionEvent) -> bool: return False
    def on_drag(self, touch: MotionEvent, delta_x: float, delta_y: float) -> bool: return False
    def on_drag_end(self, touch: MotionEvent) -> bool: return False
