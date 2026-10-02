from typing import Callable, List, Optional

from typing_extensions import TypeAlias

from libs import logger
from libs.dmx512_render import render_interpolation
from libs.dmx512_render.misc import (
    DenormalizedDMXRenderDot,
    DMXRenderDot,
    InterpolationType,
    XYGrid,
)

DotsPrePipelineCb: TypeAlias = Callable[
    [List[DMXRenderDot]],
    List[DMXRenderDot]
]
DotsPostPipelineCb: TypeAlias = Callable[
    [List[DenormalizedDMXRenderDot]],
    List[DenormalizedDMXRenderDot]
]
RenderPipelineCb: TypeAlias = Callable[
    [bytes],
    bytes
]


class RenderPipeline:
    _pre_process_dots_pipeline: List[DotsPrePipelineCb]
    _post_process_dots_pipeline: List[DotsPostPipelineCb]
    _post_process_render_pipeline: List[RenderPipelineCb]
    def __init__(
        self,
        xy_grid: Optional[XYGrid]=None,
        pre_process_dots_pipeline: Optional[List[DotsPrePipelineCb]]=None,
        post_process_dots_pipeline: Optional[List[DotsPostPipelineCb]]=None,
        post_process_render_pipeline: Optional[List[RenderPipelineCb]]=None,
    ):
        self.xy_grid = xy_grid
        self._pre_process_dots_pipeline = pre_process_dots_pipeline or []
        self._post_process_dots_pipeline = post_process_dots_pipeline or []
        self._post_process_render_pipeline = post_process_render_pipeline or []

    def set_pre_process_dots_pipeline(self, pipeline: List[DotsPrePipelineCb]):
        self._pre_process_dots_pipeline = pipeline

    def set_post_process_dots_pipeline(self, pipeline: List[DotsPostPipelineCb]):
        self._post_process_dots_pipeline = pipeline

    def set_post_process_render_pipeline(self, pipeline: List[RenderPipelineCb]):
        self._post_process_render_pipeline = pipeline

    def processing(
            self,
            dots: List[DMXRenderDot],
            default_value: int,
            xy_grid: Optional[XYGrid]=None
        ) -> bytes:
        if not xy_grid:
            xy_grid = self.xy_grid
        if not xy_grid:
            logger.warning("render pipeline: processing xy grid is None")
            return b""
        x_size, y_size = xy_grid.size_xy_getter()
        if x_size <= 0:
            return b""
        xy_grid = XYGrid(lambda: x_size, lambda: y_size)

        if not dots:
            return self._empty_dots_render(xy_grid, default_value)
        dots = self._pre_process_dots(dots)
        denorm_dots = self._denormalize_dots(xy_grid, dots)
        denorm_dots = self._post_process_dots(denorm_dots)
        if len(denorm_dots) == 1:
            return self._fill_bound_render(x_size, denorm_dots[0].y)
        render = self._render(denorm_dots)
        render = self._fill_bound_render(denorm_dots[0].x, denorm_dots[0].y) + render
        render = render + self._fill_bound_render(
            xy_grid.size_x_getter() - 1 - denorm_dots[-1].x,
            denorm_dots[-1].y
        )
        render = self._post_process_render(render)
        return render

    def _pre_process_dots(self, dots: List[DMXRenderDot]) -> List[DMXRenderDot]:
        for pipe in self._pre_process_dots_pipeline[:]:
            dots = pipe(dots)
        return dots

    def _post_process_dots(
            self,
            dots: List[DenormalizedDMXRenderDot]
        ) -> List[DenormalizedDMXRenderDot]:
        for pipe in self._post_process_dots_pipeline:
            dots = pipe(dots)
        return dots

    def _post_process_render(self, render: bytes) -> bytes:
        for pipe in self._post_process_render_pipeline[:]:
            render = pipe(render)
        return render

    def _fill_bound_render(self, count: int, value: int) -> bytes:
        return bytes([value]) * count

    def _denormalize_dots(
            self,
            xy_grid: XYGrid,
            dots: List[DMXRenderDot]
        ) -> List[DenormalizedDMXRenderDot]:
        return [
            DenormalizedDMXRenderDot(
                xy_grid.to_frame_x(dot.x),
                xy_grid.to_frame_y(dot.y),
                dot.dot_type
            )
            for dot in dots
        ]

    def _empty_dots_render(self, xy_grid: XYGrid, default_value: int) -> bytes:
        return bytes([default_value]) * xy_grid.size_x_getter()

    def _render(self, dots: List[DenormalizedDMXRenderDot]) -> bytes:
        render = bytearray()

        LINETYPE = InterpolationType.LINEAR
        i = 0
        while i < len(dots) - 1:
            dot_x, dot_y, interp = dots[i]
            next_dot_x, next_dot_y, next_interp = dots[i + 1]
            i += 1
            if (interp is LINETYPE) and (next_interp is LINETYPE):
                count = next_dot_x - dot_x + 1
                dots_render = render_interpolation.linspace(dot_y, next_dot_y, count)
                if (next_dot_y == dots_render[-1]) and (dots[i] is not dots[-1]):
                    dots_render = dots_render[:-1]
            else:
                i += 1
                spline_dots_x = [dot_x, next_dot_x]
                spline_dots_y = [dot_y, next_dot_y]
                next_dot_i = i - 1
                while i < len(dots):
                    next_dot_i = i
                    spline_dots_x.append(dots[i][0])
                    spline_dots_y.append(dots[i][1])
                    i += 1
                    if dots[next_dot_i][2] is LINETYPE:
                        i -= 1
                        break
                if len(spline_dots_x) < 3:
                    spline_dots_x.append(dots[next_dot_i][0] + 1)
                    spline_dots_y.append(dots[next_dot_i][1])

                first_spline_x = spline_dots_x[0]
                x_list = [x - first_spline_x for x in spline_dots_x]
                spline_values = render_interpolation.cubic_interpolate(
                    tuple(x_list),
                    tuple(spline_dots_y)
                )
                if next_dot_i == len(dots) - 1:
                    dots_render = spline_values
                else:
                    dots_render = spline_values[:-1]
            render += bytes(dots_render)

        return bytes(render)
