from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Final, FrozenSet, Optional, Tuple, Union

from kivy.event import EventDispatcher
from kivy.properties import Property
from kivy.uix.widget import Widget
from typing_extensions import TypeAlias

Number: TypeAlias = Union[int, float]
OptionalNumber: TypeAlias = Optional[Number]
RGBA: TypeAlias = Tuple[float, float, float, float]
RGB: TypeAlias = Tuple[float, float, float]
HSL: TypeAlias = Tuple[float, float, float]
KivyCallback: TypeAlias = Callable[[EventDispatcher, Any], None]
AnyCallback: TypeAlias = Callable[..., Any]

ImmutableTypes: TypeAlias = Union[
    None,
    bool,
    int,
    float,
    str,
    bytes,
    Enum,
    Tuple["ImmutableTypes", ...],
    FrozenSet["ImmutableTypes"]
]

class UnsetType:
    __slots__ = ()
    def __repr__(self) -> str:
        return "<UNSET>"

UNSET: Final = UnsetType()


if TYPE_CHECKING:
    WidgetProtocol = Widget
    EventDispatcherProtocol = EventDispatcher
    PropertyProtocol = Property
else:
    WidgetProtocol = object
    EventDispatcherProtocol = object
    PropertyProtocol = object
