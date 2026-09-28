fixture_preset_manager = None
param_preset_manager = None
def init():
    global fixture_preset_manager
    global param_preset_manager
    from presets.fixture_presets import FixturePresetsManager
    fixture_preset_manager = FixturePresetsManager()
    from presets.param_presets import ParamPresetsManager
    param_preset_manager = ParamPresetsManager()
