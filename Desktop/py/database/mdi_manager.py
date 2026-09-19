from kivy.properties import ObjectProperty, StringProperty
from libs.kivy_json_orm.table_implementation import DatabaseTable, DatabaseRow
from misc import constants
from enum import Enum, auto
from typing import Optional, Tuple, Dict
from libs.serialize import *
from libs.properties import ClampedNumericProperty, EnumProperty
from libs.kivy_json_orm.fields import *


class WindowManager(Enum):
    FLOATING = auto()
    TILING = auto()


class FlexManager(Enum):
    LEFT = auto()
    RIGHT = auto()
    VERTICAL = auto()


class RowMDIManager(DatabaseRow):
    workspace_index = ClampedNumericField(0, 0, constants.DATABASE_MDI_WORKSPACES_COUNT)
    window_manager = EnumField(WindowManager, WindowManager.FLOATING)
    mdi_focused = StringField(None, allownone=True)
    layout = ListField(None)


class MdiDataState(SerializableMixin):
    size_hint = ListField((None, None), allow_none=True)
    size = ListField((200, 200))
    pos = ListField((0, 0))
    flex = ObjectField(
        default=None,
        serialize=lambda self, v: v.value if v else None,
        deserialize=lambda self, v: FlexManager(v) if v else None,
        allownone=True
    )


class MdiDataFullState(SerializableMixin):
    state = NestedField(MdiDataState, default_factory=MdiDataState)
    state_saved = NestedField(
        MdiDataState,
        allownone=True,
        default=None,
        serialize=nested_optional_pair(MdiDataState)[0],
        deserialize=nested_optional_pair(MdiDataState)[1]
    )


class MdiData(SerializableMixin):
    data = DictField(
        serialize=dict_of_serializable_pair(MdiDataFullState)[0],
        deserialize=dict_of_serializable_pair(MdiDataFullState)[1]
    )

    def try_create_mdi_id(self, mdi_id: str):
        if mdi_id not in self.data:
            self.data[mdi_id] = MdiDataFullState()

    def set_size_hint(self, mdi_id: str, value: Tuple[Optional[float], Optional[float]]):
        self.try_create_mdi_id(mdi_id)
        self.data[mdi_id].state.size_hint = value

    def set_size(self, mdi_id: str, value: Tuple[Optional[float], Optional[float]]):
        self.try_create_mdi_id(mdi_id)
        self.data[mdi_id].state.size = value

    def set_pos(self, mdi_id: str, value: Tuple[Optional[float], Optional[float]]):
        self.try_create_mdi_id(mdi_id)
        self.data[mdi_id].state.pos = value

    def set_flex(self, mdi_id: str, value: Optional[FlexManager]):
        self.try_create_mdi_id(mdi_id)
        self.data[mdi_id].state.flex = value

    def get_mdi_state(self, mdi_id: str) -> MdiDataState:
        return self.data[mdi_id].state

    def set_mdi_state(self, mdi: "MDIWindow"):
        mdi_id = mdi._db_title_id
        if mdi_id in self.data:
            state = self.data[mdi_id].state
            from libs import logger
            mdi.size_hint = state.size_hint
            mdi.size = state.size
            mdi.pos = state.pos

    def save_mdi_state(self, mdi: "MDIWindow"):
        mdi_id = mdi._db_title_id
        self.try_create_mdi_id(mdi_id)
        fullstate = self.data[mdi_id]
        if fullstate.state_saved is None:
            fullstate.state_saved = MdiDataState(
                size_hint=mdi.size_hint[:],
                size=mdi.size[:],
                pos=mdi.pos[:],
            )

    def load_mdi_state(self, mdi: "MDIWindow"):
        mdi_id = mdi._db_title_id
        if mdi_id not in self.data:
            return
        fullstate = self.data[mdi_id]
        if fullstate.state_saved is not None:
            state_saved = self.data[mdi_id].state_saved
            mdi.size_hint = state_saved.size_hint
            mdi.size = state_saved.size
            mdi.pos = state_saved.pos
            fullstate.state_saved = None


class TableMDIManager(DatabaseTable):
    cls_row = RowMDIManager
    filename = "mdi_manager.json"

    mdi_data = NestedField(MdiData, default_factory=MdiData)
    workspace_index = ClampedNumericField(0, 0, constants.DATABASE_MDI_WORKSPACES_COUNT)

    def _create_default(self):
        self.mdi_data = MdiData()
        for workspace_index in range(constants.DATABASE_MDI_WORKSPACES_COUNT):
            self.add_row(workspace_index=workspace_index)
