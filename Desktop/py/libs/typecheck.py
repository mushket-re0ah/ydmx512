from typing import Any, Callable, Optional, Tuple, Union

from kivy.event import EventDispatcher
from typing_extensions import TypeAlias

Number: TypeAlias = Union[int, float]
OptionalNumber: TypeAlias = Optional[Number]
RGBA: TypeAlias = Tuple[float, float, float, float]
RGB: TypeAlias = Tuple[float, float, float]
HSL: TypeAlias = Tuple[float, float, float]
KivyCallback: TypeAlias = Callable[[EventDispatcher, Any], None]
AnyCallback: TypeAlias = Callable[..., Any]
