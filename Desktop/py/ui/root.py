from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from ui.components.database_workspace_mdi_container_manager import (
    DatabaseWorkspaceMDIContainerManager,
)
from ui.main_ribbon import MainRibbon


class Root(BoxLayout):
    main_ribbon: MainRibbon = ObjectProperty()
    mdi_container_manager: DatabaseWorkspaceMDIContainerManager = ObjectProperty()

    def on_kv_post(self, base_widget: Widget):
        self.mdi_container_manager = DatabaseWorkspaceMDIContainerManager()
        self.main_ribbon = MainRibbon(mdi_container_manager=self.mdi_container_manager)
        self.add_widget(self.main_ribbon)
        self.add_widget(self.mdi_container_manager)
        self.mdi_container_manager.load_database_data(self.main_ribbon.mdi_list)
