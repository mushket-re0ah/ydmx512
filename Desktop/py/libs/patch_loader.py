from typing import Dict


class PatchedLoader(importlib.abc.Loader):
    def __init__(self, path):
        self.path = path

    def exec_module(self, module):
        loader = importlib.machinery.SourceFileLoader(
            module.__name__,
            self.path
        )
        loader.exec_module(module)


class PatchFinder(importlib.abc.MetaPathFinder):
    def __init__(self, patches: Dict[str, str]):
        # {"имя_модуля": "путь_к_файлу"}
        self.patches = patches

    def find_spec(self, fullname, path=None, target=None):
        patch = self.patches.get(fullname)
        if patch is None:
            return None

        return importlib.machinery.ModuleSpec(
            fullname,
            PatchedLoader(patch),
            origin=patch,
        )
# using:
# finder = PatchFinder({
#     "kivy.metrics": "patches/kivy/metrics.py",
#     "kivy.clock": "patches/kivy/clock.py",
# })

# sys.meta_path.insert(0, finder)

# НАПОМИНАНИЕ а на кой оно надо?
# для будущей подмены RenderContext
