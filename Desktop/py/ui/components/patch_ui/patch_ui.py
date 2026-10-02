from typing import Any, Tuple

from kivy.lang.builder import Builder
from kivy.properties import AliasProperty, ObjectProperty
from kivy.uix.image import Image
from kivy.uix.widget import Widget

from database.patch import RowPatch
from libs.uix.button import HoverToggleButton
from libs.uix.input import HoverInput
from libs.uix.input.numeric_input import NumericInput
from libs.uix.label import RestrictedLabel
from misc import colorscheme as cs
from ui.components.base_database_grid_item import BaseDatabaseGridItem

Builder.load_file("ui/components/patch_ui/patch_ui.kv")


class BasePatchUiPanButton(HoverToggleButton):
    patch_ui = ObjectProperty()


class BasePatchUiTiltButton(HoverToggleButton):
    patch_ui = ObjectProperty()


class BasePatchUi(BaseDatabaseGridItem):
    input_start_address: NumericInput = ObjectProperty()
    input_universe: NumericInput = ObjectProperty()
    toggle_controller: HoverToggleButton = ObjectProperty()
    lbl_addr_info: RestrictedLabel = ObjectProperty()
    image_fixture: Image = ObjectProperty()
    input_title: HoverInput = ObjectProperty()
    button_pan: BasePatchUiPanButton = ObjectProperty()
    button_tilt: BasePatchUiTiltButton = ObjectProperty()
    toggle_mapper: HoverToggleButton = ObjectProperty()

    def _set_patch(self, patch: RowPatch) -> bool:
        if self.db_row != patch:
            self.db_row = patch
            return True
        return False
    patch: RowPatch = AliasProperty(
        lambda self: self.db_row,
        _set_patch,
        bind=("db_row",)
    )

    def __init__(self, **kwargs: Any):
        super().__init__(bg=cs.PatchUi.bg, **kwargs)

    def on_kv_post(self, base_widget: Widget):
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
        def on_dissmiss_menu(modal: "PatchControllerMenu"):
            modal.unbind(on_dismiss=on_dissmiss_menu)
            self.toggle_controller.is_down = False
        from ui.components.patch_ui.patch_controller import PatchControllerMenu
        menu = PatchControllerMenu(
            patch=self.patch
        )
        menu.bind(on_dismiss=on_dissmiss_menu)
        menu.open(self, pos=(self.right, self.top))

    def open_mapper_menu(self):
        def on_dissmiss_menu(modal: "PatchMapperMenu"):
            modal.unbind(on_dismiss=on_dissmiss_menu)
            self.toggle_mapper.is_down = False
        from ui.components.patch_ui.patch_mapper import PatchMapperMenu
        menu = PatchMapperMenu(
            patch=self.patch
        )
        menu.bind(on_dismiss=on_dissmiss_menu)
        menu.open(self, pos=(self.right, self.top))
