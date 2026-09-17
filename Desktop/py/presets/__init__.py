def init():
    from presets.fixture_presets import FixturePresetsManager
    globals()["fixture_preset_manager"] = FixturePresetsManager()
    from presets.param_presets import ParamPresetsManager
    globals()["param_preset_manager"] = ParamPresetsManager()
