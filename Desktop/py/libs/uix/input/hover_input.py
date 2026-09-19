from kivy.properties import BooleanProperty, ColorProperty
from kivy.clock import Clock
from libs.uix.input.textinput import CentralizedHotkeyTextInput
from libs.uix.context_menu import (
    ContextMenu, ContextMenuTemplates
)
from libs.uix import colorscheme as uix_cs
from libs.animation import StatefulColorProperty
from libs.uix.behaviors.mouse import TouchMouseBehavior
from kivy.lang import Builder
Builder.load_string("""
<-HoverInput>:  # CentralizedHotkeyTextInput
    size_hint: (None, None)
    height: "24dp"
    width: "64dp"
    padding: ["4dp", "4dp"]
    font_name: "Arial"
    font_size: "13sp"
    text_size: self.size
    halign: "center"
    valign: "center"
    cursor_color: root.foreground_color
"""
)


class HoverInput(CentralizedHotkeyTextInput):
    visible_focus = BooleanProperty(False)

    background_color = StatefulColorProperty(
        normal=uix_cs.HoverInput.background_color_normal,
        states={
            "disabled": uix_cs.HoverInput.background_color_disabled,
            "visible_focus": uix_cs.HoverInput.background_color_focused,
            "hover": uix_cs.HoverInput.background_color_hover,
        }
    )
    foreground_color = StatefulColorProperty(
        normal=uix_cs.HoverInput.foreground_color_normal,
        states={
            "disabled": uix_cs.HoverInput.foreground_color_disabled,
            "visible_focus": uix_cs.HoverInput.foreground_color_focused,
            "hover": uix_cs.HoverInput.foreground_color_hover,
        }
    )
    border_color = StatefulColorProperty(
        normal=uix_cs.HoverInput.border_color_normal,
        states={
            "disabled": uix_cs.HoverInput.border_color_disabled,
            "visible_focus": uix_cs.HoverInput.border_color_focused,
            "hover": uix_cs.HoverInput.border_color_hover,
        }
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(focus=self.focus_set_global)

    def focus_set_global(self, instance, value):
        self.visible_focus = value

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.button == "right":
            self.open_context_menu(touch.pos)
        else:
            return super().on_touch_down(touch)

    def open_context_menu(self, pos: tuple):
        if self.disabled:
            return
        selection_start = self.selection_from
        selection_end = self.selection_to
        cursor_pos = self.cursor
        self._create_context_menu().open(self, pos=pos)

        def t(*args):
            if selection_start is None or selection_end is None:
                return
            self.select_text(selection_start, selection_end)
            self.cursor = cursor_pos
        Clock.schedule_once(t, 0.2)

    def clear(self):
        self.select_all()
        self.delete_selection()

    def _create_context_menu(self) -> ContextMenu:
        return ContextMenu(items=self._create_context_menu_items(clean_btn=True))

    def _create_context_menu_items(self, clean_btn=False) -> ContextMenu:
        items = [
            ContextMenuTemplates.button(
                text="Отменить",
                on_release=lambda x: self.do_undo(),
                hotkey=frozenset({"ctrl", "z"}),
                disabled=len(self._undo) == 0
            ),
            ContextMenuTemplates.button(
                text="Вернуть",
                on_release=lambda x: self.do_redo(),
                hotkey=frozenset({"ctrl", "shift", "z"}),
                disabled=len(self._redo) == 0
            ),
            ContextMenuTemplates.separator(),
        ]
        if clean_btn:
            items.append(ContextMenuTemplates.button(
                text="Очистить",
                on_release=lambda x: self.clear(),
            ))
        items.append(
            ContextMenuTemplates.button(
                text="Вырезать",
                on_release=lambda x: self.cut(),
                hotkey=frozenset({"ctrl", "x"}),
                disabled=not self.selection_text
            ))
        items.append(
            ContextMenuTemplates.button(
                text="Копировать",
                on_release=lambda x: self.copy(),
                hotkey=frozenset({"ctrl", "c"}),
                disabled=not self.selection_text
            ))
        items.append(
            ContextMenuTemplates.button(
                text="Вставить",
                on_release=lambda x: self.paste(),
                hotkey=frozenset({"ctrl", "v"}),
            ))
        items.append(ContextMenuTemplates.separator())
        items.append(
            ContextMenuTemplates.button(
                text="Выделить все",
                on_release=lambda x: self.select_all(),
                hotkey=frozenset({"ctrl", "a"}),
            ))
        return items
