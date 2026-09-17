import os
from os import environ
from sys import platform as _sys_platform
from pathlib import Path
import shutil
import glob
from distutils.dir_util import copy_tree
import subprocess

# Добавь это здесь:
os.environ['PATH'] = f"{os.path.expanduser('~/.local/bin')}:{os.environ.get('PATH', '')}"

# Взято из kivy/utils.py
def _get_platform():
    # On Android sys.platform returns 'linux2', so prefer to check the
    # existence of environ variables set during Python initialization
    kivy_build = environ.get('KIVY_BUILD', '')
    if kivy_build in {'android', 'ios'}:
        return kivy_build
    elif 'P4A_BOOTSTRAP' in environ:
        return 'android'
    elif 'ANDROID_ARGUMENT' in environ:
        # We used to use this method to detect android platform,
        # leaving it here to be backwards compatible with `pydroid3`
        # and similar tools outside kivy's ecosystem
        return 'android'
    elif _sys_platform in ('win32', 'cygwin'):
        return 'win'
    elif _sys_platform == 'darwin':
        return 'macosx'
    elif _sys_platform.startswith('linux'):
        return 'linux'
    elif _sys_platform.startswith('freebsd'):
        return 'linux'
    return 'unknown'


EXE_DIR = "exe_nuitka"
PY_DIR = "py"
PY_FILE = "launcher.py"
PY_PATH = os.path.join(PY_DIR, PY_FILE)
REPORT_XML = False
report_xml_cmd = "--report=report_nuitka.xml" if REPORT_XML else ""
NOFOLLOW_IMPORT = [
    "numpy",
    "asyncio",
    "ssl",
    "_ssl",
    "asyncio.sslproto",
    "_hashlib",
    "PIL",
    "pygments",
    "IPython",
    "certifi",
    "yappi",
    "kivy.core.camera",
    "kivy.core.video",
    "kivy.lib.gstplayer",
    "kivy.lib._lzma",
    "kivy.lib.mtdev",
    "email",
    "html",
    "http",
    "ipaddress",
    # "sdl2.mixer"
]
CLEAR_BUILD_DIST = True
_PY_FILE_WITHOUT_EXT = PY_FILE.split('.')[0]
BUILD_DIR = Path(f"{_PY_FILE_WITHOUT_EXT}.build")
DIST_DIR = Path(f"{_PY_FILE_WITHOUT_EXT}.dist")
ONEFILE_BUILD_DIR = Path(f"{_PY_FILE_WITHOUT_EXT}.onefile-build")
CLEAR_BUILD_DIR_LIST = (BUILD_DIR, DIST_DIR, ONEFILE_BUILD_DIR)

WITH_CONSOLE = False

ICON = str(Path("py/data/imgs/logo-Y DMX контроллер.png"))


def check_nuitka():
    try:
        result = subprocess.run(['nuitka', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception("Nuitka не найден или не работает")
        return True
    except FileNotFoundError:
        return False


def get_exe_file(platform):
    base = _PY_FILE_WITHOUT_EXT
    if platform == "win":
        return f"{base}.exe"
    else:  # linux
        return f"{base}.bin"


def get_console_cmd(platform):
    if platform == "win" and not WITH_CONSOLE:
        return "--windows-console-mode=disable"
    return ""


def get_icon_cmd(platform):
    if platform == "win":
        return f"--windows-icon-from-ico=\"{ICON}\""
    elif platform == "linux":
        return f"--linux-icon=\"{ICON}\""
    return ""


def build_generic(platform):
    if not check_nuitka():
        print("Nuitka не установлен. Установите его с помощью: pip install nuitka")
        return False

    exe_file = get_exe_file(platform)
    console_cmd = get_console_cmd(platform)
    icon_cmd = get_icon_cmd(platform)
    nofollow = "".join(f"--nofollow-import-to={i} " for i in NOFOLLOW_IMPORT)
    cmd = f"nuitka --standalone --onefile {nofollow}{report_xml_cmd} {console_cmd} {icon_cmd} {PY_PATH}"
    result = os.system(cmd)
    if result != 0:
        print("Ошибка при сборке Nuitka. Проверьте логи выше.")
        return False

    if not move_exe(exe_file, platform):
        print("Ошибка при перемещении файла.")
        return False

    clear()
    return True


def build_windows():
    build_generic("win")


def build_linux():
    build_generic("linux")


def move_exe(exe_file, platform):
    exe_path = Path(exe_file)
    if not exe_path.exists():
        print(f"Исполняемый файл '{exe_file}' не найден. Сборка Nuitka, возможно, провалилась.")
        return False

    if Path(EXE_DIR).exists():
        shutil.rmtree(Path(EXE_DIR))
    copy_tree(PY_DIR, EXE_DIR)
    shutil.move(exe_path, Path(f"{EXE_DIR}/{exe_file}"))
    return True


def _delete_empty_folders(root):
    deleted = set()

    for current_dir, subdirs, files in os.walk(root, topdown=False):

        still_has_subdirs = False
        for subdir in subdirs:
            if os.path.join(current_dir, subdir) not in deleted:
                still_has_subdirs = True
                break

        if not any(files) and not still_has_subdirs:
            os.rmdir(current_dir)
            deleted.add(current_dir)

    return deleted


def clear():
    del_dir = (Path(f"{EXE_DIR}/{i}")
               for i in ("tests", "cython", "kivy", "migrate", "misc"))
    for path in (i for i in del_dir if i.exists()):
        shutil.rmtree(path)
    req_path = Path(f"{EXE_DIR}/requirements.txt")
    if req_path.exists():
        req_path.unlink()
    for fname in Path(EXE_DIR).rglob(f"*.py"):
        fname.unlink()
    for fname in Path(EXE_DIR).rglob("__pycache__"):
        shutil.rmtree(fname)

    _delete_empty_folders(EXE_DIR)

    if CLEAR_BUILD_DIST:
        for clear_dir in CLEAR_BUILD_DIR_LIST:
            if clear_dir.exists():
                shutil.rmtree(clear_dir)


if __name__ == "__main__":
    platform = _get_platform()

    if platform == "win":
        build_windows()
    elif platform == "linux":
        build_linux()
    elif platform == "unknown":
        print(f"Платформа не определена")
    else:
        print(f"Нет настроек запуска на платформе {platform}")
