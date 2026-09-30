from typing import TYPE_CHECKING, List, Set, Tuple

from libs import logger
from libs.dmx512 import dmx512
from libs.utils import ThrottledCall
from misc import constants

if TYPE_CHECKING:
    from database.playback.player import PlaybackPlayer


class PlaybackMasterPlayer:
    def __init__(self):
        self.player_list: List["PlaybackPlayer"] = []
        self.loop = ThrottledCall(self._loop, constants.DMX_WRITE_INTERVAL)

    def add_playback(self, player: "PlaybackPlayer"):
        if player not in self.player_list:
            self.player_list.append(player)

    def remove_playback(self, player: "PlaybackPlayer"):
        self.player_list.remove(player)
        self.clear_matrix_on_playback_off(player)

    def clear_matrix_on_playback_off(self, player: "PlaybackPlayer"):
        for universe, address_list in player.playback.renderer.universe_addresses.items():
            clear_address_list = address_list.copy()
            for p in self.player_list:
                p_renderer = p.playback.renderer
                if universe in p_renderer.universe_addresses:
                    clear_address_list -= p_renderer.universe_addresses[universe]
            dmx512.clear_matrix_by_address_list(universe, clear_address_list)

    def _loop(self):
        if not self.player_list:
            return
        used_fulladdresses: Set[Tuple[int, int]] = set()
        for player in reversed(self.player_list):
            if player.beat_counter is None:
                logger.debug("player not work, but in player_list")
                continue
            for patch, address_list in player.playback.renderer.patch_addresses.items():
                universe = patch.universe
                for address in address_list:
                    fulladdress = (universe, address)
                    if fulladdress in used_fulladdresses:
                        continue
                    value = player.get_patch_render(
                        patch,
                        address - patch.start_address,
                        player.beat_counter.frame_now
                    )
                    if value is not None:
                        dmx512.set_value(universe, address, value)
                        used_fulladdresses.add(fulladdress)

master_player = PlaybackMasterPlayer()
