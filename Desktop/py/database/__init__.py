from typing import TYPE_CHECKING

from libs.kivy_json_orm.database import Database
from misc import backup, constants

if TYPE_CHECKING:
    from database.brand import TableBrand
    from database.desktop_uix import TableDesktopUix
    from database.fixture import TableFixture
    from database.fixture_param import TableFixtureParam
    from database.mdi_manager import TableMDIManager
    from database.mdi_window import TableMDIWindow
    from database.misc import TableMisc
    from database.patch import TablePatch
    from database.phase_curve_type import TablePhaseCurveType
    from database.playback import TablePlayback
    from database.scene import TableScene

    class YdmxDatabase(Database):
        misc: "TableMisc"
        brand: "TableBrand"
        fixture_param: "TableFixtureParam"
        fixture: "TableFixture"
        scene: "TableScene"
        patch: "TablePatch"
        phase_curve_type: "TablePhaseCurveType"
        playback: "TablePlayback"
        mdi_window: "TableMDIWindow"
        mdi_manager: "TableMDIManager"
        desktop_uix: "TableDesktopUix"
else:
    YdmxDatabase = Database


db: YdmxDatabase
SCENE_TABLES_ORDER = ("patch", "playback", "desktop_uix")
def create_database():
    global db
    db = YdmxDatabase(constants.DATABASE_PATH, None, None, backup.do_backup)
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
