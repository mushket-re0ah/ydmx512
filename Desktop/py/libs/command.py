from typing import List


class Command:
    def execute(self) -> bool:
        return self._do_execute()

    def _do_execute(self) -> bool:
        raise NotImplementedError()

    def undo(self):
        self._do_undo()

    def _do_undo(self):
        raise NotImplementedError()

    def redo(self):
        self._do_redo()

    def _do_redo(self):
        raise NotImplementedError()

    def merge(self, command: "Command"):
        raise NotImplementedError()


class CommandSession:
    def __init__(self):
        self.commands = []

    def add_command(self, command) -> bool:
        success = command.execute()
        if not success:
            return False

        if self.commands:
            last = self.commands[-1]
            if type(last) is type(command) and last.merge(command):
                return True  # слияние удалось, новая команда не добавляется

        self.commands.append(command)
        return True

    def check_existing_commands(self) -> bool:
        return bool(self.commands)

    def get_commands(self) -> List[Command]:
        return self.commands

    def undo(self):
        for command in reversed(self.commands):
            command.undo()

    def redo(self):
        for command in self.commands:
            command.redo()


class CommandHistory:
    session_cls = CommandSession

    def __init__(self, *args, **kwargs):
        self.history = []
        self.redo_stack = []
        self.command_session: Optional[CommandSession] = None
        super().__init__(*args, **kwargs)

    def push(self, command, clear_redo=False):
        self.history.append(command)
        if clear_redo:
            self.redo_stack.clear()

    def pop(self):
        if self.history:
            return self.history.pop()
        return None

    def redo_pop(self):
        if self.redo_stack:
            return self.redo_stack.pop()
        return None

    def push_redo(self, command):
        self.redo_stack.append(command)

    def start_session(self):
        if self.command_session:
            raise RuntimeError("session already opened")
        self.command_session = self.session_cls()

    def terminate_session(self):
        if not self.command_session:
            raise RuntimeError("session not opened")
        self.command_session.undo()
        self.command_session = None

    def end_session(self):
        if not self.command_session:
            raise RuntimeError("session not opened")
        command_session = self.command_session
        self.command_session = None
        if command_session.check_existing_commands():
            self.push(command_session, clear_redo=True)

    def is_session_opened(self) -> bool:
        return self.command_session is not None

    def execute_command(self, command: Command) -> bool:
        if not self.command_session:
            raise RuntimeError()
        success = self.command_session.add_command(command)
        return success

    def undo(self):
        command_session = self.pop()
        if command_session:
            command_session.undo()
            self.push_redo(command_session)

    def redo(self):
        command_session = self.redo_pop()
        if command_session:
            command_session.redo()
            self.push(command_session, clear_redo=False)
