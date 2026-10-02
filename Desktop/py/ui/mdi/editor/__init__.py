from typing import TYPE_CHECKING, Callable, Dict, FrozenSet, Optional

from kivy.properties import ObjectProperty, StringProperty

from database import db
from database.playback import RowPlayback
from libs.kivy_json_orm.fields import (
    list_of_refs_deserializer,
    list_of_refs_serializer,
    table_ref_deserializer,
    table_ref_serializer,
)
from ui.components.database_mdi_window import DatabaseMDIWindow

if TYPE_CHECKING:
    from ui.mdi.editor.content import EditorContent


class MDIEditor(DatabaseMDIWindow):
    db_title_id: str = "editor"
    title: str = StringProperty("Редактор")

    playback: Optional[RowPlayback] = ObjectProperty(None, allownone=True, rebind=True)

    view_context_template = {
        "content.splitter_x/width": 0,
        "content.splitter_y/height": 0,
        "content.playback_map.pb_map/playback": {
            "default": None,
            "serialize": table_ref_serializer(),
            "deserialize": table_ref_deserializer(lambda: db.playback)
        },
        "content.patch_map/active_patch": {
            "default": [],
            "serialize": list_of_refs_serializer(),
            "deserialize": list_of_refs_deserializer(lambda: db.patch)
        },
        "content.patch_map.workspace_manager/workspace_now_index": 0,
        "content.playback_map.pb_map.scrollview/scroll_x": 0,
        "content.playback_map.pb_map.scrollview/scroll_y": 0,
        "content.automation.toolbar.input_zoom_y/value": 8,
    }

    content: "EditorContent" = ObjectProperty()

    def on_hidden(self, _, hidden: bool):
        super().on_hidden(_, hidden)
        if hidden or self.content:
            return
        self.__create_content()

    def __create_content(self):
        from ui.mdi.editor.content import EditorContent
        self.content = EditorContent(editor=self)
        self.add_widget(self.content)
        self.update_keyboard_context()

    def start_or_stop_playback(self):
        if not self.playback:
            return
        self.playback.player.start_or_stop()

    def create_hotkeys(self) -> Dict[FrozenSet[str], Callable[[], None]]:
        if self.content:
            return {
                **super().create_hotkeys(),
                **self.content.automation.row_panel.create_hotkeys(),
                frozenset({"space"}): self.start_or_stop_playback
            }
        return {}
