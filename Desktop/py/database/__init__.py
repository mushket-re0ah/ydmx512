from libs.kivy_json_orm.database import Database
from misc import backup, constants

db = None
SCENE_TABLES_ORDER = ("patch", "playback", "desktop_uix")
def create_database():
    global db
    db = Database(constants.DATABASE_PATH, None, None, backup.do_backup)
    from database.misc import TableMisc
    db.register("misc", TableMisc())
    from database.brand import TableBrand
    db.register("brand", TableBrand())
    from database.fixture_param import TableFixtureParam
    db.register("fixture_param", TableFixtureParam())
    from database.fixture import TableFixture
    db.register("fixture", TableFixture())
    from database.scene import TableScene
    db.register("scene", TableScene(SCENE_TABLES_ORDER))
    from database.patch import TablePatch
    db.register("patch", TablePatch())
    from database.phase_curve_type import TablePhaseCurveType
    db.register("phase_curve_type", TablePhaseCurveType())
    from database.playback import TablePlayback
    db.register("playback", TablePlayback())
    from database.mdi_window import TableMDIWindow
    db.register("mdi_window", TableMDIWindow())
    from database.mdi_manager import TableMDIManager
    db.register("mdi_manager", TableMDIManager())
    from database.desktop_uix import TableDesktopUix
    db.register("desktop_uix", TableDesktopUix())

    db.init()

    db.save_interval = db.misc.database_save_interval
    db.backup_interval = db.misc.database_backup_interval
    db.misc.bind(database_save_interval=db.setter("save_interval"))
    db.misc.bind(database_backup_interval=db.setter("backup_interval"))
