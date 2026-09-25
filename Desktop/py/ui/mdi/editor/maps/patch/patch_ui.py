from kivy.properties import BooleanProperty, ObjectProperty, ColorProperty
from kivy.lang import Builder
from kivy.clock import Clock
from database.patch import RowPatch
from libs.mouse_manager.hover import HoverBehavior
from libs.animation import AnimationBehavior
from libs.uix.button import ExpansiveToggleButtonBehavior
from libs.kivy_utils import AutoUnbindBehavior
from ui.mdi.patch_list.patch_ui import BasePatchUi
from libs.uix.label import RestrictedLabel
from libs.uix.button import HoverButton
from misc import colorscheme as cs
from libs.animation import StatefulColorProperty
from libs import logger
from ui.mdi.editor.automation.tools import InterpatchPhaseTool
from database.playback.renderer.render_data import InterpatchSpec
from kivy.uix.relativelayout import RelativeLayout
from database.playback import RowPlayback
Builder.load_file("ui/mdi/editor/maps/patch/patch_ui.kv")


class LabelInterpatchIndex(RestrictedLabel):
    pass


class ButtonInterpatchUngroup(HoverButton):
    patch_ui = ObjectProperty()

    def ungroup_interpatch(self):
        playback = self.patch_ui.playback
        if not playback:
            return
        automation = self.patch_ui.patch_map_editor.editor.content.automation
        automation.set_tool(InterpatchPhaseTool, playback.renderer.get_rows(self.patch_ui.patch))
        automation.tool_action("clear_phase")
        automation.tool_action("finish")


class EditorPatchUi(ExpansiveToggleButtonBehavior, BasePatchUi):
    is_limiters = BooleanProperty(False)
    blocked = BooleanProperty(True)  # Блок на случай если не выбран плейбек

    bg = StatefulColorProperty(
        normal=cs.EditorPatchUi.bg_normal,
        states={
            "is_down": cs.EditorPatchUi.bg_selected,
            "hover": cs.EditorPatchUi.bg_hover,
            "blocked": cs.EditorPatchUi.bg_blocked,
        }
    )
    border_color = StatefulColorProperty(
        normal=cs.EditorPatchUi.border_normal,
        states={
            "interpatch_phase_spec": cs.EditorPatchUi.border_interpatch_phase,
            "render_data_exist": cs.EditorPatchUi.border_data_exist
        }
    )
    playback = ObjectProperty()
    patch_map_editor = ObjectProperty()

    interpatch_phase_spec = ObjectProperty(None, allownone=True)
    render_data_exist = BooleanProperty(False)

    _label_interpatch_index = None
    _button_interpatch_ungroup = None

    def __init__(self, create_animation=True, **kwargs):
        patch = kwargs["patch"]
        patch_map = kwargs["patch_map"]
        patch.bind(grid_pos=self.setter("grid_pos"))
        super().__init__(**kwargs)
        self.patch_map_editor.editor_content.bind(on_render_changed=self._sync_render)

    def on_playback(self, _, playback: RowPlayback):
        self._sync_render(_, playback.renderer)

    def _sync_render(self, _, renderer):
        self.render_data_exist = renderer.patch_render_data_exist(self.patch)
        self.interpatch_phase_spec = renderer.get_interpatch_spec(self.patch)

    def on_interpatch_phase_spec(self, _, spec: InterpatchSpec):
        if not spec:
            self._remove_interpatch_widgets()
        else:
            self._update_interpatch_widgets(spec)

    def _update_interpatch_widgets(self, spec: InterpatchSpec):
        lbl_text = "M" if spec.master_patch is self.patch else str(spec.ordered_patches.index(self.patch) + 1)
        if self._label_interpatch_index:
            self._label_interpatch_index.text = lbl_text
        else:
            self._label_interpatch_index = LabelInterpatchIndex(text=lbl_text)
            self.add_widget(self._label_interpatch_index)
        if not self._button_interpatch_ungroup:
            self._button_interpatch_ungroup = ButtonInterpatchUngroup(patch_ui=self)
            self.add_widget(self._button_interpatch_ungroup)

    def _remove_interpatch_widgets(self):
        if self._label_interpatch_index:
            self.remove_widget(self._label_interpatch_index)
            self._label_interpatch_index = None
        if self._button_interpatch_ungroup:
            self.remove_widget(self._button_interpatch_ungroup)
            self._button_interpatch_ungroup = None

    _activate_block = False
    def on_is_down(self, _, is_down: bool):
        if self._activate_block:
            return
        if is_down:
            self.patch_map_editor.activate_patch(self.patch)
        else:
            self.patch_map_editor.deactivate_patch(self.patch)

    def _do_press(self):
        if not self.blocked:
            self.is_down = not self.is_down
