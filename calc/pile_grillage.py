from dataclasses import dataclass
from math import ceil

from calc.models import CalcResult, InputParams
from calc.pile_types import PileRowInput
from calc.overlap import calc_bar_effective_length, calc_overlap_m
from calc.piles import calculate_piles
from calc.rules import calc_bars_per_belt, calc_bars_per_height


@dataclass(frozen=True)
class PileGrillageCombinedResult:
    grillage: CalcResult
    piles: CalcResult
    total_length_m: float
    total_length_with_reserve_m: float
    trade_bars_count: int
    trade_bars_suggested: int


def _calculate_grillage_beams(params: InputParams) -> CalcResult:
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


def calculate_pile_grillage(
    grillage_params: InputParams,
    pile_rows: list[PileRowInput],
) -> PileGrillageCombinedResult:
    """
    Ростверк (продольная арматура балок) + сваи (вертикальная арматура).
  """
    if grillage_params.foundation_type != "pile_grillage":
        raise ValueError("Ожидается тип фундамента pile_grillage")

    grillage = _calculate_grillage_beams(grillage_params)
    active_rows = [r for r in pile_rows if r.pile_count > 0]
    if active_rows:
        piles = calculate_piles(active_rows, grillage_params.reserve_pct)
    else:
        piles = CalcResult(
            bars_per_height=0,
            bars_per_belt=0,
            overlap_m=0.0,
            segments_per_bar=0,
            bar_effective_length_m=0.0,
            total_length_m=0.0,
            total_length_with_reserve_m=0.0,
            trade_bars_count=0,
            trade_bars_suggested=0,
        )

    total = grillage.total_length_m + piles.total_length_m
    total_reserve = grillage.total_length_with_reserve_m + piles.total_length_with_reserve_m

    same_trade = (
        grillage_params.trade_bar_length_m == active_rows[0].trade_bar_length_m
        if active_rows
        else True
    )
    same_rebar = (
        grillage_params.rebar_d_mm == active_rows[0].rebar_d_mm
        if active_rows
        else True
    )

    if same_trade and same_rebar:
        trade_count = ceil(total_reserve / grillage_params.trade_bar_length_m)
    else:
        trade_count = grillage.trade_bars_count + piles.trade_bars_count

    return PileGrillageCombinedResult(
        grillage=grillage,
        piles=piles,
        total_length_m=total,
        total_length_with_reserve_m=total_reserve,
        trade_bars_count=trade_count,
        trade_bars_suggested=trade_count + 1,
    )
