def patch_window_sdl2_keyboard_input():
    from kivy.compat import unichr
    import sys
    from kivy.logger import Logger
    from kivy.base import EventLoop
    from kivy.config import Config
    from kivy.clock import Clock
    def mainloop(self):
    # for android/iOS, we don't want to have any event nor executing our
    # main loop while the pause is going on. This loop wait any event (not
    # handled by the event filter), and remove them from the queue.
    # Nothing happen during the pause on iOS, except gyroscope value sent
    # over joystick. So it's safe.
        while self._pause_loop:
            self._win.wait_event()
            if not self._pause_loop:
                break
            event = self._win.poll()
            if event is None:
                continue
            # A drop is send while the app is still in pause.loop
            # we need to dispatch it
            action, args = event[0], event[1:]
            if action.startswith('drop'):
                self._dispatch_drop_event(action, args)
            # app_terminating event might be received while the app is paused
            # in this case EventLoop.quit will be set at _event_filter
            elif EventLoop.quit:
                return

        events = []
        while True:
            try:
                event = self._win.poll()
            except SystemError:
                continue
            if not event:
                break
            if event is None:
                continue
            events.append(event)

        self.last_keyboard_text = None
        for event in events:
            action, args = event[0], event[1:]
            if action == "textinput":
                text = args[0]
                self.last_keyboard_text = text

        for event in events:
            action, args = event[0], event[1:]
            if action == 'quit':
                if self.dispatch('on_request_close'):
                    continue
                EventLoop.quit = True
                break

            elif action in ('fingermotion', 'fingerdown', 'fingerup'):
                # for finger, pass the raw event to SDL motion event provider
                # XXX this is problematic. On OSX, it generates touches with 0,
                # 0 coordinates, at the same times as mouse. But it works.
                # We have a conflict of using either the mouse or the finger.
                # Right now, we have no mechanism that we could use to know
                # which is the preferred one for the application.
                if platform in ('ios', 'android'):
                    SDL2MotionEventProvider.q.appendleft(event)
                pass

            elif action == 'mousemotion':
                x, y = args
                x, y = self._fix_mouse_pos(x, y)
                self._mouse_x = x
                self._mouse_y = y
                if not self._cursor_entered:
                    self._cursor_entered = True
                    self.dispatch('on_cursor_enter')
                # don't dispatch motion if no button are pressed
                if not self._mouse_buttons_down:
                    continue
                self._mouse_meta = self.modifiers
                self.dispatch('on_mouse_move', x, y, self.modifiers)

            elif action in ('mousebuttondown', 'mousebuttonup'):
                x, y, button = args
                x, y = self._fix_mouse_pos(x, y)
                self._mouse_x = x
                self._mouse_y = y
                if not self._cursor_entered:
                    self._cursor_entered = True
                    self.dispatch('on_cursor_enter')
                btn = 'left'
                if button == 3:
                    btn = 'right'
                elif button == 2:
                    btn = 'middle'
                elif button == 4:
                    btn = "mouse4"
                elif button == 5:
                    btn = "mouse5"
                eventname = 'on_mouse_down'
                self._mouse_buttons_down.add(button)
                if action == 'mousebuttonup':
                    eventname = 'on_mouse_up'
                    self._mouse_buttons_down.remove(button)
                self.dispatch(eventname, x, y, btn, self.modifiers)
            elif action.startswith('mousewheel'):
                x, y = self._win.get_relative_mouse_pos()
                if not self._collide_and_dispatch_cursor_enter(x, y):
                    # Ignore if the cursor position is on the window title bar
                    # or on its edges
                    continue
                self._update_modifiers()
                x, y, button = args
                btn = 'scrolldown'
                if action.endswith('up'):
                    btn = 'scrollup'
                elif action.endswith('right'):
                    btn = 'scrollright'
                elif action.endswith('left'):
                    btn = 'scrollleft'

                self._mouse_meta = self.modifiers
                self._mouse_btn = btn
                # times = x if y == 0 else y
                # times = min(abs(times), 100)
                # for k in range(times):
                self._mouse_down = True
                self.dispatch('on_mouse_down',
                    self._mouse_x, self._mouse_y, btn, self.modifiers)
                self._mouse_down = False
                self.dispatch('on_mouse_up',
                    self._mouse_x, self._mouse_y, btn, self.modifiers)

            elif action.startswith('drop'):
                self._dispatch_drop_event(action, args)
            # video resize
            elif action == 'windowresized':
                self._size = self._win.window_size
                # don't use trigger here, we want to delay the resize event
                ev = self._do_resize_ev
                if ev is None:
                    ev = Clock.schedule_once(self._do_resize, .1)
                    self._do_resize_ev = ev
                else:
                    ev()
            elif action == 'windowdisplaychanged':
                Logger.info(f"WindowSDL: Window is now on display {args[0]}")

                # The display has changed, so the density and dpi
                # may have changed too.
                self._update_density_and_dpi()

            elif action == 'windowmoved':
                self.dispatch('on_move')

            elif action == 'windowrestored':
                self.dispatch('on_restore')
                self.canvas.ask_update()

            elif action == 'windowexposed':
                self.canvas.ask_update()

            elif action == 'windowminimized':
                self.dispatch('on_minimize')
                if Config.getboolean('kivy', 'pause_on_minimize'):
                    self.do_pause()

            elif action == 'windowmaximized':
                self.dispatch('on_maximize')

            elif action == 'windowhidden':
                self.dispatch('on_hide')

            elif action == 'windowshown':
                self.dispatch('on_show')

            elif action == 'windowfocusgained':
                self._focus = True

            elif action == 'windowfocuslost':
                self._focus = False

            elif action == 'windowenter':
                x, y = self._win.get_relative_mouse_pos()
                self._collide_and_dispatch_cursor_enter(x, y)

            elif action == 'windowleave':
                self._cursor_entered = False
                self.dispatch('on_cursor_leave')

            elif action == 'joyaxismotion':
                stickid, axisid, value = args
                self.dispatch('on_joy_axis', stickid, axisid, value)
            elif action == 'joyhatmotion':
                stickid, hatid, value = args
                self.dispatch('on_joy_hat', stickid, hatid, value)
            elif action == 'joyballmotion':
                stickid, ballid, xrel, yrel = args
                self.dispatch('on_joy_ball', stickid, ballid, xrel, yrel)
            elif action == 'joybuttondown':
                stickid, buttonid = args
                self.dispatch('on_joy_button_down', stickid, buttonid)
            elif action == 'joybuttonup':
                stickid, buttonid = args
                self.dispatch('on_joy_button_up', stickid, buttonid)

            elif action in ('keydown', 'keyup'):
                mod, key, scancode, kstr = args

                try:
                    key = self.key_map[key]
                except KeyError:
                    pass

                if action == 'keydown':
                    self._update_modifiers(mod, key)
                else:
                    # ignore the key, it has been released
                    self._update_modifiers(mod)

                # if mod in self._meta_keys:
                if (key not in self._modifiers and
                        key not in self.command_keys.keys()):
                    try:
                        kstr_chr = unichr(key)
                        try:
                            # On android, there is no 'encoding' attribute.
                            # On other platforms, if stdout is redirected,
                            # 'encoding' may be None
                            encoding = getattr(sys.stdout, 'encoding',
                                               'utf8') or 'utf8'
                            kstr_chr.encode(encoding)
                            kstr = kstr_chr
                        except UnicodeError:
                            pass
                    except ValueError:
                        pass
                # if 'shift' in self._modifiers and key\
                #        not in self.command_keys.keys():
                #    return

                if action == 'keyup':
                    self.dispatch('on_key_up', key, scancode)
                    continue

                # don't dispatch more key if down event is accepted
                if self.dispatch('on_key_down', key,
                                 scancode, kstr,
                                 self.modifiers):
                    continue
                self.dispatch('on_keyboard', key,
                              scancode, kstr,
                              self.modifiers)

            elif action == 'textinput':
                text = args[0]
                self.dispatch('on_textinput', text)

            elif action == 'textedit':
                text = args[0]
                self.dispatch('on_textedit', text)

            # unhandled event !
            else:
                Logger.trace('WindowSDL: Unhandled event %s' % str(event))


    from kivy.core.window.window_sdl2 import WindowSDL
    WindowSDL.mainloop = mainloop
