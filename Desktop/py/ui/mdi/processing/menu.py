from typing import TYPE_CHECKING, Any, Dict

from kivy.lang import Builder
from kivy.properties import ObjectProperty

from libs.uix.layouts import MenuPanel

if TYPE_CHECKING:
    from ui.mdi.processing import MDIProcessing
    from ui.mdi.processing.processing_map import PlaybackMap

Builder.load_file("ui/mdi/processing/menu.kv")


class ProcessingMenu(MenuPanel):
    processing: MDIProcessing = ObjectProperty()
    map_layout: PlaybackMap = ObjectProperty()
    view_context: Dict[str, Any] = ObjectProperty()
