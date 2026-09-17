from misc import constants
from database import db
from libs.serialize import SerializableMixin
from libs.dmx512_render import InterpolationType
from database.fixture_param import RowFixtureParam
from libs.kivy_json_orm.fields import *
from libs.asset_manager import FileAssetManager


class ParamPresetData(SerializableMixin):
    title = StringField()
    dots = ListField()


class ParamPresetsManager(FileAssetManager):
    def __init__(self):
        super().__init__(constants.PRESETS_PATH, constants.PRESETS_PARAMS_SUBDIR, ParamPresetData)

    def _key_to_string(self, fixture_param: RowFixtureParam) -> str:
        return fixture_param.title_id

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
