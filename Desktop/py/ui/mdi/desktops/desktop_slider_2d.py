from kivy.lang import Builder
from libs.uix.slider2d import Slider2D  # lazy kv import initialize
from ui.mdi.desktops.desktop_uix import DesktopUix


Builder.load_file("ui/mdi/desktops/desktop_slider_2d.kv")


class DesktopSlider2D(DesktopUix):
    pass
