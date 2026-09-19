from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from pathlib import Path
import shutil
from kivy.core.text import Label as CoreLabel
from kivy.properties import ObjectProperty, ListProperty, StringProperty
from kivy.graphics import Rectangle, Color
from typing import List
from misc import logger
from misc import constants
from libs.mouse_manager import cursor_manager
from libs.sdl2_keyboard import KeyboardBehavior
from libs.kivy_patches import builder_sync, on_touch_double_tap, recycle
import libs.uix.filelist
import libs.uix.recycle_restricted_scrollview
import sys
from libs.sub_proc import exit_code


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
    error_msg = StringProperty("")

    def on_kv_post(self, _):
        if constants.DATABASE_BACKUPS_PATH.is_dir():
            self.filelist.rootpath = constants.DATABASE_BACKUPS_PATH
            self.filelist.bind(on_submit=self.on_filelist_submit)
        else:
            self.error_msg = "Отсутствует директория с резервными копиями"

    def on_filelist_submit(self, filelist, path: Path):
        database_dir = constants.DATABASE_PATH
        backup_dir = constants.DATABASE_BACKUPS_PATH
        if database_dir.is_dir():
            logger.info("Удаление текущей версии БД")
            shutil.rmtree(database_dir)
        logger.info(f"Распаковка архива БД {path}")
        shutil.unpack_archive(path, database_dir, constants.DATABASE_BACKUPS_ARCHIVE_FORMAT)

        sys.exit(exit_code.EXIT_RESTART)


class BackupApp(KeyboardBehavior, App):
    use_kivy_settings = False
    root = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        builder_sync.apply_patch()
        on_touch_double_tap.apply_patch()
        recycle.apply_patch()

        self.__register_fonts()
        cursor_manager.init()
        c = constants
        self.title = f"{c.APP_NAME} v.{c.VERSION}{c.SUB_VERSION} (BACKUP MODE)"

    def build(self):
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
                sys.exit(1)

    def open_settings(self, *largs):
        """
                Отключение меню настроек на F1
        """
        pass
