from kivy.uix.boxlayout import BoxLayout
from kivy.properties import (
    ObjectProperty, BooleanProperty, NumericProperty, AliasProperty
)
from kivy.clock import Clock
from libs.uix.button import HoverToggleButton
from libs.uix.behaviors.mouse import TouchMouseBehavior
from libs.properties import ContextualNumericProperty
from libs.animation import StatefulColorProperty
from libs.uix import colorscheme as uix_cs
from kivy.lang import Builder
from typing import Dict, Optional

Builder.load_string("""
#:import uix_cs libs.uix.colorscheme
#:import Window kivy.core.window.Window


<WorkspaceToggleButton>:  # HoverToggleButton
    text: str(self.workspace_index + 1)
    size_hint: (None, None)
    size: ("20dp", "20dp")
    font_size: "12sp"
    group: "workspace_switcher_{}".format(self.workspace_manager.uid)
    allow_no_selection: False

<WorkspaceSwitcherMenu>:  # BoxLayout
    spacing: "2dp"
    padding: "2dp"
    size_hint_y: None
    height: "24dp"
    canvas.before:
        Color:
            rgba: uix_cs.general.menu_wrap_bg
        Rectangle:
            pos: self.pos
            size: self.size

<WorkspaceManager>:  # BoxLayout
    menu: menu

    orientation: "vertical"
    spacing: "2dp"

    WorkspaceSwitcherMenu:
        id: menu
        workspace_manager: root
""")


class WorkspaceToggleButton(HoverToggleButton):
    workspace_manager = ObjectProperty()
    workspace_index = NumericProperty()
    workspace = ObjectProperty(rebind=True, allownone=True)
    is_workspace_not_contain = BooleanProperty()

    animation_time = 0.14
    color = StatefulColorProperty(
        normal=uix_cs.WorkspaceToggleButton.color_if_contain,
        states={
            "is_workspace_not_contain": uix_cs.WorkspaceToggleButton.color_if_not_contain,
        }
    )
    def set_workspace_contain(self, *args):
        self.is_workspace_not_contain = self.workspace is None or not self.workspace.if_contain

    def on_workspace(self, _, workspace):
        if workspace:
            workspace.bind(if_contain=self.set_workspace_contain)
        self.set_workspace_contain()

    def on_is_down(self, _, is_down: bool):
        if is_down:
            self.workspace_manager.set_workspace(self.workspace_index)


class WorkspaceSwitcherMenu(TouchMouseBehavior, BoxLayout):
    workspace_manager = ObjectProperty()
    toggle_list = None

    def __init__(self, **kwargs):
        self.toggle_list = []
        super().__init__(**kwargs)

    def on_kv_post(self, _):
        for i in range(self.workspace_manager.workspace_count):
            self._add_toggle(i)

    def _add_toggle(self, workspace_index: int) -> None:
        toggle = WorkspaceToggleButton(
            workspace_index=workspace_index,
            workspace_manager=self.workspace_manager,
        )
        self.toggle_list.append(toggle)
        self.add_widget(toggle)

    def get_toggle(self, toggle_id:  Optional[int]) -> HoverToggleButton:
        return self.toggle_list[toggle_id]

    def switch_toggle(self, toggle_id: Optional[int]) -> None:
        self.get_toggle(toggle_id or 0).trigger_action(0)

    def on_scroll_up(self, touch):
        self.switch_toggle(min(self.workspace_manager.workspace_now_index + 1, len(self.toggle_list) - 1))
        return False

    def on_scroll_down(self, touch):
        self.switch_toggle(max(self.workspace_manager.workspace_now_index - 1, 0))
        return False


class WorkspaceBehavior:
    if_contain = BooleanProperty(False)
    showed = BooleanProperty(False)
    index = NumericProperty()


class WorkspaceManager(BoxLayout):
    menu = ObjectProperty()

    workspace_cls = ObjectProperty()
    workspace_count = NumericProperty(9)

    workspaces: Dict[int, WorkspaceBehavior] = None
    workspace_now_index = ContextualNumericProperty(
        default=0,
        min_getter=lambda self: 0,
        max_getter=lambda self: self.workspace_count - 1,
        dependencies=["workspace_count"]
    )

    def __init__(self, **kwargs):
        self.register_event_type("on_workspace_opened")
        self.register_event_type("on_workspace_closed")
        self.register_event_type("on_workspace_created")
        self.register_event_type("on_workspace_removed")
        self.workspaces = {i: None for i in range(self.workspace_count)}
        super().__init__(**kwargs)

    def on_workspace_opened(self, workspace_index: int, workspace: WorkspaceBehavior):
        pass

    def on_workspace_closed(self, workspace_index: int, workspace: WorkspaceBehavior):
        pass

    def on_workspace_created(self, workspace_index: int, workspace: WorkspaceBehavior):
        pass

    def on_workspace_removed(self, workspace_index: int, workspace: WorkspaceBehavior):
        pass

    def on_kv_post(self, _) -> None:
        if self.workspace_cls is None:
            raise ValueError(f"{self}: workspace_cls not defined")
        initial = self.workspace_now_index
        self.set_workspace(initial)
        prop = self.property("workspace_now_index")
        if initial == prop.defaultvalue:
            prop.dispatch(self)

    def set_workspace(self, workspace_index: int) -> None:
        self.workspace_now_index = workspace_index

    def create_workspace(self, workspace_index: int) -> WorkspaceBehavior:
        workspace = self.workspaces[workspace_index]
        if workspace is None:
            workspace = self._create_workspace_instance(workspace_index)
            self.workspaces[workspace_index] = workspace
            self.menu.get_toggle(workspace_index).workspace = workspace
            self.dispatch("on_workspace_created", workspace_index, workspace)
        return workspace

    def _create_workspace_instance(self, workspace_index: int) -> WorkspaceBehavior:
        return self.workspace_cls(index=workspace_index)

    def _hide_workspace(self, index: int) -> None:
        if index is None:
            return
        workspace_now = self.workspaces[index]
        if workspace_now is not None:
            if not workspace_now.if_contain:
                self.menu.get_toggle(index).workspace = None
                self.workspaces[index] = None
                self.dispatch("on_workspace_removed", index, workspace_now)
            workspace_now.showed = False
            self.remove_widget(workspace_now)
            self.dispatch("on_workspace_closed", index, workspace_now)

    def _show_workspace(self, workspace_index: int, workspace: WorkspaceBehavior) -> None:
        self.add_widget(workspace)
        self.workspace_now_index = workspace_index
        self.workspaces[workspace_index] = workspace
        workspace.showed = True
        self.menu.get_toggle(workspace_index).workspace = workspace
        self.menu.switch_toggle(workspace_index)
        self.dispatch("on_workspace_opened", workspace_index, workspace)

    workspace_now = AliasProperty(
        lambda self: self.create_workspace(self.workspace_now_index),
        bind=["workspace_now_index"], rebind=True
    )

    prev_workspace_index = None
    def on_workspace_now_index(self, _, index: int):
        self._hide_workspace(self.prev_workspace_index)
        workspace = self.create_workspace(index)
        self._show_workspace(index, workspace)
        self.prev_workspace_index = index
