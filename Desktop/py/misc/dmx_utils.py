from database.playback import PlaybackRenderRow
from database.patch import RowPatch
from libs.dmx512 import dmx512
from typing import List, Dict


def set_dmx_by_rows(row_to_value: Dict[PlaybackRenderRow, int]):
    for row, value in row_to_value.items():
        patch = row.patch
        universe = patch.universe
        address = patch.start_address + row.fixture_index
        if value is None:
            dmx512.set_default_value(universe, address)
        else:
            dmx512.set_value(universe, address, value)

def update_dmx512_by_patch_list(renderer, patch_list: List[RowPatch]):
    dmx512.clear_matrix_all()
    for patch in patch_list:
        universe = patch.universe
        for address in renderer.patch_addresses.get(patch, []):
            index = address - patch.start_address
            value = renderer.get_patch_render(patch, index)[0]
            dmx512.set_value(universe, address, value)
