import subprocess
import threading
import time
import sys
import os
from misc import exit_code
from misc import constants
from misc import logger
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
    logger.init()
    logger.info("Лаунчер запущен")
    exec_backup_menu = False
    logger.init()
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
