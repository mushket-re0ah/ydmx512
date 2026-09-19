from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from libs.uix.layouts import StencilBoxLayout
from libs.uix.scroll_layout import ScrollLayout
from database.fixture_param import RowFixtureParam
from database.fixture import RowFixture, FixtureChannelsGroup
from misc import constants
from libs import sub_proc
from pathlib import Path
import shutil
from database.brand import RowBrand
from database import db
from misc import logger


Builder.load_file("ui/mdi/library/fixture_editor.kv")


class LibraryFixtureParam(BoxLayout):
    fixture_param: RowFixtureParam = ObjectProperty()
    param_list = ObjectProperty()
    group_index = NumericProperty()

    library = ObjectProperty()
    context = ObjectProperty()
    edit_exist = BooleanProperty(False)

    def set_fixture_param(self, param: RowFixtureParam):
        self.param_list[self.group_index] = param
        self.library.property("view_context").dispatch(self.library)


class LibraryFixtureParamGroup(BoxLayout):
    scrollview = ObjectProperty()
    box = ObjectProperty()

    group: FixtureChannelsGroup = ObjectProperty()

    library = ObjectProperty()
    context = ObjectProperty()
    master_widget = ObjectProperty()
    edit_exist = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for param in self.group.param_list:
            self.add_param(param)

    def on_edit_exist(self, _, edit_exist: bool):
        for fixture_param_ui in self.box.children:
            fixture_param_ui.edit_exist = edit_exist

    def set_title(self, title: str):
        self.__set_context("title", title)

    def set_repeat_count(self, repeat_count: int):
        if self.edit_exist:
            logger.warning("Попытка изменения repeat_count у существующей фикстуры")
            return
        self.__set_context("repeat_count", repeat_count)

    def set_linear(self, linear: bool):
        self.__set_context("linear", linear)

    def __set_context(self, attr: str, value: any):
        if getattr(self.group, attr) != value:
            setattr(self.group, attr, value)
            self.library.property("view_context").dispatch(self.library)

    def add_param(self, param: RowFixtureParam=None):
        if self.edit_exist:
            logger.warning("Попытка добавить параметр существующей фикстуре")
            return
        if param is None:
            param = db.fixture_param.get_default_row()
            self.__add_param_to_context(param)
        self.box.add_widget(LibraryFixtureParam(
            library=self.library,
            context=self.context,
            fixture_param=param,
            param_list=self.group.param_list,
            group_index=len(self.box.children))
        )

    def __add_param_to_context(self, param: RowFixtureParam):
        if self.edit_exist:
            logger.warning("Попытка добавить параметр существующей фикстуре")
            return
        self.group.param_list.append(param)
        self.library.property("view_context").dispatch(self.library)


class LibraryFixtureParams(ScrollLayout):
    scrollview = ObjectProperty()
    box = ObjectProperty()

    library = ObjectProperty()
    fixture = ObjectProperty()
    context = ObjectProperty()
    edit_exist = BooleanProperty(False)

    def on_kv_post(self, _):
        super().on_kv_post(_)
        for group in self.context.channels_groups:
            self.add_group(group)

    def on_edit_exist(self, _, edit_exist: bool):
        for param_group_ui in self.box.children:
            param_group_ui.edit_exist = edit_exist

    def add_group(self, group: FixtureChannelsGroup=None):
        if self.edit_exist:
            logger.warning("Попытка создания группы в существующей фикстуре")
            return
        if group is None:
            group = FixtureChannelsGroup()
            self.__add_group_to_context(group)
        param_group = LibraryFixtureParamGroup(
            master_widget=self,
            library=self.library,
            group=group,
            context=self.context
        )
        self.box.add_widget(param_group)

    def __add_group_to_context(self, group: FixtureChannelsGroup):
        if self.edit_exist:
            logger.warning("Попытка создания группы в существующей фикстуре")
            return
        self.context.channels_groups.append(group)
        self.library.property("view_context").dispatch(self.library)

    def remove_group(self, group_ui: LibraryFixtureParamGroup):
        if self.edit_exist:
            logger.warning("Попытка удаления группы в существующей фикстуре")
            return
        self.context.channels_groups.remove(group_ui.group)
        self.box.remove_widget(group_ui)
        self.library.property("view_context").dispatch(self.library)


class LibraryFixtureEditor(StencilBoxLayout):
    library = ObjectProperty()

    fixture = ObjectProperty()
    context = ObjectProperty()

    title = StringProperty()
    note = StringProperty()
    brand = ObjectProperty()
    icon = StringProperty((constants.DEFAULT_FIXTURE_ICON).as_posix())
    temp_dependence = NumericProperty()

    # ui
    input_title = ObjectProperty()
    input_note = ObjectProperty()
    dropdown_brand = ObjectProperty()
    btn_icon_now = ObjectProperty()
    fixture_params = ObjectProperty()

    edit_exist = BooleanProperty()

    def __init__(self, **kwargs):
        context = kwargs["context"]
        fixture = kwargs["fixture"]
        library = kwargs["library"]
        edit_exist = fixture is not None
        library.view_context.fixture_now = fixture
        if context.fixture is not fixture:
            self.__init_context(fixture, context, library)
            super().__init__(
                title=fixture.title,
                note=fixture.note,
                brand=fixture.brand,
                icon=(constants.FIXTURE_IMGS_PATH / fixture.icon).as_posix(),
                temp_dependence=fixture.temp_dependence,
                edit_exist=edit_exist,
                **kwargs)
        else:
            super().__init__(
                title=context.title,
                note=context.note,
                brand=context.brand,
                icon=context.icon,
                temp_dependence=context.temp_dependence,
                edit_exist=edit_exist,
                **kwargs)
        library.property("view_context").dispatch(library)

    def on_kv_post(self, _):
        self.fixture_params.edit_exist = self.edit_exist

    def close(self):
        self.library.change_context_now(self.library.Contexts.MENU)

    def set_title(self, title: str):
        self.title = title
        self.__set_context("title", title)

    def set_note(self, note: str):
        self.note = note
        self.__set_context("note", note)

    def set_brand(self, brand: RowBrand):
        self.brand = brand
        self.__set_context("brand", brand)

    def set_icon(self, icon: str):
        self.icon = icon
        self.__set_context("icon", icon)

    def set_temp_dependence(self, temp_dependence: int):
        self.temp_dependence = temp_dependence
        self.__set_context("temp_dependence", temp_dependence)

    def save(self):
        if self.fixture:
            self.fixture.edit(**self.__get_save_kwargs())
        else:
            db.fixture.add_row(**self.__get_save_kwargs())
        self.context.set_default()
        self.library.property("view_context").dispatch(self.library)
        self.close()

    def __get_save_kwargs(self) -> dict:
        return {
            "title": self.title,
            "note": self.note,
            "brand": self.brand,
            "icon": Path(self.icon).name,
            "temp_dependence": self.temp_dependence,
            "channels_groups": self.context.channels_groups
        }

    def __init_context(self, fixture: RowFixture, context, library):
        context.fixture = fixture
        context.title = fixture.title
        context.note = fixture.note
        context.brand = fixture.brand
        context.icon = (constants.FIXTURE_IMGS_PATH / fixture.icon).as_posix()
        context.temp_dependence = fixture.temp_dependence
        channels_groups = [i.get_copy() for i in fixture.channels_groups]
        context.channels_groups = channels_groups
        library.property("view_context").dispatch(library)

    def __set_context(self, attr: str, value: any):
        if getattr(self.context, attr) != value:
            setattr(self.context, attr, value)
            self.library.property("view_context").dispatch(self.library)

    def _select_fixture_icon(self):
        sub_proc.open_file(self.__on_open_file,
                           path=str(constants.FIXTURE_IMGS_PATH),
                           filters=["*.png", "*.jpeg", "*.jpg"],
                           title="Выберите иконку для фикстуры")

    def __on_open_file(self, filepath: str):
        if not filepath:
            return
        filepath = Path(filepath)
        if self.__is_file_in_fixture_dir(filepath):
            # Значит, файл взят из папки с картинками фикстур
            new_filepath = self.__path_to_fixture_icon(filepath)
        else:
            # Файл находится не в constants.FIXTURE_IMGS_PATH
            new_filepath = self.__copy_file_to_fixture_img_dir(filepath)
        self.set_icon(new_filepath.as_posix())

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
