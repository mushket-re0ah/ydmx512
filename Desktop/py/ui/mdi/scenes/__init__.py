from kivy.properties import ObjectProperty, StringProperty
from ui.components.mdi_window import MDIWindow


class MDIScenes(MDIWindow):
    _db_title_id = "scene"

    title_id = StringProperty(_db_title_id)
    title = StringProperty("Сцены")

    menu = ObjectProperty()
    table = ObjectProperty()

    def on_open(self):
        if not self.menu:
            self.__create_menu()
            self.add_widget(self.menu)
            self.__create_table()
            self.add_widget(self.table)
            # self.__init_context()

    def __create_menu(self):
        from ui.mdi.scenes.menu import SceneMenu
        self.menu = SceneMenu(scene_ui=self)

    def __create_table(self):
        from ui.mdi.scenes.table import SceneTable
        self.table = SceneTable()

    # def change_context_now(self, context: SceneUiContexts, row: RowFixture = None):
    #     new_state = self._state_factory(context, row)
        
    #     if isinstance(self.context_state, new_state.__class__):
    #         return

    #     self.context_state.exit(self)
    #     self.context_state = new_state
    #     self.context_state.enter(self)
