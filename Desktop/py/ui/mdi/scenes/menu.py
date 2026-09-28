from kivy.properties import ObjectProperty
from kivy.lang import Builder
from libs.uix.layouts import MenuPanel
from database import db


Builder.load_file("ui/mdi/scenes/menu.kv")


class SceneMenu(MenuPanel):
    scene_ui = ObjectProperty()

    def create_scene(self):
        db.scene.add_row()
