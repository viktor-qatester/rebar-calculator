from math import ceil

from calc.models import CalcResult
from calc.pile_types import PileRowInput
from calc.overlap import calc_bar_effective_length, calc_overlap_m
from calc.rules import calc_bars_per_pile


def calculate_piles(rows: list[PileRowInput], reserve_pct: float) -> CalcResult:
    """Метраж вертикальной арматуры свай (несколько типов)."""
    total = 0.0
    total_segments = 0
    bars_per_pile_max = 0
    overlap_m = 0.0
    trade_len = rows[0].trade_bar_length_m if rows else 6.0

    for row in rows:
        if row.pile_count <= 0:
            continue
        overlap = calc_overlap_m(row.rebar_d_mm)
        overlap_m = overlap
        bars_per_pile = calc_bars_per_pile(row.pile_diameter_mm)
        bars_per_pile_max = max(bars_per_pile_max, bars_per_pile)
        bar_effective, segments = calc_bar_effective_length(
            row.pile_length_m,
            row.trade_bar_length_m,
            overlap,
        )
        total += row.pile_count * bars_per_pile * bar_effective
        total_segments = max(total_segments, segments)
        trade_len = row.trade_bar_length_m

    total_reserve = total * (1 + reserve_pct / 100)
    trade_count = ceil(total_reserve / trade_len) if trade_len > 0 else 0

    return CalcResult(
        bars_per_height=bars_per_pile_max,
        bars_per_belt=sum(r.pile_count for r in rows if r.pile_count > 0),
        overlap_m=overlap_m,
        segments_per_bar=total_segments,
        bar_effective_length_m=0.0,
        total_length_m=total,
        total_length_with_reserve_m=total_reserve,
        trade_bars_count=trade_count,
        trade_bars_suggested=trade_count + 1,
    )
