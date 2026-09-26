from kivy.properties import StringProperty, ObjectProperty, NumericProperty, AliasProperty
from ui.components.database_mdi_window import DatabaseMDIWindow
from libs.serialize import *
from typing import List, Optional
from misc import constants
from libs.properties import ClampedNumericProperty


class MDIChecker(DatabaseMDIWindow):
    _db_title_id = "checker"

    title = StringProperty("Прозвон")
    universe_now = ClampedNumericProperty(1, 1, constants.DMX_UNIVERSE_COUNT)

    menu = ObjectProperty()
    channels_ui = ObjectProperty()

    view_context_template = {
        "universe_now": 1,
        "channels_ui.channel_sliders.scrollview/scroll_element@universe_now": 0
    }

    def on_hidden(self, _, hidden: bool):
        super().on_hidden(_, hidden)
        if hidden or self.menu:
            return
        self.__create_channels_ui()
        self.__create_menu()

    def __create_menu(self):
        from ui.mdi.checker.menu import CheckerMenu
        self.menu = CheckerMenu(checker=self)
        self.add_widget(self.menu, 1)

    def __create_channels_ui(self):
        from ui.mdi.checker.channels_ui import CheckerChannelsUi
        self.channels_ui = CheckerChannelsUi(checker=self)
        self.add_widget(self.channels_ui)
        self.channels_ui.channel_sliders.scrollview.bind(
            scroll_element=self.setter("address_start")
        ) 

    def set_address_start(self, scroll_element: int):
        self.channels_ui.channel_sliders.scroll_element = scroll_element
        return True
    address_start = AliasProperty(
        lambda self: self.channels_ui.channel_sliders.scroll_element + 1 if self.channels_ui.channel_sliders.scroll_element else 0,
        set_address_start
    )

    def create_hotkeys(self) -> Optional[dict]:
        return {
            **super().create_hotkeys(),
            **{
                frozenset({"left"}): self._handle_scroll_left,
                frozenset({"right"}): self._handle_scroll_right,
            }
        }

    def _handle_scroll_left(self):
        self.address_start -= 1

    def _handle_scroll_right(self):
        self.address_start += 1
