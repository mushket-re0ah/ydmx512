from kivy.properties import ObjectProperty, StringProperty
from ui.components.database_mdi_window import DatabaseMDIWindow
from database import db
from libs.sdl2_keyboard.scancodes import SDL_SCANCODE_TO_KEYCODE_MAP


class MDIProcessing(DatabaseMDIWindow):
    _db_title_id = "processing"
    title = StringProperty("Процессинг")

    menu = ObjectProperty()
    map_section = ObjectProperty()

    def on_hidden(self, _, hidden: bool):
        super().on_hidden(_, hidden)
        if hidden or self.menu:
            return
        self.__create_playback_map()
        self.__create_menu()

    def create_playback(self):
        db.playback.add_row()

    def __create_menu(self):
        from ui.mdi.processing.menu import ProcessingMenu
        self.menu = ProcessingMenu(
            processing=self,
            map_layout=self.map_section.pb_map,
            view_context=self.view_context)
        self.add_widget(self.menu, 1)

    def __create_playback_map(self):
        from ui.mdi.processing.processing_map import PlaybackMapSection
        self.map_section = PlaybackMapSection(
            processing=self,
            view_context=self.view_context)
        self.add_widget(self.map_section)

    def on_key_down(self, scancode: int, keycode: str):
        self.map_section.pb_map.on_key_down(SDL_SCANCODE_TO_KEYCODE_MAP[scancode])

    def on_key_up(self, scancode: int, keycode: str):
        self.map_section.pb_map.on_key_up(SDL_SCANCODE_TO_KEYCODE_MAP[scancode])
