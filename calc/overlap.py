from math import ceil

from calc.constants import OVERLAP_FACTOR


def calc_overlap_m(diameter_mm: int) -> float:
    return OVERLAP_FACTOR * diameter_mm / 1000


def calc_bar_effective_length(
    run_length_m: float,
    trade_bar_length_m: float,
    overlap_m: float,
) -> tuple[float, int]:
    """Длина одного продольного прутка с учётом стыков из торговых хлыстов."""
    segments = ceil(run_length_m / trade_bar_length_m)
    effective = run_length_m + (segments - 1) * overlap_m
    return effective, segments
