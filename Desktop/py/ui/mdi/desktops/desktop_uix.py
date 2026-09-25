from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import (
    ObjectProperty, ColorProperty, BooleanProperty, NumericProperty,
    StringProperty
)
from kivy.clock import Clock
from kivy.animation import Animation
from libs.uix.button import ImageToggleButton
from database.desktop_uix import RowDesktopUix
from typing import Tuple
from kivy.lang import Builder
from misc import colorscheme as cs
from misc.player.status import PlayerStatus
from libs.uix.map_layout import MapGridItemBehavior


Builder.load_file("ui/mdi/desktops/desktop_uix.kv")


class MomentToggleButton(ImageToggleButton):
    is_moment = BooleanProperty(False)

    def _do_release(self, *args):
        if self.is_moment:
            super().trigger_action(0)


class DesktopUix(MapGridItemBehavior, RelativeLayout):
    desktop_map = ObjectProperty()
    desktop_uix = ObjectProperty(rebind=True)

    bg = ColorProperty((1, 1, 1, 1))
    bg_image = StringProperty()
    opacity = NumericProperty(1)

    trigger_save_pos = None
    def __init__(self, create_animation=True, **kwargs):
        self.trigger_save_pos = Clock.create_trigger(self._save_pos, 0)
        self.bind(grid_pos=self.trigger_save_pos)
        super().__init__(selectable=True, **kwargs)
        self._do_create_animation(create_animation)

    def on_kv_post(self, _):
        super().on_kv_post(_)
        self.grid_pos = self._get_init_attrs(self.desktop_uix, self.desktop_map)
        self.desktop_uix.player.bind(status=self.on_player_status)
        self.on_player_status(None, self.desktop_uix.player.status)

    def on_player_status(self, _, status: PlayerStatus):
        self.animation = Animation(bg=status.value.bg, duration=0.2).start(self)

    def _do_create_animation(self, create_animation: bool):
        if create_animation:
            self.opacity = 0
            self.animation = Animation(opacity=1, duration=0.2).start(self)

    def _get_init_attrs(self,
                        desktop_uix: RowDesktopUix,
                        desktop_map: MapScrollLayout) -> Tuple[int, int]:
        if desktop_uix.grid_pos[0] is None:
            return desktop_map.find_empty_pos(*self.grid_pos)
        else:
            return desktop_uix.grid_pos

    def _save_pos(self, _):
        self.desktop_uix.edit(grid_pos=self.grid_pos)

    def _self_destroy(self):
        self.disabled = True
        anim = Animation(opacity=0, bg=cs.PlaybackUi.bg_delete, duration=0.2)
        anim.bind(on_complete=self.on_self_destroy)
        anim.start(self)

    def on_self_destroy(self, *args):
        self.parent.map_layout.remove_widget(self)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        if super().on_touch_down(touch):
            return True
        if touch.button == "right":
            self._open_context_menu(touch.pos)
            return True
        return False

    def _open_context_menu(self, pos: Tuple[float, float]):
        from ui.mdi.desktops.uix_context_menu import DesktopUixContextMenu
        DesktopUixContextMenu(
            desktop_uix=self.desktop_uix
        ).open(self)
