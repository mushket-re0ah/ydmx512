from kivy.properties import (
    StringProperty, NumericProperty, BooleanProperty, ObjectProperty,
    ReferenceListProperty, AliasProperty, DictProperty
)
from kivy.clock import Clock
from kivy.utils import boundary
from misc import constants
from libs.kivy_json_orm.table_implementation import DatabaseTable, DatabaseRow
from database.fixture import RowFixture
from database.fixture_param import RowFixtureParam
from database.scene import RowScene, TableScene, SceneTableMixin, SceneRowMixin
from database import db
from typing import Tuple, Dict, List, Optional
from libs.dmx512 import dmx512
from libs.serialize import *
from libs.properties import ClampedNumericProperty
from libs.kivy_utils import AutoUnbindBehavior
from libs.kivy_json_orm.fields import *


class RowPatch(SceneRowMixin, DatabaseRow):
    title = StringField("Без названия")

    fixture = RefField("fixture", fallback_fn=lambda db: db.fixture.get_default_row())
    universe = ClampedNumericField(1, 1, constants.DMX_UNIVERSE_COUNT)
    start_address = ClampedNumericField(1, 1, constants.DMX_ADDRESS_COUNT)
    invert_pan = BooleanField(False)
    invert_tilt = BooleanField(False)
    correction_pan = ClampedNumericField(0, -255, 255)
    correction_tilt = ClampedNumericField(0, -255, 255)
    virtual_dimmer = ClampedNumericField(100, constants.DIMMER_MINIMUM, constants.DIMMER_MAXIMUM)
    grid_pos = ListField([None, None])
    workspace = NumericField(0)

    is_address_conflict = BooleanProperty(False)
    param_list_unpacked = ObjectProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._table.update_address_info(self.universe)

    def after_deserialize(self):
        self._table.check_address_conflict(self.universe)
        self._table.update_address_info(self.universe)

    _prev_fixture = None
    def on_fixture(self, _, fixture: RowFixture):
        if fixture is not self._prev_fixture:
            if self._prev_fixture:
                self.unbind_from(self._prev_fixture)
            self.bind_to(fixture, param_list_unpacked=self.setter("param_list_unpacked"))
            self._prev_fixture = fixture
            self.param_list_unpacked = fixture.param_list_unpacked

    def on_start_address(self, _, start_address: int):
        self._table.check_address_conflict(self.universe)
        self._table.update_address_info(self.universe)

    _prev_universe = None
    def on_universe(self, _, universe: int):
        if universe != self._prev_universe:
            self._table.check_address_conflict(self._prev_universe)
            self._table.check_address_conflict(universe)
            self._prev_universe = universe
            self._table.update_address_info(self.universe)

    def get_end_address(self) -> int:
        self._table.check_address_conflict(self.universe)
        return boundary(
            self.start_address + len(self.param_list_unpacked) - 1,
            1, constants.DMX_ADDRESS_COUNT
        )
    end_address = AliasProperty(
        get_end_address, None,
        bind=["start_address", "param_list_unpacked"], cache=True
    )

    def remove(self) -> "DatabaseRow":
        super().remove()

    def on_remove(self):
        self._table.check_address_conflict(self.universe)
        self._table.update_address_info(universe)

    def on_workspace(self, _, workspace: int):
        self._table.dispatch("on_workspace_any_patch", self, workspace)


class TablePatch(SceneTableMixin, DatabaseTable):
    cls_row = RowPatch

    __events__ = ("on_workspace_any_patch",) + DatabaseTable.__events__

    address_info: Dict[Tuple[int, int], List[Tuple[RowPatch, RowFixtureParam]]] = DictProperty()

    trigger_check_address_conflict = None
    _universes_need_to_check = None
    def __init__(self, **kwargs):
        self.trigger_check_address_conflict = Clock.create_trigger(
                                        self._check_address_conflict, -1)
        self.update_address_info = Clock.create_trigger(self._update_address_info)
        self._universes_need_to_check = set()
        super().__init__(**kwargs)

    def on_scene_change(self, old_scene: RowScene, new_scene: RowScene):
        self._update_address_info(None)
        for patch in self.rows.values():
            self.check_address_conflict(patch.universe)

    def add_row(self, **kwargs) -> DatabaseRow:
        if "start_address" not in kwargs:
            kwargs["start_address"] = self.find_free_start_address(
                kwargs["universe"], len(kwargs["fixture"].param_list_unpacked)
            )
        return super().add_row(**kwargs)

    def _update_address_info(self, _):
        address_info = {}

        dmx512.clear_default_matrix_all()
        patch_universes = set()
        for patch in self.rows.values():
            universe = patch.universe
            patch_universes.add(universe)
            param_list = patch.fixture.param_list_unpacked
            for index, address in enumerate(range(patch.start_address, patch.end_address + 1)):
                fixture_param = param_list[index]

                address_info.setdefault((universe, address), []).append((patch, fixture_param))

                dmx512.set_default_matrix_value(
                    universe,
                    address,
                    fixture_param.default_value
                )
        for universe in patch_universes:
            dmx512.clear_matrix(universe)

        self.address_info = address_info

    def get_address_info(self, universe: int, address: int) -> Optional[Tuple[RowPatch, RowFixtureParam]]:
        return self.address_info.get((universe, address), None)

    def check_address_conflict(self, universe: int):
        self._universes_need_to_check.add(universe)
        self.trigger_check_address_conflict()

    def _check_address_conflict(self, _):
        def inner(patch_list: Tuple[RowPatch]):
            sorted_patches = [i for i in sorted(patch_list,
                                                key=lambda x: x.start_address)]
            n = len(sorted_patches)
            if n == 0:
                return
            elif n == 1:
                patch_list[0].is_address_conflict = False
                return

            conflict_patches = set()
            prev_patch = sorted_patches[0]
            for i in range(1, n):
                patch = sorted_patches[i]
                if patch.start_address <= prev_patch.end_address:
                    conflict_patches.add(patch)
                    conflict_patches.add(prev_patch)
                prev_patch = patch

            for patch in sorted_patches:
                patch.is_address_conflict = patch in conflict_patches

        for universe in self._universes_need_to_check:
            inner([i for i in self.rows.values() if i.universe == universe])
        self._universes_need_to_check.clear()

    def find_free_start_address(self, universe: int, length: int) -> int:
        used = sorted(
            (r.start_address, r.end_address)
            for r in self.rows.values() if r.universe == universe
        )
        start = 1
        for used_start, used_end in used:
            if start + length - 1 < used_start:
                return start
            start = max(start, used_end + 1)
        return start if start + length - 1 <= constants.DMX_ADDRESS_COUNT else constants.DMX_ADDRESS_COUNT

    def on_workspace_any_patch(self, patch: RowPatch, workspace: int):
        pass
