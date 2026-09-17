from threading import Thread
from misc import logger
from misc import constants
from libs.utils import ThrottledCall
import time
from database import db
from libs import beat_counter
from libs.dmx512 import dmx512
from libs.serial.observer import observer as serial_observer
from libs.midi.observer import observer as midi_observer
from database.playback.player import master_player as playback_master_player


def init():
    logger.info("event thread init")
    thread = Thread(target=loop,
                    daemon=True,)
    thread.start()


EVENT_THREAD_TIME: float = 1.0 / constants.EVENT_THREAD_FPS
def loop():
    while True:
        try:  # вообще как бы лишний, но пусть будет
            _loop()
        except Exception:
            logger.error("event thread", exc_info=True)
            time.sleep(EVENT_THREAD_TIME)


serial_monitor_connections = ThrottledCall(
    serial_observer.monitor_connections,
    constants.SERIAL_MONITORING_CALL_INTERVAL
)
midi_monitor_connections = ThrottledCall(
    midi_observer.monitor_connections,
    constants.MIDI_MONITORING_CALL_INTERVAL
)

# если где-то ошибка то цикл не пойдет дальше, последующие системы не отработают
# поэтому нужен list
_callback_list = [
    db.save_throttled,
    db.backup_throttled,
    serial_monitor_connections,
    midi_monitor_connections,
    dmx512.loop,
    beat_counter.loop,
    playback_master_player.loop,
]
def _loop():
    next_time = time.monotonic() + EVENT_THREAD_TIME
    last_time = time.monotonic()

    while True:
        now = time.monotonic()
        dt = now - last_time
        last_time = now

        for callback in _callback_list:
            try:
                callback(dt)
            except Exception:
                logger.error("event thread", exc_info=True)

        next_time += EVENT_THREAD_TIME
        sleep_time = next_time - time.monotonic()
        if sleep_time > 0:
            time.sleep(sleep_time)
