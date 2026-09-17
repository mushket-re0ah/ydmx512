from kivy.properties import StringProperty, ObjectProperty, ListProperty, AliasProperty
from database.brand import RowBrand
from database.fixture_param import RowFixtureParam
from database import db
from libs.kivy_json_orm.table_implementation import DatabaseTable, DatabaseRow
from typing import NamedTuple, List, Tuple, Dict
from misc import constants
from collections import defaultdict
from libs.serialize import *
from libs.properties import ClampedNumericProperty
from libs.kivy_json_orm.fields import *


class FixtureParamMapKey(NamedTuple):
    param: RowFixtureParam
    is_linear: bool


class FixtureChannelsGroup(SerializableMixin):
    title = StringField()
    repeat_count = NumericField(1)
    linear = BooleanField(False)
    param_list = ListRefField(lambda: db.fixture_param)


class RowFixture(DatabaseRow):
    title = StringField("Noname")
    note = StringField("")
    brand = RefField("brand", default_factory=lambda: db.brand.get_default_row())
    icon = StringField("none.png", allownone=True)
    temp_dependence = ClampedNumericField(
        constants.FIXTURE_TEMP_DEPENDENCE_DEFAULT,
        constants.FIXTURE_TEMP_DEPENDENCE_MIN,
        constants.FIXTURE_TEMP_DEPENDENCE_MAX
    )
    channels_groups: List[FixtureChannelsGroup] = ListNestedField(FixtureChannelsGroup)

    def get_param_list_unpacked(self) -> Tuple[RowFixtureParam]:
        param_list_unpacked = []
        for group in self.channels_groups:
            param_list_unpacked += group.param_list * group.repeat_count
        return tuple(param_list_unpacked)
    param_list_unpacked = AliasProperty(
        get_param_list_unpacked, None,
        bind=["channels_groups"], cache=True
    )

    def get_param_map(self) -> Dict[RowFixtureParam, List[int]]:
        param_map = defaultdict(list)
        index = 0
        for group in self.channels_groups:
            for _ in range(group.repeat_count):
                for param in group.param_list:
                    param_key = FixtureParamMapKey(param, group.linear)
                    param_map[param_key].append(index)
                    index += 1
        return param_map
    param_map = AliasProperty(
        get_param_map,
        bind=["channels_groups"], cache=True
    )

    def get_is_dynamic(self) -> bool:
        return any(param.is_dynamic for param in self.param_list_unpacked)
    is_dynamic = AliasProperty(
        get_is_dynamic, None,
        bind=["param_list_unpacked"], cache=True
    )


class TableFixture(DatabaseTable):
    cls_row = RowFixture
    filename = "fixture.json"

    def _create_default(self):
        def _make_param_list(str_params: List[str]) -> List[RowFixtureParam]:
            result = [self.database.fixture_param.by_title_id(param) for param in str_params]
            if None in result:
                raise ValueError("not existed fixture param")
            return result

        self.add_row(
            title="Noname",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Группа #1",
                    param_list=_make_param_list(
                        ['dimmer', 'strobe', 'func', 'func', 'red', 'green',
                         'blue', 'white']),
                ),
            ]
        )
        self.add_row(
            title="Noname #2",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Группа #1",
                    param_list=_make_param_list(
                        ['pan', 'tilt']),
                ),
            ]
        )
        self.add_row(
            title="Noname #3",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Группа #1",
                    param_list=_make_param_list(
                        ['dimmer', 'pan', 'tilt']),
                ),
            ]
        )
        self.add_row(
            title="slimPar 12x3w ",
            note="Прожектор Shehds SlimPar RGBW 12x3w ",
            icon="par.png",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Группа #1",
                    param_list=_make_param_list(
                        ['dimmer', 'strobe', 'func', 'func_spd', 'red',
                         'green', 'blue', 'white']),
                ),
            ]
        )
        self.add_row(
            title="Beam 90w",
            note="Прибор типа Beam Shehds mini-beam 90w RGBW ",
            icon="beam.png",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Группа #1",
                    param_list=_make_param_list(
                        ['pan', 'pan_16_bit', 'tilt', 'tilt_16_bit', 'speed',
                         'dimmer', 'strobe', 'red', 'green', 'blue', 'white',
                         'func', 'reset']),
                ),
            ]
        )
        self.add_row(
            title="Belka 89Ch",
            note="Прибор типа Sunstrip Led Belka 12x3w с подсветкой RGB ",
            icon="bar.png",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Main",
                    param_list=_make_param_list(
                        ['dimmer', 'strobe']),
                ),
                FixtureChannelsGroup(
                    title="Amber",
                    repeat_count=12,
                    linear=True,
                    param_list=_make_param_list(
                        ['amber']),
                ),
                FixtureChannelsGroup(
                    title="RGB",
                    repeat_count=24,
                    linear=True,
                    param_list=_make_param_list(
                        ['red', 'green', 'blue']),
                ),
                FixtureChannelsGroup(
                    title="Add",
                    param_list=_make_param_list(
                        ['color', 'func', 'func_spd', 'reserve']),
                ),
            ]
        )
        self.add_row(
            title="Belka 9Ch",
            note="Прибор типа Sunstrip Led Belka 12x3w с подсветкой RGB ",
            icon="bar.png",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Main",
                    param_list=_make_param_list(
                        ['dimmer', 'strobe', 'red', 'green', 'green', 'amber',
                         'color', 'func', 'func_spd']),
                ),
            ]
        )
        self.add_row(
            title="TabPar 7x18w",
            note="Прожектор Shehds RGBWAUV 7x18w ",
            icon="par.png",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Main",
                    param_list=_make_param_list(
                        ['dimmer', 'red', 'green', 'blue', 'white', 'amber',
                         'uv', 'strobe', 'func', 'func_spd', 'reserve']),
                ),
            ]
        )
        self.add_row(
            title="Par 18x18w",
            note="Прожектор Shehds PAR 18x18w RGBWA+UV ",
            icon="par.png",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Main",
                    param_list=_make_param_list(
                        ['dimmer', 'strobe', 'func', 'func_spd', 'red',
                         'green', 'blue', 'white', 'amber', 'uv', 'reserve']),
                ),
            ]
        )
        self.add_row(
            title="LedBar 24x8w",
            note="LedBar 24x8w RGBW mode D",
            icon="bar.png",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Группа #1",
                    repeat_count=8,
                    param_list=_make_param_list(
                        ['red', 'green', 'blue', 'white']),
                ),
            ]
        )
        self.add_row(
            title="Spot 60w 9ch",
            note="",
            icon="spot.png",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Группа #1",
                    param_list=_make_param_list(
                        ['pan', 'tilt', 'color', 'gobo', 'strobe', 'dimmer',
                         'speed', 'func', 'reset']),
                ),
            ]
        )
        self.add_row(
            title="LedBar 24x8w A",
            note="mode A",
            icon="bar.png",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Группа #1",
                    param_list=_make_param_list(
                        ['dimmer', 'red', 'green', 'blue', 'white', 'strobe',
                         'func', 'func_spd', 'red', 'green', 'blue', 'white']),
                ),
            ]
        )
        self.add_row(
            title="Beam 6x25w 12ch",
            note="12ch",
            icon="beam.png",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Группа #1",
                    param_list=_make_param_list(
                        ['pan', 'tilt', 'speed', 'dimmer', 'strobe', 'color',
                         'prism', 'focus', 'reserve', 'func', 'func', 'reserve']),
                ),
            ]
        )
        self.add_row(
            title="Beam 6x25w 20ch",
            note="20ch рекомендую",
            icon="beam.png",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Группа #1",
                    param_list=_make_param_list(
                        ['pan', 'pan_16_bit', 'tilt', 'tilt_16_bit', 'speed',
                         'dimmer', 'strobe']),
                ),
                FixtureChannelsGroup(
                    title="Группа #2",
                    repeat_count=6,
                    param_list=_make_param_list(
                        ['dimmer']),
                ),
                FixtureChannelsGroup(
                    title="Группа #3",
                    param_list=_make_param_list(
                        ['color', 'prism', 'func', 'func_spd', 'func',
                         'func', 'reserve']),
                ),
            ]
        )
        self.add_row(
            title="ThunderWash",
            note="6ch вар 1",
            icon="strobe.png",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Группа #1",
                    param_list=_make_param_list(
                        ['dimmer', 'strobe', 'red', 'green', 'blue', 'reset']),
                ),
            ]
        )
        self.add_row(
            title="ThunderWash #2",
            note="6ch вар 2",
            icon="wash.png",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Группа #1",
                    param_list=_make_param_list(
                        ['dimmer', 'strobe', 'strobe', 'red', 'green', 'blue']),
                ),
            ]
        )
        self.add_row(
            title="Wash 36x10",
            note="Wash 36x10 Юля",
            icon="wash.png",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Группа #1",
                    param_list=_make_param_list(
                        ['pan', 'pan_16_bit', 'tilt', 'tilt_16_bit', 'dimmer',
                         'strobe', 'red', 'green', 'blue', 'white', 'zoom',
                         'speed', 'color', 'func', 'reserve']),
                ),
            ]
        )
        self.add_row(
            title="Beam Bar 8x12 ch 38",
            note="Led Beam 8x12W RGB ch 38 SHEHDS",
            icon="bar.png",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Группа #1",
                    param_list=_make_param_list(
                        ['pan', 'speed', 'func', 'func_spd', 'dimmer',
                         'strobe']),
                ),
                FixtureChannelsGroup(
                    title="Группа #2",
                    repeat_count=8,
                    param_list=_make_param_list(
                        ['red', 'green', 'blue', 'white']),
                ),
            ]
        )
        self.add_row(
            title="Wash",
            note="36x12w",
            icon="wash.png",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Группа #1",
                    param_list=_make_param_list(
                        ['pan', 'tilt', 'speed', 'dimmer', 'red', 'green',
                         'blue', 'white', 'strobe', 'zoom', 'func', 'func_spd',
                         'reserve', 'reserve', 'reserve', 'reserve']),
                ),
            ]
        )
        self.add_row(
            title="Hazer",
            note="Hazer",
            icon="effects.png",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Группа #1",
                    param_list=_make_param_list(
                        ['dimmer']),
                ),
            ]
        )
        self.add_row(
            title="Wash 19x15w 14Ch",
            note="Vadik Koss V-show",
            icon="wash.png",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Группа #1",
                    param_list=_make_param_list(
                        ['strobe', 'dimmer', 'focus', 'pan', 'pan_16_bit',
                         'tilt', 'tilt_16_bit', 'func', 'color', 'red',
                         'green', 'blue', 'white', 'lamp_on']),
                ),
            ]
        )
        self.add_row(
            title="Wash 19x15 Ch25",
            note="Vadik Koss V-show",
            icon="wash.png",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Группа #1",
                    param_list=_make_param_list(
                        ['strobe', 'dimmer', 'focus', 'pan', 'pan_16_bit',
                         'tilt', 'tilt_16_bit', 'func', 'color', 'red',
                         'green', 'blue', 'white', 'lamp_on', 'func',
                         'func_spd', 'func', 'func_spd', 'func', 'strobe',
                         'dimmer', 'color', 'red', 'green', 'blue']),
                ),
            ]
        )
        self.add_row(
            title="Beam R7",
            note="""18 каналов: 
- 14 канал Микропрограмма
- 15 канал Сброс 
- 16 канал Лампа (200-205 Вкл; 26-100 Выкл)""",
            icon="beam.png",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Группа #1",
                    param_list=_make_param_list(
                        ['color', 'strobe', 'dimmer', 'gobo', 'prism',
                         'prism_rotary', 'uv', 'frost', 'zoom', 'pan',
                         'pan_16_bit', 'tilt', 'tilt_16_bit', 'func',
                         'reset', 'lamp_on', 'func', 'func_spd']),
                ),
            ]
        )
        self.add_row(
            title="Flash 2x100w",
            note="8 Ch",
            icon="flash.png",
            channels_groups=[
                FixtureChannelsGroup(
                    title="Группа #1",
                    param_list=_make_param_list(
                        ['dimmer', 'strobe', 'func', 'func_spd', 'white',
                         'amber', 'white', 'amber']),
                ),
            ]
        )

    def get_default_row(self) -> RowFixtureParam:
        return self.rows[next(iter(self.rows))]
