from math import ceil

from calc.models import CalcResult, InputParams
from calc.overlap import calc_bar_effective_length, calc_overlap_m
from calc.rules import calc_bars_per_belt, calc_bars_per_height


def calculate_strip(params: InputParams) -> CalcResult:
    if params.foundation_type != "strip":
        raise ValueError("v0.1 поддерживает только ленточный фундамент")

    bars_h = params.bars_per_height or calc_bars_per_height(params.height_cm)
    bars_b = params.bars_per_belt or calc_bars_per_belt(params.width_cm)
    overlap = calc_overlap_m(params.rebar_d_mm)

    bar_effective, segments = calc_bar_effective_length(
        params.total_length_m,
        params.trade_bar_length_m,
        overlap,
    )

    total = bars_h * bars_b * bar_effective
    total_reserve = total * (1 + params.reserve_pct / 100)
    trade_count = ceil(total_reserve / params.trade_bar_length_m)

    return CalcResult(
        bars_per_height=bars_h,
        bars_per_belt=bars_b,
        overlap_m=overlap,
        segments_per_bar=segments,
        bar_effective_length_m=bar_effective,
        total_length_m=total,
        total_length_with_reserve_m=total_reserve,
        trade_bars_count=trade_count,
        trade_bars_suggested=trade_count + 1,
    )
