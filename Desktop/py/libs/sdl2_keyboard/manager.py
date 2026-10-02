from dataclasses import dataclass
from typing import Callable, Dict, FrozenSet, List, Optional, Set

from kivy.core.window import Window, WindowBase

from libs.sdl2_keyboard.patch import patch_window_sdl2_keyboard_input
from libs.sdl2_keyboard.scancodes import (
    SDL_SCANCODE_TO_KEYCODE_MAP,
    key_is_valid,
    scancode_is_modifier,
)


def normalize_hotkey(hotkey: FrozenSet[str]) -> FrozenSet[str]:
    return frozenset({key.upper() for key in hotkey})


def hotkey_to_str(hotkey: FrozenSet[str]) -> str:
    hotkey = normalize_hotkey(hotkey)
    # Определяем порядок модификаторов
    modifiers_order = ["CTRL", "SHIFT", "ALT"]
    # Сортируем модификаторы в нужном порядке
    sorted_modifiers = [key for key in modifiers_order if key in hotkey]
    # Извлекаем обычные клавиши (должна быть только одна)
    normal_keys = hotkey - set(modifiers_order)
    normal_part = next(iter(normal_keys), "") if normal_keys else ""
    # Объединяем части в строку
    return ' + '.join(sorted_modifiers + ([normal_part] if normal_part else []))


@dataclass
class KeyboardInputContext:
    is_blocked: bool = False
    hotkeys: Optional[Dict[FrozenSet[str], Callable[[], None]]] = None
    hotkeys_up: Optional[Dict[FrozenSet[str], Callable[[], None]]] = None
    on_key_down: Optional[Callable[[int, str], None]] = None
    on_key_up: Optional[Callable[[int, str], None]] = None

    def __post_init__(self):
        self.hotkeys = self._parse_hotkeys(self.hotkeys)
        self.hotkeys_up = self._parse_hotkeys(self.hotkeys_up)

    def _parse_hotkeys(
        self,
        hotkeys: Optional[Dict[FrozenSet[str], Callable[[], None]]],
    ) -> Optional[Dict[FrozenSet[str], Callable[[], None]]]:
        if not hotkeys:
            return None

        return {self._parse_hotkey(hotkey): callback
                    for hotkey, callback in hotkeys.items()}

    def _parse_hotkey(self, hotkey: FrozenSet[str]) -> FrozenSet[str]:
        new_hotkey = normalize_hotkey(hotkey)
        if not all(key_is_valid(key) for key in new_hotkey):
            raise ValueError(f"Error: invalid key in \"{hotkey}\"")
        return new_hotkey


_initialized = False
_last_keyboard_text: str = ""
_contexts: List[KeyboardInputContext] = []
_modifiers: Set[str] = set()

# public
def register_context(context: KeyboardInputContext):
    if context not in _contexts:
        _contexts.insert(0, context)

def unregister_context(context: KeyboardInputContext):
    if context in _contexts:
        _contexts.remove(context)

def init():
    global _initialized
    if not _initialized:
        patch_window_sdl2_keyboard_input()
        Window.bind(on_key_down=_on_key_down, on_key_up=_on_key_up)
        _initialized = True
    else:
        raise RuntimeError("keyboard_manager already initialized")

def check_shift() -> bool:
    return "SHIFT" in _modifiers


def check_ctrl() -> bool:
    return "CTRL" in _modifiers


def check_alt() -> bool:
    return "ALT" in _modifiers

# private
def _create_hotkey(key: str) -> FrozenSet[str]:
    return frozenset({key, *_modifiers})

def _processing_contexts(hotkey: FrozenSet[str],
                         contexts: List[KeyboardInputContext],
                         scancode: int,
                         codepoint: str,
                         stop_on_first: bool) -> bool:
    for ctx in contexts:
        if ctx.hotkeys and hotkey in ctx.hotkeys:
            ctx.hotkeys[hotkey]()
            if stop_on_first:
                return True

    for ctx in contexts:
        if ctx.on_key_down:
            ctx.on_key_down(scancode, codepoint)
            if stop_on_first:
                return True
    return stop_on_first and bool(contexts)

def _on_key_down(
        window: WindowBase,
        keycode: str,
        scancode: int,
        codepoint: int,
        modifiers: List[str]
    ):
    global _last_keyboard_text
    _last_keyboard_text = window.last_keyboard_text

    key = SDL_SCANCODE_TO_KEYCODE_MAP[scancode]
    _add_modifier(scancode, key)

    hotkey = _create_hotkey(key)

    block_contexts = [i for i in _contexts if i.is_blocked]
    other_contexts = [i for i in _contexts if not i.is_blocked]
    if _processing_contexts(hotkey, block_contexts, scancode, _last_keyboard_text, True):
        return
    _processing_contexts(hotkey, other_contexts, scancode, _last_keyboard_text, False)

def _processing_contexts_up(
        hotkey: FrozenSet[str],
        contexts: List[KeyboardInputContext],
        scancode: int,
        codepoint: str,
        stop_on_first: bool
    ) -> bool:
    for ctx in contexts:
        if ctx.hotkeys_up and hotkey in ctx.hotkeys_up:
            ctx.hotkeys_up[hotkey]()
            if stop_on_first:
                return True

    for ctx in contexts:
        if ctx.on_key_up:
            ctx.on_key_up(scancode, codepoint)
            if stop_on_first:
                return True
    return stop_on_first and bool(contexts)

def _on_key_up(_window: WindowBase, _keycode: str, scancode: int):
    key = SDL_SCANCODE_TO_KEYCODE_MAP[scancode]
    _remove_modifier(scancode, key)

    hotkey = _create_hotkey(key)

    block_contexts = [i for i in _contexts if i.is_blocked]
    other_contexts = [i for i in _contexts if not i.is_blocked]
    if _processing_contexts_up(hotkey, block_contexts, scancode, _last_keyboard_text, True):
        return
    _processing_contexts_up(hotkey, other_contexts, scancode, _last_keyboard_text, False)

def _add_modifier(scancode: int, key: str) -> None:
    if scancode_is_modifier(scancode) and key not in _modifiers:
        _modifiers.add(key)

def _remove_modifier(scancode: int, key: str) -> None:
    if scancode_is_modifier(scancode) and key in _modifiers:
        _modifiers.discard(key)
