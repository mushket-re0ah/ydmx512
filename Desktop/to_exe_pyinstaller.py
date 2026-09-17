import PyInstaller.__main__
from pathlib import Path
import os
import shutil
import glob
from distutils.dir_util import copy_tree


# Pyinstaller ДОЛЖЕН БЫТЬ 5.6.2
# pip install pyinstaller==5.6.2 pyinstaller-hooks-contrib==2022.13
#
# UPD
# Необязательно, у меня удалось собрать на 5.13.2, правда сборка шла минут 40,
# намного дольше старой версии. Разницы в exe не заметил. Вес файла почти
# тот же, в процессах памяти даже больше занимают, в чем цимес не понял.


SPEC_FNAME = "to_exe_pyinstaller.spec"
EXE_DIR = "exe_pyinstaller"
PY_DIR = "py"

CLEAR_BUILD_DIST = True
EXE_ONLY = True


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


def create_exe():
    PyInstaller.__main__.run([SPEC_FNAME])


def move_exe():
    if not os.path.isdir(EXE_DIR):
        copy_tree(PY_DIR, EXE_DIR)
    shutil.copy(Path("dist/main.exe"), Path(f"{EXE_DIR}/main.exe"))


def clear():
    if os.path.isdir("database"):
        os.rmdir("database")

    if EXE_ONLY:
        tests_path = Path(f"{EXE_DIR}/tests")
        if tests_path.exists():
            shutil.rmtree(tests_path)
        cython_path = Path(f"{EXE_DIR}/cython")
        if cython_path.exists():
            shutil.rmtree(cython_path)
        kivy_path = Path(f"{EXE_DIR}/kivy")
        if kivy_path.exists():
            shutil.rmtree(kivy_path)
        migrate_path = Path(f"{EXE_DIR}/migrate")
        if migrate_path.exists():
            shutil.rmtree(migrate_path)
        misc_path = Path(f"{EXE_DIR}/misc")
        if misc_path.exists():
            shutil.rmtree(misc_path)
        req_path = Path(f"{EXE_DIR}/requirements.txt")
        if req_path.exists():
            req_path.unlink()
        for fname in Path(EXE_DIR).rglob(f"*.py"):
            fname.unlink()
        for fname in Path(EXE_DIR).rglob("__pycache__"):
            shutil.rmtree(fname)

        _delete_empty_folders(EXE_DIR)

    if CLEAR_BUILD_DIST:
        build_path = Path(f"build")
        if build_path.exists():
            shutil.rmtree(build_path)
        dist_path = Path(f"dist")
        if dist_path.exists():
            shutil.rmtree(dist_path)


if __name__ == '__main__':
    create_exe()
    move_exe()
    clear()
