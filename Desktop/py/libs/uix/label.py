from typing import Any, Literal, Optional, Tuple

from kivy.clock import Clock
from kivy.core.text import DEFAULT_FONT
from kivy.core.text import Label as CoreLabel
from kivy.graphics.texture import Texture
from kivy.lang import Builder
from kivy.properties import (
    ListProperty,
    NumericProperty,
    ObjectProperty,
    OptionProperty,
    StringProperty,
    VariableListProperty,
)
from kivy.uix.widget import Widget

from libs.animation import StatefulColorProperty
from libs.typecheck import RGBA
from libs.uix import colorscheme as uix_cs

Builder.load_string("""
<RestrictedLabel>:
    canvas:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            texture: self.texture
            size: self.texture_size
            pos: (\
                int(self.center_x - self.texture_size[0] / 2.0),\
                int(self.center_y - self.texture_size[1] / 2.0)\
            )
"""
)


class RestrictedLabel(Widget):
    _font_properties: Tuple[str, ...] = (
        "text", "font_size", "font_name", "color",
        "halign", "valign", "padding", "text_size",
    )

    _label: Optional[CoreLabel]
    def __init__(self, **kwargs: Any):
        self._trigger_texture = Clock.create_trigger(self.texture_update, -1)
        super().__init__(**kwargs)

        d = RestrictedLabel._font_properties
        fbind = self.fbind
        update = self._trigger_texture_update

        for x in d:
            fbind(x, update, x)

        self._label = None
        self._create_label()

        # force the texture creation
        self._trigger_texture()

    def _create_label(self):
        dkw = {x: getattr(self, x) for x in self._font_properties}
        dkw["usersize"] = self.text_size
        self._label = CoreLabel(**dkw)

    def _trigger_texture_update(self, name:str="", source:Optional[Widget]=None, value:Any=None):
        # check if the label core class need to be switch to a new one
        if source:
            if name == "text":
                self._label.text = value  # pyright: ignore[reportOptionalMemberAccess]
            elif name == "text_size":
                self._label.usersize = value  # pyright: ignore[reportOptionalMemberAccess]
            elif name == "font_size":
                self._label.options[name] = value  # pyright: ignore[reportOptionalMemberAccess]
            else:
                self._label.options[name] = value  # pyright: ignore[reportOptionalMemberAccess]

        self._trigger_texture()

    def texture_update(self, *_:Any):
        self.texture = None

        if (not self._label.text or  # pyright: ignore[reportOptionalMemberAccess]
                (self.halign == "justify") and
                not self._label.text.strip()):  # pyright: ignore[reportOptionalMemberAccess]
            self.texture_size = (0, 0)
        else:
            self._label.refresh()  # pyright: ignore[reportOptionalMemberAccess]
            texture = self._label.texture  # pyright: ignore[reportOptionalMemberAccess]
            if texture is not None:
                self.texture = self._label.texture  # pyright: ignore[reportOptionalMemberAccess]
                self.texture_size = list(self.texture.size)  # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]

    text: str = StringProperty("")

    text_size: Tuple[float, float] = ListProperty([None, None])  # pyright: ignore[reportArgumentType]

    font_name: str = StringProperty(DEFAULT_FONT)

    font_size: float = NumericProperty("15sp")

    padding: Tuple[float, float, float, float] = VariableListProperty([0, 0, 0, 0])  # pyright: ignore[reportArgumentType]

    halign: Literal["left", "center", "right", "justify", "auto"] = OptionProperty(
                        "auto", options=["left", "center", "right", "justify", "auto"])

    valign: Literal["bottom", "middle", "center", "top"] = OptionProperty("bottom",
                            options=["bottom", "middle", "center", "top"])

    color: RGBA = StatefulColorProperty(
        normal=uix_cs.Label.fg,
        states={
            "disabled": uix_cs.Label.fg_disabled,
        }
    )

    texture: Optional[Texture] = ObjectProperty(None, allownone=True)

    texture_size: Tuple[int, int] = ListProperty([0, 0])  # pyright: ignore[reportArgumentType]
