from typing import Any, Tuple

from kivy.lang import Builder
from kivy.properties import AliasProperty, ObjectProperty
from kivy.utils import boundary

from libs.sdl2_keyboard.scancodes import (
    SDL_SCANCODE_DOWN,
    SDL_SCANCODE_TO_KEYCODE_MAP,
    SDL_SCANCODE_UP,
)
from libs.uix.button import ColorToggleButton
from libs.uix.color_selector import ColorSelector  # lazy kv import initialize
from libs.uix.input.hover_input import HoverInput
from libs.uix.layouts import ModalBoxLayout

Builder.load_string("""
#:import get_color_from_hex kivy.utils.get_color_from_hex

<HEXAInput>:  # HoverInput
    color_toggle: color_toggle

    halign: "left"
    -font_name: "Roboto Mono"
    hover: color_toggle.hover
    ColorToggleButton:
        id: color_toggle
        size_hint: (None, None)
        size: (root.height - dp(2 * root.padding[1]), root.height - dp(2 * root.padding[1]))
        pos: (root.right - (root.height - dp(2 * root.padding[1])) - dp(root.padding[0]), dp(root.y + root.padding[1]))
        on_release: root.open_modal()
        color: get_color_from_hex(root.text) or get_color_from_hex("#FFFFFF")

<HEXAInputModal>:  # ModalBoxLayout
    color_selector: color_selector
    size_hint: (None, None)
    size: (512, 512)
    ColorSelector:
        id: color_selector
"""
)


class HEXAInputModal(ModalBoxLayout):
    color_selector: ColorSelector = ObjectProperty()


class HEXAInput(HoverInput):
    color_toggle: ColorToggleButton = ObjectProperty()

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, multiline=False, **kwargs)
        self.fbind("cursor", self.recalc_cursor_width)

    def delete_selection(self, from_undo: bool=False):
        return

    def recalc_cursor_width(self, _, cursor: Tuple[int, int]):
        if cursor[0] == len(self.text):
            return
        self.cursor_width = self._get_text_width(self.text[cursor[0]],
                                                 self.tab_width,
                                                 self._label_cached)

    def _set_cursor(self, pos: Tuple[int, int]) -> bool:
        self._cursor = [boundary(pos[0], 1, len(self.text) - 1), 0]
        return True

    cursor: Tuple[int, int] = AliasProperty(HoverInput._get_cursor, _set_cursor)

    def do_backspace(self, *_, **_k: Any):
        cursor_x, _ = self.cursor
        if 1 <= cursor_x < len(self.text):
            self.cursor = [cursor_x - 1, self.cursor[1]]

    HEX_DIGITS: str = "0123456789ABCDEF"
    _last_keycode: str = None
    def on_key_down(self, scancode: int, keycode: str):
        keycode = SDL_SCANCODE_TO_KEYCODE_MAP[scancode]
        self._last_keycode = keycode
        cursor_x, _ = self.cursor
        if scancode not in {SDL_SCANCODE_UP, SDL_SCANCODE_DOWN} or\
               not 1 <= cursor_x < len(self.text):
            super().on_key_down(scancode, keycode)
            return

        delta = 1 if scancode == SDL_SCANCODE_UP else -1
        new_index = self.HEX_DIGITS.index(self.text[cursor_x]) + delta

        if 0 <= new_index < len(self.HEX_DIGITS):
            hex_char = self.HEX_DIGITS[new_index]
            self.text = f"{self.text[:cursor_x]}{hex_char}{self.text[cursor_x+1:]}"
            self.cursor = [cursor_x, self.cursor[1]]
        super().on_key_down(scancode, keycode)

    def insert_text(self, substring: str, from_undo: bool=False):
        keycode = self._last_keycode
        if keycode not in "0123456789ABCDEF":
            return
        cursor_x = self.cursor[0]
        self.text = self.text[:cursor_x] + keycode + self.text[cursor_x + 1:]
        self.cursor = [cursor_x + 1, self.cursor[1]]

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
