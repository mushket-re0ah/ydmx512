from typing import Tuple
from kivy.lang import Builder
from kivy.properties import (
    ObjectProperty, BooleanProperty, StringProperty, AliasProperty
)
from kivy.animation import Animation
from libs.uix.button import ImageToggleButton
from database.desktop_uix import RowDesktopUix
from misc.player.status import PlayerStatus
from ui.components.base_database_grid_item import BaseDatabaseGridItem
from typing_extensions import Self


Builder.load_file("ui/mdi/desktops/desktop_uix.kv")


class MomentToggleButton(ImageToggleButton):
    is_moment = BooleanProperty(False)

    def _do_release(self, *args):
        if self.is_moment:
            super().trigger_action(0)


class DesktopUix(BaseDatabaseGridItem):
    desktop_map = ObjectProperty()
    bg_image = StringProperty()

    def _set_desktop_uix(self, desktop_uix: RowDesktopUix) -> bool:
        if self.db_row != desktop_uix:
            self.db_row = desktop_uix
            return True
        return False
    desktop_uix = AliasProperty(
        lambda self: self.db_row, _set_desktop_uix, bind=["db_row"]
    )

    def __init__(self, **kwargs):
        self.bind(grid_pos=self._save_pos)
        super().__init__(selectable=True, **kwargs)

    def on_kv_post(self, base_widget: Self):
        super().on_kv_post(base_widget)
        self.desktop_uix.player.bind(status=self.on_player_status)
        self.on_player_status(None, self.desktop_uix.player.status)

    def on_player_status(self, _, status: PlayerStatus):
        self.animation = Animation(bg=status.value.bg, duration=0.2)
        self.animation.start(self)

    def _open_context_menu(self, _pos: Tuple[float, float]):
        from ui.mdi.desktops.uix_context_menu import DesktopUixContextMenu
        DesktopUixContextMenu(
            desktop_uix=self.desktop_uix
        ).open(self)
