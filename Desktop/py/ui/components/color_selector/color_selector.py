from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import (
    NumericProperty, ListProperty, ObjectProperty, ReferenceListProperty,
)
from kivy.graphics.texture import Texture
from misc.colorpicker_utils import get_color_data
from typing import Tuple


class ColorSelectorSquare(Widget):
    color = ListProperty([1, 0, 0])  # Текущий цвет в RGB

    red = NumericProperty(0)
    green = NumericProperty(0)
    blue = NumericProperty(0)
    rgb = ReferenceListProperty(red, green, blue)

    hue = NumericProperty(0)
    saturate = NumericProperty(0)
    lightness = NumericProperty(0.4)
    hsl = ReferenceListProperty(hue, saturate, lightness)

    texture_size = NumericProperty(256)  # Размер текстуры
    texture = ObjectProperty()
    marker_x = NumericProperty(0)
    marker_y = NumericProperty(0)
    marker_xy = ReferenceListProperty(marker_x, marker_y)

    marker_graphics_x = NumericProperty(0)
    marker_graphics_y = NumericProperty(0)
    marker_graphics_pos = ReferenceListProperty(marker_graphics_x, marker_graphics_y)

    MARKER_SIZE = 10

    def __init__(self, **kwargs):
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

    def on_rgb(self, _, rgb: Tuple[float, float, float]):
        # self.hsl = colorsys.rgb_to_hsl(*rgb)
        pass

    def on_hsl(self, _, hsl: Tuple[float, float, float]):
        # self.rgb = colorsys.hsl_to_rgb(*hsl)
        self.marker_xy = int(self.hue * 255), int(self.saturate * 255)
        self.update_color(*self.marker_xy)

    def update_texture(self, *args):
        # Создаем массив цветов
        width = self.texture.width
        height = self.texture.height
        
        # data = get_color_data(width, height, self.lightness)
        data = get_color_data(
            width, height, self.lightness
        )

        self.data = data

        # Обновляем текстуру
        self.texture.blit_buffer(data, bufferfmt='ubyte', colorfmt='rgb')
        self.texture.flip_vertical()
        self.update_color(*self.marker_xy)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.select_color(touch.x, touch.y)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
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

        self.rgb = [r/255, g/255, b/255]
        self.hsl = [x/255, y/255, self.lightness]


class ColorSelector(BoxLayout):
    selector = ObjectProperty(rebind=True)
