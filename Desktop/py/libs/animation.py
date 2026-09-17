from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import ColorProperty
from kivy.utils import get_color_from_hex, boundary
from typing import Tuple


class ColorDiff:
    def __init__(self, dr: int, dg: int, db: int, da: int):
        self.dr = dr / 255
        self.dg = dg / 255
        self.db = db / 255
        self.da = da / 255

    def __repr__(self) -> str:
        return f"ColorDiff({self.dr}, {self.dg}, {self.db}, {self.da})"


class StatefulColorProperty(ColorProperty):
    """Свойство цвета, которое автоматически регистрирует _animation_params и
       _animation_triggers. Предназначен для работы с AnimationBehavior"""

    def __init__(self, normal, states, **kwargs):
        super().__init__(normal, **kwargs)
        self.normal = normal
        self.states = states

    def __set_name__(self, owner, name):
        super().__set_name__(owner, name)
        # Инициализируем словари в классе, если их ещё нет
        if not hasattr(owner, "_animation_params") or owner._animation_params is None:
            owner._animation_params = {}
        else:
            owner._animation_params = owner._animation_params.copy()

        if not hasattr(owner, "_animation_triggers") or owner._animation_triggers is None:
            owner._animation_triggers = {}
        else:
            owner._animation_triggers = owner._animation_triggers.copy()

        params = {}
        triggers = {}
        for state, color in self.states.items():
            params[state] = color
            if isinstance(state, tuple):
                # Составной ключ -> проверяем все атрибуты
                triggers[state] = lambda self, s=state: all(getattr(self, attr, False) for attr in s)
            else:
                # Одиночный ключ
                triggers[state] = lambda self, s=state: getattr(self, s, False)

        owner._animation_params[name] = params
        owner._animation_triggers[name] = triggers

    def set_normal(self, obj, new_normal):
        # Сохраняем нормальный цвет для этого конкретного экземпляра
        setattr(obj, f'_normal_{self.name}', new_normal)
        obj._set_colors()

    def get_normal(self, obj):
        # Если экземпляр переопределил нормальный цвет, берём его,
        # иначе возвращаем классовый default (self.normal)
        return getattr(obj, f'_normal_{self.name}', self.normal)


class AnimationBehavior:
    # Работает в связке с StatefulColorProperty
    animation_time = 0.2
    animation_fps = 8
    _animation_params = {}  # Надо переопределить
    # Используйте StatefulColorProperty
    # Пример: _animation_params = {
    #     "value_track_color": {
    #         "normal": cs.HoverSlider.value_track_color_normal,
    #         "hover": cs.HoverSlider.value_track_color_hover
    #     },
    #     "background_color": {
    #         "normal": cs.HoverSlider.background_color_normal,
    #         "hover": cs.HoverSlider.background_color_hover
    #     }
    # }
    _animation_triggers = {}  # Надо переопределить, учитывая порядок проверки
    # Используйте StatefulColorProperty
    # _animation_triggers = {
    #     "value_track_color": {
    #         "hover": lambda self: self.hover
    #      },
    #      ...
    # }
    _animation_block = True  # Первый кадр анимация недоступна
    _trigger_animate = {}

    _animation = None
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._trigger_animate = Clock.create_trigger(self._animate, -1)
        self._make_animation_binds()
        Clock.schedule_once(self._animation_unblock, -1)

    def _animation_unblock(self, _):
        self._animation_block = False
        self._set_colors()

    def _make_animation_binds(self):
        for param, triggers in self._animation_triggers.items():
            for state in triggers:
                if isinstance(state, tuple):
                    for attr in state:
                        self.fbind(attr, self._trigger_animate)
                else:
                    self.fbind(state, self._trigger_animate)

    def _animate(self, _):
        if self._animation_block:
            return
        if self._animation:
            for prop, value in self._animation._animated_properties.items():
                setattr(self, prop, value)
            Animation.cancel_all(self)
        anim = Animation(**self._get_colors(),
                         duration=self.animation_time,
                         step=self.animation_time / self.animation_fps)
        anim.start(self)
        anim.bind(on_complete=self.on_animation_complete)
        self._animation = anim

    def on_animation_complete(self, *args):
        self._animation = None

    def _get_state(self, param) -> str:
        for trigger, getter in self._animation_triggers[param].items():
            if getter(self):
                return trigger
        return "normal"

    def _set_colors(self):
        for attr, color in self._get_colors().items():
            setattr(self, attr, color)

    def _get_color(self, param, state, colors):
        prop = self.property(param)
        normal = prop.get_normal(self)
        if state == "normal":
            return normal
        value = colors[state]
        if isinstance(value, ColorDiff):
            return (
                boundary(normal[0] + value.dr, 0.0, 1.0),
                boundary(normal[1] + value.dg, 0.0, 1.0),
                boundary(normal[2] + value.db, 0.0, 1.0),
                boundary(normal[3] + value.da, 0.0, 1.0),
            )
        else:
            return value

    def _get_colors(self) -> dict:
        result = {}
        for param, colors in self._animation_params.items():
            state = self._get_state(param)
            result[param] = self._get_color(param, state, colors)
        return result
