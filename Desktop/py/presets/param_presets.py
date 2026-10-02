from typing import Tuple

from database import db
from database.fixture_param import RowFixtureParam
from libs.asset_manager import FileAssetManager
from libs.dmx512_render import InterpolationType
from libs.kivy_json_orm.fields import ListField, StringField
from libs.serialize import SerializableMixin
from misc import constants


class ParamPresetData(SerializableMixin):
    title: str = StringField()
    dots: Tuple[Tuple[float, float, InterpolationType]] = ListField()


class ParamPresetsManager(FileAssetManager):
    def __init__(self):
        super().__init__(constants.PRESETS_PATH, constants.PRESETS_PARAMS_SUBDIR, ParamPresetData)

    def _key_to_string(self, key: RowFixtureParam) -> str:
        return key.title_id if key.title_id is not None else key.title

    def _get_asset_stem(self, asset: RowFixtureParam) -> str:
        return asset.title

    def _create_default(self):
        self.add_asset(db.fixture_param.by_title_id("pan"), ParamPresetData(
            title="Круг",
            dots=[
                [0.0, 100/255, InterpolationType.SPLINE.value],
                [0.5, 60/255, InterpolationType.SPLINE.value],
                [1.0, 100/255, InterpolationType.SPLINE.value]
            ])
        )
        self.add_asset(db.fixture_param.by_title_id("tilt"), ParamPresetData(
            title="Круг",
            dots=[
                [0.0, 100/255, InterpolationType.SPLINE.value],
                [0.5, 60/255, InterpolationType.SPLINE.value],
                [1.0, 100/255, InterpolationType.SPLINE.value]
            ])
        )
