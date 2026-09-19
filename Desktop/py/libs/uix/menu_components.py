# RestrictedLabel
# HoverInput
# NumericInput
# HoverToggleButton
# MidiInput
# HotkeyInput
# RecycleSpinner
# ColorToggleButton
from kivy.lang import Builder

Builder.load_string("""
<MenuLabel@RestrictedLabel>:
    size_hint: (1, 1)
    font_size: "12sp"
    canvas.before:
        Color:
            rgba: cs.LabelRow.bg
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

