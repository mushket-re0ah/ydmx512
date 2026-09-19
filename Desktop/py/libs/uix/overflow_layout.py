from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, ListProperty
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from libs.uix.layouts import ModalBoxLayout
from libs.mouse_manager.hover import NestedHoverBehavior
from typing import List
from kivy.lang import Builder


Builder.load_string("""
<OverflowLayout>:  # BoxLayout

<OverflowLayoutModal>:  # ModalBoxLayout
    width: self.minimum_width
"""
)


class OverflowLayoutModal(ModalBoxLayout):
    allow_hover_outside = True

    overflow_layout = ObjectProperty()

    def open(self, *args, **kwargs):
        super().open(*args, **kwargs)
        self.bind_to(Window, mouse_pos=self.check_mouse_pos)

    def on_dismiss(self, *args):
        self.clear_widgets()
        self.unbind_from(Window)

    def check_mouse_pos(self, _, mouse_pos: tuple):
        if not (self.overflow_layout.collide_point(*mouse_pos) or\
                self.collide_point(*mouse_pos)):
            self.dismiss()

    def on_touch_down(self, touch):
        return Widget.on_touch_down(self, touch)


class OverflowLayout(NestedHoverBehavior, BoxLayout):
    widget_list = ListProperty()
    modal = ObjectProperty(allownone=True)

    def __init__(self, **kwargs):
        self.trigger_update_overflow = Clock.create_trigger(self.update_overflow, -1)
        self.bind(
            width=self.trigger_update_overflow,
            widget_list=self.trigger_update_overflow,
            real_hover=self.trigger_update_overflow
        )
        super().__init__(**kwargs)

    def add_widget(self, widget, index=0, canvas=None):
        self.widget_list.append(widget)

    def update_overflow(self, _):
        if self.modal:
            return
        widgets_fits = self.calc_widget_fit()
        if not self.real_hover:
            self.clear_widgets()
            for c in widgets_fits:
                super().add_widget(c)
        elif widgets_fits != self.widget_list:
            self.open_modal(widgets_fits)

    def open_modal(self, widgets_fits: List[Widget]):
        modal = OverflowLayoutModal(
            overflow_layout=self,
            orientation="horizontal"
        )
        modal_widgets = [i for i in self.widget_list if i not in widgets_fits]
        for c in modal_widgets:
            modal.add_widget(c)
        modal.height = self.height
        modal_x = widgets_fits[-1].right if widgets_fits else self.x
        modal.open(None, pos=(modal_x, self.top))
        modal.bind(
            on_dismiss=self.on_dismiss_modal,
        )
        self.modal = modal

    def calc_widget_fit(self) -> List[Widget]:
        widget_fits = []
        for widget in self.widget_list:
            if widget.right < self.right:
                widget_fits.append(widget)
            else:
                break
        return widget_fits

    def on_dismiss_modal(self, _):
        self.modal = None
        self.trigger_set_real_hover()
        self.trigger_update_overflow()
