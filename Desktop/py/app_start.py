from typing import Optional
import sys
import os
from libs import logger
from libs.sub_proc import exit_code
from misc import constants


def import_cython_files() -> int:
    try:
        import libs.dmx512_render.render_interpolation
        import libs.uix.color_selector.colorpicker_utils
    except ModuleNotFoundError:
        try:
            logger.info("cythonized files don't exist: try to create them")
            from misc.build_cython import do_cythonize
            try:
                do_cythonize()
            except Exception:
                logger.error(exc_info=True)
                return exit_code.EXIT_FAILURE
            logger.info("cythonized successful")
            import libs.dmx512_render.render_interpolation
            import libs.uix.color_selector.colorpicker_utils
        except Exception:
            logger.error(exc_info=True)
            return exit_code.EXIT_FAILURE
    return exit_code.EXIT_SUCCESS


def init_config_kivy() -> int:
    try:
        from misc import config_kivy
        config_kivy.init()
    except Exception:
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
    except Exception:
        logger.error(exc_info=True)
        return exit_code.EXIT_FAILURE
    return exit_code.EXIT_SUCCESS


def create_app() -> Optional["DesktopApp"]:
    try:
        from app import DesktopApp
        return DesktopApp()
    except Exception:
        logger.error(exc_info=True)
        return None


def kivy_execute() -> int:
    logger.info("==== Запуск kivy приложения... ====")

    if constants.PROFILING_CPU:
        import yappi
        yappi.set_clock_type("cpu")
        yappi.start()
        # from scalene import scalene_profiler
        # scalene_profiler.start()

    if init_config_kivy() == exit_code.EXIT_FAILURE:
        return exit_code.EXIT_FAILURE
    if import_cython_files() == exit_code.EXIT_FAILURE:
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
    except Exception:
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


def main():
    try:
        import faulthandler
        import signal

        faulthandler.register(
            signal.SIGUSR1,
            all_threads=True,
            chain=False,
        )
    except:
        pass

    logger.init(constants.LOGS_PATH, constants.MAX_LOG_FILES, constants.SESSION_LOG_ENV_KEY)
    exec_backup_menu = os.environ.get(constants.BACKUP_MENU_ENV_KEY)
    exec_backup_menu = exec_backup_menu == constants.BACKUP_MENU_ENV_KEY_TRUE

    exit_status = exit_code.EXIT_SUCCESS
    if exec_backup_menu:
        try:
            exit_status = backup_menu_execute()
        except Exception:
            exit_status = exit_code.EXIT_FAILURE
            logger.error(exc_info=True)
        logger.info("==== Завершение backup menu приложения... ====")
    else:
        try:
            exit_status = kivy_execute()
        except Exception:
            exit_status = exit_code.EXIT_FAILURE
            logger.error(exc_info=True)
        logger.info("==== Завершение kivy приложения... ====")

    sys.exit(exit_status)

if __name__ == "__main__":
    main()
