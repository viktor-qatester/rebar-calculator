from dataclasses import dataclass


@dataclass(frozen=True)
class PileRowInput:
    pile_diameter_mm: int
    pile_length_m: float
    pile_count: int
    rebar_d_mm: int
    trade_bar_length_m: float
