import sys
from multiprocessing import Queue
from typing import Any, List, Optional

from libs.sub_proc.exit_code import ExitCode


def start(queue: Queue[Any],
          path: Optional[str]=None,
          multiple: bool=False,
          filters: Optional[List[str]]=None,
          preview: bool=True,
          title: Optional[str]=None,
          icon: Optional[str]=None,
          show_hidden: bool=False):
    def _on_selection(paths: List[str]):
        queue.put(paths if multiple else (paths[0] if paths else None))

    if filters is None:
        filters = []

    try:
        from plyer import filechooser
        path = filechooser.open_file(
            path=path,
            multiple=multiple,
            filters=filters,
            preview=preview,
            title=title,
            icon=icon,
            show_hidden=show_hidden,
            on_selection=_on_selection
        )
        sys.exit(ExitCode.SUCCESS)
    except Exception:
        import traceback
        queue.put(traceback.format_exc())
        sys.exit(ExitCode.FAILURE)
