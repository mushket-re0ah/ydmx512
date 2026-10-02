from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

from libs.kivy_json_orm.fields import ClampedNumericField, ListField, StringField
from libs.kivy_json_orm.table_implementation import DatabaseRow, DatabaseTable
from misc import constants

if TYPE_CHECKING:
    from database import YdmxDatabase


class RowMDIManager(DatabaseRow):
    database: "YdmxDatabase"  # pyright: ignore[reportIncompatibleMethodOverride]
    table: "TableMDIManager" # pyright: ignore[reportIncompatibleVariableOverride]

    workspace_index: int = ClampedNumericField(0, 0, constants.DATABASE_MDI_WORKSPACES_COUNT)
    layout_mode: str = StringField(None)
    layout: Union[List[str], List[List[str]]] = ListField(None)
    mdi_focused: Optional[str] = StringField(None, allownone=True)


class TableMDIManager(DatabaseTable):
    database: "YdmxDatabase" # pyright: ignore[reportIncompatibleVariableOverride]
    get_row_by_id: Callable[[int], Optional[RowMDIManager]] # pyright: ignore[reportIncompatibleMethodOverride]
    rows: Dict[int, RowMDIManager] # pyright: ignore[reportIncompatibleVariableOverride]
    get_row_by_attribute: Callable[[str, Any], Optional[RowMDIManager]] # pyright: ignore[reportIncompatibleMethodOverride]
    on_add_row: Callable[[RowMDIManager], None] # pyright: ignore[reportIncompatibleMethodOverride]
    on_remove_row: Callable[[RowMDIManager], None] # pyright: ignore[reportIncompatibleMethodOverride]
    add_row: Callable[..., RowMDIManager] # pyright: ignore[reportIncompatibleMethodOverride]
    remove_row: Callable[[RowMDIManager], None] # pyright: ignore[reportIncompatibleMethodOverride]
    __getattr__: Callable[[str], Callable[[Any], Optional[RowMDIManager]]] # pyright: ignore[reportIncompatibleMethodOverride]

    cls_row = RowMDIManager
    filename = "mdi_manager.json"

    workspace_index: int = ClampedNumericField(0, 0, constants.DATABASE_MDI_WORKSPACES_COUNT)

    def _create_default(self):
        for workspace_index in range(constants.DATABASE_MDI_WORKSPACES_COUNT):
            self.add_row(workspace_index=workspace_index)
