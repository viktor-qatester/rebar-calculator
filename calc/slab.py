import math
from calc.models import InputParams, CalcResult

def calculate_slab(params: InputParams, slab_length_m: float, slab_width_m: float, grid_step_cm: float) -> CalcResult:
    """
    Расчёт горизонтальной арматуры для плитного фундамента (двухслойная сетка).
    """
    grid_step_m = grid_step_cm / 100.0
    overlap_m = (40 * params.rebar_d_mm) / 1000.0
    trade_len = params.trade_bar_length_m

    if trade_len >= slab_length_m:
        segments_per_long_bar = 1
        bar_eff_len_long = trade_len
    else:
        bar_eff_len_long = trade_len - overlap_m
        if bar_eff_len_long <= 0:
            raise ValueError("Длина торгового прутка слишком мала для обеспечения нахлёста!")
        segments_per_long_bar = math.ceil(slab_length_m / bar_eff_len_long)

    if trade_len >= slab_width_m:
        segments_per_cross_bar = 1
        bar_eff_len_cross = trade_len
    else:
        bar_eff_len_cross = trade_len - overlap_m
        if bar_eff_len_cross <= 0:
            raise ValueError("Длина торгового прутка слишком мала для обеспечения нахлёста!")
        segments_per_cross_bar = math.ceil(slab_width_m / bar_eff_len_cross)

    lines_along_length = math.floor(slab_width_m / grid_step_m) + 1
    lines_along_width = math.floor(slab_length_m / grid_step_m) + 1

    total_long_meters = lines_along_length * slab_length_m
    total_cross_meters = lines_along_width * slab_width_m
    
    net_length_m = (total_long_meters + total_cross_meters) * 2
    reserve_factor = 1.1
    total_length_with_reserve_m = net_length_m * reserve_factor

    total_bars_count = (
        (lines_along_length * segments_per_long_bar) + 
        (lines_along_width * segments_per_cross_bar)
    ) * 2

    trade_bars_suggested = total_bars_count + 1

    return CalcResult(
        total_length_m=net_length_m,
        total_length_with_reserve_m=total_length_with_reserve_m,
        trade_bars_count=total_bars_count,
        trade_bars_suggested=trade_bars_suggested,
        overlap_m=overlap_m,
        bars_per_height=2,
        bars_per_belt=lines_along_length + lines_along_width,
        segments_per_bar=max(segments_per_long_bar, segments_per_cross_bar),
        bar_effective_length_m=min(bar_eff_len_long, bar_eff_len_cross)
    )