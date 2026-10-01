from typing import TYPE_CHECKING

from kivy.properties import ObjectProperty, StringProperty

from libs.sdl2_keyboard.scancodes import SDL_SCANCODE_TO_KEYCODE_MAP
from ui.components.database_mdi_window import DatabaseMDIWindow

if TYPE_CHECKING:
    from ui.mdi.desktops.desktop_map_section import DesktopMapSection


class MDIDesktops(DatabaseMDIWindow):
    _db_title_id: str = "desktops"
    title: str = StringProperty("Рабочие столы")

    desktop_map: "DesktopMapSection" = ObjectProperty()

    def on_hidden(self, _, hidden: bool):
        super().on_hidden(_, hidden)
        if hidden or self.desktop_map:
            return
        self.__create_map()

    def __create_map(self):
        from ui.mdi.desktops.desktop_map_section import DesktopMapSection
        self.desktop_map = DesktopMapSection(desktops=self)
        self.add_widget(self.desktop_map)

    def on_key_down(self, scancode: int, keycode: str):
        self.desktop_map.on_key_down(SDL_SCANCODE_TO_KEYCODE_MAP[scancode])

    def on_key_up(self, scancode: int, keycode: str):
        self.desktop_map.on_key_up(SDL_SCANCODE_TO_KEYCODE_MAP[scancode])
