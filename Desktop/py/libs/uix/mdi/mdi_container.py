from kivy.uix.stencilview import StencilView
from kivy.properties import ObjectProperty, ListProperty, AliasProperty
from libs.uix.context_menu import ContextMenu, ContextMenuTemplates
from typing import Optional, List, Type
from libs.kivy_utils import AutoUnbindBehavior
from .mdi_window import MDIWindow
from .layout_mode import (
    ILayoutMode, TilingLayoutMode, FloatingLayoutMode
)
from kivy.uix.relativelayout import RelativeLayout
from kivy.lang import Builder

Builder.load_string("""
<-MDIContainer>:  # RelativeLayout
    size_hint: (1, 1)
    canvas.before:
        StencilPush
        Rectangle:
            pos: self.pos
            size: self.size
        StencilUse

        PushMatrix
        Translate:
            xy: self.pos

    canvas.after:
        PopMatrix

        StencilUnUse
        Rectangle:
            pos: self.pos
            size: self.size
        StencilPop
"""
)

class MDIContainer(AutoUnbindBehavior, RelativeLayout, StencilView):
    mdi_focused: Optional[MDIWindow] = ObjectProperty(None, allownone=True)
    mdi_list_showed: List[MDIWindow] = ListProperty()

    if_contain = AliasProperty(
        lambda self: len(self.mdi_list_showed) > 0,
        bind=["mdi_list_showed"]
    )

    _layout_mode: ILayoutMode = ObjectProperty(allownone=False, rebind=True)
    def get_layout_mode(self) -> ILayoutMode:
        if not self._layout_mode:
            self._layout_mode = FloatingLayoutMode(self, self._layout_mode)
            self._layout_mode.register_keyboard_context()
        return self._layout_mode
    def set_layout_mode(self, layout_mode: Type[ILayoutMode]):
        if isinstance(self._layout_mode, layout_mode):
            return False
        if self._layout_mode:
            self._layout_mode.unregister_keyboard_context()

        for mdi in self.mdi_list_showed:
            mdi.clear_layout_state()

        self._layout_mode = layout_mode(self, self._layout_mode)
        self._layout_mode.register_keyboard_context()
        return True
    layout_mode = AliasProperty(
        get_layout_mode,
        set_layout_mode
    )

    def on_mdi_list_showed(self, _, mdi_list_showed: List[MDIWindow]):
        self.layout_mode.sync_mdi_list_showed(mdi_list_showed)

    _kv_ready = False
    def on_kv_post(self, _):
        super().on_kv_post(_)
        self._kv_ready = True

    def _on_mdi_kv_post(self, mdi: MDIWindow, _):
        mdi.unbind(on_kv_post=self._on_mdi_kv_post)
        if not mdi.hidden:
            self._add_mdi_widget(mdi)

    def add_widget(self, widget, *args, **kwargs):
        if not isinstance(widget, MDIWindow):
            raise TypeError("add_widget for MDIContainer must be MDIWindow")
        if not self._kv_ready:
            widget.bind(on_kv_post=self._on_mdi_kv_post)
            return
        self._add_mdi_widget(widget)

    def _add_mdi_widget(self, mdi):
        if mdi in self.mdi_list_showed:
            self.set_focus(mdi)
            return

        mdi.mdi_container = self
        self.layout_mode.show_mdi(mdi)
        self.mdi_list_showed.append(mdi)
        self.set_focus(mdi)
        was_hidden = mdi.hidden
        mdi.hidden = False
        if was_hidden:
            mdi.property("hidden").dispatch(mdi)

    def remove_widget(self, widget, *args, **kwargs):
        if not isinstance(widget, MDIWindow):
            raise TypeError("remove_widget for MDIContainer must be MDIWindow")
        widget.mdi_container = None
        if widget in self.mdi_list_showed:
            self.layout_mode.hide_mdi(widget)
            self.mdi_list_showed.remove(widget)
        if not self.mdi_list_showed:
            self.set_focus(None)
        widget.hidden = True

    def clear_widgets(self):
        for mdi in self.mdi_list_showed[:]:
            self.remove_widget(mdi)

    def _layout_add_widget(self, widget, *args, **kwargs):
        RelativeLayout.add_widget(self, widget, *args, **kwargs)

    def _layout_remove_widget(self, widget, *args, **kwargs):
        RelativeLayout.remove_widget(self, widget, *args, **kwargs)

    def _clear_layout_widgets(self):
        for child in self.children[:]:
            RelativeLayout.remove_widget(self, child)

    def switch_focus(self):
        if not self.mdi_list_showed:
            return
        current_idx = self.mdi_list_showed.index(self.mdi_focused) if self.mdi_focused else -1
        new_idx = (current_idx + 1) % len(self.mdi_list_showed)
        self.set_focus(self.mdi_list_showed[new_idx])

    def on_touch_down(self, touch):
        touch.push()
        touch.apply_transform_2d(self.to_local)
        if self.collide_point(*touch.pos) and not self.layout_mode.find_mdi_at_pos(touch.pos):
            if touch.button == "right":
                self.open_context_menu(touch.pos)
                touch.pop()
                return True
        ret = self.layout_mode.handle_touch_down(touch)
        touch.pop()
        return ret

    def on_touch_move(self, touch):
        touch.push()
        touch.apply_transform_2d(self.to_local)
        ret = self.layout_mode.handle_touch_move(touch)
        touch.pop()
        return ret

    def on_touch_up(self, touch):
        touch.push()
        touch.apply_transform_2d(self.to_local)
        ret = self.layout_mode.handle_touch_up(touch)
        touch.pop()
        return ret

    def on_mouse_move(self, pos):
        self.layout_mode.handle_mouse_move(self.to_local(*pos))

    def set_focus(self, mdi_window):
        self._discard_focus()
        if mdi_window is None:
            return
        mdi_window.focus = True
        self.mdi_focused = mdi_window
        self.layout_mode.on_mdi_focus(mdi_window)

    def _discard_focus(self):
        if self.mdi_focused:
            self.mdi_focused.focus = False
        self.mdi_focused = None

    LAYOUT_MODES = (
        FloatingLayoutMode,
        TilingLayoutMode,
    )
    def open_context_menu(self, pos):
        ctx_menu = ContextMenu(items=[
            ContextMenuTemplates.button(
                text="Закрыть все окна",
                on_release=self.close_all_windows,
            ),
            ContextMenuTemplates.spinner(
                text="Оконный менеджер",
                values=self.LAYOUT_MODES,
                selected=type(self.layout_mode),
                value_to_host=lambda cls: cls.title,
                on_select=lambda _, cls: setattr(self, "layout_mode", cls),
            )
        ])
        ctx_menu.open(self, pos=self.to_window(*pos))

    def close_all_windows(self, _):
        for mdi in self.mdi_list_showed[:]:
            self.remove_widget(mdi)


if __name__ == "__main__":
    from kivy.app import App
    from kivy.lang import Builder
    from kivy.properties import ObjectProperty
    from libs.uix.mdi.mdi_container import MDIContainer
    from kivy.uix.boxlayout import BoxLayout
    from libs.uix.mdi.layout_mode import (
        ILayoutMode, TilingLayoutMode, FloatingLayoutMode
    )
    from libs.uix.button import HoverToggleButton
    from libs import sdl2_keyboard

    sdl2_keyboard.init()


    class MDIHoverToggleButton(HoverToggleButton):
        mdi = ObjectProperty()
        mdi_container = ObjectProperty()

        def on_kv_post(self, _):
            super().on_kv_post(_)
            self.mdi.bind(hidden=self._set_state_by_mdi)
            self._set_state_by_mdi(self.mdi, self.mdi.hidden)

        def _set_state_by_mdi(self, _, hidden: bool):
            self.state = "normal" if hidden else "down"

        def on_state(self, _, state: str):
            if state == "down":
                self.mdi_container.add_widget(self.mdi)
            elif state == "normal":
                self.mdi_container.remove_widget(self.mdi)


    Builder.load_string("""
    #:import FloatingLayoutMode libs.uix.mdi.layout_mode.FloatingLayoutMode
    #:import TilingLayoutMode libs.uix.mdi.layout_mode.TilingLayoutMode

    <MDIBox@BoxLayout>:
        canvas:
            Color:
                rgba: (1, 0, 0, 1)
            Rectangle:
                size: self.size
                pos: self.pos

    <Root>:
        orientation: "vertical"
        ribbon: ribbon
        mdi_container: mdi_container
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
                text: "1"
                mdi: mdi_1.__self__
                mdi_container: mdi_container
            MDIHoverToggleButton:
                text: "2"
                mdi: mdi_2.__self__
                mdi_container: mdi_container
            MDIHoverToggleButton:
                text: "3"
                mdi: mdi_3.__self__
                mdi_container: mdi_container
            MDIHoverToggleButton:
                text: "4"
                mdi: mdi_4.__self__
                mdi_container: mdi_container
        MDIContainer:
            id: mdi_container
            layout_mode: TilingLayoutMode
            MDIWindow:
                id: mdi_1
                title: "test#1"
                hidden: True
                MDIBox:
            MDIWindow:
                id: mdi_2
                title: "test#2"
                hidden: True
                MDIBox:
            MDIWindow:
                id: mdi_3
                title: "test#3"
                hidden: True
                MDIBox:
            MDIWindow:
                id: mdi_4
                title: "test#4"
                MDIBox:
    """
    )

    class Root(BoxLayout):
        ribbon = ObjectProperty()
        mdi_container = ObjectProperty()

    class Test(App):
        def build(self):
            return Root()

    Test().run()
