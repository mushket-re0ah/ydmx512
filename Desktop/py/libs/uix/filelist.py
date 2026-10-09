from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple, Type, Union

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import (
    BooleanProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
    VariableListProperty,
)
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.widget import Widget

from libs.uix.button import HoverButton
from libs.uix.recycle_restricted_scrollview import RecycleRestrictedScrollView
from libs.uix.scroll_layout import ScrollLayout

Builder.load_string("""
#:import uix_cs libs.uix.colorscheme

<FileListButton>:  # HoverButton
    halign: "left"
    valign: "center"
    text_size: self.size
    padding: ["8dp", 0, 0, 0]
    normal_background_color: uix_cs.FileListButton.dir_bg\
                            if self.is_dir_button else uix_cs.FileListButton.file_bg


<Filelist>:  # ScrollLayout
    size_hint: None, None

    scrollview: scrollview
    RecycleRestrictedScrollView:
        id: scrollview
        viewclass: root.viewclass
        scroll_by_content: True
        do_scroll_x: False
        do_scroll_by_element: True
        RecycleBoxLayout:
            size_hint: (1, None)
            orientation: "vertical"
            default_size_hint: (1, None)
            width: self.minimum_width
            height: self.minimum_height
            default_size: (None, root.cls_height)
            padding: root.box_padding
            spacing: root.box_spacing
"""
)

class FileListItemBehavior(RecycleDataViewBehavior):
    path: Path = ObjectProperty()
    filelist: "Filelist" = ObjectProperty()
    is_dir_button: bool = BooleanProperty(False)

    def on_release(self):
        if self.is_dir_button:
            self.filelist.path = self.path
        else:
            self.filelist.dispatch("on_submit", self.path)


class FileListButton(FileListItemBehavior, HoverButton):
    def __init__(self, **kwargs: Any):
        set_colors_ev = Clock.create_trigger(self.update_colors, 0)
        self.set_colors_ev = set_colors_ev
        self.bind(is_dir_button=set_colors_ev)
        super().__init__(**kwargs)

    def update_colors(self, _: Any):
        self._set_colors()


class Filelist(ScrollLayout):
    cls_height: float = NumericProperty("26dp")
    box_padding: Tuple[float, float, float, float] = VariableListProperty([0, 0, 0, 0])  # pyright: ignore[reportArgumentType]
    box_spacing: float = NumericProperty(0)

    scrollview: RecycleRestrictedScrollView = ObjectProperty()  # pyright: ignore[reportIncompatibleVariableOverride]

    rootpath: Path = ObjectProperty()
    path: Path = ObjectProperty()
    filters: Tuple[str] = ListProperty()

    update_interval: float = 1.0

    @staticmethod
    def _default_sorting_method(paths: Tuple[Path, ...]) -> Tuple[Path, ...]:
        return paths

    sorting_method: Callable[[Tuple[Path, ...]], Tuple[Path, ...]] = ObjectProperty(
        _default_sorting_method
    )

    viewclass: Union[str, Type[Widget]] = ObjectProperty(FileListButton)

    __events__ = ('on_submit',)

    prev_path: Path
    def __init__(self, **kwargs: Any):
        self.update_ev = Clock.create_trigger(self.update, -1)
        self.bind(
            rootpath=self.update_ev,
            path=self.update_ev,
            filters=self.update_ev
        )
        super().__init__(**kwargs)
        Clock.schedule_interval(self.update, self.update_interval)

    def on_submit(self, path: Path):
        pass

    def on_rootpath(self, _, rootpath: Path):
        self.path = rootpath
        self.prev_path = rootpath

    def update(self, _: float):
        path = self.path
        rootpath = self.rootpath
        if not path:
            return
        if not path.exists() or not path.is_dir():
            self.path = self.rootpath
            return
        data: List[Dict[str, Any]] = []
        try:
            if path != rootpath:
                data.append(self.create_item("..", path.parent, True))

            itemlist = tuple(path.iterdir())

            dirlist = self.sorting_method(
                tuple(item for item in itemlist if item.is_dir())
            )
            filelist = self.sorting_method(
                tuple(item for item in itemlist if self.check_path_by_filter(item))
            )

            for item in dirlist:
                data.append(self.create_item(f"> {item.name}", item, True))
            for item in filelist:
                data.append(self.create_item(item.name, item, False))
            self.scrollview.data = data
            self.prev_path = self.path
        except PermissionError:
            self.path = self.prev_path

    def create_item(self, text: str, path: Path, is_dir: bool) -> Dict[str, Any]:
        return {
            "text": text,
            "path": path,
            "filelist": self,
            "is_dir_button": is_dir
        }

    def check_path_by_filter(self, path: Path) -> bool:
        if path.is_dir() or path.name.startswith("."):
            return False
        if not self.filters:
            return True
        ext = path.suffix[1:].lower()
        return ext in self.filters or "." not in path.name
