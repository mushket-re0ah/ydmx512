from typing import Any, List

from kivy.lang import Builder
from kivy.properties import ObjectProperty

from database.patch import RowPatch
from database.playback.renderer import PlaybackRenderer
from presets import fixture_preset_manager
from presets.fixture_presets import (
    FixturePresetData,
    FixturePresetPhaseData,
    FixturePresetRowData,
    FixturePresetsManager,
)
from ui.components.file_preset_manager import FilePresetModal, MenuPresetManager
from ui.mdi.editor.automation.rows import RowPanel
from ui.mdi.editor.automation.tools import LoadFixturePresetTool

Builder.load_file("ui/mdi/editor/automation/toolbar/menu_preset_fixture.kv")


class ModalSaveFixturePreset(FilePresetModal):
    asset_manager: FixturePresetsManager = ObjectProperty(fixture_preset_manager)
    patch: RowPatch = ObjectProperty()
    renderer: PlaybackRenderer = ObjectProperty()

    def create_preset(self) -> FixturePresetData:
        rows_data = [
            FixturePresetRowData(
                active=row.active,
                dots=[[dot.x, dot.y, dot.dot_type.value] for dot in row.dots]
            )
            for row in self.renderer.get_rows(self.patch)
        ]

        phases_data: List[FixturePresetPhaseData] = []
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
            phases=tuple(phases_data)
        )


class MenuPresetFixture(MenuPresetManager):
    asset_manager: FixturePresetsManager = ObjectProperty(fixture_preset_manager)
    row_panel: RowPanel = ObjectProperty()
    patch: RowPatch = ObjectProperty()

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.allow_create_preset = self.row_panel.has_any_data

    def load_preset(self, preset: FixturePresetData):
        self.row_panel.automation.set_tool(LoadFixturePresetTool, preset, self.patch)

    def create_modal(self) -> ModalSaveFixturePreset:
        return ModalSaveFixturePreset(
            category_key=self.category_key,
            patch=self.patch,
            renderer=self.row_panel.renderer
        )
