# https://github.com/kivy/kivy/issues/9375

def apply_patch():
    from kivy.input.providers.mouse import MouseMotionEventProvider

    def on_mouse_motion(self, win, x, y, modifiers):
        nx, ny = win.to_normalized_pos(x, y)
        ny = 1.0 - ny
        if self.current_drag:
            touch = self.current_drag
            touch.move([nx, ny])
            touch.update_graphics(win)
            self.waiting_event.append(('update', touch))

        # deleted in master
        # elif self.alt_touch is not None and 'alt' not in modifiers:
            # alt just released ?
            # is_double_tap = 'shift' in modifiers
            # self.create_touch(win, nx, ny, False, True, [])

    def on_mouse_press(self, win, x, y, button, modifiers):
        if self.test_activity():
            return
        nx, ny = win.to_normalized_pos(x, y)
        ny = 1.0 - ny
        found_touch = self.find_touch(win, nx, ny)
        if found_touch:
            self.current_drag = found_touch
        else:
            # exist in master
            # is_double_tap = 'shift' in modifiers

            do_graphics = (
                not self.disable_multitouch
                and (button != 'left' or 'ctrl' in modifiers)
            )
            touch = self.create_touch(
                win, nx, ny, False, do_graphics, button
            )

            # deleted in master
            # if 'alt' in modifiers:
            #     self.alt_touch = touch
            #     self.current_drag = None

    MouseMotionEventProvider.on_mouse_motion = on_mouse_motion
    MouseMotionEventProvider.on_mouse_press = on_mouse_press
