from kivy.properties import ObjectProperty
from libs.uix.layouts import MenuPanel
from kivy.lang import Builder
from database import db


Builder.load_file("ui/mdi/scenes/menu.kv")


class SceneMenu(MenuPanel):
    scene_ui = ObjectProperty()

    def create_scene(self):
        db.scene.add_row()
