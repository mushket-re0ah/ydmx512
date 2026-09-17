from typing import NamedTuple
from enum import Enum
from misc import colorscheme as cs
from misc import imgs_path


class _PlayerStatusValue(NamedTuple):
    bg: list  # rgba
    img: str


class PlayerStatus(Enum):
    WORK    = _PlayerStatusValue(
                    cs.PlaybackUi.bg_work_normal,
                    imgs_path.playback_status_work
            )
    STOP    = _PlayerStatusValue(
                    cs.PlaybackUi.bg_stop_normal,
                    imgs_path.playback_status_stop
            )
    ATTACK  = _PlayerStatusValue(
                    cs.PlaybackUi.bg_attack_normal,
                    imgs_path.playback_status_attack
            )
    RELEASE = _PlayerStatusValue(
                    cs.PlaybackUi.bg_release_normal,
                    imgs_path.playback_status_release
            )
