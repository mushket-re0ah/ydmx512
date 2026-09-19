"""
    Модуль, предназначенный для логгирования. Работает на уровне конкретного
процесса и не позволяет внутри одного процесса иметь несколько потоков
логгирования.
"""
from datetime import datetime
from misc import constants
from pathlib import Path
import logging
import os


LEVEL = logging.DEBUG
DIR = None
MAX_LOG_FILES = None
FILEPATH = None
LOG = None


def init(logs_dir: Path, max_log_files=10, session_env_key: str=None):
    if not isinstance(session_env_key, str):
        raise ValueError("session_env_key is not str")
    global FILEPATH
    global LEVEL
    global DIR
    global MAX_LOG_FILES
    global LOG
    DIR = logs_dir
    MAX_LOG_FILES = max_log_files

    logs_dir.mkdir(exist_ok=True)
    clean_old_logs()

    if LOG:
        for handler in LOG.handlers[:]:
            handler.close()
            LOG.removeHandler(handler)

    log_filepath_env = os.environ.get(session_env_key)
    if log_filepath_env:
        FILEPATH = logs_dir / log_filepath_env
        info_msg = f"Продолжение сеанса logging в {log_filepath_env}"
    else:
        filename = datetime.now().strftime("%d-%m-%Y_%H.%M.%S.log")
        os.environ[session_env_key] = filename
        FILEPATH = logs_dir / filename
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
    global DIR
    global MAX_LOG_FILES
    log_files = sorted(DIR.glob("*.log"),
                       key=lambda f: f.stat().st_mtime)
    if len(log_files) > MAX_LOG_FILES:
        files_to_remove = log_files[:len(log_files) - MAX_LOG_FILES]
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
