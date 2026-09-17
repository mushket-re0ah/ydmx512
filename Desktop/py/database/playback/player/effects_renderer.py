from typing import Optional, List
from database.patch import RowPatch
from database.fixture_param import DIMMER_TITLE_ID
from misc.player.status import PlayerStatus
from misc.player.render_utils import SoftEffectsRenderer, apply_value_modifiers
from misc.player import render_utils
import time


class PlayerEffectsRenderer:
    def __init__(self, player):
        self.player = player
        self.soft_renderer = player.soft_renderer
        self.do_cycle_last_frame = False

    def on_status_change(self, status):
        self.soft_renderer.reset(status)
        if status is PlayerStatus.STOP:
            self.do_cycle_last_frame = False

    def check_last_frame(self):
        if self.player.status is PlayerStatus.WORK and self.player.is_cycle_last_frame:
            self.do_cycle_last_frame = True
            self.player.property("beat_now").dispatch(self.player)

    def discard_soft_render(self):
        self.soft_renderer.reset(PlayerStatus.STOP)

    def get_patch_render(self, patch: RowPatch, fixture_index: int, frame: int) -> Optional[int]:
        renderer = self.player.playback.renderer
        patch_render = renderer.get_patch_render(patch, fixture_index)
        if not patch_render:
            return None

        if self.player.soft_play and self.player.status is not PlayerStatus.WORK:
            value = self._get_render_soft_value(patch, fixture_index, frame, patch_render)
        else:
            value = self._get_render_value(patch_render, frame)

        param = patch.fixture.param_list_unpacked[fixture_index]
        value = apply_value_modifiers(
            value, param.title_id, patch.invert_pan, patch.invert_tilt,
            renderer.all_params_intensive, renderer.intensive, patch.virtual_dimmer,
            patch.correction_pan if renderer.correction_pan else 0,
            patch.correction_tilt if renderer.correction_tilt else 0
        )

        value = self._apply_fade_to_black(patch, fixture_index, value)
        return value

    def _apply_bounce(self, frame: int) -> int:
        if not self.player.bounce:
            return frame
        if self.player._bounce_direction == -1 and frame == 0:
            return -1
        return self.player._bounce_direction * frame

    def _get_render_value(self, patch_render: List[int], frame: int) -> int:
        if self.do_cycle_last_frame:
            return patch_render[-1]
        else:
            return patch_render[self._apply_bounce(frame)]

    def _get_render_soft_value(self, patch: RowPatch, fixture_index: int,
                               frame: int, patch_render: List[int]) -> int:
        is_attack = self.player.status is PlayerStatus.ATTACK
        param = patch.fixture.param_list_unpacked[fixture_index]
        return self.soft_renderer.get_soft_value(
            is_attack, fixture_index, frame, self.player.frame_count,
            live_value=patch_render[0] if is_attack else patch_render[self._apply_bounce(frame)],
            default_value=param.default_value
        )

    def _apply_fade_to_black(self, patch: RowPatch, fixture_index: int,
            value: int) -> int:
        if not self.player.fade_to_black:
            return value
        fade_time_sec = self.player.fade_to_black_time / 1000
        time_from_start = time.time() - self.player.time_start
        if patch.fixture.is_dynamic and time_from_start < fade_time_sec:
            param = patch.fixture.param_list_unpacked[fixture_index]
            if param.title_id == DIMMER_TITLE_ID:
                return 0
        return value
