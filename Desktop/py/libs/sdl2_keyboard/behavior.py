from typing import Callable, Dict, FrozenSet

from libs.sdl2_keyboard.manager import KeyboardInputContext, register_context, unregister_context


class KeyboardBehavior:
    keyboard_context = None

    def register_keyboard_context(self):
        self.keyboard_context = self.create_keyboard_context()
        if self.keyboard_context:
            register_context(self.keyboard_context)

    is_blocked_keyboard = False
    def create_keyboard_context(self) -> KeyboardInputContext:
        return KeyboardInputContext(
            is_blocked=self.is_blocked_keyboard,
            hotkeys=self.create_hotkeys(),
            hotkeys_up=self.create_hotkeys_up(),
            on_key_down=self.on_key_down,
            on_key_up=self.on_key_up,
        )

    def on_key_down(self, scancode: int, keycode: str):
        pass

    def on_key_up(self, scancode: int, keycode: str):
        pass

    def create_hotkeys(self) -> Dict[FrozenSet[str], Callable[[], None]]:
        return {}

    def create_hotkeys_up(self) -> Dict[FrozenSet[str], Callable[[], None]]:
        return {}

    def unregister_keyboard_context(self):
        if self.keyboard_context:
            unregister_context(self.keyboard_context)
            self.keyboard_context = None

    def update_keyboard_context(self):
        self.unregister_keyboard_context()
        self.register_keyboard_context()
