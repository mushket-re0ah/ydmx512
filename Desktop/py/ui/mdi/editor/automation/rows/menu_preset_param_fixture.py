from kivy.properties import ObjectProperty
from presets import param_preset_manager
from presets.param_presets import ParamPresetData
from ui.components.file_preset_manager import FilePresetModal, MenuPresetManager
from ui.mdi.editor.automation.tools import DiscardRowTool, LoadParamPresetTool
from kivy.lang import Builder


Builder.load_file("ui/mdi/editor/automation/rows/menu_preset_param_fixture.kv")


class ModalSaveParamFixturePreset(FilePresetModal):
    asset_manager = ObjectProperty(param_preset_manager)
    render_row = ObjectProperty()

    def create_preset(self):
        return ParamPresetData(
            title=self.title,
            dots=[[dot.x, dot.y, dot.dot_type.value] for dot in self.render_row.dots]
        )


class MenuPresetParamFixture(MenuPresetManager):
    asset_manager = ObjectProperty(param_preset_manager)
    row_panel = ObjectProperty()
    render_rows = ObjectProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allow_create_preset = any(row.has_data for row in self.render_rows)

    def copy(self):
        self.row_panel.copy_rows(self.render_rows, True)
        self.dismiss()

    def paste(self):
        self.row_panel.paste_rows(self.render_rows)
        self.dismiss()

    def load_preset(self, preset: ParamPresetData):
        self.row_panel.automation.set_tool(LoadParamPresetTool, preset, self.render_rows)
        self.dismiss()

    def discard_row(self):
        self.row_panel.automation.set_tool(DiscardRowTool, self.render_rows)
        self.dismiss()

    def create_modal(self) -> "Modal":
        return ModalSaveParamFixturePreset(
            category_key=self.category_key,
            render_row=self.render_rows[0]
        )
