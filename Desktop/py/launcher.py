import subprocess
import threading
import time
import sys
import os
from libs.sub_proc import exit_code
from misc import constants
from libs import logger
from pathlib import Path

# Определяем директорию, где находится скрипт или исполняемый файл
if getattr(sys, "frozen", False):
    # Для Nuitka или PyInstaller
    SCRIPT_DIR = Path(sys.executable).parent
else:
    # Для обычного Python-скрипта
    SCRIPT_DIR = Path(__file__).parent

APP_FILENAME = SCRIPT_DIR / "app_start.py"


def print_output(pipe):
    for line in iter(pipe.readline, ''):
        if line:
            line = line.rstrip()  # Убираем \n
            if line:
                print(line)
                sys.stdout.flush()


def run_kivy_app(exec_backup_menu: bool):
    env = os.environ.copy()
    if exec_backup_menu:
        env[constants.BACKUP_MENU_ENV_KEY] = constants.BACKUP_MENU_ENV_KEY_TRUE
    else:
        env[constants.BACKUP_MENU_ENV_KEY] = constants.BACKUP_MENU_ENV_KEY_FALSE
    process = subprocess.Popen([sys.executable, "-u", APP_FILENAME],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               bufsize=1,
                               universal_newlines=True,
                               encoding="utf-8",
                               env=env)
    output_thread = threading.Thread(target=print_output, args=(process.stdout,))
    # output_thread.daemon = True
    output_thread.start()

    process.wait()
    output_thread.join()
    process.stdout.close()
    return process.returncode


if __name__ == "__main__":
    from misc import constants
    logger.init(constants.LOGS_PATH, constants.MAX_LOG_FILES, constants.SESSION_LOG_ENV_KEY)
    logger.info("Лаунчер запущен")
    exec_backup_menu = False
    while True:
        try:
            logger.info("Запуск kivy...")
            kivy_exit_code = run_kivy_app(exec_backup_menu)
            logger.info(f"Процесс kivy завершен с кодом {kivy_exit_code}")
            if kivy_exit_code == exit_code.EXIT_FAILURE and exec_backup_menu:
                logger.info(f"Крах Backup Menu (exit code: {kivy_exit_code}. Смерть через 3 секунды.")
                time.sleep(3)
                sys.exit(exit_code.EXIT_FAILURE)
            exec_backup_menu = False
            if kivy_exit_code == exit_code.EXIT_SUCCESS:
                logger.info(f"Процесс kivy успешно завершен")
                sys.exit(exit_code.EXIT_SUCCESS)
            elif kivy_exit_code == exit_code.EXIT_RESTART:
                logger.info(f"Перезапуск kivy")
            else:
                logger.info(f"Крах Kivy (exit code: {kivy_exit_code})")
                exec_backup_menu = True
        except Exception as e:
            logger.info(f"Ошибка в лаунчере: {e}. Смерть через 3 секунды.")
            time.sleep(3)
            sys.exit(exit_code.EXIT_FAILURE)

# from kivy.app import App
# from kivy.lang import Builder
# from kivy.properties import ObjectProperty
# from kivy.uix.boxlayout import BoxLayout
# from libs import sdl2_keyboard
# from libs.uix.map_layout import *
# from libs.mouse_manager import cursor_manager


# class TestGridWidget(MapGridItemBehavior, BoxLayout):
#     pass


# Builder.load_string("""
# <TestGridWidget>:
#     size_hint: (None, None)
#     canvas:
#         Color:
#             rgba: (1, 0, 0, 1)
#         Rectangle:
#             size: self.size
#             pos: self.pos

# <Root>:
#     map_layout: map_layout
#     w1: w1
#     w2: w2
#     padding: (40, 40, 40, 40)
#     MyMapLayout:
#         id: map_layout
#         grid_padding: [8, 8, 8, 8]
#         grid_spacing_size: [4, 4]
#         cell_size: [16, 16]
#         # grid_inversion_y: True
#         max_grid_size: [24, 24]
#         selectable: False
#         TestGridWidget:
#             id: w1
#             grid_size: [3, 3]
#             grid_pos: [0, 0]
#             selectable: True
#         TestGridWidget:
#             id: w2
#             grid_size: [3, 3]
#             grid_pos: [0, 3]
#             selectable: True
#         TestGridWidget:
#             id: w3
#             grid_size: [3, 3]
#             grid_pos: [3, 0]
#             selectable: True
# """
# )


# class Root(BoxLayout):
#     w1 = ObjectProperty()
#     map_layout = ObjectProperty()

#     def on_kv_post(self, _):
#         # self.map_layout.move_grid_item(self.w1, 2, 2)
#         # self.map_layout.remove_widget(self.w2)
#         pass


# class Test(App):
#     def build(self):
#         return Root()

# if __name__ == "__main__":
#     sdl2_keyboard.init()
#     cursor_manager.init()
#     from libs.mouse_manager.hover import HoverBehavior
#     Test().run()
