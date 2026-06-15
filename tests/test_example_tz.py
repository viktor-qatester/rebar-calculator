import pytest

from calc.models import InputParams
from calc.strip import calculate_strip


def test_tz_section_6_longitudinal():
    params = InputParams(
        foundation_type="strip",
        height_cm=60,
        width_cm=40,
        total_length_m=74,
        rebar_d_mm=10,
        trade_bar_length_m=6,
        reserve_pct=10,
    )
    result = calculate_strip(params)

    assert result.bars_per_height == 2
    assert result.bars_per_belt == 2
    assert result.overlap_m == pytest.approx(0.4)
    assert result.segments_per_bar == 13
    assert result.bar_effective_length_m == pytest.approx(78.8)
    assert result.total_length_m == pytest.approx(315.2)
    assert result.total_length_with_reserve_m == pytest.approx(346.72)
    assert result.trade_bars_count == 58
    assert result.trade_bars_suggested == 59
