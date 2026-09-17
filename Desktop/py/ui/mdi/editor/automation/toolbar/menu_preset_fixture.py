from kivy.properties import ObjectProperty
from presets import fixture_preset_manager
from presets.fixture_presets import (
    FixturePresetData, FixturePresetPhaseData, FixturePresetRowData
)
from ui.components.file_preset_manager import FilePresetModal, MenuPresetManager
from ui.mdi.editor.automation.tools import LoadFixturePresetTool
from kivy.lang import Builder


Builder.load_file("ui/mdi/editor/automation/toolbar/menu_preset_fixture.kv")


class ModalSaveFixturePreset(FilePresetModal):
    asset_manager = ObjectProperty(fixture_preset_manager)
    patch = ObjectProperty()
    renderer = ObjectProperty()

    def create_preset(self):
        rows_data = [
            FixturePresetRowData(
                active=row.active,
                dots=[[dot.x, dot.y, dot.dot_type.value] for dot in row.dots]
            )
            for row in self.renderer.get_rows(self.patch)
        ]

        phases_data = []
        for spec in self.renderer._row_phase_specs_by_patch.get(self.patch, []):
            phases_data.append(
                FixturePresetPhaseData(
                    indices=spec.indices,
                    amount=spec.amount,
                    curve=spec.curve,
                    inverted=spec.inverted,
                    dots=[[dot.x, dot.y, dot.dot_type.value] for dot in spec.dots]
                )
            )

        return FixturePresetData(
            title=self.title,
            rows=rows_data,
            phases=phases_data
        )


class MenuPresetFixture(MenuPresetManager):
    asset_manager = ObjectProperty(fixture_preset_manager)
    row_panel = ObjectProperty()
    patch = ObjectProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allow_create_preset = self.row_panel.has_any_data

    def load_preset(self, preset):
        self.row_panel.automation.set_tool(LoadFixturePresetTool, preset, self.patch)

    def create_modal(self) -> "Modal":
        return ModalSaveFixturePreset(
            category_key=self.category_key,
            patch=self.patch,
            renderer=self.row_panel.renderer
        )
