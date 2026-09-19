from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ColorProperty, NumericProperty, ObjectProperty
from libs.uix import colorscheme as uix_cs
from kivy.uix.stencilview import StencilView
from libs.uix.behaviors.modal import ModalBehavior
from kivy.lang import Builder

Builder.load_string("""
#:import uix_cs libs.uix.colorscheme

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


class MenuPanel(StencilBoxLayout):
    pass


class SectionPanel(BoxLayout):
    title_text = StringProperty("NOT SETTED (SECTION PANEL)")
    bg = ColorProperty(uix_cs.SectionPanel.bg)
    fg = ColorProperty(uix_cs.SectionPanel.fg)
    halign = StringProperty("left")
    valign = StringProperty("top")
    font_size = NumericProperty("11dp")
    section_label = ObjectProperty()


class SubSectionPanel(SectionPanel):
    def add_widget(self, widget, index=0, canvas=None):
        # inverted
        super().add_widget(widget, len(self.children) + 1, canvas)


class ModalBoxLayout(ModalBehavior, BoxLayout):
    pass


class WindowModalBoxLayout(ModalBoxLayout):
    pass
