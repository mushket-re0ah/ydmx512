import sys
from multiprocessing import Queue
from pathlib import Path
from typing import Any, List, Optional

from libs.sub_proc import AsyncProcessCallback, AsyncProcessContext, run_async_process
from libs.sub_proc.exit_code import ExitCode
from misc import constants


def do_backup(callback: Optional[AsyncProcessCallback]=None):
    from database import db

    run_async_process(
        AsyncProcessContext(
            module="BACKUP",
            process_target=_start,
            callback=callback,
            block_gui=False,
            process_args={
                "backup_max_count": db.misc.database_backup_max_count
            }
        )
    )


def _start(queue: "Queue[Any]", backup_max_count: int):
    try:
        _create_backup_dir()
        _create_backup()
        _clean_old_backups(backup_max_count)
        sys.exit(ExitCode.SUCCESS)
    except Exception:
        import traceback
        queue.put(traceback.format_exc())
        sys.exit(ExitCode.FAILURE)


def _create_backup():
    import shutil
    shutil.make_archive(
        _get_backup_filename(),
        constants.DATABASE_BACKUPS_ARCHIVE_FORMAT,
        constants.DATABASE_PATH
    )


def _create_backup_dir():
    constants.DATABASE_BACKUPS_PATH.mkdir(exist_ok=True)


def _get_backup_filename() -> str:
    from datetime import datetime
    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    return str(constants.DATABASE_BACKUPS_PATH / timestamp)


def _clean_old_backups(backup_max_count: int):
    backups = _get_backups()
    if len(backups) > backup_max_count:
        for old_backup in backups[:len(backups) - backup_max_count]:
            try:
                old_backup.unlink()
            except Exception as e:
                print(f"Error deleting {old_backup}: {e}")


def _get_backups() -> List[Path]:
    backup_dir = constants.DATABASE_BACKUPS_PATH
    return sorted(
        backup_dir.glob(f"*{constants.DATABASE_BACKUPS_ARCHIVE_EXTENSION}"),
        key=lambda f: f.stat().st_mtime
    )
