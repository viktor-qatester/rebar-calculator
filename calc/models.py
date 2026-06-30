from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

FoundationType = Literal["strip", "slab", "pile_grillage"]


@dataclass(frozen=True)
class CalcResult:
    bars_per_height: int
    bars_per_belt: int
    overlap_m: float
    segments_per_bar: int
    bar_effective_length_m: float
    total_length_m: float
    total_length_with_reserve_m: float
    trade_bars_count: int
    trade_bars_suggested: int


@dataclass(frozen=True)
class InputParams:
    foundation_type: FoundationType
    height_cm: float
    width_cm: float
    total_length_m: float
    rebar_d_mm: int
    trade_bar_length_m: float
    bars_per_height: int | None = None
    bars_per_belt: int | None = None
    reserve_pct: float = 10.0
