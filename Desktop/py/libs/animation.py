from typing import Any, Callable, Dict, Optional, Tuple, Union

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.properties import ColorProperty
from kivy.utils import boundary

from libs.typecheck import RGBA


class ColorDiff:
    def __init__(self, dr: int, dg: int, db: int, da: int):
        self.dr: float = dr / 255
        self.dg: float = dg / 255
        self.db: float = db / 255
        self.da: float = da / 255

    def __repr__(self) -> str:
        return f"ColorDiff({self.dr}, {self.dg}, {self.db}, {self.da})"


class StatefulColorProperty(ColorProperty):
    """Свойство цвета, которое автоматически регистрирует animation_params и
       animation_triggers. Предназначен для работы с AnimationBehavior"""

    def __init__(
            self,
            normal: RGBA,
            states: Dict[Union[str, Tuple[str, ...]], Union[ColorDiff, RGBA]],
            **kwargs: Any
        ):
        super().__init__(normal, **kwargs)
        self.normal = normal
        self.states = states

    def __set_name__(self, owner: "AnimationBehavior", name: str):
        super().__set_name__(owner, name)
        # Инициализируем словари в классе, если их ещё нет
        if not hasattr(owner, "animation_params") or owner.animation_params is None:
            owner.animation_params = {}
        else:
            owner.animation_params = owner.animation_params.copy()

        if not hasattr(owner, "animation_triggers") or owner.animation_triggers is None:
            owner.animation_triggers = {}
        else:
            owner.animation_triggers = owner.animation_triggers.copy()

        params = {}
        triggers = {}
        for state, color in self.states.items():
            params[state] = color
            if isinstance(state, tuple):
                # Составной ключ -> проверяем все атрибуты
                triggers[state] = lambda self, s=state:\
                                         all(getattr(self, attr, False) for attr in s)
            else:
                # Одиночный ключ
                triggers[state] = lambda self, s=state: getattr(self, s, False)

        owner.animation_params[name] = params
        owner.animation_triggers[name] = triggers

    def set_normal(self, obj: "AnimationBehavior", new_normal: RGBA):
        # Сохраняем нормальный цвет для этого конкретного экземпляра
        setattr(obj, f'_normal_{self.name}', new_normal)
        obj._set_colors()

    def get_normal(self, obj: "AnimationBehavior") -> RGBA:
        # Если экземпляр переопределил нормальный цвет, берём его,
        # иначе возвращаем классовый default (self.normal)
        return getattr(obj, f'_normal_{self.name}', self.normal)


class AnimationBehavior:
    # Работает в связке с StatefulColorProperty
    # Используйте StatefulColorProperty, не пишите params и trigger руками
    # Больше не поддерживается без StatefulColorProperty
    animation_time: float = 0.2
    animation_fps: int = 8
    animation_params: Dict[str, Dict[str, Union[ColorDiff, RGBA]]] = {}
    animation_triggers: Dict[str, Dict[str, Callable[[EventDispatcher], bool]]] = {}
    _animation_block: bool = True  # Первый кадр анимация недоступна

    _animation: Optional[Animation] = None
    def __init__(self, **kwargs: Any):
        self._trigger_animate = Clock.create_trigger(self._animate, -1)
        super().__init__(**kwargs)
        self._make_animation_binds()
        Clock.schedule_once(self._animation_unblock, -1)

    def _animation_unblock(self, dt: float):
        self._animation_block = False
        self._set_colors()

    def _make_animation_binds(self):
        for triggers in self.animation_triggers.values():
            for state in triggers:
                if isinstance(state, tuple):
                    for attr in state:
                        self.fbind(attr, self._trigger_animate)
                else:
                    self.fbind(state, self._trigger_animate)

    def _animate(self, _: float):
        if self._animation_block:
            return
        if self._animation:
            for prop, value in self._animation._animated_properties.items():
                setattr(self, prop, value)
            Animation.cancel_all(self)
        if self.animation_time == 0:
            for attr, color in self._get_colors().items():
                setattr(self, attr, color)
            return
        anim = Animation(**self._get_colors(),
                         duration=self.animation_time,
                         step=self.animation_time / self.animation_fps)
        anim.start(self)
        anim.bind(on_complete=self.on_animation_complete)
        self._animation = anim

    def on_animation_complete(self, *_):
        self._animation = None

    def _get_state(self, param: str) -> str:
        for trigger, getter in self.animation_triggers[param].items():
            if getter(self):
                return trigger
        return "normal"

    def _set_colors(self):
        for attr, color in self._get_colors().items():
            setattr(self, attr, color)

    def _get_color(self, param: str, state: str, colors: Dict[str, Union[ColorDiff, RGBA]]) -> RGBA:
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
        return value

    def _get_colors(self) -> Dict[str, RGBA]:
        result: Dict[str, RGBA] = {}
        for param, colors in self.animation_params.items():
            state = self._get_state(param)
            result[param] = self._get_color(param, state, colors)
        return result
