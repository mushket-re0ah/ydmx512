from kivy.properties import AliasProperty, ObjectProperty
from kivy.utils import boundary
from ui.components.input import HoverInput
from libs.uix.layouts import ModalBoxLayout
from libs.sdl2_keyboard.scancodes import *


class HEXAInputModal(ModalBoxLayout):
    pass


class HEXAInput(HoverInput):
    color_toggle = ObjectProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, multiline=False, **kwargs)
        self.fbind("cursor", self.recalc_cursor_width)

    def delete_selection(self, from_undo=False):
        return

    def recalc_cursor_width(self, instance, cursor: tuple):
        if cursor[0] == len(self.text):
            return
        self.cursor_width = self._get_text_width(self.text[cursor[0]],
                                                 self.tab_width,
                                                 self._label_cached)

    def _set_cursor(self, pos):
        self._cursor = [boundary(pos[0], 1, len(self.text) - 1), 0]
        return True

    cursor = AliasProperty(HoverInput._get_cursor, _set_cursor)

    def do_backspace(self, **kwargs):
        cursor_x, _ = self.cursor
        if (1 <= cursor_x < len(self.text)):
            self.cursor = [cursor_x - 1, self.cursor[1]]

    _last_keycode = None
    def on_key_down(self, scancode: int, keycode: str):
        keycode = SDL_SCANCODE_TO_KEYCODE_MAP[scancode]
        self._last_keycode = keycode
        cursor_x, _ = self.cursor
        if scancode not in {SDL_SCANCODE_UP, SDL_SCANCODE_DOWN} or\
               not (1 <= cursor_x < len(self.text)):
            super().on_key_down(scancode, keycode)
            return

        HEX_DIGITS = "0123456789ABCDEF"
        delta = 1 if scancode == SDL_SCANCODE_UP else -1
        new_index = HEX_DIGITS.index(self.text[cursor_x]) + delta

        if 0 <= new_index < len(HEX_DIGITS):
            HEX = HEX_DIGITS[new_index]
            self.text = f"{self.text[:cursor_x]}{HEX}{self.text[cursor_x+1:]}"
            self.cursor = [cursor_x, self.cursor[1]]
        super().on_key_down(scancode, keycode)

    def insert_text(self, substring, from_undo=False):
        keycode = self._last_keycode
        if keycode not in "0123456789ABCDEF":
            return
        cursor_x = self.cursor[0]
        self.text = self.text[:cursor_x] + keycode + self.text[cursor_x + 1:]
        self.cursor = [cursor_x + 1, self.cursor[1]]

    def _update_graphics(self, *largs):
        super()._update_graphics()
        self.canvas.add(self.color_toggle.canvas)

    modal = None
    def open_modal(self):
        modal = HEXAInputModal()
        modal.open(self)
        self.modal = modal
        modal.bind(on_dismiss=self.on_dismiss_modal)
        self.color_toggle.is_down = True


    def on_dismiss_modal(self, _):
        self.modal = None
        self.color_toggle.is_down = False
