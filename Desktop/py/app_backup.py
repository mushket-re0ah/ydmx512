import shutil
import sys
from pathlib import Path
from typing import Any

from kivy.app import App
from kivy.core.text import Label as CoreLabel
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from typing_extensions import Self

from libs import logger
from libs.kivy_patches import builder_sync, on_touch_double_tap, recycle
from libs.mouse_manager import cursor_manager
from libs.sdl2_keyboard import KeyboardBehavior
from libs.sub_proc.exit_code import ExitCode
from libs.uix.filelist import Filelist  # lazy kv import initialize
from misc import constants

Builder.load_string(
"""
#:import cs misc.colorscheme
#:import constants misc.constants
#:import imgs_path misc.imgs_path

<Root>:
    filelist: filelist

    orientation: "vertical"

    RestrictedLabel:
        text: "Произошла критическая ошибка при работе приложения (подробнее смотрите в последнем файле логов). Выберите версию программы, к которой хотите откатиться."
        size_hint: (1, None)
        text_size: self.width, None
        height: self.texture_size[1]
        halign: "center"

    RestrictedLabel:
        text: root.error_msg
        size_hint: (1, None)
        height: "50dp" if root.error_msg else 0

    Filelist:
        id: filelist
        size_hint: (1, 1)
        filters: ["gz"]
""")


class Root(BoxLayout):
    error_msg: str = StringProperty("")
    filelist: Filelist = ObjectProperty()

    def on_kv_post(self, base_widget: Self):
        if constants.DATABASE_BACKUPS_PATH.is_dir():
            self.filelist.rootpath = constants.DATABASE_BACKUPS_PATH
            self.filelist.bind(on_submit=self.on_filelist_submit)
        else:
            self.error_msg = "Отсутствует директория с резервными копиями"

    def on_filelist_submit(self, _: Filelist, path: Path):
        database_dir = constants.DATABASE_PATH
        if database_dir.is_dir():
            logger.info("Удаление текущей версии БД")
            shutil.rmtree(database_dir)
        logger.info(f"Распаковка архива БД {path}")
        shutil.unpack_archive(path, database_dir, constants.DATABASE_BACKUPS_ARCHIVE_FORMAT)

        sys.exit(ExitCode.RESTART)


class BackupApp(KeyboardBehavior, App):
    use_kivy_settings = False
    root: Root = ObjectProperty()

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        builder_sync.apply_patch()
        on_touch_double_tap.apply_patch()
        recycle.apply_patch()

        self.__register_fonts()
        cursor_manager.init()
        c = constants
        self.title = f"{c.APP_NAME} v.{c.VERSION}{c.SUB_VERSION} (BACKUP MODE)"

    def build(self) -> Root:
        self.root = Root()
        return self.root

    def __register_fonts(self):
        for name, file in (
                ("Ebrima", "ebrima.ttf"),
                ("Arial", "arial.ttf"),
                ("Roboto Mono", "robotomono.ttf"),
                ("Calibri", "calibri.ttf"),
            ):
            try:
                CoreLabel.register(name, (constants.FONTS_PATH / file).as_posix())
            except Exception:
                logger.error(f"Failed to register font '{name}'", exc_info=True)
                sys.exit(ExitCode.FAILURE)

    def open_settings(self, *_):
        """
                Отключение меню настроек на F1
        """
        return
