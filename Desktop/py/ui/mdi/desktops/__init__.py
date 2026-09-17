from ui.components.mdi_window import MDIWindow
from kivy.properties import StringProperty, ObjectProperty
from libs.sdl2_keyboard.scancodes import SDL_SCANCODE_TO_KEYCODE_MAP


class MDIDesktops(MDIWindow):
    _db_title_id = "desktops"
    title_id = StringProperty(_db_title_id)
    title = StringProperty("Рабочие столы")

    desktop_map = ObjectProperty()

    def on_open(self):
        if not self.desktop_map:
            self.__create_map()

    def __create_map(self):
        from ui.mdi.desktops.desktop_map import DesktopMap
        self.desktop_map = DesktopMap(
            desktops=self
        )
        self.add_widget(self.desktop_map)

    def on_key_down(self, scancode: int, keycode: str):
        self.desktop_map.on_key_down(SDL_SCANCODE_TO_KEYCODE_MAP[scancode])

    def on_key_up(self, scancode: int, keycode: str):
        self.desktop_map.on_key_up(SDL_SCANCODE_TO_KEYCODE_MAP[scancode])
