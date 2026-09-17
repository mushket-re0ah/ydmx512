from kivy.properties import ObjectProperty, AliasProperty
from kivy.lang import Builder
from libs.uix.layouts import ModalBoxLayout
from database.playback import RowPlayback


Builder.load_file("ui/components/playback_ui/playback_context_menu.kv")
Builder.load_file("ui/components/menu_components.kv")


class PlaybackContextMenu(ModalBoxLayout):
    playback_list = ObjectProperty()
    first_playback = AliasProperty(
        lambda self: self.playback_list[0], bind=["playback_list"]
    )

    def edit_playbacks_title(self, title: str):
        for i, playback in enumerate(self.playback_list):
            if len(self.playback_list) == 1:
                playback.edit(title=title)
            else:
                playback.edit(title=f"{title} #{i + 1}")

    def edit_playbacks(self, **kwargs):
        for playback in self.playback_list:
            playback.edit(**kwargs)

    def edit_playbacks_player(self, **kwargs):
        for playback in self.playback_list:
            playback.player.edit(**kwargs)

    def edit_playbacks_renderer(self, **kwargs):
        for playback in self.playback_list:
            playback.renderer.edit(**kwargs)
