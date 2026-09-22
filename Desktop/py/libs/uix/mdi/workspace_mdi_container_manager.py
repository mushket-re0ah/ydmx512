from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.widget import Widget
from libs.uix.workspace_manager import WorkspaceManager, WorkspaceBehavior
from libs.uix.button import HoverToggleButton
from libs.uix.mdi.layout_mode import TilingLayoutMode, FloatingLayoutMode
from .mdi_window import MDIWindow
from .workspace_mdi_container import WorkspaceMDIContainer
from misc import constants
from typing import Optional
from libs.uix.mdi.layout_mode.tiling import TilingOrientation
from libs.properties import BindableObjectProperty
from libs.kivy_utils import AutoUnbindBehavior
from kivy.lang import Builder

Builder.load_string("""
#:import TilingLayoutMode libs.uix.mdi.layout_mode.TilingLayoutMode
#:import FloatingLayoutMode libs.uix.mdi.layout_mode.FloatingLayoutMode
#:import TilingOrientation libs.uix.mdi.layout_mode.tiling.TilingOrientation

<TilingOrientationSwitcher>:
    text: "Вертикаль" if self.is_down else "Горизонталь"
    size_hint: (None, 1)
    width: "128dp"
    on_is_down: self.mdi_manager.workspace_now.layout_mode.tiling_orientation = TilingOrientation.VERTICAL if self.is_down else TilingOrientation.HORIZONTAL
    is_down: not ((isinstance(self.mdi_manager.workspace_now.layout_mode, TilingLayoutMode) and self.mdi_manager.workspace_now.layout_mode.tiling_orientation) is TilingOrientation.HORIZONTAL)

<LayoutModeSwitcher>:
    text: "Tiling" if self.is_down else "Floating"
    size_hint: (None, 1)
    width: "128dp"
    is_down: isinstance(self.mdi_manager.workspace_now.layout_mode, TilingLayoutMode)


<WorkspaceMDIContainerManager>:  # WorskpaceManager
"""
)

class LayoutModeSwitcher(HoverToggleButton):
    mdi_manager = ObjectProperty(rebind=True)

    def on_press(self):
        workspace = self.mdi_manager.workspace_now
        if isinstance(workspace.layout_mode, TilingLayoutMode):
            workspace.layout_mode = FloatingLayoutMode
        else:
            workspace.layout_mode = TilingLayoutMode
        self.mdi_manager.refresh_menu()

class TilingOrientationSwitcher(HoverToggleButton):
    mdi_manager = ObjectProperty(rebind=True)


class WorkspaceMDIContainerManager(AutoUnbindBehavior, WorkspaceManager):
    workspace_cls = ObjectProperty(WorkspaceMDIContainer)
    workspace_count = NumericProperty(constants.DATABASE_MDI_WORKSPACES_COUNT)
    window_switcher = ObjectProperty()
    orientation_switcher = ObjectProperty(allownone=True)

    def on_kv_post(self, _):
        super().on_kv_post(_)
        self.menu.add_widget(Widget(size_hint=(1, 1)))
        self.window_switcher = LayoutModeSwitcher(mdi_manager=self)
        self.menu.add_widget(self.window_switcher)
        self.bind(workspace_now=self.refresh_menu)
        self.refresh_menu()

    def refresh_menu(self, *args):
        workspace = self.workspace_now
        if workspace is None:
            return

        if isinstance(workspace.layout_mode, TilingLayoutMode):
            if self.orientation_switcher is None:
                self.orientation_switcher = TilingOrientationSwitcher(mdi_manager=self)
                self.menu.add_widget(self.orientation_switcher, 1)
        else:
            if self.orientation_switcher is not None:
                self.menu.remove_widget(self.orientation_switcher)
                self.orientation_switcher = None

    def show_mdi(self, mdi: MDIWindow, workspace_index: Optional[int] = None):
        workspace_index = self.workspace_now_index if workspace_index is None else workspace_index

        workspace = self.workspaces[workspace_index]
        if workspace is None:
            workspace = self.create_workspace(workspace_index)

        if mdi.mdi_container is workspace:
            workspace.set_focus(mdi)
            return

        if mdi.mdi_container is not None:
            mdi.mdi_container.remove_widget(mdi)

        workspace.add_widget(mdi)

    def hide_mdi(self, mdi: MDIWindow):
        if mdi.mdi_container is not None:
            mdi.mdi_container.remove_widget(mdi)

    def _create_workspace_instance(self, workspace_index: int) -> WorkspaceBehavior:
        return self.workspace_cls(index=workspace_index)


if __name__ == "__main__":
    from kivy.app import App
    from kivy.lang import Builder
    from kivy.properties import ObjectProperty
    from libs.uix.mdi.mdi_window import MDIWindow
    from libs.uix.mdi.workspace_mdi_container import WorkspaceMDIContainer
    from libs.uix.mdi.workspace_mdi_container_manager import WorkspaceMDIContainerManager
    from kivy.uix.boxlayout import BoxLayout
    from libs.uix.mdi.layout_mode import (
        ILayoutMode, TilingLayoutMode, FloatingLayoutMode
    )
    from libs.uix.button import HoverToggleButton
    from libs import sdl2_keyboard

    sdl2_keyboard.init()


    class MDIHoverToggleButton(HoverToggleButton):
        mdi = ObjectProperty()
        mdi_container_manager = ObjectProperty()

        def on_mdi(self, _, mdi):
            mdi.bind(hidden=self._set_state_by_mdi)
            self._set_state_by_mdi(mdi, mdi.hidden)

        def _set_state_by_mdi(self, _, hidden: bool):
            self.state = "normal" if hidden else "down"

        def on_state(self, _, state: str):
            if state == "down":
                self.mdi_container_manager.show_mdi(self.mdi)
            elif state == "normal":
                self.mdi_container_manager.hide_mdi(self.mdi)


    class TestMDIWindow(MDIWindow):
        pass

    Builder.load_string("""
    <MDIBox@BoxLayout>:
        canvas:
            Color:
                rgba: (1, 0, 0, 1)
            Rectangle:
                size: self.size
                pos: self.pos

    <TestMDIWindow>:  # MDIWindow
        MDIBox:

    <Root>:
        orientation: "vertical"
        ribbon: ribbon
        mdi_container_manager: mdi_container_manager
        mdi_toggle_1: mdi_toggle_1
        mdi_toggle_2: mdi_toggle_2
        mdi_toggle_3: mdi_toggle_3
        mdi_toggle_4: mdi_toggle_4
        BoxLayout:
            id: ribbon
            size_hint_y: 0.2
            canvas:
                Color:
                    rgba: (0, 1, 0, 1)
                Rectangle:
                    size: self.size
                    pos: self.pos
            MDIHoverToggleButton:
                id: mdi_toggle_1
                text: "1"
            MDIHoverToggleButton:
                id: mdi_toggle_2
                text: "2"
            MDIHoverToggleButton:
                id: mdi_toggle_3
                text: "3"
            MDIHoverToggleButton:
                id: mdi_toggle_4
                text: "4"
        WorkspaceMDIContainerManager:
            id: mdi_container_manager
    """
    )


    class Root(BoxLayout):
        ribbon = ObjectProperty()
        mdi_container_manager = ObjectProperty()
        mdi_toggle_1 = ObjectProperty()
        mdi_toggle_2 = ObjectProperty()
        mdi_toggle_3 = ObjectProperty()
        mdi_toggle_4 = ObjectProperty()

        def on_kv_post(self, _):
            self.mdi_1 = TestMDIWindow(title="test#1", hidden=True)
            self.mdi_2 = TestMDIWindow(title="test#2", hidden=True)
            self.mdi_3 = TestMDIWindow(title="test#3", hidden=True)
            self.mdi_4 = TestMDIWindow(title="test#4", hidden=True)
            self.mdi_toggle_1.mdi_container_manager = self.mdi_container_manager
            self.mdi_toggle_1.mdi = self.mdi_1
            self.mdi_toggle_2.mdi_container_manager = self.mdi_container_manager
            self.mdi_toggle_2.mdi = self.mdi_2
            self.mdi_toggle_3.mdi_container_manager = self.mdi_container_manager
            self.mdi_toggle_3.mdi = self.mdi_3
            self.mdi_toggle_4.mdi_container_manager = self.mdi_container_manager
            self.mdi_toggle_4.mdi = self.mdi_4


    class Test(App):
        def build(self):
            return Root()

    Test().run()
