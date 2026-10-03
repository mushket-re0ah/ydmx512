from kivy.lang import Builder
from kivy.properties import ObjectProperty

from database import db
from libs.uix.layouts import MenuPanel
from ui.mdi.scenes import MDIScenes

Builder.load_file("ui/mdi/scenes/menu.kv")


class SceneMenu(MenuPanel):
    scene_ui: MDIScenes = ObjectProperty()

    def create_scene(self):
        db.scene.add_row()
