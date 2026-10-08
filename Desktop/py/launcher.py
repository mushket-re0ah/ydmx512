import os
import subprocess
import sys
import threading
import time
from typing import TextIO

from libs import logger
from libs.sub_proc.exit_code import ExitCode
from misc import constants


def print_output(pipe: TextIO):
    for line in iter(pipe.readline, ''):
        if line:
            line = line.rstrip()  # Убираем \n
            if line:
                print(line)
                sys.stdout.flush()

def run_kivy_app(do_exec_backup_menu: bool) -> int:
    env = os.environ.copy()
    if do_exec_backup_menu:
        env[constants.BACKUP_MENU_ENV_KEY] = constants.BACKUP_MENU_ENV_KEY_TRUE
    else:
        env[constants.BACKUP_MENU_ENV_KEY] = constants.BACKUP_MENU_ENV_KEY_FALSE
    with subprocess.Popen(
            [sys.executable, "-u", constants.APP_FILENAME],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
            encoding="utf-8",
            env=env
        ) as process:

        output_thread = threading.Thread(
            target=print_output,
            args=(process.stdout,),
            daemon=True
        )
        output_thread.start()

        process.wait()
        return process.returncode


if __name__ == "__main__":
    logger.init(constants.LOGS_PATH, constants.MAX_LOG_FILES)
    exec_backup_menu = False
    while True:
        try:
            logger.info("Запуск kivy...")
            kivy_exit_code = run_kivy_app(exec_backup_menu)
            logger.info(f"Процесс kivy завершен с кодом {kivy_exit_code}")
            if kivy_exit_code == ExitCode.FAILURE and exec_backup_menu:
                logger.info(f"Крах Backup Menu (exit code: {kivy_exit_code}.")
                time.sleep(3)
                sys.exit(ExitCode.FAILURE)
            exec_backup_menu = False
            if kivy_exit_code == ExitCode.SUCCESS:
                logger.info("Процесс kivy успешно завершен")
                os._exit(ExitCode.SUCCESS)
            elif kivy_exit_code == ExitCode.RESTART:
                logger.info("Перезапуск kivy")
            else:
                logger.info(f"Крах Kivy (exit code: {kivy_exit_code})")
                exec_backup_menu = True
        except Exception as e:
            logger.info(f"Ошибка в лаунчере: {e}. Смерть через 3 секунды.")
            time.sleep(3)
            sys.exit(ExitCode.FAILURE)
