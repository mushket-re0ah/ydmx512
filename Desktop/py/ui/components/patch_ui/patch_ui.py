from typing import Tuple
from kivy.lang.builder import Builder
from kivy.properties import ObjectProperty, AliasProperty
from libs.uix.button import HoverToggleButton
from database.patch import RowPatch
from ui.components.base_database_grid_item import BaseDatabaseGridItem
from misc import colorscheme as cs
from typing_extensions import Self


Builder.load_file("ui/components/patch_ui/patch_ui.kv")


class BasePatchUiPanButton(HoverToggleButton):
    patch_ui = ObjectProperty()


class BasePatchUiTiltButton(HoverToggleButton):
    patch_ui = ObjectProperty()


class BasePatchUi(BaseDatabaseGridItem):
    input_start_address = ObjectProperty()
    input_universe = ObjectProperty()
    lbl_addr_info = ObjectProperty()
    image_fixture = ObjectProperty()
    toggle_controller = ObjectProperty()
    input_title = ObjectProperty()
    button_pan = ObjectProperty()
    button_tilt = ObjectProperty()

    def _set_patch(self, patch: RowPatch) -> bool:
        if self.db_row != patch:
            self.db_row = patch
            return True
        return False
    patch = AliasProperty(
        lambda self: self.db_row, _set_patch, bind=["db_row"]
    )

    def __init__(self, **kwargs):
        super().__init__(bg=cs.PatchUi.bg, **kwargs)

    def on_kv_post(self, base_widget: Self):
        super().on_kv_post(base_widget)
        self._create_pan_tilt_toggle()

    def _create_pan_tilt_toggle(self):
        if self.patch.fixture.is_dynamic:
            self.button_pan = BasePatchUiPanButton(patch_ui=self)
            self.button_tilt = BasePatchUiTiltButton(patch_ui=self)
            self.add_widget(self.button_pan)
            self.add_widget(self.button_tilt)

    def _open_context_menu(self, _pos: Tuple[float, float]):
        from ui.components.patch_ui.patch_context_menu import PatchContextMenu
        PatchContextMenu(
            patch=self.patch
        ).open(self)

    def open_controller_menu(self):
        from ui.components.patch_ui.patch_controller import PatchControllerMenu
        PatchControllerMenu(
            patch=self.patch
        ).open(self, pos=(self.right, self.top))
