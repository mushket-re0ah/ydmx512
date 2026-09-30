from kivy.lang import Builder
from kivy.properties import ObjectProperty

from libs.uix.input.numeric_input import NumericInput
from libs.uix.layouts import SubSectionPanel
from libs.uix.rotary_button import RotaryButton

Builder.load_file("ui/main_ribbon/scene_dimmer.kv")


class SceneDimmer(SubSectionPanel):
	numeric: NumericInput = ObjectProperty()
	rotary: RotaryButton = ObjectProperty()
