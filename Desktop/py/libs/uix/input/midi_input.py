from kivy.properties import NumericProperty
from libs.midi.notes import MIDI_NOTES
from libs.uix.input.numeric_input import NumericInput
from libs.uix.context_menu import (
    ContextMenu, ContextMenuTemplates
)
from database import db
from kivy.lang import Builder
Builder.load_string("""
#:import uix_cs libs.uix.colorscheme

<MidiInput>:  # NumericInput
    normal_background_color: uix_cs.MidiInput.background_color_normal
    normal_foreground_color: uix_cs.MidiInput.foreground_color_normal
    allow_empty: True
"""
)


class MidiInput(NumericInput):
    minimum = NumericProperty(0)
    maximum = NumericProperty(127)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_filter = None
        self.input_type = "text"

    def _str_to_value(self, text: str) -> bool:
        if text in ("", "-"):
            if self.allow_empty:
                return None
            else:
                return self.default_value
        midi_notes = db.misc.midi_notes
        if midi_notes == "NUMERIC":
            value = float(text) if self.input_filter == "float" else int(
                float(text))
            return self._value_bounds(value)
        else:
            try:
                value = float(text) if self.input_filter == "float" else int(
                    float(text))
                return self._value_bounds(value)
            except ValueError:
                notes = MIDI_NOTES[midi_notes]
                if text in notes:
                    return notes.index(text)
                else:
                    return self._value_bounds(self.value)

    def _set_text_by_value(self):
        if self.value is None:
            self.text = ""
            return
        midi_notes = db.misc.midi_notes
        if midi_notes == "NUMERIC":
            self.text = self._value_to_str(self.value)
        else:
            notes = MIDI_NOTES[midi_notes]
            self.text = notes[self.value]

    def _create_context_menu(self) -> ContextMenu:
        return ContextMenu(items=self._create_context_menu_items(clean_btn=False))

    def _create_context_menu_items(self, clean_btn=False) -> ContextMenu:
        items = super()._create_context_menu_items()
        midi_notes = db.misc.midi_notes
        if midi_notes != "NUMERIC":
            notes = MIDI_NOTES[midi_notes]
            items.append(ContextMenuTemplates.separator())
            items.append(ContextMenuTemplates.spinner(
                text="Нота",
                values=notes,
                selected=self.text,
                on_select=self.on_select_spinner_context
            ))
        return items

    def on_select_spinner_context(self, _, note: str):
        midi_notes = db.misc.midi_notes
        if midi_notes != "NUMERIC":
            notes = MIDI_NOTES[midi_notes]
            self.value = notes.index(note)
