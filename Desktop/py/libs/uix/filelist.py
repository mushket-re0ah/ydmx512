from kivy.properties import (
    ObjectProperty, ListProperty, BooleanProperty, NumericProperty
)
from kivy.clock import Clock
from libs.uix.scroll_layout import ScrollLayout
from libs.uix.button import HoverButton
from kivy.lang import Builder
from pathlib import Path

Builder.load_string("""
#:import uix_cs libs.uix.colorscheme

<FileListButton>:  # HoverButton
    halign: "left"
    valign: "center"
    text_size: self.size
    padding: ["8dp", 0, 0, 0]
    normal_background_color: uix_cs.FileListButton.dir_bg if self.is_dir_button else uix_cs.FileListButton.file_bg


<Filelist>:  # ScrollLayout
    size_hint: None, None

    scrollview: scrollview
    RecycleRestrictedScrollView:
        id: scrollview
        viewclass: "FileListButton"
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
"""
)


class FileListButton(HoverButton):
    path = ObjectProperty()
    filelist = ObjectProperty()
    is_dir_button = BooleanProperty()

    set_colors_ev = None
    def __init__(self, **kwargs):
        set_colors_ev = Clock.create_trigger(self.update_colors, 0)
        self.set_colors_ev = set_colors_ev
        self.bind(is_dir_button=set_colors_ev)
        super().__init__(**kwargs)

    def update_colors(self, _):
        self._set_colors()

    def on_release(self):
        if self.is_dir_button:
            self.filelist.path = self.path
        else:
            self.filelist.dispatch("on_submit", self.path)


class Filelist(ScrollLayout):
    cls_height = NumericProperty("26dp")

    scrollview = ObjectProperty()

    rootpath = ObjectProperty()
    path = ObjectProperty()
    filters = ListProperty([])

    __events__ = ('on_submit',)

    prev_path = None
    update_ev = None
    def __init__(self, **kwargs):
        update_ev = Clock.create_trigger(self.update, -1)
        self.update_ev = update_ev
        self.bind(
            rootpath=self.update_ev,
            path=self.update_ev,
            filters=self.update_ev
        )
        super().__init__(**kwargs)

    def on_submit(self, path: Path):
        pass

    def on_rootpath(self, instance, rootpath: Path):
        self.path = rootpath
        self.prev_path = rootpath

    def update(self, _):
        path = self.path
        rootpath = self.rootpath
        if not path:
            return
        if not path.exists() or not path.is_dir():
            self.path = self.rootpath
            return
        data = []
        try:
            if path != rootpath:
                data.append(self.create_item("..", path.parent, True))

            itemlist = tuple(path.iterdir())
            dirlist = tuple(i for i in itemlist if i.is_dir())
            filelist = tuple(i for i in itemlist if self.check_path_by_filter(i))

            for item in dirlist:
                data.append(self.create_item(f"> {item.name}", item, True))
            for item in filelist:
                data.append(self.create_item(item.name, item, False))
            self.scrollview.data = data
            self.prev_path = self.path
        except PermissionError:
            self.path = self.prev_path

    def create_item(self, text: str, path: Path, is_dir: bool) -> dict:
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
