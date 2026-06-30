"""
Упрощённый калькулятор горизонтальной (продольной) арматуры ленточного и плитного фундамента.
Не заменяет проект конструктора.
"""

import streamlit as st

# models — первым, до остальных модулей calc
from calc.models import InputParams
from calc.pile_types import PileRowInput
from calc.constants import (
    DISCLAIMER,
    FOUNDATION_TYPES,
    FOUNDATION_TYPES_COMING_SOON,
    REBAR_DIAMETERS_MM,
    TRADE_BAR_LENGTHS_M,
)
from calc.strip import calculate_strip
from calc.slab import calculate_slab
from calc.pile_grillage import calculate_pile_grillage

# Диаметры бетонных свай (мм) — по типовому проекту: 200 / 300 / 400
PILE_DIAMETERS_MM = (200, 300, 400)


def _trade_bar_inputs(prefix: str, default_rebar: int = 12, default_trade: float = 6.0) -> tuple[int, float]:
    col1, col2 = st.columns(2)
    rebar_d = col1.selectbox(
        "Диаметр арматуры, мм",
        options=list(REBAR_DIAMETERS_MM),
        index=list(REBAR_DIAMETERS_MM).index(default_rebar) if default_rebar in REBAR_DIAMETERS_MM else 0,
        key=f"{prefix}_rebar_d",
    )
    trade_preset = col2.selectbox(
        "Длина прутка в продаже, м",
        options=[*TRADE_BAR_LENGTHS_M, "Свой"],
        key=f"{prefix}_trade_preset",
    )
    trade_custom = st.number_input(
        "Своя длина прутка, м",
        min_value=0.1,
        value=default_trade,
        step=0.5,
        disabled=trade_preset != "Свой",
        key=f"{prefix}_trade_custom",
    )
    trade_len = trade_custom if trade_preset == "Свой" else float(trade_preset)
    return int(rebar_d), trade_len


st.set_page_config(page_title="Калькулятор арматуры", layout="centered", page_icon="🏗️")

st.title("Калькулятор арматуры 3.0")
st.caption(DISCLAIMER)

with st.form("calc_form"):
    st.subheader("Геометрия фундамента")
    
    # Выбор типа фундамента
    foundation_type = st.selectbox(
        "Тип фундамента",
        options=list(FOUNDATION_TYPES.keys()),
        format_func=lambda key: FOUNDATION_TYPES[key],
    )
    for key, label in FOUNDATION_TYPES_COMING_SOON.items():
        st.caption(f"• {label}")

    st.divider()

    # Инициализируем переменные дефолтными значениями, чтобы Python не ругался
    height_cm = 60.0
    width_cm = 40.0
    total_length_m = 74.0
    
    slab_length_m = 10.0
    slab_width_m = 10.0
    slab_thickness_cm = 30.0
    grid_step_cm = 20.0

    grillage_length_m = 50.0
    grillage_rebar_d_mm = 12
    grillage_trade_bar_length_m = 6.0
    pile_rows_data: list[PileRowInput] = []
    bars_per_height = None
    bars_per_belt = None
    rebar_d_mm = 10
    trade_bar_length_m = 6.0

    # --- ДИНАМИЧЕСКИЕ ПОЛЯ В ЗАВИСИМОСТИ ОТ ВЫБОРА ---
    if foundation_type == "strip":
        st.write("##### Параметры ленты")
        col1, col2, col3 = st.columns(3)
        height_cm = col1.number_input("Высота, см", min_value=1.0, value=60.0, step=5.0)
        width_cm = col2.number_input("Ширина, см", min_value=1.0, value=40.0, step=5.0)
        total_length_m = col3.number_input("Суммарная длина стен, м", min_value=0.1, value=74.0, step=1.0)
    
    elif foundation_type == "slab":
        st.write("##### Параметры плиты")
        col1, col2 = st.columns(2)
        slab_length_m = col1.number_input("Длина плиты, м", min_value=1.0, value=10.0, step=1.0)
        slab_width_m = col2.number_input("Ширина плиты, м", min_value=1.0, value=10.0, step=1.0)
        
        col3, col4 = st.columns(2)
        slab_thickness_cm = col3.number_input("Толщина плиты, см", min_value=1.0, value=30.0, step=5.0)
        grid_step_cm = col4.number_input("Шаг сетки армирования, см", min_value=5.0, value=20.0, step=5.0)

    elif foundation_type == "pile_grillage":
        st.write("##### Ростверк (балки)")
        col1, col2, col3 = st.columns(3)
        grillage_length_m = col1.number_input(
            "Длина ростверка, м",
            min_value=0.1,
            value=50.0,
            step=1.0,
            help="Сложите длины всех балок по плану",
        )
        width_cm = col2.number_input("Ширина ростверка, см", min_value=1.0, value=40.0, step=5.0)
        height_cm = col3.number_input("Высота ростверка, см", min_value=1.0, value=70.0, step=5.0)

        st.write("##### Арматура ростверка")
        grillage_rebar_d_mm, grillage_trade_bar_length_m = _trade_bar_inputs("grillage", 12, 6.0)

        auto_belts = st.checkbox("Пояса по высоте — автоматически", value=True)
        if not auto_belts:
            bars_per_height = st.number_input("Поясов вручную", min_value=1, value=3, step=1)
        auto_width_bars = st.checkbox("Прутков на пояс — автоматически по ширине", value=True)
        if not auto_width_bars:
            bars_per_belt = st.number_input("Прутков на пояс", min_value=1, value=2, step=1)

        st.write("##### Сваи")
        st.caption("До 3 типов свай (разный диаметр). Количество 0 — пропустить тип.")
        for idx, pile_d in enumerate(PILE_DIAMETERS_MM, start=1):
            st.markdown(f"**Тип {idx} — свая ø{pile_d} мм**")
            c1, c2, c3 = st.columns(3)
            pile_diameter = c1.selectbox(
                "Диаметр сваи, мм",
                options=list(PILE_DIAMETERS_MM),
                index=list(PILE_DIAMETERS_MM).index(pile_d),
                key=f"pile_d_{idx}",
            )
            pile_length = c2.number_input(
                "Длина сваи, м",
                min_value=0.1,
                value=1.95,
                step=0.05,
                key=f"pile_len_{idx}",
            )
            pile_count = c3.number_input(
                "Количество, шт",
                min_value=0,
                value=0,
                step=1,
                key=f"pile_cnt_{idx}",
            )
            pile_rebar_d, pile_trade_len = _trade_bar_inputs(f"pile_{idx}", 12, 6.0)
            pile_rows_data.append(
                PileRowInput(
                    pile_diameter_mm=int(pile_diameter),
                    pile_length_m=float(pile_length),
                    pile_count=int(pile_count),
                    rebar_d_mm=pile_rebar_d,
                    trade_bar_length_m=pile_trade_len,
                )
            )

    if foundation_type != "pile_grillage":
        st.subheader("Арматура")
        col4, col5 = st.columns(2)
        rebar_d_mm = col4.selectbox("Диаметр, мм", options=list(REBAR_DIAMETERS_MM))
        trade_preset = col5.selectbox(
            "Длина прутка в продаже, м",
            options=[*TRADE_BAR_LENGTHS_M, "Свой"],
        )
        trade_custom = st.number_input(
            "Своя длина прутка, м",
            min_value=0.1,
            value=6.0,
            step=0.5,
            disabled=trade_preset != "Свой",
        )
        trade_bar_length_m = trade_custom if trade_preset == "Свой" else float(trade_preset)

        st.subheader("Настройки расчёта")

        if foundation_type == "strip":
            auto_belts = st.checkbox("Пояса по высоте — автоматически", value=True)
            if not auto_belts:
                bars_per_height = st.number_input("Поясов вручную", min_value=1, value=2, step=1)
            auto_width_bars = st.checkbox("Прутков на пояс — автоматически по ширине", value=True)
            if not auto_width_bars:
                bars_per_belt = st.number_input("Прутков на пояс", min_value=1, value=2, step=1)
        elif foundation_type == "slab":
            st.info("Для плитного фундамента расчет производится автоматически для двух слоев сетки (верхнего и нижнего).")

    st.caption("Запас: +10% к метражу. Хомуты в сваях — в следующей версии.")
    submitted = st.form_submit_button("Посчитать", type="primary")

# --- ЛОГИКА ОБРАБОТКИ НАЖАТИЯ КНОПКИ ---
if submitted:
    if foundation_type == "strip":
        params = InputParams(
            foundation_type=foundation_type,
            height_cm=height_cm,
            width_cm=width_cm,
            total_length_m=total_length_m,
            rebar_d_mm=int(rebar_d_mm),
            trade_bar_length_m=trade_bar_length_m,
            bars_per_height=int(bars_per_height) if bars_per_height is not None else None,
            bars_per_belt=int(bars_per_belt) if bars_per_belt is not None else None,
            reserve_pct=10.0,
        )
        result = calculate_strip(params)

        st.success("Расчёт выполнен")
        st.markdown("### Итог")
        m1, m2, m3 = st.columns(3)
        m1.metric("Метраж (без запаса)", f"{result.total_length_m:.1f} м")
        m2.metric("Метраж (+10%)", f"{result.total_length_with_reserve_m:.1f} м")
        m3.metric(f"Прутков {trade_bar_length_m:g} м", f"{result.trade_bars_count} шт.")

        st.info(f"Рекомендуем взять **{result.trade_bars_suggested}** прутков (+1 на всякий случай).")

        st.markdown("### Промежуточные расчёты")
        st.table({
            "Параметр": ["Поясов по высоте", "Продольных прутков на пояс", "Нахлёст, м", f"Кусков {trade_bar_length_m:g} м на один пруток", "Эфф. длина одного прутка, м"],
            "Значение": [result.bars_per_height, result.bars_per_belt, f"{result.overlap_m:.2f}", result.segments_per_bar, f"{result.bar_effective_length_m:.1f}"]
        })

    elif foundation_type == "pile_grillage":
        params = InputParams(
            foundation_type=foundation_type,
            height_cm=height_cm,
            width_cm=width_cm,
            total_length_m=grillage_length_m,
            rebar_d_mm=grillage_rebar_d_mm,
            trade_bar_length_m=grillage_trade_bar_length_m,
            bars_per_height=int(bars_per_height) if bars_per_height is not None else None,
            bars_per_belt=int(bars_per_belt) if bars_per_belt is not None else None,
            reserve_pct=10.0,
        )
        combined = calculate_pile_grillage(params, pile_rows_data)

        st.success("Расчёт выполнен")
        st.markdown("### Итог (ростверк + сваи)")
        m1, m2, m3 = st.columns(3)
        m1.metric("Метраж (без запаса)", f"{combined.total_length_m:.1f} м")
        m2.metric("Метраж (+10%)", f"{combined.total_length_with_reserve_m:.1f} м")
        m3.metric("Прутков к закупке", f"{combined.trade_bars_count} шт.")

        st.info(f"Рекомендуем взять **{combined.trade_bars_suggested}** прутков (+1 на всякий случай).")

        st.markdown("### Ростверк")
        g = combined.grillage
        st.table({
            "Параметр": ["Метраж, м", "Метраж +10%, м", f"Прутков {grillage_trade_bar_length_m:g} м"],
            "Значение": [
                f"{g.total_length_m:.1f}",
                f"{g.total_length_with_reserve_m:.1f}",
                g.trade_bars_count,
            ],
        })

        st.markdown("### Сваи")
        p = combined.piles
        if p.total_length_m > 0:
            st.table({
                "Параметр": ["Свай, шт", "Прутков в одной свае", "Метраж, м", "Метраж +10%, м"],
                "Значение": [
                    p.bars_per_belt,
                    p.bars_per_height,
                    f"{p.total_length_m:.1f}",
                    f"{p.total_length_with_reserve_m:.1f}",
                ],
            })
        else:
            st.caption("Сваи не заданы (везде количество 0).")

        st.markdown("### Промежуточные расчёты (ростверк)")
        st.table({
            "Параметр": [
                "Поясов по высоте",
                "Продольных прутков на пояс",
                "Нахлёст, м",
                "Эфф. длина одного прутка, м",
            ],
            "Значение": [
                g.bars_per_height,
                g.bars_per_belt,
                f"{g.overlap_m:.2f}",
                f"{g.bar_effective_length_m:.1f}",
            ],
        })

    elif foundation_type == "slab":
        params = InputParams(
            foundation_type=foundation_type,
            height_cm=slab_thickness_cm,
            width_cm=slab_width_m * 100.0,
            total_length_m=(slab_length_m + slab_width_m) * 2,
            rebar_d_mm=int(rebar_d_mm),
            trade_bar_length_m=trade_bar_length_m,
            bars_per_height=None,
            bars_per_belt=None,
            reserve_pct=10.0,
        )
        result = calculate_slab(params, slab_length_m, slab_width_m, grid_step_cm)

        st.success("Расчёт выполнен")
        st.markdown("### Итог")
        m1, m2, m3 = st.columns(3)
        m1.metric("Метраж (без запаса)", f"{result.total_length_m:.1f} м")
        m2.metric("Метраж (+10%)", f"{result.total_length_with_reserve_m:.1f} м")
        m3.metric(f"Прутков {trade_bar_length_m:g} м", f"{result.trade_bars_count} шт.")

        st.info(f"Рекомендуем взять **{result.trade_bars_suggested}** прутков (+1 на всякий случай).")

        st.markdown("### Промежуточные расчёты")
        st.table({
            "Параметр": ["Слоёв армирования", "Всего рядов (верх + низ)", "Нахлёст при стыковке, м", "Макс. кусков прутка на сторону", "Эфф. длина прутка (мин), м"],
            "Значение": [result.bars_per_height, result.bars_per_belt, f"{result.overlap_m:.2f}", result.segments_per_bar, f"{result.bar_effective_length_m:.1f}"]
        })

    # Общий блок исходных данных
    st.markdown("### Исходные данные")
    if foundation_type == "slab":
        sizes = f"{slab_length_m}×{slab_width_m} м"
        thickness = f"{slab_thickness_cm} см"
    elif foundation_type == "pile_grillage":
        pile_summary = ", ".join(
            f"ø{r.pile_diameter_mm}×{r.pile_count}"
            for r in pile_rows_data
            if r.pile_count > 0
        ) or "не заданы"
        sizes = f"Ростверк: {grillage_length_m} м; сваи: {pile_summary}"
        thickness = f"{height_cm} см"
        rebar_info = f"ростверк ø{grillage_rebar_d_mm}, сваи — по типам"
        trade_info = f"ростверк {grillage_trade_bar_length_m:g} м"
    else:
        sizes = f"Стены: {total_length_m} м"
        thickness = f"{height_cm} см"
        rebar_info = rebar_d_mm
        trade_info = trade_bar_length_m

    if foundation_type != "pile_grillage":
        rebar_info = rebar_d_mm
        trade_info = trade_bar_length_m

    st.table({
        "Параметр": ["Тип фундамента", "Размеры", "Высота/Толщина", "Диаметр арматуры", "Длина прутка, м"],
        "Значение": [
            FOUNDATION_TYPES[foundation_type],
            sizes,
            thickness,
            rebar_info,
            trade_info,
        ],
    })