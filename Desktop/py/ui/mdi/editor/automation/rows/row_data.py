from kivy.event import EventDispatcher
from kivy.properties import (
    BooleanProperty, ListProperty, ObjectProperty, AliasProperty,
    NumericProperty, DictProperty
)
from database.patch import RowPatch
from typing import List, Optional
from database.playback import PlaybackRenderRow
from kivy.clock import Clock
from libs.kivy_utils import AutoUnbindBehavior


class RowParamData(AutoUnbindBehavior, EventDispatcher):
    row_panel = ObjectProperty()
    automation = ObjectProperty()
    playback = ObjectProperty()
    patch_group = ListProperty()
    fixture_index = ObjectProperty()
    fixture_param = ObjectProperty()
    render_rows = ObjectProperty()
    address_list = ObjectProperty()
    selected = BooleanProperty(False)
    active = BooleanProperty()
    phase_interpatch_x = NumericProperty(None, allownone=True, rebind=True)
    master_render_row = AliasProperty(lambda self: self.render_rows[0])
    has_data = BooleanProperty(False)

    render_rows_by_address = DictProperty({})

    row_phase_spec = ObjectProperty(None, allownone=True)
    interpatch_spec = ObjectProperty(None, allownone=True)

    __events__ = ("on_data_changed",)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._on_data_changed_trigger = Clock.create_trigger(self.dispatch_on_data_changed, -1)
        self.bind_to(
            self,
            patch_group=self._on_data_changed_trigger,
            fixture_index=self._on_data_changed_trigger,
            fixture_param=self._on_data_changed_trigger,
            render_rows=self._on_data_changed_trigger,
            address_list=self._on_data_changed_trigger,
            selected=self._on_data_changed_trigger,
            active=self._on_data_changed_trigger,
            phase_interpatch_x=self._on_data_changed_trigger,
        )
        self.automation.editor_content.bind(on_render_changed=self._on_data_changed_trigger)
        self.bind_to(self.master_render_row, active=self.set_active)
        self.active = self.master_render_row.active
        self.row_phase_spec = self.master_render_row.row_phase_spec
        self.interpatch_spec = self.master_render_row.interpatch_spec
        self.set_phase_interpatch_x_by_spec()

    def dispatch_on_data_changed(self, *args):
        self.dispatch("on_data_changed")

    def on_data_changed(self):
        self.has_data = any(row.has_data for row in self.render_rows)
        self.row_phase_spec = self.master_render_row.row_phase_spec
        self.interpatch_spec = self.master_render_row.interpatch_spec
        self.set_phase_interpatch_x_by_spec()

    def set_phase_interpatch_x_by_spec(self):
        if self.interpatch_spec:
            self.phase_interpatch_x = self.interpatch_spec.linked_shifts.get(
                self.master_render_row.fixture_index, None
            )
            if self.phase_interpatch_x is None:
                raise RuntimeError(f"why spec return None for phase_interpatch_x? fixture_index={self.master_render_row.fixture_index}, shifts={self.interpatch_spec.linked_shifts}")
        else:
            self.phase_interpatch_x = None

    def set_active(self, _, value: bool):
        self.active = value

    def get_master_render_rows(self) -> List[PlaybackRenderRow]:
        result = {}
        for row in self.render_rows:
            if row.patch not in result:
                result[row.patch] = row
        return list(result.values())

    master_patch = AliasProperty(
        lambda self: self.patch_group[0] if self.patch_group else None,
        bind=["patch_group"],
        cache=True
    )

    def get_allow_interpatch_phase(self) -> bool:
        if not self.patch_group or not self.render_rows:
            return False
        return len(self.patch_group) > 1 and len(self.render_rows) > 1
    allow_interpatch_phase = AliasProperty(
        get_allow_interpatch_phase,
        bind=["patch_group", "render_rows"]
    )

    def get(self, key, default=None):
        return getattr(self, key, default)

    def items(self):
        attrs = (
            "row_panel", "automation", "playback", "patch_group",
            "fixture_index", "fixture_param", "render_rows", "address_list",
            "selected", "master_patch", "master_render_row"
        )
        return ((attr, getattr(self, attr)) for attr in attrs)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)


class RowsDataManager(list):
    def get_all_render_rows(self) -> List[List[PlaybackRenderRow]]:
        return [row for data_row in self for row in data_row.render_rows]

    def get_selected_data_rows(self) -> List[RowParamData]:
        return [i for i in self if i.selected]

    def get_selected_render_rows(self):
        rows = []
        for data_row in self.get_selected_data_rows():
            for fulladdress, active in data_row.address_list.items():
                if active:
                    rows.extend(data_row.render_rows_by_address.get(fulladdress, ()))
        return rows

    def dispatch_row_change(self):
        for data_row in self:
            data_row._on_data_changed_trigger()
