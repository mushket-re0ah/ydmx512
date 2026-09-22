from ..workspace_manager import WorkspaceBehavior
from .mdi_container import MDIContainer

class WorkspaceMDIContainer(MDIContainer, WorkspaceBehavior):
    def on_showed(self, _, showed: bool):
        layout_mode = self.layout_mode
        if showed:
            layout_mode.register_keyboard_context()
        else:
            layout_mode.unregister_keyboard_context()
