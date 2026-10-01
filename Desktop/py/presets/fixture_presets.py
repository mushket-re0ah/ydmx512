from pathlib import Path
from typing import Any, Optional, Tuple

from database import db
from database.fixture import RowFixture
from database.phase_curve_type import RowPhaseCurveType
from database.playback.renderer.render_data import PlaybackRenderRow
from libs import logger
from libs.asset_manager import FileAssetManager
from libs.dmx512_render.misc import InterpolationType
from libs.kivy_json_orm.fields import (
    BooleanField,
    ClampedNumericField,
    ListField,
    ListNestedField,
    RefField,
    StringField,
)
from libs.serialize import SerializableMixin
from misc import constants


class FixturePresetRowData(SerializableMixin):
    active: bool = BooleanField(False)
    dots: Tuple[Tuple[float, float, InterpolationType]] = ListField()

class FixturePresetPhaseData(SerializableMixin):
    indices: Tuple[int, ...] = ListField()
    amount: float = ClampedNumericField(0.0, -1.0, 1.0)
    curve: RowPhaseCurveType = RefField(
        lambda: db.phase_curve_type,
        default_factory=lambda: db.phase_curve_type.get_default_row()
    )
    inverted: bool = BooleanField(False)
    dots: Tuple[Tuple[float, float, InterpolationType]] = ListField()

class FixturePresetData(SerializableMixin):
    title: str = StringField()
    rows: Tuple[PlaybackRenderRow, ...] = ListNestedField(FixturePresetRowData)
    phases: Tuple[FixturePresetPhaseData, ...] = ListNestedField(FixturePresetPhaseData)


class FixturePresetsManager(FileAssetManager):
    def __init__(self):
        super().__init__(
            constants.PRESETS_PATH,
            constants.PRESETS_FIXTURE_SUBDIR,
            FixturePresetData
        )

    def get_asset_by_path(self, filepath: Path) -> Any:
        preset = super().get_asset_by_path(filepath)
        if preset is None:
            return None
        fixture = self._get_fixture_by_path(filepath)
        if not fixture:
            return None

        param_count = len(fixture.param_list_unpacked)
        if len(preset.rows) != param_count:
            logger.warning(f"Fixture Presets: preset \"{filepath}\" имеет {len(preset.rows)} строк,"
                           f" но фикстура \"{fixture}\" имеет {param_count} каналов")
            return None

        for phase in preset.phases:
            if any(index < 0 or index >= param_count for index in phase.indices):
                logger.warning(f"Fixture Presets: фаза пресета \"{filepath}\" имеет невалидные "
                               f"indices {phase.indices} выходящие за пределы количества каналов"
                                " либо отрицательные")
                return None
            if len(phase.indices) < 2:
                logger.warning(f"Fixture Presets: фаза пресета \"{filepath}\" имеет indices менее "
                               f"чем с двумя элементами {phase.indices}")
                return None

        return preset

    def _key_to_string(self, key: RowFixture) -> str:
        return str(key._id)

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
