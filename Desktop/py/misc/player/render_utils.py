from kivy.utils import boundary
from misc.player.status import PlayerStatus
from database.fixture_param import DIMMER_TITLE_ID, PAN_TITLE_ID, TILT_TITLE_ID
from database import db


def apply_dimmer(value: int, intensive: int = 100, virtual_dimmer: int = 100) -> int:
    dimmer_mod = db.scene.scene_now_dimmer / 100
    dimmer_mod *= intensive / 100
    if virtual_dimmer:
        dimmer_mod *= virtual_dimmer / 100
    return int(value * dimmer_mod)


def apply_dynamic_param(value: int, invert_pan: bool, correction: int = 0) -> int:
    if correction:
        cor = -correction if invert_pan else correction
        value = boundary(value + cor, 0, 255)
    if invert_pan:
        value = value ^ 255
    return value


def apply_value_modifiers(
        value: int,
        param_title_id,
        invert_pan,
        invert_tilt,
        all_params_intensive=False,
        intensive=100,
        virtual_dimmer=100,
        correction_pan=0,
        correction_tilt=0
        ) -> int:
    if all_params_intensive and param_title_id != DIMMER_TITLE_ID:
        value = int(value * (intensive / 100))

    if param_title_id == DIMMER_TITLE_ID:
        return apply_dimmer(value, intensive, virtual_dimmer)
    elif param_title_id == PAN_TITLE_ID:
        return apply_dynamic_param(value, invert_pan, correction_pan)
    elif param_title_id == TILT_TITLE_ID:
        return apply_dynamic_param(value, invert_tilt, correction_tilt)
    else:
        return value


class SoftEffectsRenderer:
    def __init__(self):
        self._attack_data = {}
        self._release_data = {}

    def init_attack_step(self, key, frame: int, total_frames: int,
                         start_value: int, end_value: int):
        self._init_step(self._attack_data, key, frame, total_frames, start_value, end_value)

    def get_attack_value(self, key, frame: int) -> int:
        return self._get_value(self._attack_data, key, frame)

    def init_release_step(self, key, frame: int, total_frames: int,
                          start_value: int, end_value: int):
        self._init_step(self._release_data, key, frame, total_frames, start_value, end_value)

    def get_release_value(self, key, frame: int) -> int:
        return self._get_value(self._release_data, key, frame)

    @staticmethod
    def _init_step(data, key, frame, total_frames, start_value, end_value):
        remaining = total_frames - frame
        step = (end_value - start_value) / remaining if remaining > 0 else 0
        data[key] = (frame, start_value, step)

    @staticmethod
    def _get_value(data, key, frame):
        if key not in data:
            return None
        nframe, start, step = data[key]
        return int(start + (frame - nframe) * step)

    def reset(self, status: PlayerStatus):
        if status is PlayerStatus.WORK:
            self._attack_data.clear()
        elif status is PlayerStatus.STOP:
            self._attack_data.clear()
            self._release_data.clear()

    def has_attack_data(self):
        return bool(self._attack_data)

    def has_release_data(self):
        return bool(self._release_data)

    def get_soft_value(
        self,
        is_attack: bool,
        key,
        frame: int,
        total_frames: int,
        live_value: int,      # текущее "живое" значение (для атаки — конечное, для релиза — fallback-начало)
        default_value: int    # значение по умолчанию (для атаки — начальное, для релиза — конечное)
    ) -> int:
        """
        Возвращает интерполированное значение для ключа key.
        Если данных для данного ключа нет, автоматически инициализирует шаг.
        При релизе автоматически использует текущее значение атаки (если оно есть) как стартовое.
        """
        data = self._attack_data if is_attack else self._release_data
        if key not in data:
            if is_attack:
                start = default_value
                end = live_value
            else:  # релиз
                # если есть данные атаки для этого ключа, берём из них текущее значение
                if key in self._attack_data:
                    start = self._get_value(self._attack_data, key, frame)
                    if start is None:  # на всякий случай fallback
                        start = live_value
                else:
                    start = live_value
                end = default_value
            self._init_step(data, key, frame, total_frames, start, end)
        return self._get_value(data, key, frame)
