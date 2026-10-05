from kivy.lang import Builder
from kivy.properties import ObjectProperty

from database import db
from libs.uix.button import HoverToggleButton
from libs.uix.layouts import MenuPanel
from ui.mdi.library import LibraryContentEnum, MDILibrary

Builder.load_file("ui/mdi/library/menu.kv")


class LibraryMenu(MenuPanel):
    library: MDILibrary = ObjectProperty()

    toggle_fixture: HoverToggleButton = ObjectProperty()
    toggle_params: HoverToggleButton = ObjectProperty()
    toggle_brands: HoverToggleButton = ObjectProperty()

    def change_content(self, content_enum: LibraryContentEnum):
        self.library.change_content(content_enum)

    def on_create_release(self):
        content_enum = self.library.content_enum
        if content_enum is LibraryContentEnum.FIXTURE:
            self.library.change_content(LibraryContentEnum.FIXTURE_EDITOR, None)
        elif content_enum is LibraryContentEnum.FIXTURE_PARAMS:
            db.fixture_param.add_row()
        elif content_enum is LibraryContentEnum.BRAND:
            db.brand.add_row()
