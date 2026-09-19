from kivy.uix.relativelayout import RelativeLayout
from kivy.lang.builder import Builder
from kivy.properties import ObjectProperty, ColorProperty, NumericProperty
from kivy.animation import Animation
from ui.components.scroll_layout_map import GridBehavior
from ui.components.scroll_layout_map import MapScrollLayout
from libs.uix.button import HoverToggleButton
from database.patch import RowPatch
from typing import Tuple
from misc import colorscheme as cs


Builder.load_file("ui/components/patch_ui/patch_ui.kv")


class BasePatchUiPanButton(HoverToggleButton):
    patch_ui = ObjectProperty()


class BasePatchUiTiltButton(HoverToggleButton):
    patch_ui = ObjectProperty()


class BasePatchUi(GridBehavior, RelativeLayout):
    input_start_address = ObjectProperty()
    input_universe = ObjectProperty()
    lbl_addr_info = ObjectProperty()
    image_fixture = ObjectProperty()
    toggle_controller = ObjectProperty()
    input_title = ObjectProperty()
    button_pan = ObjectProperty()
    button_tilt = ObjectProperty()

    patch_map: MapScrollLayout = ObjectProperty()
    patch: RowPatch = ObjectProperty(rebind=True)
    bg = ColorProperty(cs.PatchUi.bg)
    opacity = NumericProperty(1)

    def __init__(self, create_animation=True, **kwargs):
        super().__init__(**kwargs)
        self._do_create_animation(create_animation)

    def on_kv_post(self, _):
        patch = self.patch
        patch_map = self.patch_map
        self._create_pan_tilt_toggle(patch)
        self.grid_x, self.grid_y = self._get_init_attrs(patch, patch_map)
        if patch.grid_pos[0] is None:
            self._save_pos(None)

    def _do_create_animation(self, create_animation: bool):
        if create_animation:
            Animation(opacity=1, duration=0.2).start(self)

    def _create_pan_tilt_toggle(self, patch: RowPatch):
        if patch.fixture.is_dynamic:
            self.button_pan = BasePatchUiPanButton(patch_ui=self)
            self.button_tilt = BasePatchUiTiltButton(patch_ui=self)
            self.add_widget(self.button_pan)
            self.add_widget(self.button_tilt)

    def _get_init_attrs(self,
                        patch: RowPatch,
                        patch_map: MapScrollLayout) -> Tuple[int, int]:
        if patch.grid_pos[0] is None:
            return patch_map.find_empty_pos(self)
        else:
            return patch.grid_pos

    def _save_pos(self, _):
        self.patch.edit(grid_pos=(self.grid_x, self.grid_y))

    def _self_destroy(self):
        self.disabled = True
        anim = Animation(opacity=0, bg=cs.PatchUi.bg_delete, duration=0.2)
        anim.bind(on_complete=self.on_self_destroy)
        anim.start(self)

    def on_self_destroy(self, *args):
        self.parent.remove_widget(self)

    def open_context_menu(self, pos: Tuple[float, float]):
        from ui.components.patch_ui.patch_context_menu import PatchContextMenu
        PatchContextMenu(
            patch=self.patch
        ).open(self)

    def open_controller_menu(self):
        from ui.components.patch_ui.patch_controller import PatchControllerMenu
        PatchControllerMenu(
            patch=self.patch
        ).open(self, pos=(self.right, self.top))

    def _check_allow_move_widget(self, widget) -> bool:
        if widget is self:
            return True
        if widget in {self.input_start_address, self.input_universe, self.input_title, self.button_pan, self.button_tilt}:
            return False
        elif widget in (self.lbl_addr_info, self.image_fixture):
            return True
        else:
            raise ValueError(f"unexpected widget {widget}")
