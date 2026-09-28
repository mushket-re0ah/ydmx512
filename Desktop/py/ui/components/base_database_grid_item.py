from typing import Tuple
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import ObjectProperty, ColorProperty
from kivy.animation import Animation
from libs.uix.map_layout import MapGridItemBehavior, MapLayout
from libs.kivy_json_orm.table_implementation import DatabaseRow
from misc import colorscheme as cs


class BaseDatabaseGridItem(MapGridItemBehavior, RelativeLayout):
    db_row: DatabaseRow = ObjectProperty(rebind=True)
    map_layout: MapLayout = ObjectProperty(allownone=True, rebind=True)
    bg = ColorProperty()

    def __init__(self, create_animation=True, **kwargs):
        super().__init__(opacity=0.0 if create_animation else 1.0, **kwargs)
        self._do_create_animation(create_animation)

    def on_kv_post(self, _):
        super().on_kv_post(_)
        self.grid_pos = self._get_grid_pos()

    def _do_create_animation(self, create_animation: bool):
        if create_animation:
            Animation(opacity=1, duration=0.2).start(self)

    def _get_grid_pos(self) -> Tuple[int, int]:
        if self.db_row.grid_pos[0] is None:
            grid_pos = self.map_layout.find_empty_pos(*self.grid_size)
            if grid_pos[0] is None:
                return (0, 0)
            return grid_pos
        return self.db_row.grid_pos

    def _self_destroy(self):
        self.disabled = True
        anim = Animation(opacity=0, bg=cs.BaseDatabaseGridItem.bg_delete, duration=0.2)
        anim.bind(on_complete=self.on_self_destroy)
        anim.start(self)

    def on_self_destroy(self, *_):
        self.map_layout.remove_widget(self)

    def _save_pos(self, *_):
        self.db_row.edit(grid_pos=self.grid_pos)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        if super().on_touch_down(touch):
            return True
        if touch.button == "right":
            self._open_context_menu(touch.pos)
            return True
        return False
