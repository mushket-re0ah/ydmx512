from typing import List, Optional, Union

from libs.kivy_json_orm.fields import ClampedNumericField, ListField, StringField
from libs.kivy_json_orm.table_implementation import DatabaseRow, DatabaseTable
from misc import constants


class RowMDIManager(DatabaseRow):
    workspace_index: int = ClampedNumericField(0, 0, constants.DATABASE_MDI_WORKSPACES_COUNT)
    layout_mode: str = StringField(None)
    layout: Union[List[str], List[List[str]]] = ListField(None)
    mdi_focused: Optional[str] = StringField(None, allownone=True)


class TableMDIManager(DatabaseTable):
    cls_row = RowMDIManager
    filename = "mdi_manager.json"

    workspace_index: int = ClampedNumericField(0, 0, constants.DATABASE_MDI_WORKSPACES_COUNT)

    def _create_default(self):
        for workspace_index in range(constants.DATABASE_MDI_WORKSPACES_COUNT):
            self.add_row(workspace_index=workspace_index)
