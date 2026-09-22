from kivy.properties import ObjectProperty, StringProperty
from ui.components.database_mdi_window import DatabaseMDIWindow


class MDIScenes(DatabaseMDIWindow):
    _db_title_id = "scene"
    title = StringProperty("Сцены")

    menu = ObjectProperty()
    table = ObjectProperty()

    def on_hidden(self, _, hidden: bool):
        super().on_hidden(_, hidden)
        if hidden or self.menu:
            return
        self.__create_menu()
        self.add_widget(self.menu)
        self.__create_table()
        self.add_widget(self.table)

    def __create_menu(self):
        from ui.mdi.scenes.menu import SceneMenu
        self.menu = SceneMenu(scene_ui=self)

    def __create_table(self):
        from ui.mdi.scenes.table import SceneTable
        self.table = SceneTable()
