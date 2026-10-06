import shutil
from pathlib import Path
from typing import Any, List, Optional, Tuple

from kivy.lang import Builder
from kivy.properties import (
    BooleanProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout

from database import db
from database.brand import RowBrand
from database.fixture import FixtureChannelsGroup, RowFixture
from database.fixture_param import RowFixtureParam
from libs import logger, sub_proc
from libs.uix.button import HoverButton
from libs.uix.input import HoverInput
from libs.uix.layouts import StencilBoxLayout
from libs.uix.recycle_spinner import RecycleSpinner
from libs.uix.restricted_scrollview import RestrictedScrollView
from libs.uix.scroll_layout import ScrollLayout
from libs.utils import with_item, without_item
from misc import constants
from ui.mdi.library import LibraryContentEnum, MDILibrary

Builder.load_file("ui/mdi/library/fixture_editor.kv")


class LibraryFixtureParam(BoxLayout):
    fixture_param: RowFixtureParam = ObjectProperty()
    group_index: int = NumericProperty()

    param_group: "LibraryFixtureParamGroup" = ObjectProperty()

    edit_mode: bool = BooleanProperty(False)

    def set_fixture_param(self, param: RowFixtureParam):
        self.param_group.set_fixture_param(self, param)

    def copy(self):
        self.param_group.add_param(self.fixture_param)

    def remove(self):
        self.param_group.remove_param(self)


class LibraryFixtureParamGroup(BoxLayout):
    scrollview: RestrictedScrollView = ObjectProperty()
    box: BoxLayout = ObjectProperty()

    group: FixtureChannelsGroup = ObjectProperty()

    library: MDILibrary = ObjectProperty()
    fixture_editor: "LibraryFixtureEditor" = ObjectProperty()
    fixture_params: "LibraryFixtureParams" = ObjectProperty()

    edit_mode: bool = BooleanProperty()

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        for param in self.group.param_list:
            self.add_param(param, init=True)

    def set_title(self, title: str):
        self.__set_context("title", title)

    def set_repeat_count(self, repeat_count: int):
        if self.edit_mode:
            logger.warning("Попытка изменения repeat_count у существующей фикстуры")
            return
        self.__set_context("repeat_count", repeat_count)

    def set_linear(self, linear: bool):
        self.__set_context("linear", linear)

    def __set_context(self, attr: str, value: Any):
        if getattr(self.group, attr) != value:
            setattr(self.group, attr, value)
            self.fixture_editor.property("channels_groups").dispatch(self.fixture_editor)

    def set_fixture_param(
            self,
            param_ui: LibraryFixtureParam,
            fixture_param: RowFixtureParam
        ):
        self.group.param_list[param_ui.group_index] = fixture_param
        self.fixture_editor.property("channels_groups").dispatch(self.fixture_editor)

    def add_param(
            self,
            param: Optional[RowFixtureParam]=None,
            init:bool=False
        ):
        if self.edit_mode and not init:
            logger.warning("Попытка добавить параметр существующей фикстуре")
            return
        if param is None:
            param = db.fixture_param.get_default_row()
            self._add_param_to_context(param, init=init)
        self.box.add_widget(LibraryFixtureParam(
                param_group=self,
                fixture_param=param,
                group_index=len(self.box.children),
                edit_mode=self.edit_mode
            ),
        )
        self.re_indexate()

    def remove_param(
        self,
        param_ui: LibraryFixtureParam
    ):
        if self.edit_mode:
            logger.warning("Попытка удалить параметр существующей фикстуре")
            return
        self.box.remove_widget(param_ui)
        logger.debug(param_ui, self.group.param_list[param_ui.group_index])        
        del self.group.param_list[param_ui.group_index]
        self.fixture_editor.property("channels_groups").dispatch(self.fixture_editor)
        self.re_indexate()

    def _add_param_to_context(
            self,
            param: RowFixtureParam,
            init:bool=False
        ):
        if self.edit_mode and not init:
            logger.warning("Попытка добавить параметр существующей фикстуре")
            return
        if not init:
            self.group.param_list.append(param)
            self.fixture_editor.property("channels_groups").dispatch(self.fixture_editor)

    def re_indexate(self):
        for i, param_ui in enumerate(reversed(self.box.children)):
            param_ui.group_index = i


class LibraryFixtureParams(ScrollLayout):
    scrollview: RestrictedScrollView = ObjectProperty()
    box: BoxLayout = ObjectProperty()

    library: MDILibrary = ObjectProperty()
    fixture_editor: "LibraryFixtureEditor" = ObjectProperty()

    edit_mode: bool = BooleanProperty()

    def init(self, edit_mode:bool):
        self.edit_mode = edit_mode
        for group in self.fixture_editor.channels_groups:
            self.add_group(group, init=True)

    def add_group(
            self,
            group:Optional[FixtureChannelsGroup]=None,
            init:bool=False
        ):
        if self.edit_mode and not init:
            logger.warning("Попытка создания группы в существующей фикстуре")
            return
        if group is None:
            group = FixtureChannelsGroup()
            self.add_group_to_context(group, init)
        param_group = LibraryFixtureParamGroup(
            edit_mode=self.edit_mode,
            fixture_editor=self.fixture_editor,
            fixture_params=self,
            library=self.library,
            group=group
        )
        self.box.add_widget(param_group)

    def add_group_to_context(
            self,
            group: FixtureChannelsGroup,
            init:bool=False
        ):
        if self.edit_mode and not init:
            logger.warning("Попытка создания группы в существующей фикстуре")
            return
        self.fixture_editor.channels_groups = with_item(
            self.fixture_editor.channels_groups,
            group
        )

    def remove_group(self, group_ui: LibraryFixtureParamGroup):
        if self.edit_mode:
            logger.warning("Попытка удаления группы в существующей фикстуре")
            return
        self.box.remove_widget(group_ui)
        self.fixture_editor.channels_groups = without_item(
            self.fixture_editor.channels_groups,
            group_ui.group
        )


class LibraryFixtureEditor(StencilBoxLayout):
    library: MDILibrary = ObjectProperty()

    title: str = StringProperty()
    note: str = StringProperty()
    brand: RowBrand = ObjectProperty()
    icon: str = StringProperty((constants.DEFAULT_FIXTURE_ICON).as_posix())
    temp_dependence: int = NumericProperty()
    channels_groups: Tuple[FixtureChannelsGroup, ...] = ListProperty(force_dispatch=True)

    # ui
    input_title: HoverInput = ObjectProperty()
    input_note: HoverInput = ObjectProperty()
    dropdown_brand: RecycleSpinner = ObjectProperty()
    btn_icon_now: HoverButton = ObjectProperty()
    fixture_params: LibraryFixtureParams = ObjectProperty()

    edit_mode: bool = BooleanProperty()

    groups_count: int = NumericProperty()
    params_count: int = NumericProperty()

    def on_channels_groups(self, _, channels_groups: Tuple[FixtureChannelsGroup, ...]):
        self.groups_count = len(channels_groups)
        self.params_count = len(RowFixture.unpack_param_list(channels_groups))

    def init(self):
        self.edit_mode = self.library.fixture_editor_edit_mode
        self.fixture_params.init(self.edit_mode)

    def close(self):
        self.library.change_content(LibraryContentEnum.FIXTURE)

    def save(self):
        save_kwargs = {
            "title": self.title,
            "note": self.note,
            "brand": self.brand,
            "icon": Path(self.icon).name,
            "temp_dependence": self.temp_dependence,
            "channels_groups": list(self.channels_groups)
        }
        if self.library.fixture_editor_edit_mode:
            self.library.context_fixture.edit(**save_kwargs)
        else:
            db.fixture.add_row(**save_kwargs)
        self.close()
        self.library.reset_editor_data()

    def _select_fixture_icon(self):
        sub_proc.open_file(
            self.__on_open_file,
            path=str(constants.FIXTURE_IMGS_PATH),
            filters=(
                ("Images", "*.png", "*.jpeg", "*.jpg"),
                ("PNG", "*.png",),
                ("JPEG", "*.jpeg", "*.jpg"),
            ),
            multiple=False,
            title="Выберите иконку для фикстуры",
            preview=True
        )

    def __on_open_file(self, filepath_str: Optional[str]):
        if filepath_str is None:
            return
        filepath = Path(filepath_str)
        if self.__is_file_in_fixture_dir(filepath):
            # Значит, файл взят из папки с картинками фикстур
            new_filepath = self.__path_to_fixture_icon(filepath)
        else:
            # Файл находится не в constants.FIXTURE_IMGS_PATH
            new_filepath = self.__copy_file_to_fixture_img_dir(filepath)
        self.icon = new_filepath.as_posix()

    def __copy_file_to_fixture_img_dir(self, filepath: Path) -> Path:
        new_filepath = self.__path_to_fixture_icon(filepath)
        if new_filepath.is_file():
            # Файл с таким именем уже существует, переименовываем
            new_filepath = self.__generate_unique_path(new_filepath)
        shutil.copy(str(filepath), str(new_filepath))
        return new_filepath

    def __is_file_in_fixture_dir(self, filepath: Path) -> bool:
        fullpath_fixture_imgs = Path.cwd() / constants.FIXTURE_IMGS_PATH
        filepath_dir = filepath.parent
        return filepath_dir.resolve() == fullpath_fixture_imgs.resolve()

    def __generate_unique_path(self, filepath: Path) -> Path:
        # Генерация уникального имени файла. Например, в папке существует файл
        # image.png, а filepath тоже image.png, функция вернет image (1).png,
        # а если image (1).png существует, то image (2).png и т.д.
        stem = filepath.stem
        suffix = filepath.suffix

        counter = 1
        while True:
            new_stem = f"{stem} ({counter})"
            new_path = filepath.with_name(f"{new_stem}{suffix}")
            if not new_path.exists():
                return new_path
            counter += 1

    def __path_to_fixture_icon(self, filepath: Path) -> Path:
        return constants.FIXTURE_IMGS_PATH / filepath.name
