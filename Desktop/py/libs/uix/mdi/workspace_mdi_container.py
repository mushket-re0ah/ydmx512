from libs.uix.mdi.mdi_container import MDIContainer
from libs.uix.workspace_manager import WorkspaceBehavior


class WorkspaceMDIContainer(MDIContainer, WorkspaceBehavior):
    def on_showed(self, _, showed: bool):
        layout_mode = self.layout_mode
        if showed:
            layout_mode.register_keyboard_context()
        else:
            layout_mode.unregister_keyboard_context()
