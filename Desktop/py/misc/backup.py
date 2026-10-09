import sys
from multiprocessing import Queue
from pathlib import Path
from typing import Any, List, Optional

from libs.sub_proc import AsyncProcessCallback, AsyncProcessContext, run_async_process
from libs.sub_proc.exit_code import ExitCode
from misc import constants


def do_backup(
        callback: Optional[AsyncProcessCallback]=None,
        do_clean_backups: bool=True
    ):
    from database import db

    run_async_process(
        AsyncProcessContext(
            module="BACKUP",
            process_target=_start,
            callback=callback,
            block_gui=False,
            process_args={
                "backup_max_count": db.misc.database_backup_max_count,
                "do_clean_backups": do_clean_backups
            }
        )
    )


def _start(queue: "Queue[Any]", backup_max_count: int, do_clean_backups: bool):
    try:
        _create_backup_dir()
        _create_backup()
        if do_clean_backups:
            _clean_old_backups(backup_max_count)
        queue.put(True)
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
    backups = get_backups()
    if len(backups) > backup_max_count:
        for old_backup in backups[:len(backups) - backup_max_count]:
            try:
                old_backup.unlink()
            except Exception as e:
                print(f"Error deleting {old_backup}: {e}")


def get_backups() -> List[Path]:
    backup_dir = constants.DATABASE_BACKUPS_PATH
    return sorted(
        backup_dir.glob(f"*{constants.DATABASE_BACKUPS_ARCHIVE_EXTENSION}"),
        key=lambda f: f.stat().st_mtime
    )


_pending_restore_path: Optional[Path] = None


def schedule_restore(path: Path):
    global _pending_restore_path
    _pending_restore_path = path


def apply_pending_restore():
    global _pending_restore_path

    path = _pending_restore_path
    _pending_restore_path = None

    if path is None:
        return

    import shutil
    import tempfile

    path = path.resolve(strict=True)
    backup_dir = constants.DATABASE_BACKUPS_PATH.resolve(strict=True)

    if (
        path.parent != backup_dir
        or not path.is_file()
        or not path.name.endswith(
            constants.DATABASE_BACKUPS_ARCHIVE_EXTENSION
        )
    ):
        raise ValueError(f"Недопустимый архив резервной копии: {path}")

    database_path = constants.DATABASE_PATH

    with tempfile.TemporaryDirectory(
        prefix=".database_restore_",
        dir=constants.SCRIPT_DIR,
    ) as temp:
        temp_path = Path(temp)
        extracted_path = temp_path / "extracted"
        previous_path = temp_path / "previous"
        extracted_path.mkdir()

        shutil.unpack_archive(
            str(path),
            str(extracted_path),
            constants.DATABASE_BACKUPS_ARCHIVE_FORMAT,
        )

        if not any(extracted_path.iterdir()):
            raise ValueError(f"Архив БД пуст: {path}")

        if database_path.exists():
            database_path.replace(previous_path)

        try:
            extracted_path.replace(database_path)
        except Exception:
            if previous_path.exists() and not database_path.exists():
                previous_path.replace(database_path)
            raise
