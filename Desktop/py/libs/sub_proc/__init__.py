import os
import threading
from multiprocessing import Pipe, Process, Queue
from multiprocessing.connection import Connection
from typing import Any, Callable, Dict, NamedTuple, Optional, Tuple, Union

from typing_extensions import TypeAlias

from libs import logger
from libs.sub_proc.exit_code import ExitCode
from libs.sub_proc.ipc import PROCESS_CANCEL_MSG

AsyncProcessCallback: TypeAlias = Callable[[Any], None]
AsyncProcessTarget: TypeAlias = Callable[..., ExitCode]
AsyncProcessStopHandler: TypeAlias = Callable[[], None]


def _default_stop_handler():
    os._exit(ExitCode.CANCELLED)


class AsyncProcessContext(NamedTuple):
    module: str
    process_target: AsyncProcessTarget
    callback: Optional[AsyncProcessCallback]
    block_gui: bool
    process_args: Dict[str, Any]
    stop_handler: AsyncProcessStopHandler = _default_stop_handler


def run_async_process(context: AsyncProcessContext):
    process, process_queue, send_connection = _start_process(context)
    _block_gui(context.block_gui, process, send_connection)
    _wait_for_process_result(context, process, process_queue, send_connection)


def _block_gui(
        block_gui: bool,
        process: Process,
        send_connection: Connection
    ):
    if block_gui:
        from libs.sub_proc import _modal_block
        _modal_block.start(process, send_connection)


def _unblock_gui(block_gui: bool):
    if block_gui:
        from libs.sub_proc import _modal_block
        _modal_block.stop()


def _wait_for_process_result(
        context: AsyncProcessContext,
        process: Process,
        process_queue: "Queue[Any]",
        send_connection: Connection
    ):
    from kivy.clock import Clock
    def wait_result(_:Any):
        if not process.is_alive():
            result = None
            if process.exitcode == ExitCode.SUCCESS:
                result = _handle_success(context.module, process, process_queue)
            elif process.exitcode == ExitCode.FAILURE:
                _handle_failure(context.module, process, process_queue)
                result = None
            elif process.exitcode == ExitCode.CANCELLED:
                _handle_cancelled(context.module, process, process_queue)
                result = None
            else:
                _handle_undefined(context.module, process, process_queue)
                result = None
            clock.cancel()
            process_queue.close()
            send_connection.close()
            _unblock_gui(context.block_gui)
            if context.callback is not None:
                context.callback(result)
    clock = Clock.schedule_interval(wait_result, 0.1)


def _handle_success(module: str, process: Process, process_queue: "Queue[Any]") -> Any:
    result = None if process_queue.empty() else process_queue.get_nowait()
    logger.info(f"[{module}]: success {process}, result={result}")
    return result


def _handle_failure(module: str, process: Process, process_queue: "Queue[Any]"):
    trace = None if process_queue.empty() else process_queue.get_nowait()
    logger.error(f"[{module}]: failure {process}, trace={trace}")


def _handle_cancelled(module: str, process: Process, process_queue: "Queue[Any]"):
    logger.info(f"[{module}]: cancelled {process}")


def _handle_undefined(module: str, process: Process, process_queue: "Queue[Any]"):
    logger.error(f"[{module}]: undefined {process}, exitcode={process.exitcode}")


def _start_process(context: AsyncProcessContext) -> Tuple[Process, "Queue[Any]", Connection]:
    process_queue: "Queue[Any]" = Queue()  # noqa: UP037
    recv_connection, send_connection = Pipe(duplex=False)

    process = Process(
        target=wrapped_target,
        kwargs={
            "queue": process_queue,
            "recv_connection": recv_connection,
            "stop_handler": context.stop_handler,
            "module": context.module,
            "process_target": context.process_target,
            "process_args": context.process_args,
        },
        daemon=True
    )
    process.start()
    recv_connection.close()
    logger.info(f"[{context.module}]: start process {process}")
    return (process, process_queue, send_connection)


def wrapped_target(
        queue: "Queue[Any]",
        recv_connection: Connection,
        stop_handler: AsyncProcessStopHandler,
        module: str,
        process_target: AsyncProcessTarget,
        process_args: Dict[str, Any]
    ) -> Any:
    logger.init()
    threading.Thread(
        target=_stop_listener,
        args=(recv_connection, stop_handler, module),
        daemon=True
    ).start()
    return process_target(queue=queue, **process_args)


def _stop_listener(
        recv_connection: Connection,
        stop_handler: AsyncProcessStopHandler,
        module: str
    ):
    try:
        msg = recv_connection.recv()
    except (EOFError, OSError):
        return
    if msg != PROCESS_CANCEL_MSG:
        logger.warning(f"[{module}]: recv unrecognized message {msg}")
        return
    try:
        logger.info(f"[{module}]: cancel requested")
        stop_handler()
    except Exception:
        logger.error(f"[{module}]: stop handler failed", exc_info=True)


def open_file(
        callback: AsyncProcessCallback,
        path: Optional[str]=None,
        multiple: bool=False,
        filters: Optional[Union[Tuple[str, ...], Tuple[Tuple[str, ...], ...]]]=None,
        title: Optional[str]=None,
        icon: Optional[str]=None,
        preview: bool=False,
        show_hidden: bool=False,
    ):
    from libs.sub_proc import _open_file
    if filters is None:
        filters = tuple()

    run_async_process(
        AsyncProcessContext(
            module="OPEN_FILE",
            process_target=_open_file.start,
            callback=callback,
            block_gui=True,
            process_args={
                "path": path,
                "multiple": multiple,
                "filters": filters,
                "preview": preview,
                "title": title,
                "icon": icon,
                "show_hidden": show_hidden
            }
        )
    )


# def open_dir(callback: Callable, **kwargs:Any):
#     raise NotImplementedError
#     from libs.sub_proc import _open_dir

#     run_async_process(
#         AsyncProcessContext(
#             module="OPEN_DIR",
#             process_target=_open_dir.start,
#             callback=callback,
#             block_gui=True,
#             process_args=kwargs
#         )
#     )


# def save_file(callback: Callable, **kwargs):
#     raise NotImplementedError
#     from libs.sub_proc import _save_file

#     run_async_process(
#         AsyncProcessContext(
#             module="SAVE_FILE",
#             process_target=_save_file.start,
#             callback=callback,
#             block_gui=True,
#             process_args=kwargs
#         )
#     )
