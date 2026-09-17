def open_dir(connection, kwargs):
    raise NotImplementedError
    # from main_process.subprocess.filechooser.plyer import filechooser
    # from ipc_protocol.main.main_kivy import MainToKivyMessage
    # path = filechooser.choose_dir(**kwargs)
    # connection.send((MainToKivyMessage.CHOOSE_DIR, path))
