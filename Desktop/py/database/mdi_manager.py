from libs.kivy_json_orm.table_implementation import DatabaseTable, DatabaseRow
from libs.kivy_json_orm.fields import ClampedNumericField, StringField, ListField
from misc import constants


class RowMDIManager(DatabaseRow):
    workspace_index = ClampedNumericField(0, 0, constants.DATABASE_MDI_WORKSPACES_COUNT)
    layout_mode = StringField(None)
    layout = ListField(None)
    mdi_focused = StringField(None, allownone=True)


class TableMDIManager(DatabaseTable):
    cls_row = RowMDIManager
    filename = "mdi_manager.json"

    workspace_index = ClampedNumericField(0, 0, constants.DATABASE_MDI_WORKSPACES_COUNT)

    def _create_default(self):
        for workspace_index in range(constants.DATABASE_MDI_WORKSPACES_COUNT):
            self.add_row(workspace_index=workspace_index)
