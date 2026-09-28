from kivy.lang import Builder
from libs.uix.label import RestrictedLabel
from libs.uix.input.hover_input import HoverInput
from libs.uix.input.numeric_input import NumericInput
from libs.uix.input.hotkey_input import HotkeyInput
from libs.uix.input.midi_input import MidiInput
from libs.uix.button import HoverToggleButton
from libs.uix.button import ColorToggleButton
from libs.uix.recycle_spinner import RecycleSpinner

Builder.load_string("""
#:import uix_cs libs.uix.colorscheme

<MenuLabel@RestrictedLabel>:
    size_hint: (1, 1)
    font_size: "12sp"
    canvas.before:
        Color:
            rgba: uix_cs.LabelRow.bg
        Rectangle:
            pos: self.pos
            size: self.size


<MenuHoverInput@HoverInput>:
    size_hint: (1, 1)
    font_size: "11sp"


<MenuNumericInput@NumericInput>:
    size_hint: (1, 1)
    font_size: "11sp"


<MenuToggleButton@HoverToggleButton>:
    size_hint: (1, 1)
    font_size: "11sp"


<MenuMidiInput@MidiInput>:
    size_hint: (1, 1)
    font_size: "11sp"


<MenuHotkeyInput@HotkeyInput>:
    size_hint: (1, 1)
    font_size: "11sp"


<MenuSpinner@RecycleSpinner>:
    size_hint: (1, 1)
    font_size: "11sp"


<MenuColorToggle@ColorToggleButton>:
    size_hint: (None, None)
    size: ("30dp", "30dp")
    source: imgs_path.button_thumb_normal
"""
)

class MenuLabel(RestrictedLabel):
    pass

class MenuHoverInput(HoverInput):
    pass

class MenuNumericInput(NumericInput):
    pass

class MenuToggleButton(HoverToggleButton):
    pass

class MenuMidiInput(MidiInput):
    pass

class MenuHotkeyInput(HotkeyInput):
    pass

class MenuSpinner(RecycleSpinner):
    pass

class MenuColorToggle(ColorToggleButton):
    pass
