from misc import logger, exit_code
from typing import Callable, List, Tuple, NamedTuple


class AsyncProcessContext(NamedTuple):
    module: str
    process_target: Callable
    callback: Callable
    block_gui: bool
    process_kwargs: dict


def __run_async_process(context: AsyncProcessContext):
    process, process_queue = __start_process(context)
    __block_gui(context.block_gui, process)
    __wait_for_process_result(context, process, process_queue)


def __block_gui(block_gui: bool, process):
    if block_gui:
        from misc.sub_proc import _modal_block
        _modal_block.start(process)


def __unblock_gui(block_gui: bool):
    if block_gui:
        from misc.sub_proc import _modal_block
        _modal_block.stop()


def __wait_for_process_result(context: AsyncProcessContext,
                              process,
                              process_queue):
    from kivy.clock import Clock
    def wait_result(_):
        if not process.is_alive():
            if process.exitcode == exit_code.EXIT_SUCCESS:
                result = __handle_success(context.module, process, process_queue)
            elif process.exitcode == exit_code.EXIT_FAILURE:
                result = __handle_failure(context.module, process, process_queue)
            if context.callback:
                context.callback(result)
            clock.cancel()
            process_queue.close()
            __unblock_gui(context.block_gui)
    clock = Clock.schedule_interval(wait_result, 0.1)


def __handle_success(module: str, process, process_queue) -> any:
    result = None if process_queue.empty() else process_queue.get_nowait()
    logger.info(f"[{module}]: success {process}, result={result}")
    return result


def __handle_failure(module: str, process, process_queue) -> any:
    trace = process_queue.get_nowait()
    logger.error(f"[{module}]: failure {process}, trace={trace}")
    return None


def __start_process(context: AsyncProcessContext) -> Tuple["Process", "Queue"]:
    import multiprocessing
    import queue
    process_queue = multiprocessing.Queue()

    process = multiprocessing.Process(
            target=context.process_target,
            kwargs={"queue": process_queue, **context.process_kwargs},
            daemon=True
    )
    process.start()
    logger.info(f"[{context.module}]: start process {process}")
    return process, process_queue


def do_backup(callback: Callable):
    from misc.sub_proc import _backup
    from database import db

    __run_async_process(
        AsyncProcessContext(
            module="BACKUP",
            process_target=_backup.start,
            callback=callback,
            block_gui=False,
            process_kwargs={
                "backup_max_count": db.misc.database_backup_max_count
            }
        )
    )


def open_file(callback: Callable, **kwargs):
    from misc.sub_proc import _open_file

    __run_async_process(
        AsyncProcessContext(
            module="OPEN_FILE",
            process_target=_open_file.start,
            callback=callback,
            block_gui=True,
            process_kwargs=kwargs
        )
    )


def open_dir(callback: Callable, **kwargs):
    from misc.sub_proc import _open_dir

    __run_async_process(
        AsyncProcessContext(
            module="OPEN_DIR",
            process_target=_open_dir.start,
            callback=callback,
            block_gui=True,
            process_kwargs=kwargs
        )
    )


def save_file(callback: Callable, **kwargs):
    from misc.sub_proc import _save_file

    __run_async_process(
        AsyncProcessContext(
            module="SAVE_FILE",
            process_target=_save_file.start,
            callback=callback,
            block_gui=True,
            process_kwargs=kwargs
        )
    )
