def clean_build():
    import os
    import glob
    import shutil
    if os.path.exists("build"):
        shutil.rmtree("build")
    for c_file in glob.glob("libs/dmx512_render/*.c"):
        os.remove(c_file)
    for c_file in glob.glob("libs/uix/color_selector/*.c"):
        os.remove(c_file)

def do_cythonize():
    import os
    import sys
    from setuptools import Extension, setup
    from Cython.Build import cythonize

    # работаем от корня проекта независимо от того, откуда запущен скрипт
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    sys.argv = ("build_cython.py", "build_ext", "--inplace")

    modules = (
        ("libs.dmx512_render.render_interpolation", "libs/dmx512_render/render_interpolation"),
        ("libs.uix.color_selector.colorpicker_utils", "libs/uix/color_selector/colorpicker_utils"),
    )

    extensions = [
        Extension(name=name, sources=[f"{path}.pyx"])
        for name, path in modules
    ]

    setup(
        name="my_app",
        ext_modules=cythonize(
            extensions,
            compiler_directives={
                'boundscheck': False,
                'wraparound': False,
                'cdivision': True,
                'nonecheck': False,
                'language_level': 3,
                'infer_types': True,
                'initializedcheck': False,
                'c_string_type': 'str',
                'c_string_encoding': 'ascii'
            },
        )
    )
    clean_build()


if __name__ == '__main__':
    do_cythonize()
