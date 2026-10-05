"""
    Модуль, предназначенный для логгирования. Работает на уровне конкретного
процесса и не позволяет внутри одного процесса иметь несколько потоков
логгирования.
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from misc import constants

_logger: Optional[logging.Logger] = None
def init(
        logs_dir: Optional[Path]=None,
        max_log_files: Optional[int]=None,
        session_env_key: str=constants.SESSION_LOG_ENV_KEY):
    global _logger
    if _logger is not None:
        for handler in _logger.handlers[:]:
            handler.close()
            _logger.removeHandler(handler)

    log_filepath_env = os.environ.get(session_env_key, None)
    if log_filepath_env is None:
        if logs_dir is None:
            raise ValueError()
        if max_log_files is None:
            raise ValueError()
        logs_dir.mkdir(exist_ok=True)
        clean_old_logs(logs_dir, max_log_files)

        filename = datetime.now().strftime("%d-%m-%Y_%H.%M.%S.log")
        filepath = logs_dir / filename
        os.environ[session_env_key] = str(filepath)
        info_msg = f"Новый сеанс logging в {filename}"
    else:
        filepath = Path(log_filepath_env)
        # info_msg = f"Продолжение сеанса logging в {filepath.name}"
        info_msg = None

    _logger = logging.getLogger()
    _logger.setLevel(constants.LOG_LEVEL)
    _logger.propagate = False

    file_handler = logging.FileHandler(filepath, mode="a", encoding="utf-8", delay=False)
    formatter = logging.Formatter("%(asctime)s : [%(levelname)s] : %(message)s")
    file_handler.setFormatter(formatter)
    _logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(constants.LOG_LEVEL)
    stream_handler.setFormatter(formatter)
    _logger.addHandler(stream_handler)

    if info_msg is not None:
        _logger.info(info_msg)


def clean_old_logs(logs_dir: Path, max_log_files: int):
    log_files = sorted(logs_dir.glob("*.log"),
                       key=lambda f: f.stat().st_mtime)
    if len(log_files) > max_log_files:
        files_to_remove = log_files[:len(log_files) - max_log_files]
        for file in files_to_remove:
            try:
                file.unlink(missing_ok=True)
            except OSError:
                pass


def set_level(level: int):
    _get_logger().setLevel(level)


def debug(*args: Any) -> None:
    _get_logger().debug(", ".join(str(i) for i in args))


def info(*args: Any) -> None:
    _get_logger().info(", ".join(str(i) for i in args))


def warning(*args: Any, exc_info:bool=False) -> None:
    _get_logger().warning(", ".join(str(i) for i in args), exc_info=exc_info)


def error(*args: Any, exc_info:bool=False) -> None:
    _get_logger().error(", ".join(str(i) for i in args), exc_info=exc_info)


def critical(*args: Any, exc_info:bool=False) -> None:
    _get_logger().critical(", ".join(str(i) for i in args), exc_info=exc_info)


def _get_logger() -> logging.Logger:
    if _logger is None:
        raise RuntimeError("Logging is not initialized")
    return _logger
