from libs.sub_proc import exit_code
import sys
from typing import List


def start(queue: "multiprocessing.Queue",
          path: str=None,
          multiple: bool=False,
          filters: list=[],
          preview: bool=True,
          title: str=None,
          icon: str=None,
          show_hidden: bool=False):
    def _on_selection(paths: List[str]):
        queue.put(paths if multiple else (paths[0] if paths else None))

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
                    on_selection=_on_selection)
        sys.exit(exit_code.EXIT_SUCCESS)
    except Exception as e:
        import traceback
        queue.put(traceback.format_exc())
        sys.exit(exit_code.EXIT_FAILURE)
