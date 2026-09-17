from kivy.properties import ObjectProperty, StringProperty
from ui.components.mdi_window import MDIWindow
from database import db
from libs.sdl2_keyboard.scancodes import SDL_SCANCODE_TO_KEYCODE_MAP


class MDIProcessing(MDIWindow):
    _db_title_id = "processing"
    title_id = StringProperty(_db_title_id)
    title = StringProperty("Процессинг")

    menu = ObjectProperty()
    processing_map = ObjectProperty()

    def on_open(self):
        if not self.menu:
            self.__create_playback_map()
            self.__create_menu()

    def create_playback(self):
        db.playback.add_row()

    def __create_menu(self):
        from ui.mdi.processing.menu import ProcessingMenu
        self.menu = ProcessingMenu(
            processing=self,
            processing_map=self.processing_map,
            view_context=self.view_context)
        self.add_widget(self.menu, 1)

    def __create_playback_map(self):
        from ui.mdi.processing.processing_map import PlaybackMap
        self.processing_map = PlaybackMap(
            processing=self,
            view_context=self.view_context)
        self.add_widget(self.processing_map)

    def on_key_down(self, scancode: int, keycode: str):
        self.processing_map.on_key_down(SDL_SCANCODE_TO_KEYCODE_MAP[scancode])

    def on_key_up(self, scancode: int, keycode: str):
        self.processing_map.on_key_up(SDL_SCANCODE_TO_KEYCODE_MAP[scancode])
