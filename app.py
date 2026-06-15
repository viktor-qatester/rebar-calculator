"""
Упрощённый калькулятор горизонтальной (продольной) арматуры ленточного и плитного фундамента.
Не заменяет проект конструктора.
"""

import streamlit as st

from calc.constants import (
    DISCLAIMER,
    FOUNDATION_TYPES,
    FOUNDATION_TYPES_COMING_SOON,
    REBAR_DIAMETERS_MM,
    TRADE_BAR_LENGTHS_M,
)
from calc.models import InputParams
from calc.strip import calculate_strip
from calc.slab import calculate_slab

st.set_page_config(page_title="Калькулятор арматуры", layout="wide")

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

    # --- ОБЩИЕ НАСТРОЙКИ АРМАТУРЫ ---
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
    
    # Настройки слоев
    if foundation_type == "strip":
        auto_belts = st.checkbox("Пояса по высоте — автоматически", value=True)
        bars_per_height = None
        if not auto_belts:
            bars_per_height = st.number_input("Поясов вручную", min_value=1, value=2, step=1)

        auto_width_bars = st.checkbox("Прутков на пояс — автоматически по ширине", value=True)
        bars_per_belt = None
        if not auto_width_bars:
            bars_per_belt = st.number_input("Прутков на пояс", min_value=1, value=2, step=1)
    
    elif foundation_type == "slab":
        st.info("Для плитного фундамента расчет производится автоматически для двух слоев сетки (верхнего и нижнего).")
        bars_per_height = None
        bars_per_belt = None

    st.caption("Запас: +10% к метражу. Поперечная арматура — в следующей версии.")
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
    st.table({
        "Параметр": ["Тип фундамента", "Размеры", "Высота/Толщина", "Диаметр арматуры, мм", "Длина прутка, м"],
        "Значение": [
            FOUNDATION_TYPES[foundation_type],
            f"{slab_length_m}x{slab_width_m} м" if foundation_type == "slab" else f"Стены: {total_length_m} м",
            f"{slab_thickness_cm} см" if foundation_type == "slab" else f"{height_cm} см",
            rebar_d_mm,
            trade_bar_length_m,
        ]
    })