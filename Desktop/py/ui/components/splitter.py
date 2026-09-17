from kivy.uix.splitter import Splitter
from kivy.properties import ObjectProperty
from ui.components.button import ImageButton
from kivy.lang import Builder

Builder.load_file("ui/components/splitter.kv")


class HoverSplitterStrip(ImageButton):
    pass


class HoverSplitter(Splitter):
    strip_cls = ObjectProperty(HoverSplitterStrip)
