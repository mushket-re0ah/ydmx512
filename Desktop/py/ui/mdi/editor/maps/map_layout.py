from kivy.properties import NumericProperty, ColorProperty, ReferenceListProperty
from libs.uix.workspace_manager import WorkspaceBehavior
from typing import Tuple
from kivy.lang import Builder
from libs.uix.map_layout import MapLayout
from misc import colorscheme as cs


Builder.load_string("""
<EditorMapLayout>:
    selectable: False
    max_grid_size: [constants.MAP_LAYOUT_MAX_SIZE, constants.MAP_LAYOUT_MAX_SIZE]
    grid_padding: [2, 2, 2, 2]
    grid_spacing: [4, 4]
    canvas.before:
        Color:
            rgba: root.outbound_background_color
        Rectangle:
            pos: self.pos
            size: self.size

<WorkspaceEditorMapLayout>:
    if_contain: False if self.layout is None else len(self.grid_items) > 0
""")


class EditorMapLayout(MapLayout):
    outbound_background_color = ColorProperty(cs.EditorMapLayout.outbound_background_color)
    _offset_x = NumericProperty(0)
    _offset_y = NumericProperty(0)
    _offset = ReferenceListProperty(_offset_x, _offset_y)

    def cell_to_pixel(self, cell_x: int, cell_y: int) -> Tuple[float, float]:
        return super().cell_to_pixel(
            cell_x - self._offset_x,
            cell_y - self._offset_y,
        )

    def pixel_to_cell(self, x, y, ignore_spaces=False, allow_outbound=False):
        result = super().pixel_to_cell(x, y, ignore_spaces, allow_outbound)
        if result is None:
            return None
        return (result[0] + self._offset_x, result[1] + self._offset_y)

    def _calc_grid_size(self, _):
        padding_w = self.grid_padding[0] + self.grid_padding[2]
        padding_h = self.grid_padding[1] + self.grid_padding[3]

        widgets = self.grid_items[:]

        if not widgets:
            self._offset = (0, 0)
            self._grid_size = (0, 0)
            self.max_grid_size = (0, 0)
            self.wrap_layout.size = (
                max(self.scrollview.width, padding_w),
                max(self.scrollview.height, padding_h),
            )
            return

        min_x = min(w.grid_x for w in widgets)
        min_y = min(w.grid_y for w in widgets)
        max_x = max(w.grid_x + w.grid_width  for w in widgets)
        max_y = max(w.grid_y + w.grid_height for w in widgets)

        old_offset = (self._offset_x, self._offset_y)
        new_offset = (min_x, min_y)

        self._offset = new_offset

        columns = max_x - min_x
        rows = max_y - min_y
        self.max_grid_size = (columns, rows)
        self._grid_size = (columns, rows)

        grid_w, grid_h = self.grid_size_to_pixel(columns, rows)
        self.wrap_layout.size = (grid_w + padding_w, grid_h + padding_h)

        # Сдвиг изменился — пересчитать позиции всех виджетов.
        if new_offset != old_offset:
            for w in widgets:
                w._trigger_update_geometry()


class WorkspaceEditorMapLayout(EditorMapLayout, WorkspaceBehavior):
    pass
