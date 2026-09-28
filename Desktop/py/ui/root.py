from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty

from ui.main_ribbon import MainRibbon
from ui.components.database_workspace_mdi_container_manager import DatabaseWorkspaceMDIContainerManager
# pseudo lazy...
import libs.uix.layouts  # lazy kv import initialize
import libs.uix.label  # lazy kv import initialize
import libs.uix.button  # lazy kv import initialize
import libs.uix.splitter  # lazy kv import initialize
import libs.uix.input  # lazy kv import initialize
import libs.uix.rotary_button  # lazy kv import initialize
import libs.uix.restricted_scrollview  # lazy kv import initialize
import libs.uix.recycle_restricted_scrollview  # lazy kv import initialize
import libs.uix.recycle_dropdown  # lazy kv import initialize
import libs.uix.recycle_spinner  # lazy kv import initialize
import libs.uix.scroll_layout  # lazy kv import initialize
import libs.uix.workspace_manager  # lazy kv import initialize
import libs.uix.context_menu  # lazy kv import initialize
import libs.uix.snippet  # lazy kv import initialize
import libs.uix.database_table  # lazy kv import initialize
import libs.uix.mdi.mdi_window  # lazy kv import initialize
import libs.uix.filelist  # lazy kv import initialize
import libs.uix.map_layout  # lazy kv import initialize


class Root(BoxLayout):
    main_ribbon = ObjectProperty()
    mdi_container_manager = ObjectProperty()

    def on_kv_post(self, _):
        self.mdi_container_manager = DatabaseWorkspaceMDIContainerManager()
        self.main_ribbon = MainRibbon(mdi_container_manager=self.mdi_container_manager)
        self.add_widget(self.main_ribbon)
        self.add_widget(self.mdi_container_manager)
        self.mdi_container_manager.load_database_data(self.main_ribbon.mdi_list)
