"""Проверка эталонного расчёта из ТЗ (без pytest)."""

from calc.models import InputParams
from calc.strip import calculate_strip


def main() -> None:
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

    assert result.bars_per_height == 2, result.bars_per_height
    assert result.bars_per_belt == 2, result.bars_per_belt
    assert abs(result.overlap_m - 0.4) < 1e-9, result.overlap_m
    assert result.segments_per_bar == 13, result.segments_per_bar
    assert abs(result.bar_effective_length_m - 78.8) < 1e-9, result.bar_effective_length_m
    assert abs(result.total_length_m - 315.2) < 1e-9, result.total_length_m
    assert abs(result.total_length_with_reserve_m - 346.72) < 1e-9, result.total_length_with_reserve_m
    assert result.trade_bars_count == 58, result.trade_bars_count
    assert result.trade_bars_suggested == 59, result.trade_bars_suggested

    print("OK: все проверки пройдены")
    print(f"  Метраж без запаса: {result.total_length_m} м")
    print(f"  Метраж +10%:       {result.total_length_with_reserve_m} м")
    print(f"  Прутков 6 м:       {result.trade_bars_count} шт.")


if __name__ == "__main__":
    main()
