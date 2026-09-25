from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from ui.mdi.editor.maps.playback import playback_map
from ui.mdi.editor.maps.patch import patch_map
import ui.mdi.editor.automation
from libs.properties import BindableObjectProperty


Builder.load_file("ui/mdi/editor/content.kv")


class EditorContent(BoxLayout):
    editor = ObjectProperty()

    playback = ObjectProperty(None, allownone=True, rebind=True)
    renderer = BindableObjectProperty(
        bind={"on_render_changed": "_redispatch_render_changed"},
    )

    playback_map = ObjectProperty()
    patch_map = ObjectProperty()
    automation = ObjectProperty()

    splitter_x = ObjectProperty()
    splitter_y = ObjectProperty()

    __events__ = ("on_render_changed",)

    def on_playback(self, _, playback):
        self.renderer = playback.renderer if playback else None

    def _redispatch_render_changed(self, renderer):
        self.dispatch("on_render_changed", renderer)

    def on_render_changed(self, renderer):
        pass
