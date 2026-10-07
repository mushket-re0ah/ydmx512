import os
import sys

from libs import logger
from libs.sub_proc.exit_code import ExitCode
from misc import constants


def kivy_execute() -> ExitCode:
    def init_config_kivy() -> ExitCode:
        try:
            from misc import config_kivy
            config_kivy.init()
        except Exception:
            logger.error(exc_info=True)
            return ExitCode.FAILURE
        return ExitCode.SUCCESS

    def import_cython_files() -> ExitCode:
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
                    return ExitCode.FAILURE
                logger.info("cythonized successful")
                import libs.dmx512_render.render_interpolation
                import libs.uix.color_selector.colorpicker_utils  # noqa: F401
            except Exception:
                logger.error(exc_info=True)
                return ExitCode.FAILURE
        return ExitCode.SUCCESS

    def init_database() -> ExitCode:
        try:
            import database
            database.create_database()
        except SystemExit as e:
            logger.error(exc_info=True)
            return ExitCode(e.code)
        except Exception:
            logger.error(exc_info=True)
            return ExitCode.FAILURE
        return ExitCode.SUCCESS

    logger.info("==== Запуск kivy приложения... ====")

    if constants.PROFILING_CPU:
        import yappi
        yappi.set_clock_type("cpu")
        yappi.start()
        # from scalene import scalene_profiler
        # scalene_profiler.start()

    if init_config_kivy() == ExitCode.FAILURE:
        return ExitCode.FAILURE

    if import_cython_files() == ExitCode.FAILURE:
        return ExitCode.FAILURE

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
    from libs import midi
    midi.init(
        constants.MIDI_CHECK_MESSAGES_CALL_INTERVAL,
        constants.MIDI_TRY_CONNECTION_TIME
    )

    init_database_status = init_database()
    if init_database_status != ExitCode.SUCCESS:
        return init_database_status


    try:
        from app import DesktopApp
        application = DesktopApp()
    except Exception:
        logger.error(exc_info=True)
        return ExitCode.FAILURE

    exit_status = ExitCode.SUCCESS
    try:
        application.run()
    except SystemExit as e:  # ловим sys.exit
        exit_status = ExitCode(e.code)
        raise
    except Exception:
        logger.error(exc_info=True)
        exit_status = ExitCode.FAILURE
    finally:
        try:
            from database import db
            db.save_all()
        except Exception:
            logger.error(exc_info=True)
            if exit_status == ExitCode.SUCCESS:
                exit_status = ExitCode.FAILURE

    return exit_status


def backup_menu_execute() -> ExitCode:
    exit_status = ExitCode.SUCCESS
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
        exit_status = ExitCode(e.code)
        raise
    except Exception:
        logger.error(exc_info=True)
        exit_status = ExitCode.FAILURE
    return exit_status


def main() -> ExitCode:
    try:
        import faulthandler
        import signal

        faulthandler.register(
            signal.SIGUSR1,
            all_threads=True,
            chain=False,
        )
    except BaseException:
        pass

    logger.init()
    exec_backup_menu = os.environ.get(constants.BACKUP_MENU_ENV_KEY)
    exec_backup_menu = exec_backup_menu == constants.BACKUP_MENU_ENV_KEY_TRUE

    exit_status = ExitCode.SUCCESS
    if exec_backup_menu:
        try:
            exit_status = backup_menu_execute()
        except Exception:
            exit_status = ExitCode.FAILURE
            logger.error(exc_info=True)
        logger.info("==== Завершение backup menu приложения... ====")
    else:
        try:
            exit_status = kivy_execute()
        except Exception:
            exit_status = ExitCode.FAILURE
            logger.error(exc_info=True)
        logger.info("==== Завершение kivy приложения... ====")

    return exit_status

if __name__ == "__main__":
    sys.exit(main())
