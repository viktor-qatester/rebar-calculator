"""Форматирование результатов расчёта для Telegram."""

from calc.models import CalcResult


def format_strip_result(
    result: CalcResult,
    trade_bar_m: float,
    notes: list[str] | None = None,
) -> str:
    text = (
        "✅ *Ленточный фундамент*\n\n"
        f"Метраж без запаса: *{result.total_length_m:.1f} м*\n"
        f"Метраж +10%: *{result.total_length_with_reserve_m:.1f} м*\n"
        f"Прутков {trade_bar_m:g} м: *{result.trade_bars_count} шт.*\n"
        f"Рекомендую: *{result.trade_bars_suggested} шт.* (+1)\n\n"
        f"Поясов: {result.bars_per_height} · прутков в ряду: {result.bars_per_belt}\n"
        f"Нахлёст: {result.overlap_m:.2f} м"
    )
    if notes:
        for note in notes:
            text += f"\n_{note}_"
    return text


def format_slab_result(result: CalcResult, trade_bar_m: float) -> str:
    return (
        "✅ *Плитный фундамент*\n\n"
        f"Метраж без запаса: *{result.total_length_m:.1f} м*\n"
        f"Метраж +10%: *{result.total_length_with_reserve_m:.1f} м*\n"
        f"Прутков {trade_bar_m:g} м: *{result.trade_bars_count} шт.*\n"
        f"Рекомендую: *{result.trade_bars_suggested} шт.* (+1)\n\n"
        f"Слоёв сетки: {result.bars_per_height} · рядов: {result.bars_per_belt}\n"
        f"Нахлёст: {result.overlap_m:.2f} м"
    )


def format_piles_result(result: CalcResult) -> str:
    return (
        "✅ *Сваи*\n\n"
        f"Свай всего: *{result.bars_per_belt} шт.*\n"
        f"Прутков в одной свае: *{result.bars_per_height}*\n"
        f"Метраж без запаса: *{result.total_length_m:.1f} м*\n"
        f"Метраж +10%: *{result.total_length_with_reserve_m:.1f} м*\n"
        f"Прутков к закупке: *{result.trade_bars_count} шт.*\n"
        f"Рекомендую: *{result.trade_bars_suggested} шт.* (+1)"
    )
