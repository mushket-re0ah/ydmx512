from misc import logger
from misc import exit_code
from typing import Optional
import sys


def import_cython_files() -> int:
    try:
        import libs.dmx512_render.render_interpolation
        import misc.colorpicker_utils
    except ModuleNotFoundError:
        try:
            logger.info("cythonized files don't exist: try to create them")
            from misc.build_cython import do_cythonize
            try:
                do_cythonize()
            except Exception as e:
                logger.error(exc_info=True)
                return exit_code.EXIT_FAILURE
            logger.info("cythonized successful")
            import libs.dmx512_render.render_interpolation
            import misc.colorpicker_utils
        except Exception as e:
            logger.error(exc_info=True)
            return exit_code.EXIT_FAILURE
    return exit_code.EXIT_SUCCESS


def init_config_kivy() -> int:
    try:
        from misc import config_kivy
        config_kivy.init()
    except Exception as e:
        logger.error(exc_info=True)
        return exit_code.EXIT_FAILURE
    return exit_code.EXIT_SUCCESS


def init_database() -> int:
    try:
        import database
        database.create_database()
    except SystemExit as e:
        logger.error(exc_info=True)
        return e.code
    except Exception as e:
        logger.error(exc_info=True)
        return exit_code.EXIT_FAILURE
    return exit_code.EXIT_SUCCESS


def create_app() -> Optional["DesktopApp"]:
    try:
        from app import DesktopApp
        return DesktopApp()
    except Exception as e:
        logger.error(exc_info=True)
        return None


def kivy_execute() -> int:
    from misc import exit_code
    logger.info("==== Запуск kivy приложения... ====")

    if constants.PROFILING_CPU:
        import yappi
        yappi.set_clock_type("cpu")
        yappi.start()
        # from scalene import scalene_profiler
        # scalene_profiler.start()

    if import_cython_files() == exit_code.EXIT_FAILURE:
        return exit_code.EXIT_FAILURE
    if init_config_kivy() == exit_code.EXIT_FAILURE:
        return exit_code.EXIT_FAILURE

    from libs import sdl2_keyboard
    sdl2_keyboard.init()

    from libs import beat_counter
    beat_counter.init(
        constants.TEMP_MINIMUM, constants.TEMP_MAXIMUM,
        constants.BEATS_COUNT_MINIMIUM, constants.BEATS_COUNT_MAXIMUM,
        constants.FRAMES_IN_BEAT
    )

    from libs import dmx512
    dmx512.init(
        constants.DMX_UNIVERSE_COUNT,
        constants.SERIAL_TIMEOUT,
        constants.SERIAL_BAUDRATE,
        constants.SERIAL_TRY_CONNECTION_TIME,
        constants.DMX_HELLO_MSG,
        constants.DMX_MESSAGE_BYTEORDER,
        constants.DMX_LIGHT_FPS,
        constants.DMX_ADDRESS_COUNT,
        constants.DMX_KEY_FRAME_TIME,
    )

    init_database_status = init_database()
    if init_database_status != exit_code.EXIT_SUCCESS:
        return init_database_status
    application = create_app()
    if not application:
        return exit_code.EXIT_FAILURE

    exit_status = exit_code.EXIT_SUCCESS
    try:
        application.run()
    except SystemExit as e:  # ловим sys.exit
        exit_status = e.code
        raise
    except Exception as e:
        logger.error(exc_info=True)
        exit_status = exit_code.EXIT_FAILURE
    finally:
        try:
            from database import db
            db.save_all()
        except Exception:
            logger.error(exc_info=True)
            if exit_status == exit_code.EXIT_SUCCESS:
                exit_status = exit_code.EXIT_FAILURE

    return exit_status


def backup_menu_execute():
    from misc import exit_code
    from misc import logger
    import sys
    exit_status = exit_code.EXIT_SUCCESS
    logger.info("==== Запуск backup menu приложения... ====")

    from misc import config_kivy
    config_kivy.init(backup_mode=True)

    from libs import sdl2_keyboard
    sdl2_keyboard.init()

    try:
        from app_backup import BackupApp
        app = BackupApp()
        app.run()
    except SystemExit as e:
        exit_status = e.code
        raise
    except Exception:
        logger.error(exc_info=True)
        exit_status = exit_code.EXIT_FAILURE
    return exit_status


if __name__ == '__main__':
    from misc import logger
    from misc import exit_code
    logger.init()
    import os
    from misc import constants
    exec_backup_menu = os.environ.get(constants.BACKUP_MENU_ENV_KEY)
    exec_backup_menu = exec_backup_menu == constants.BACKUP_MENU_ENV_KEY_TRUE

    if exec_backup_menu:
        try:
            exit_status = backup_menu_execute()
        except Exception as e:
            exit_status = exit_code.EXIT_FAILURE
            logger.error(exc_info=True)
        logger.info("==== Завершение backup menu приложения... ====")
        sys.exit(exit_status)
    else:
        try:
            exit_status = kivy_execute()
        except Exception as e:
            exit_status = exit_code.EXIT_FAILURE
            logger.error(exc_info=True)
        logger.info("==== Завершение kivy приложения... ====")

        import sys
        import threading
        import traceback


        logger.info("=== THREADS BEFORE EXIT ===")

        frames = sys._current_frames()

        for thread in threading.enumerate():
            logger.info(
                f"thread={thread.name!r}, "
                f"ident={thread.ident}, "
                f"native_id={thread.native_id}, "
                f"daemon={thread.daemon}, "
                f"alive={thread.is_alive()}"
            )

            frame = frames.get(thread.ident)
            if frame:
                logger.info(
                    "".join(traceback.format_stack(frame))
                )
        sys.exit(exit_status)
