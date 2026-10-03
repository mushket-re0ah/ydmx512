from math import ceil, floor
from typing import Optional, Tuple

from kivy.lang import Builder
from kivy.properties import ColorProperty, NumericProperty, ReferenceListProperty

from libs.typecheck import RGBA
from libs.uix.map_layout import MapLayout
from libs.uix.workspace_manager import WorkspaceBehavior
from misc import colorscheme as cs

Builder.load_string("""
<EditorMapLayout>:
    selectable: False
    cell_size: constants.MAP_LAYOUT_CELL_SIZE
    max_grid_size: constants.MAP_LAYOUT_MAX_GRID_SIZE
    grid_padding: constants.MAP_LAYOUT_GRID_PADDING
    grid_spacing: constants.MAP_LAYOUT_GRID_SPACING
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
    outbound_background_color: RGBA = ColorProperty(cs.EditorMapLayout.outbound_background_color)
    _offset_x: int = NumericProperty(0)
    _offset_y: int = NumericProperty(0)
    _offset: Tuple[int, int] = ReferenceListProperty(_offset_x, _offset_y)

    def cell_to_pixel(self, cell_x: int, cell_y: int) -> Tuple[float, float]:
        return super().cell_to_pixel(cell_x - self._offset_x, cell_y - self._offset_y)

    def pixel_to_cell(
            self,
            x: float,
            y: float,
            ignore_spaces:bool=False,
            allow_outbound:bool=False
        ) -> Optional[Tuple[int, int]]:
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
            # self.max_grid_size = (0, 0)
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
        # self.max_grid_size = (columns, rows)
        self._grid_size = (columns, rows)

        grid_w, grid_h = self.grid_size_to_pixel(columns, rows)
        self.wrap_layout.size = (grid_w + padding_w, grid_h + padding_h)

        # Сдвиг изменился — пересчитать позиции всех виджетов.
        if new_offset != old_offset:
            for w in widgets:
                w.trigger_update_geometry()

    def _draw_grid(self, _):
        if not self.layout:
            return

        if not self.grid_show:
            self._grid_render_size = (0, 0)
            return

        step_x = self._step_x
        step_y = self._step_y

        if step_x <= 0 or step_y <= 0:
            self._grid_render_size = (0, 0)
            return

        # Пиксельная позиция viewport внутри content.
        scrollable_width = max(0, self.layout.width - self.scrollview.width)
        scrollable_height = max(0, self.layout.height - self.scrollview.height)

        max_grid_w, max_grid_h = self.grid_size_to_pixel(self._columns, self._rows)

        visible_x0 = self.scrollview.scroll_x * scrollable_width
        visible_x1 = min(max_grid_w, visible_x0 + self.scrollview.width)

        visible_y0 = (1.0 - self.scrollview.scroll_y) * scrollable_height
        visible_y1 = min(max_grid_h, visible_y0 + self.scrollview.height)

        rect_left = floor(visible_x0 / step_x) * step_x
        rect_bottom = floor(visible_y0 / step_y) * step_y

        render_size = (
            max(0, ceil((visible_x1 - rect_left) / step_x)) * step_x,
            max(0, ceil((visible_y1 - rect_bottom) / step_y)) * step_y,
        )

        texture = self._get_grid_texture()
        if render_size[0] > 0 and render_size[1] > 0:
            texture.uvsize = (
                render_size[0] / step_x,
                render_size[1] / step_y,
            )

        self._grid_texture = texture
        self._grid_render_pos = (rect_left, rect_bottom)
        self._grid_render_size = render_size
        self.property("_grid_texture").dispatch(self)


class WorkspaceEditorMapLayout(EditorMapLayout, WorkspaceBehavior):
    pass
