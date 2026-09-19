from kivy.uix.splitter import Splitter
from kivy.properties import ObjectProperty
from libs.uix.button import ImageButton
from kivy.lang import Builder

Builder.load_string("""
<HoverSplitterStrip>:  # ImageButton
    border: self.parent.border if self.parent else (3, 3, 3, 3)
    horizontal: '_h' if self.parent and self.parent.sizable_from[0] in  ('t', 'b') else ''
    background_normal: 'atlas://data/images/defaulttheme/splitter{}{}'.format('_disabled' if self.disabled else '', self.horizontal)
    background_down: 'atlas://data/images/defaulttheme/splitter_down{}{}'.format('_disabled' if self.disabled else '', self.horizontal)
"""
)


class HoverSplitterStrip(ImageButton):
    pass


class HoverSplitter(Splitter):
    strip_cls = ObjectProperty(HoverSplitterStrip)
