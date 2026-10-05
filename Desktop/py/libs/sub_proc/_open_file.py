import platform
import sys
from multiprocessing import Queue
from typing import Any, List, Optional, Tuple

from libs.sub_proc.exit_code import ExitCode


def start(
        queue: Queue[Any],
        path: Optional[str],
        multiple: bool,
        filters: Tuple[str, ...],
        title: Optional[str],
        icon: Optional[str],
        preview: bool,
        show_hidden: bool
    ):
    def _on_selection(paths: List[str]):
        queue.put(paths if multiple else (paths[0] if paths else None))

    try:
        from plyer import filechooser
        kwargs = {
            "path": path,
            "multiple": multiple,
            "filters": filters,
            "preview": preview,
            "title": title,
            "icon": icon,
            "show_hidden": show_hidden,
            "on_selection": _on_selection
        }

        if platform.system() != "Windows":
            kwargs.pop("title")

        path = filechooser.open_file(**kwargs)
        sys.exit(ExitCode.SUCCESS)
    except Exception:
        import traceback
        queue.put(traceback.format_exc())
        sys.exit(ExitCode.FAILURE)
