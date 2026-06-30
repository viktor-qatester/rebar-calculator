def calc_bars_per_height(height_cm: float) -> int:
    """Упрощённо: количество горизонтальных поясов по высоте."""
    if height_cm <= 60:
        return 2
    if height_cm <= 100:
        return 3
    return 4


def calc_bars_per_belt(width_cm: float) -> int:
    """Сколько продольных прутков в одном поясе (по ширине ленты). Упрощённо."""
    if width_cm <= 40:
        return 2
    if width_cm <= 60:
        return 3
    return 4


def calc_bars_per_pile(_pile_diameter_mm: int) -> int:
    """Упрощённо: вертикальных прутков в одной свае (по проекту обычно 4)."""
    return 4
