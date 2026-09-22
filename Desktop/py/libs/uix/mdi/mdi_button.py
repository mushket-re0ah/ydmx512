from libs.uix.button import ImageToggleButton, ImageButton
from kivy.lang import Builder
from kivy.properties import ObjectProperty

Builder.load_string("""
#:import imgs_path misc.imgs_path
<MDIButtonLock>:  # ImageToggleButton
    size_hint: (None, None)
    size: ("20dp", "20dp")
    -background_normal: imgs_path.mdi_lock_normal
    -background_down: imgs_path.mdi_lock_down

<MDIButtonExpand>:  # ImageToggleButton
    size_hint: (None, None)
    size: ("20dp", "20dp")
    -background_normal: imgs_path.mdi_expand_normal
    -background_down: imgs_path.mdi_expand_down
    discard_state_release: False

<MDIButtonClose>:  # ImageButton
    size_hint: (None, None)
    size: ("20dp", "20dp")
    -background_normal: imgs_path.mdi_close_normal
    -background_down: imgs_path.mdi_close_down
    on_release: root.close()
""")

class MDIStateToggleBehavior:
    mdi = ObjectProperty(allownone=False)
    state_key = None  # for override

    def on_mdi(self, _, mdi):
        mdi.bind(state=self.on_mdi_state)
        self.on_mdi_state(mdi, mdi.state)

    def on_mdi_state(self, _, state: dict):
        self.is_down = self.mdi.get_layout_state(self.state_key, False)
        self.set_disabled_by_state(state)

    def on_is_down(self, _, is_down: bool):
        self.mdi.set_layout_state(**{self.state_key: is_down})

    def set_disabled_by_state(self, state: dict):
        pass


class MDIButtonLock(MDIStateToggleBehavior, ImageToggleButton):
    state_key = "locked"

class MDIButtonExpand(MDIStateToggleBehavior, ImageToggleButton):
    state_key = "expanded"

    def set_disabled_by_state(self, state: dict):
        self.disabled = self.mdi.get_layout_state("locked", False)


class MDIButtonClose(ImageButton):
    mdi = ObjectProperty(allownone=False)

    def close(self):
        self.mdi.mdi_container.remove_widget(self.mdi)
