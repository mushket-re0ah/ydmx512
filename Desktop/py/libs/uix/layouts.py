from typing import Literal

from kivy.lang import Builder
from kivy.properties import ColorProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.stencilview import StencilView
from kivy.uix.widget import Widget

from libs.typecheck import RGBA
from libs.uix import colorscheme as uix_cs
from libs.uix.behaviors.modal import ModalBehavior
from libs.uix.label import RestrictedLabel

Builder.load_string("""
#:import uix_cs libs.uix.colorscheme

<StencilBoxLayout>:  # StencilView, BoxLayout

<-StencilRelativeLayout>:  # RelativeLayout
    canvas.before:
        StencilPush
        Rectangle:
            pos: self.pos
            size: self.size
        StencilUse

        PushMatrix
        Translate:
            xy: (round(self.x), round(self.y))

    canvas.after:
        PopMatrix

        StencilUnUse
        Rectangle:
            pos: self.pos
            size: self.size
        StencilPop

<MenuPanel>:  # StencilBoxLayout
    padding: ["4dp", "4dp", "4dp", "4dp"]
    spacing: "2dp"
    size_hint: (1, None)
    height: "64dp"
    canvas.before:
        Color:
            rgb: uix_cs.MenuPanel.bg
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: uix_cs.MenuPanel.border
        Line:
            width: dp(2)
            rectangle: (self.x, self.y, self.width, self.height)


<SectionPanel>:  # BoxLayout
    section_label: section_label
    orientation: "vertical"
    padding: ["2dp", 0, "2dp", "2dp"]
    spacing: "2dp"
    size_hint: (None, 1)
    width: self.minimum_width
    canvas.before:
        Color:
            rgb: root.bg
        Rectangle:
            pos: self.pos
            size: self.size
    RestrictedLabel:
        id: section_label
        size_hint: (1, None) if root.orientation == "vertical" else (1, 1)
        text: root.title_text
        size: self.texture_size
        text_size: self.size
        halign: root.halign
        valign: root.valign
        font_size: root.font_size
        color: root.fg


<SubSectionPanel>:  # SectionPanel
    -bg: uix_cs.SubSectionPanel.bg
    -fg: uix_cs.SubSectionPanel.fg
    font_size: "12sp"


<ModalBoxLayout>:  # BoxLayout
    size_hint: (None, None)
    orientation: "vertical"
    spacing: "3dp"
    padding: ("4dp", "4dp")
    canvas:
        Color:
            rgba: uix_cs.Modal.bg
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: uix_cs.Modal.border_color
        Line:
            width: dp(1.0)
            rectangle: (self.x, self.y, self.width, self.height)


<WindowModalBoxLayout>:  # ModalBoxLayout
    canvas.before:
        Color:
            rgba: (0, 0, 0, 0.7)
        Rectangle:
            pos: (0, 0)
            size: Window.size
    pos: (Window.width - self.width) / 2, (Window.height - self.height) / 2
""")


class StencilBoxLayout(StencilView, BoxLayout):
    pass


class StencilRelativeLayout(RelativeLayout):
    pass


class MenuPanel(StencilBoxLayout):
    pass


class SectionPanel(BoxLayout):
    title_text: str = StringProperty("NOT SETTED (SECTION PANEL)")
    bg: RGBA = ColorProperty(uix_cs.SectionPanel.bg)
    fg: RGBA = ColorProperty(uix_cs.SectionPanel.fg)
    halign: Literal["left", "center", "right", "justify", "auto"] = StringProperty("left")
    valign: Literal["bottom", "middle", "center", "top"] = StringProperty("top")
    font_size: float = NumericProperty("11dp")
    section_label: RestrictedLabel = ObjectProperty()


class SubSectionPanel(SectionPanel):
    def add_widget(self, widget: Widget, index:int=0, canvas=None):
        # inverted
        super().add_widget(widget, len(self.children) + 1, canvas)


class ModalBoxLayout(ModalBehavior, BoxLayout):
    pass


class WindowModalBoxLayout(ModalBoxLayout):
    pass
