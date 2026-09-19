from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty

import ui.components
import ui.main_ribbon
import ui.mdi.mdi_container_manager
import ui.mdi.mdi_container

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
import ui.components.scroll_layout_map
import libs.uix.workspace_manager
import libs.uix.context_menu
import libs.uix.snippet
import libs.uix.database_table
import ui.components.mdi_window
import libs.uix.filelist


class Root(BoxLayout):
    main_ribbon = ObjectProperty()
    mdi_container_manager = ObjectProperty()
