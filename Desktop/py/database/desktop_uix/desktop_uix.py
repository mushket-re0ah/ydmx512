from kivy.properties import (
    StringProperty, NumericProperty, ReferenceListProperty, ColorProperty,
    BooleanProperty, AliasProperty, ObjectProperty
)
from kivy.clock import Clock
from kivy.utils import boundary
from libs.kivy_json_orm.table_implementation import DatabaseTable, DatabaseRow
from database.scene import RowScene, TableScene, SceneTableMixin, SceneRowMixin
from database.patch import RowPatch
from database.fixture_param import RowFixtureParam
from enum import Enum, auto
from misc import constants
from typing import Optional, Tuple
from database.desktop_uix.player import DesktopUixPlayer
from libs.serialize import *
from libs.properties import ClampedNumericProperty, EnumProperty
from libs.kivy_json_orm.fields import *
from misc.player.status import PlayerStatus
from misc.player.render_utils import SoftEffectsRenderer


class DesktopUixType(Enum):
    rotary_button = auto()
    slider2d = auto()


class RowDesktopUix(SceneRowMixin, DatabaseRow):
    title = StringField("")
    uix_type = EnumField(DesktopUixType, DesktopUixType.rotary_button)
    grid_pos = ListField([None, None])
    workspace = NumericField(0)
    color = ColorField((1, 1, 1, 1))
    _active = BooleanField(False)
    patch = BindableObjectRefField(
        "patch",
        allownone=True,
        bind={
            "start_address": "update_force_by_patch",
            "universe": "update_force_by_patch",
            "invert_pan": "update_force_by_patch",
            "invert_tilt": "update_force_by_patch",
            "virtual_dimmer": "update_force_by_patch",
        },
        on_set="on_patch_changed"
    )
    fixture_param_1_index = NumericField(None, allownone=True)
    fixture_param_2_index = NumericField(None, allownone=True)

    value_1_minimum = ClampedNumericField(0, 0, 255)
    value_1_maximum = ClampedNumericField(255, 0, 255)
    value_1_inversion = BooleanField(False)
    _value_1 = ContextualNumericField(
        default=0,
        min_getter=lambda self: self.value_1_minimum,
        max_getter=lambda self: self.value_1_maximum,
        dependencies=("value_1_minimum", "value_1_maximum")
    )
    value_2_minimum = ClampedNumericField(0, 0, 255)
    value_2_maximum = ClampedNumericField(255, 0, 255)
    value_2_inversion = BooleanField(False)
    _value_2 = ContextualNumericField(
        default=0,
        min_getter=lambda self: self.value_2_minimum,
        max_getter=lambda self: self.value_2_maximum,
        dependencies=("value_2_minimum", "value_2_maximum")
    )

    player = NestedField(DesktopUixPlayer, default_factory=DesktopUixPlayer, rebind=True)
    trigger_update_active = None

    def __init__(self, *args, **kwargs):
        self.trigger_update_active = Clock.create_trigger(self.update_active, -1)
        self.bind(link_active=self.trigger_update_active)
        super().__init__(*args, **kwargs)

    def on_player(self, _, player: DesktopUixPlayer):
        player.parent_row = self

    def on_patch_changed(self, new_patch):
        if new_patch is None:
            self.fixture_param_1_index = None
            self.fixture_param_2_index = None

    def set_active(self, active: bool):
        if not self.link_active or (self.player.status is PlayerStatus.RELEASE):
            active = False
        if self._active == active:
            return False
        self._active = active
        return True

    active = AliasProperty(
        lambda self: self._active, set_active
    )

    def update_force_by_patch(self, *args):
        self.property("fixture_param_1_index").dispatch(self)
        self.property("fixture_param_2_index").dispatch(self)
        self.player.trigger_update_force_value()

    def get_fixture_param(self, n: int) -> Optional[RowFixtureParam]:
        fparam_index = getattr(self, f"fixture_param_{n}_index")
        if self.patch and fparam_index is not None:
            return self.patch.param_list_unpacked[fparam_index]
        else:
            return None
    fixture_param_1 = AliasProperty(
        lambda self: self.get_fixture_param(1),
        bind=["patch", "fixture_param_1_index"],
        cache=True
    )
    fixture_param_2 = AliasProperty(
        lambda self: self.get_fixture_param(2),
        bind=["patch", "fixture_param_2_index"],
        cache=True
    )

    def get_link_active(self) -> bool:
        return self.patch and (
             self.fixture_param_1_index is not None or
             self.fixture_param_2_index is not None
        )
    link_active = AliasProperty(
        get_link_active,
        bind=["patch", "fixture_param_1_index", "fixture_param_2_index"]
    )

    def update_active(self, _):
        if not self.link_active:
            self.active = False

    value_1_allow = AliasProperty(
        lambda self: self.fixture_param_1_index is not None,
        bind=["fixture_param_1_index"]
    )

    value_1 = AliasProperty(
        lambda self: self._value_1 ^ 255 if self.value_1_inversion else self._value_1,
        lambda self, val: setattr(self, "_value_1", val),
        bind=["_value_1", "value_1_inversion"]
    )

    link_active_value_1 = AliasProperty(
        lambda self: self.link_active and self.value_1_allow,
        bind=["link_active", "value_1_allow"]
    )

    value_2_allow = AliasProperty(
        lambda self: self.fixture_param_2_index is not None and self.uix_type is DesktopUixType.slider2d,
        bind=["fixture_param_2_index"]
    )

    value_2 = AliasProperty(
        lambda self: self._value_2 ^ 255 if self.value_2_inversion else self._value_2,
        lambda self, val: setattr(self, "_value_2", val),
        bind=["_value_2", "value_2_inversion"]
    )

    link_active_value_2 = AliasProperty(
        lambda self: self.link_active and self.value_2_allow,
        bind=["link_active", "value_2_allow"]
    )


class TableDesktopUix(SceneTableMixin, DatabaseTable):
    cls_row = RowDesktopUix
