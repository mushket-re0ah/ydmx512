from misc import constants
from database import db
from database.fixture import RowFixture
from libs.serialize import SerializableMixin
from database.playback.renderer.render_data import PlaybackRenderRow
from database.phase_curve_type import RowPhaseCurveType
from libs.kivy_json_orm.fields import *
from libs.asset_manager import FileAssetManager
from pathlib import Path
from typing import Any, Optional
from misc import logger


class FixturePresetRowData(SerializableMixin):
    active = BooleanField(False)
    dots = ListField()

class FixturePresetPhaseData(SerializableMixin):
    indices = ListField()
    amount = ClampedNumericField(0.0, -1.0, 1.0)
    curve = RefField(lambda: db.phase_curve_type, default_factory=lambda: db.phase_curve_type.get_default_row())
    inverted = BooleanField(False)
    dots = ListField()

class FixturePresetData(SerializableMixin):
    title = StringField()
    rows = ListNestedField(FixturePresetRowData)
    phases = ListNestedField(FixturePresetPhaseData)


class FixturePresetsManager(FileAssetManager):
    def __init__(self):
        super().__init__(constants.PRESETS_PATH, constants.PRESETS_FIXTURE_SUBDIR, FixturePresetData)

    def get_asset_by_path(self, filepath: Path) -> Any:
        preset = super().get_asset_by_path(filepath)
        if preset is None:
            return None
        fixture = self._get_fixture_by_path(filepath)
        if not fixture:
            return None

        param_count = len(fixture.param_list_unpacked)
        if len(preset.rows) != param_count:
            logger.warning(f"Fixture Presets: preset \"{filepath}\" имеет {len(preset.rows)} строк, но фикстура \"{fixture}\" имеет {param_count} каналов")
            return None

        for phase in preset.phases:
            if any(index < 0 or index >= param_count for index in phase.indices):
                logger.warning(f"Fixture Presets: фаза пресета \"{filepath}\" имеет невалидные indices {phase.indices} выходящие за пределы количества каналов либо отрицательные")
                return None
            if len(phase.indices) < 2:
                logger.warning(f"Fixture Presets: фаза пресета \"{filepath}\" имеет indices менее чем с двумя элементами {phase.indices}")
                return None

        return preset

    def _key_to_string(self, fixture: RowFixture) -> str:
        return str(fixture._id)

    def _get_fixture_by_path(self, filepath: Path) -> Optional[RowFixture]:
        try:
            fixture_id = int(filepath.parent.name)
        except (ValueError, AttributeError):
            logger.warning(f"Fixture Presets: не удалось извлечь fixture id из строки {filepath}")
            return None

        fixture = db.fixture.get_row_by_id(fixture_id)
        if fixture is None:
            logger.warning(f"Fixture Presets: не удалось найти фикстуру с id={fixture_id}")
        return fixture
