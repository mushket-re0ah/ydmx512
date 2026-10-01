from typing import Any, Tuple

from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.input.motionevent import MotionEvent
from kivy.lang import Builder
from kivy.properties import (
    ListProperty,
    NumericProperty,
    ObjectProperty,
    ReferenceListProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from libs.uix.color_selector.colorpicker_utils import get_color_data

from libs.typecheck import HSL, RGB

Builder.load_string("""
<ColorSelectorSquare>:  # Widget
    canvas:
        Color:
            rgba: (1, 1, 1, 1)
        Rectangle:
            texture: self.texture
            size: self.size
            pos: self.pos
        Color:
            rgba: (1, 1, 1, 1)
        SmoothEllipse:
            pos: self.marker_graphics_pos
            size: (self.MARKER_SIZE, self.MARKER_SIZE)

<ColorSelector>:  # BoxLayout
    selector: selector
    BoxLayout:
        orientation: "vertical"
        Label:
            text: "HSL: {}".format([int(selector.hue * 255), int(selector.saturate * 255), int(selector.lightness * 255)])
            size_hint: (1, 0.2)
        Label:
            text: "RGB: {}".format([int(selector.red * 255), int(selector.green * 255), int(selector.blue * 255)])
            size_hint: (1, 0.2)

        BoxLayout:
            Label:
                text: "Hue"
            Slider:
                min: 0
                max: 1
                on_value: selector.hue = self.value
                value: selector.hue
        BoxLayout:
            Label:
                text: "Saturate"
            Slider:
                min: 0
                max: 1
                on_value: selector.saturate = self.value
                value: selector.saturate
        BoxLayout:
            Label:
                text: "Lightness"
            Slider:
                min: 0
                max: 1
                on_value: selector.lightness = self.value
                value: selector.lightness

        BoxLayout:
            Label:
                text: "Red"
            Slider:
                min: 0
                max: 1
                on_value: selector.red = self.value
                value: selector.red
        BoxLayout:
            Label:
                text: "Green"
            Slider:
                min: 0
                max: 1
                on_value: selector.green = self.value
                value: selector.green
        BoxLayout:
            Label:
                text: "Blue"
            Slider:
                min: 0
                max: 1
                on_value: selector.blue = self.value
                value: selector.blue

        Widget:
            canvas:
                Color:
                    rgb: root.selector.rgb if root.selector else [1, 1, 1]
                Rectangle:
                    size: self.size
                    pos: self.pos
    ColorSelectorSquare:
        id: selector
        size_hint: (None, None)
        size: (256, 256)
"""
)


class ColorSelectorSquare(Widget):
    color: RGB = ListProperty([1, 0, 0])  # Текущий цвет в RGB

    red: float = NumericProperty(0)
    green: float = NumericProperty(0)
    blue: float = NumericProperty(0)
    rgb: RGB = ReferenceListProperty(red, green, blue)

    hue: float = NumericProperty(0)
    saturate: float = NumericProperty(0)
    lightness: float = NumericProperty(0.4)
    hsl: HSL = ReferenceListProperty(hue, saturate, lightness)

    texture_size: float = NumericProperty(256)  # Размер текстуры
    texture: Texture = ObjectProperty()
    marker_x: int = NumericProperty(0)
    marker_y: int = NumericProperty(0)
    marker_xy: Tuple[int, int] = ReferenceListProperty(marker_x, marker_y)

    marker_graphics_x: float = NumericProperty(0)
    marker_graphics_y: float = NumericProperty(0)
    marker_graphics_pos: Tuple[float, float] = ReferenceListProperty(marker_graphics_x, marker_graphics_y)

    MARKER_SIZE = 10

    def __init__(self, **kwargs: Any):
        self.data: bytes = b''
        self.trigger_update_texture = Clock.create_trigger(self.update_texture, -1)
        self.trigger_update_marker_graphics_pos = Clock.create_trigger(
                                self.update_marker_graphics_pos, -1)
        super().__init__(**kwargs)
        self.texture = Texture.create(size=(self.texture_size, self.texture_size))

        self.bind(
            pos=self.trigger_update_texture,
            size=self.trigger_update_texture,
            lightness=self.trigger_update_texture
        )
        self.bind(
            pos=self.trigger_update_marker_graphics_pos,
            size=self.trigger_update_marker_graphics_pos,
            marker_xy=self.trigger_update_marker_graphics_pos
        )

    def on_rgb(self, _, rgb: RGB):
        # self.hsl = colorsys.rgb_to_hsl(*rgb)
        pass

    def on_hsl(self, _, hsl: HSL):
        # self.rgb = colorsys.hsl_to_rgb(*hsl)
        self.marker_xy = int(self.hue * 255), int(self.saturate * 255)
        self.update_color(*self.marker_xy)

    def update_texture(self, *_):
        # Создаем массив цветов
        width: float = self.texture.width
        height: float = self.texture.height

        # data = get_color_data(width, height, self.lightness)
        data: bytes = get_color_data(
            width, height, self.lightness
        )

        self.data = data

        # Обновляем текстуру
        self.texture.blit_buffer(data, bufferfmt='ubyte', colorfmt='rgb')
        self.texture.flip_vertical()
        self.update_color(*self.marker_xy)

    def on_touch_down(self, touch: MotionEvent) -> bool:
        if self.collide_point(*touch.pos):
            self.select_color(touch.x, touch.y)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch: MotionEvent) -> bool:
        if self.collide_point(*touch.pos):
            self.select_color(touch.x, touch.y)
            return True
        return super().on_touch_move(touch)

    def update_marker_graphics_pos(self, _):
        x = self.marker_x / (self.texture.width - 1)
        y = self.marker_y / (self.texture.height - 1)

        x = x * self.width + self.x - self.MARKER_SIZE / 2
        y = y * self.height + self.y - self.MARKER_SIZE / 2

        self.marker_graphics_pos = x, y

    def select_color(self, x: float, y: float):
        x = (x - self.x) / self.width
        y = (y - self.y) / self.height
        x = int((self.texture.width - 1) * x)
        y = int((self.texture.height - 1) * y)
        self.marker_xy = x, y
        self.update_color(x, y)

    def update_color(self, x: int, y: int):
        index = int((y * self.texture.width + x) * 3)

        pixels = self.data
        r = pixels[index]
        g = pixels[index + 1]
        b = pixels[index + 2]

        self.rgb = (r/255, g/255, b/255)
        self.hsl = (x/255, y/255, self.lightness)


class ColorSelector(BoxLayout):
    selector: ColorSelectorSquare = ObjectProperty(rebind=True)
