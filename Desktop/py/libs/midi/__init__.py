from kivy.event import EventDispatcher


class MIDIDispatcher(EventDispatcher):
    __events__ = ("on_note_on", "on_note_off", "on_controller_change",)

    def on_note_on(self, channel: int, intensive: int):
        pass

    def on_note_off(self, channel: int, intensive: int):
        pass

    def on_controller_change(self, channel: int, intensive: int):
        pass


midi = MIDIDispatcher()
