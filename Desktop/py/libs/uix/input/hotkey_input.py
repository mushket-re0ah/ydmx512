from libs.sdl2_keyboard.scancodes import SDL_SCANCODE_TO_KEYCODE_MAP
from typing import Optional
from libs.uix.input import HoverInput
from kivy.lang import Builder
Builder.load_string("""
<HotkeyInput>:  # HoverInput
"""
)


class HotkeyInput(HoverInput):
    def keyboard_on_textinput(self, window, text: str):
        # запрет на стандартный ввод текста. Только через keyboard_on_key_down
        return

    is_blocked_keyboard = True
    def create_hotkeys(self) -> Optional[dict]:
        return None

    def on_key_down(self, scancode: int, keycode: str):
        self.text = SDL_SCANCODE_TO_KEYCODE_MAP[scancode]
