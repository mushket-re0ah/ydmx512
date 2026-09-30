from multiprocessing import Process, Queue
from typing import Any, Callable, Dict, NamedTuple, Optional, Tuple

from typing_extensions import TypeAlias

from libs import logger
from libs.sub_proc.exit_code import ExitCode

AsyncProcessCallback: TypeAlias = Callable[[Any], None]
AsyncProcessTarget: TypeAlias = Callable[..., ExitCode]


class AsyncProcessContext(NamedTuple):
    module: str
    process_target: AsyncProcessTarget
    callback: Optional[AsyncProcessCallback]
    block_gui: bool
    process_args: Dict[str, Any]


def run_async_process(context: AsyncProcessContext):
    process, process_queue = _start_process(context)
    _block_gui(context.block_gui, process)
    _wait_for_process_result(context, process, process_queue)


def _block_gui(block_gui: bool, process: Process):
    if block_gui:
        from libs.sub_proc import _modal_block
        _modal_block.start(process)


def _unblock_gui(block_gui: bool):
    if block_gui:
        from libs.sub_proc import _modal_block
        _modal_block.stop()


def _wait_for_process_result(context: AsyncProcessContext,
                             process: Process,
                             process_queue: Queue[Any]):
    from kivy.clock import Clock
    def wait_result(_):
        if not process.is_alive():
            result = ExitCode.FAILURE
            if process.exitcode == ExitCode.SUCCESS:
                result = _handle_success(context.module, process, process_queue)
            elif process.exitcode == ExitCode.FAILURE:
                _handle_failure(context.module, process, process_queue)
                result = None
            if context.callback is not None:
                context.callback(result)
            clock.cancel()
            process_queue.close()
            _unblock_gui(context.block_gui)
    clock = Clock.schedule_interval(wait_result, 0.1)


def _handle_success(module: str, process: Process, process_queue: Queue[Any]) -> Any:
    result = None if process_queue.empty() else process_queue.get_nowait()
    logger.info(f"[{module}]: success {process}, result={result}")
    return result


def _handle_failure(module: str, process: Process, process_queue: Queue[Any]):
    trace = process_queue.get_nowait()
    logger.error(f"[{module}]: failure {process}, trace={trace}")


def _start_process(context: AsyncProcessContext) -> Tuple[Process, Queue[Any]]:
    process_queue: Queue[Any] = Queue()

    process = Process(
        target=context.process_target,
        kwargs={"queue": process_queue, **context.process_args},
        daemon=True
    )
    process.start()
    logger.info(f"[{context.module}]: start process {process}")
    return (process, process_queue)


def open_file(callback: AsyncProcessCallback, **kwargs: Any):
    from libs.sub_proc import _open_file

    run_async_process(
        AsyncProcessContext(
            module="OPEN_FILE",
            process_target=_open_file.start,
            callback=callback,
            block_gui=True,
            process_args=kwargs
        )
    )


def open_dir(callback: Callable, **kwargs):
    raise NotImplementedError
    from libs.sub_proc import _open_dir

    run_async_process(
        AsyncProcessContext(
            module="OPEN_DIR",
            process_target=_open_dir.start,
            callback=callback,
            block_gui=True,
            process_args=kwargs
        )
    )


def save_file(callback: Callable, **kwargs):
    raise NotImplementedError
    from libs.sub_proc import _save_file

    run_async_process(
        AsyncProcessContext(
            module="SAVE_FILE",
            process_target=_save_file.start,
            callback=callback,
            block_gui=True,
            process_args=kwargs
        )
    )
