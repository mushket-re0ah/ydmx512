"""
    Модуль, предназначенный для логгирования. Работает на уровне конкретного
процесса и не позволяет внутри одного процесса иметь несколько потоков
логгирования.
"""
from datetime import datetime
from misc import constants
import logging
import os


LEVEL = logging.DEBUG
FILEPATH = None
LOG = None


def init():
    global FILEPATH
    global LEVEL
    global LOG

    constants.LOGS_PATH.mkdir(exist_ok=True)
    clean_old_logs()

    if LOG:
        for handler in LOG.handlers[:]:
            handler.close()
            LOG.removeHandler(handler)

    log_filepath_env = os.environ.get(constants.SESSION_LOG_ENV_KEY)
    if log_filepath_env:
        FILEPATH = constants.LOGS_PATH / log_filepath_env
        info_msg = f"Продолжение сеанса logging в {log_filepath_env}"
    else:
        filename = datetime.now().strftime("%d-%m-%Y_%H.%M.%S.log")
        os.environ[constants.SESSION_LOG_ENV_KEY] = filename
        FILEPATH = constants.LOGS_PATH / filename
        info_msg = f"Новый сеанс logging в {filename}"

    LOG = logging.getLogger()
    LOG.setLevel(LEVEL)
    LOG.propagate = False

    file_handler = logging.FileHandler(FILEPATH, mode="a", encoding="utf-8", delay=False)
    formatter = logging.Formatter("%(asctime)s : [%(levelname)s] : %(message)s")
    file_handler.setFormatter(formatter)
    LOG.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(LEVEL)
    stream_handler.setFormatter(formatter)
    LOG.addHandler(stream_handler)

    LOG.info(info_msg)


def clean_old_logs():
    log_files = sorted(constants.LOGS_PATH.glob("*.log"),
                       key=lambda f: f.stat().st_mtime)
    if len(log_files) > constants.MAX_LOG_FILES:
        files_to_remove = log_files[:len(log_files) - constants.MAX_LOG_FILES]
        for file in files_to_remove:
            try:
                file.unlink()
            except BaseException:
                pass


def set_level(level: int):
    LOG.setLevel(level)


def debug(*args):
    global LOG
    LOG.debug(", ".join([str(i) for i in args]))


def info(*args):
    global LOG
    LOG.info(", ".join([str(i) for i in args]))


def warning(*args, exc_info=None):
    global LOG
    LOG.warning(", ".join([str(i) for i in args]), exc_info=exc_info)


def error(*args, exc_info=None):
    global LOG
    LOG.error(", ".join([str(i) for i in args]), exc_info=exc_info)


def critical(*args, exc_info=None):
    global LOG
    LOG.critical(", ".join([str(i) for i in args]), exc_info=exc_info)
