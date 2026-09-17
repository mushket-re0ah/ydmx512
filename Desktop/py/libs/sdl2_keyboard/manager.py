from kivy.core.window import Window
from dataclasses import dataclass
from typing import Optional, Dict, Callable, List
from .scancodes import SDL_SCANCODE_TO_KEYCODE_MAP, scancode_is_modifier, key_is_valid
from .patch import patch_window_sdl2_keyboard_input


def normalize_hotkey(hotkey: frozenset) -> frozenset:
    return frozenset({key.upper() for key in hotkey})


def hotkey_to_str(hotkey: frozenset) -> str:
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
    hotkeys: Optional[Dict[frozenset, Callable]] = None
    hotkeys_up: Optional[Dict[frozenset, Callable]] = None
    on_key_down: Optional[Callable] = None
    on_key_up: Optional[Callable] = None

    def __post_init__(self):
        self.hotkeys = self._parse_hotkeys(self.hotkeys)
        self.hotkeys_up = self._parse_hotkeys(self.hotkeys_up)

    def _parse_hotkeys(self, hotkeys: Optional[Dict[frozenset, Callable]]) -> Optional[dict]:
        if not hotkeys:
            return None

        return {self._parse_hotkey(hotkey): callback
                    for hotkey, callback in hotkeys.items()}

    def _parse_hotkey(self, hotkey: frozenset) -> frozenset:
        new_hotkey = normalize_hotkey(hotkey)
        if not all(key_is_valid(key) for key in new_hotkey):
            raise ValueError(f"Error: invalid key in \"{hotkey}\"")
        return new_hotkey


_initialized = False
_last_keyboard_text = None
_contexts: List[KeyboardInputContext] = []
_modifiers = set()

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
        raise Exception("keyboard_manager already initialized")

def check_shift() -> bool:
    return "SHIFT" in _modifiers


def check_ctrl() -> bool:
    return "CTRL" in _modifiers


def check_alt() -> bool:
    return "ALT" in _modifiers

# private
def _create_hotkey(key) -> frozenset:
    return frozenset({key, *_modifiers})

def _processing_contexts(hotkey: frozenset,
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
    return stop_on_first and contexts

def _on_key_down(window, _keycode, scancode, codepoint, _modifiers):
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

def _processing_contexts_up(hotkey: frozenset,
                            contexts: List[KeyboardInputContext],
                            scancode: int,
                            codepoint: str,
                            stop_on_first: bool) -> bool:
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
    return stop_on_first and contexts

def _on_key_up(window, keycode, scancode):
    key = SDL_SCANCODE_TO_KEYCODE_MAP[scancode]
    _remove_modifier(scancode, key)

    hotkey = _create_hotkey(key)

    block_contexts = [i for i in _contexts if i.is_blocked]
    other_contexts = [i for i in _contexts if not i.is_blocked]
    if _processing_contexts_up(hotkey, block_contexts, scancode, _last_keyboard_text, True):
        return
    _processing_contexts_up(hotkey, other_contexts, scancode, _last_keyboard_text, False)

def _add_modifier(scancode, key) -> None:
    if scancode_is_modifier(scancode) and key not in _modifiers:
        _modifiers.add(key)

def _remove_modifier(scancode, key) -> None:
    if scancode_is_modifier(scancode) and key in _modifiers:
        _modifiers.discard(key)
