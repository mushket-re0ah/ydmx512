from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Tuple, Type, TypedDict

from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.widget import Widget

from database import db
from libs.uix.button import HoverToggleButton
from libs.uix.input.numeric_input import NumericInput
from libs.uix.layouts import SectionPanel
from libs.uix.recycle_restricted_scrollview import RecycleRestrictedScrollView
from libs.uix.recycle_spinner import RecycleSpinner
from libs.uix.restricted_scrollview import RestrictedScrollView
from libs.uix.scroll_layout import ScrollLayout

if TYPE_CHECKING:
    from ui.mdi.settings.content import SettingsContent

Builder.load_file("ui/mdi/settings/sections.kv")


@dataclass(frozen=True)
class SettingSpec:
    key: str
    title: str
    target: Callable[[], Any]
    widget_cls: Type[Widget]
    widget_attrs: Dict[str, Any]
    widget_value_attr: str
    description: str
    restart_required: bool = False


class SettingsRow(BoxLayout):
    spec: SettingSpec = ObjectProperty()
    settings_content: "SettingsContent" = ObjectProperty()

    widget_box: BoxLayout = ObjectProperty()

    _target: Any
    _value_widget: Widget

    def on_kv_post(self, base_widget: Widget):
        super().on_kv_post(base_widget)

        spec = self.spec
        self._target = spec.target()

        widget_kwargs = dict(spec.widget_attrs)
        widget_kwargs[spec.widget_value_attr] = getattr(
            self._target, spec.key
        )

        self._value_widget = spec.widget_cls(**widget_kwargs)
        self.widget_box.add_widget(self._value_widget, 1)

        self._value_widget.bind(**{
            spec.widget_value_attr: self._on_widget_value
        })
        self._target.bind(**{
            spec.key: self._on_target_value
        })

    def _on_widget_value(self, _: Widget, value: Any):
        spec = self.spec
        if getattr(self._target, spec.key) != value:
            setattr(self._target, spec.key, value)
        if spec.restart_required:
            self.settings_content.restart_required = True

    def _on_target_value(self, _: Any, value: Any):
        attr = self.spec.widget_value_attr
        if getattr(self._value_widget, attr) != value:
            setattr(self._value_widget, attr, value)


class SettingsSection(BoxLayout):
    title: str
    SPECS: Tuple[SettingSpec, ...] = ()

    scroll_layout: ScrollLayout = ObjectProperty()
    scrollview: RestrictedScrollView = ObjectProperty()
    row_box: BoxLayout = ObjectProperty()
    settings_content: "SettingsContent" = ObjectProperty()

    def on_kv_post(self, base_widget: Widget):
        super().on_kv_post(base_widget)

        for spec in self.SPECS:
            self.row_box.add_widget(
                SettingsRow(
                    spec=spec,
                    settings_content=self.settings_content
                )
            )


class SettingsInterface(SettingsSection):
    title = "Интерфейс"

    SPECS = (
        SettingSpec(
            key="density",
            title="Масштаб интерфейса",
            target=lambda: db.misc,
            widget_cls=NumericInput,
            widget_attrs={
                "step_mouse_scroll": 0.01,
                "size_hint": (1, 1),
                "allow_empty": False,
                "decimals": 2,
                "input_filter": "float",
                "minimum": db.misc.property("density").get_min(db.misc),
                "maximum": db.misc.property("density").get_max(db.misc),
            },
            widget_value_attr="value",
            description="Масштаб элементов интерфейса",
        ),
        SettingSpec(
            key="scale_font",
            title="Масштаб шрифта",
            target=lambda: db.misc,
            widget_cls=NumericInput,
            widget_attrs={
                "step_mouse_scroll": 0.01,
                "size_hint": (1, 1),
                "allow_empty": False,
                "decimals": 2,
                "input_filter": "float",
                "minimum": db.misc.property("scale_font").get_min(db.misc),
                "maximum": db.misc.property("scale_font").get_max(db.misc),
            },
            widget_value_attr="value",
            description="Масштабирование текста",
        ),
        SettingSpec(
            key="use_system_cursor",
            title="Системный курсор",
            target=lambda: db.misc,
            widget_cls=HoverToggleButton,
            widget_attrs={
                "size_hint": (1, 1),
            },
            widget_value_attr="is_down",
            description="Использовать системный курсор вместо курсора приложения",
        ),
    )


class SettingsGraphics(SettingsSection):
    title = "Графика"

    SPECS = (
        SettingSpec(
            key="fps",
            title="Максимальный FPS",
            target=lambda: db.misc,
            widget_cls=NumericInput,
            widget_attrs={
                "step_mouse_scroll": 1,
                "size_hint": (1, 1),
                "allow_empty": False,
                "decimals": 0,
                "input_filter": "int",
                "minimum": db.misc.property("fps").get_min(db.misc),
                "maximum": db.misc.property("fps").get_max(db.misc),
            },
            widget_value_attr="value",
            description="Максимальная частота кадров",
            restart_required=True,
        ),
        SettingSpec(
            key="multisamples",
            title="Сглаживание",
            target=lambda: db.misc,
            widget_cls=NumericInput,
            widget_attrs={
                "step_mouse_scroll": 1,
                "size_hint": (1, 1),
                "allow_empty": False,
                "decimals": 0,
                "input_filter": "int",
                "minimum": db.misc.property("multisamples").get_min(db.misc),
                "maximum": db.misc.property("multisamples").get_max(db.misc),
            },
            widget_value_attr="value",
            description="Уровень сглаживания",
            restart_required=True,
        ),
        SettingSpec(
            key="vsync",
            title="Вертикальная синхронизация",
            target=lambda: db.misc,
            widget_cls=RecycleSpinner,
            widget_attrs={
                "size_hint": (1, 1),
                "values": db.misc.property("vsync").options
            },
            widget_value_attr="selected",
            description="Синхронизация отрисовки с обновлением дисплея",
            restart_required=True,
        ),
    )


class SettingsDatabase(SettingsSection):
    title = "База данных"

    SPECS = (
        SettingSpec(
            key="database_save_interval",
            title="Интервал сохранения",
            target=lambda: db.misc,
            widget_cls=NumericInput,
            widget_attrs={
                "step_mouse_scroll": 1.0,
                "size_hint": (1, 1),
                "allow_empty": False,
                "decimals": 1,
                "input_filter": "float",
                "minimum": db.misc.property("database_save_interval").get_min(db.misc),
                "maximum": db.misc.property("database_save_interval").get_max(db.misc),
            },
            widget_value_attr="value",
            description="Период между автоматическими сохранениями базы данных (секунды)",
        ),
        SettingSpec(
            key="database_backup_interval",
            title="Интервал резервного копирования",
            target=lambda: db.misc,
            widget_cls=NumericInput,
            widget_attrs={
                "step_mouse_scroll": 1.0,
                "size_hint": (1, 1),
                "allow_empty": False,
                "decimals": 1,
                "input_filter": "float",
                "minimum": db.misc.property("database_backup_interval").get_min(db.misc),
                "maximum": db.misc.property("database_backup_interval").get_max(db.misc),
            },
            widget_value_attr="value",
            description="Период между созданием резервных копий (секунды)",
        ),
        SettingSpec(
            key="database_backup_max_count",
            title="Максимальное количество резервных копий",
            target=lambda: db.misc,
            widget_cls=NumericInput,
            widget_attrs={
                "step_mouse_scroll": 1,
                "size_hint": (1, 1),
                "allow_empty": False,
                "decimals": 0,
                "input_filter": "int",
                "minimum": db.misc.property("database_backup_max_count").get_min(db.misc),
                "maximum": db.misc.property("database_backup_max_count").get_max(db.misc),
            },
            widget_value_attr="value",
            description="При превышении лимита старые копии удаляются",
        ),
    )


class SettingsMidi(SettingsSection):
    title = "MIDI"
    SPECS = (
        SettingSpec(
            key="midi_notes",
            title="Формат midi-нот",
            target=lambda: db.misc,
            widget_cls=RecycleSpinner,
            widget_attrs={
                "size_hint": (1, 1),
                "values": db.misc.property("midi_notes").options
            },
            widget_value_attr="selected",
            description="Формат отображения и ввода нот в midi-полях",
        ),
    )


class SettingsBackupBox(BoxLayout):
    pass


class SettingsBackups(SettingsSection):
    title = "Резервные копии"


class _SettingsSectionToggleViewDataDict(TypedDict):
    section_cls: Type[SettingsSection]
    settings_content: "SettingsContent"
    state: str


class SettingsSectionToggle(RecycleDataViewBehavior, HoverToggleButton):
    section_cls: Type[SettingsSection] = ObjectProperty()
    settings_content: "SettingsContent" = ObjectProperty()

    def __init__(self, *args: Any, **kwargs: Any):
        self.rv: Optional[RecycleRestrictedScrollView] = None
        self.index: Optional[int] = None
        super().__init__(
            *args,
            group="settings_section_toggle",
            allow_no_selection=False,
            **kwargs
        )

    def on_press(self):
        self.settings_content.on_select_section(self.section_cls)
        if self.rv is None or self.index is None:
            return
        for i, rv_data in enumerate(self.rv.data):
            rv_data["state"] = self.state if i == self.index else "normal"

    def refresh_view_attrs( # pyright: ignore[reportIncompatibleMethodOverride]
            self,
            rv: RecycleRestrictedScrollView,
            index: int,
            data: _SettingsSectionToggleViewDataDict
        ):
        self.rv = rv
        self.index = index
        super().refresh_view_attrs(rv, index, data)  # pyright: ignore[reportArgumentType]


class SettingsSections(ScrollLayout):
    scrollview: RecycleRestrictedScrollView  # pyright: ignore[reportIncompatibleVariableOverride]
    content: "SettingsContent" = ObjectProperty()

    SECTION_CLASSES = (
        SettingsInterface,
        SettingsGraphics,
        SettingsDatabase,
        SettingsMidi,
        SettingsBackups,
    )

    def on_content(self, _, content: "SettingsContent"):
        self.scrollview.data = [
            _SettingsSectionToggleViewDataDict(
                section_cls=section_cls,
                settings_content=self.content,
                state="down" if i == 0 else "normal"
            )
            for i, section_cls in enumerate(self.SECTION_CLASSES)
        ]
        content.on_select_section(self.SECTION_CLASSES[0])
