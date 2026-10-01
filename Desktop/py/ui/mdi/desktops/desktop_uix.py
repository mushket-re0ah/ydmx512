from typing import TYPE_CHECKING, Any, Tuple

from kivy.animation import Animation
from kivy.lang import Builder
from kivy.properties import AliasProperty, BooleanProperty, ObjectProperty, StringProperty
from kivy.uix.widget import Widget

from database.desktop_uix import RowDesktopUix
from database.desktop_uix.player import DesktopUixPlayer
from libs.uix.button import ImageToggleButton
from misc.player.status import PlayerStatus
from ui.components.base_database_grid_item import BaseDatabaseGridItem

if TYPE_CHECKING:
    from ui.mdi.desktops.desktop_map import DesktopMap

Builder.load_file("ui/mdi/desktops/desktop_uix.kv")


class MomentToggleButton(ImageToggleButton):
    is_moment: bool = BooleanProperty(False)

    def _do_release(self, *args: Any):
        if self.is_moment:
            super().trigger_action(0)


class DesktopUix(BaseDatabaseGridItem):
    desktop_map: "DesktopMap" = ObjectProperty()
    bg_image: str = StringProperty()

    def _set_desktop_uix(self, desktop_uix: RowDesktopUix) -> bool:
        if self.db_row != desktop_uix:
            self.db_row = desktop_uix
            return True
        return False
    desktop_uix: RowDesktopUix = AliasProperty(
        lambda self: self.db_row,
        _set_desktop_uix,
        bind=("db_row",)
    )

    def __init__(self, **kwargs: Any):
        self.bind(grid_pos=self._save_pos)
        super().__init__(selectable=True, **kwargs)

    def on_kv_post(self, base_widget: Widget):
        super().on_kv_post(base_widget)
        self.desktop_uix.player.bind(status=self.on_player_status)
        self.on_player_status(self.desktop_uix.player, self.desktop_uix.player.status)

    def on_player_status(self, _: DesktopUixPlayer, status: PlayerStatus):
        self.animation = Animation(bg=status.value.bg, duration=0.2)
        self.animation.start(self)

    def _open_context_menu(self, pos: Tuple[float, float]):
        from ui.mdi.desktops.uix_context_menu import DesktopUixContextMenu
        DesktopUixContextMenu(
            desktop_uix=self.desktop_uix
        ).open(self)
