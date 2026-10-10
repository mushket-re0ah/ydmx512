from typing import TYPE_CHECKING, Optional

from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout

from database.playback import RowPlayback
from database.playback.renderer import PlaybackRenderer
from libs.properties import BindableObjectProperty
from libs.uix.splitter import HoverSplitter
from ui.mdi.editor.automation import Automation  # lazy kv import initialize
from ui.mdi.editor.maps.patch.patch_map import PatchEditorMap  # lazy kv import initialize
from ui.mdi.editor.maps.playback.playback_map import (
    PlaybackEditorMapSection,  # lazy kv import initialize
)

if TYPE_CHECKING:
    from ui.mdi.editor import MDIEditor

Builder.load_file("ui/mdi/editor/content.kv")


class EditorContent(BoxLayout):
    editor: "MDIEditor" = ObjectProperty()

    playback: Optional[RowPlayback] = ObjectProperty(None, allownone=True, rebind=True)
    renderer: Optional[PlaybackRenderer] = BindableObjectProperty(
        bind={"on_render_changed": "_redispatch_render_changed"},
        allownone=True
    )

    playback_map: PlaybackEditorMapSection = ObjectProperty()
    patch_map: PatchEditorMap = ObjectProperty()
    automation: Automation = ObjectProperty()

    splitter_x: HoverSplitter = ObjectProperty()
    splitter_y: HoverSplitter = ObjectProperty()

    __events__ = ("on_render_changed",)

    def on_playback(self, _, playback: Optional[RowPlayback]):
        self.renderer = playback.renderer if playback else None

    def _redispatch_render_changed(self, renderer: PlaybackRenderer):
        self.dispatch("on_render_changed", renderer)

    def on_render_changed(self, renderer: PlaybackRenderer):
        pass
