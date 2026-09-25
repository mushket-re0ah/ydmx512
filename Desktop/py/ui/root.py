from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty

import ui.components
from ui.main_ribbon import MainRibbon
from ui.components.database_workspace_mdi_container_manager import DatabaseWorkspaceMDIContainerManager
import libs.uix.layouts
import libs.uix.label
import libs.uix.button
import libs.uix.splitter
import libs.uix.input
import libs.uix.rotary_button
import libs.uix.restricted_scrollview
import libs.uix.recycle_restricted_scrollview
import libs.uix.recycle_dropdown
import libs.uix.recycle_spinner
import libs.uix.scroll_layout
import libs.uix.workspace_manager
import libs.uix.context_menu
import libs.uix.snippet
import libs.uix.database_table
import libs.uix.mdi.mdi_window
import libs.uix.filelist
import libs.uix.map_layout


class Root(BoxLayout):
    main_ribbon = ObjectProperty()
    mdi_container_manager = ObjectProperty()

    def on_kv_post(self, _):
        self.mdi_container_manager = DatabaseWorkspaceMDIContainerManager()
        self.main_ribbon = MainRibbon(mdi_container_manager=self.mdi_container_manager)
        self.add_widget(self.main_ribbon)
        self.add_widget(self.mdi_container_manager)
        self.mdi_container_manager.load_database_data(self.main_ribbon.mdi_list)
