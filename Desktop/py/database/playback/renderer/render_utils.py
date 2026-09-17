from kivy.utils import boundary
from database.patch import RowPatch
from libs.dmx512_render import render_interpolation
from database.fixture_param import RowFixtureParam
from typing import List, Dict, Set
from enum import Enum, auto
from dataclasses import dataclass, field
from collections import defaultdict
import itertools
from libs.dmx512_render import DMXRenderDot, InterpolationType


def get_rows_to_dots_all(
    render_rows: List["PlaybackRenderRow"]
) -> Dict["PlaybackRenderRow", List[DMXRenderDot]]:
    rows_dots = defaultdict(list)
    for row in render_rows:
        rows_dots[row] = row.dots
    return rows_dots

def get_rows_to_dots_by_x(
    render_rows: List["PlaybackRenderRow"], x: float
) -> Dict["PlaybackRenderRow", List[DMXRenderDot]]:
    rows_dots = defaultdict(list)
    for row in render_rows:
        dot = row.dots.find_dot_by_x(x, render_rows[0].renderer.xy_grid)
        if dot:
            rows_dots[row].append(dot)
    return rows_dots

def get_dots_by_x(
    render_rows: List["PlaybackRenderRow"], x: float
) -> List[DMXRenderDot]:
    dots = []
    for row in render_rows:
        dot = row.dots.find_dot_by_x(x, render_rows[0].renderer.xy_grid)
        if dot is not None and dot not in dots:
            dots.append(dot)
    return dots

def get_dots_by_area(
    render_rows: List["PlaybackRenderRow"],
    x: float, y: float, width: float, height: float
) -> List[DMXRenderDot]:
    dots = []
    for row in render_rows:
        for dot in row.dots.find_dots_by_area(x, y, width, height):
            if dot not in dots:
                dots.append(dot)
    return dots

def get_patch_render_rows(
    render_rows: List["PlaybackRenderRow"]
) -> Dict[RowPatch, List["PlaybackRenderRow"]]:
    rows = defaultdict(list)
    for row in render_rows:
        rows[row.patch].append(row)
    return rows
