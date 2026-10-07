from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.properties import (
    AliasProperty,
    BooleanProperty,
    DictProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
)

from database.fixture_param import RowFixtureParam
from database.patch import RowPatch
from database.playback import PlaybackRenderRow
from database.playback.playback import RowPlayback
from database.playback.renderer.render_data import InterpatchSpec, RowPhaseSpec
from libs.dmx512.misc import FullAddress
from libs.kivy_mixins import AutoUnbindBehavior

if TYPE_CHECKING:
    from ui.mdi.editor.automation import Automation
    from ui.mdi.editor.automation.rows import RowPanel


class RowParamData(AutoUnbindBehavior, EventDispatcher):
    row_panel: "RowPanel" = ObjectProperty()
    automation: "Automation" = ObjectProperty()
    playback: RowPlayback = ObjectProperty()
    patch_group: Tuple[RowPatch, ...] = ListProperty()
    fixture_index: Dict[RowPatch, Tuple[int, ...]] = ObjectProperty()
    fixture_param: RowFixtureParam = ObjectProperty()
    render_rows: Tuple[PlaybackRenderRow, ...] = ObjectProperty()
    address_list: Dict[FullAddress, bool] = ObjectProperty()
    selected: bool = BooleanProperty(False)
    active: bool = BooleanProperty()
    phase_interpatch_x: Optional[float] = NumericProperty(None, allownone=True, rebind=True)
    master_render_row: PlaybackRenderRow = AliasProperty(lambda self: self.render_rows[0])
    has_data: bool = BooleanProperty(False)

    render_rows_by_address: Dict[FullAddress, Tuple[PlaybackRenderRow, ...]] = DictProperty({})

    row_phase_spec: Optional[RowPhaseSpec] = ObjectProperty(None, allownone=True)
    interpatch_spec: Optional[InterpatchSpec] = ObjectProperty(None, allownone=True)

    __events__ = ("on_data_changed",)

    def __init__(self, **kwargs: Any):
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

    def dispatch_on_data_changed(self, *_:Any):
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
                raise RuntimeError(f"fixture_index={self.master_render_row.fixture_index}, "
                                   f"shifts={self.interpatch_spec.linked_shifts}")
        else:
            self.phase_interpatch_x = None

    def set_active(self, _, value: bool):
        self.active = value

    def get_master_render_rows(self) -> List[PlaybackRenderRow]:
        result: Dict[RowPatch, PlaybackRenderRow] = {}
        for row in self.render_rows:
            if row.patch not in result:
                result[row.patch] = row
        return list(result.values())

    master_patch: RowPatch = AliasProperty(
        lambda self: self.patch_group[0] if self.patch_group else None,
        bind=("patch_group",),
        cache=True
    )

    def get_allow_interpatch_phase(self) -> bool:
        if not self.patch_group or not self.render_rows:
            return False
        return len(self.patch_group) > 1 and len(self.render_rows) > 1
    allow_interpatch_phase: bool = AliasProperty(
        get_allow_interpatch_phase,
        bind=("patch_group", "render_rows",)
    )

    def get(self, key: str, default:Any=None) -> Any:
        return getattr(self, key, default)

    def items(self) -> Tuple[Tuple[str, Any], ...]:
        attrs = (
            "row_panel", "automation", "playback", "patch_group",
            "fixture_index", "fixture_param", "render_rows", "address_list",
            "selected", "master_patch", "master_render_row"
        )
        return tuple((attr, getattr(self, attr)) for attr in attrs)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any):
        setattr(self, key, value)


class RowsDataManager(List[RowParamData]):
    def get_all_render_rows(self) -> List[PlaybackRenderRow]:
        return [row for data_row in self for row in data_row.render_rows]

    def get_selected_data_rows(self) -> List[RowParamData]:
        return [i for i in self if i.selected]

    def get_selected_render_rows(self) -> List[PlaybackRenderRow]:
        rows: List[PlaybackRenderRow] = []
        for data_row in self.get_selected_data_rows():
            for fulladdress, active in data_row.address_list.items():
                if active:
                    rows.extend(data_row.render_rows_by_address.get(fulladdress, ()))
        return rows

    def dispatch_row_change(self):
        for data_row in self:
            data_row._on_data_changed_trigger()
