"""Обработчики Telegram-бота."""

from __future__ import annotations

import logging
from typing import Any

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.file_inspector import inspect_bytes
from bot.formatters import format_piles_result, format_slab_result, format_strip_result
from calc.constants import DEFAULT_RESERVE_PCT, DISCLAIMER
from calc.models import InputParams
from calc.pile_types import PileRowInput
from calc.piles import calculate_piles
from calc.slab import calculate_slab
from calc.strip import calculate_strip
from calc.rules import calc_bars_per_belt, calc_bars_per_height

logger = logging.getLogger(__name__)

# Состояния диалогов
(
    STRIP_HEIGHT,
    STRIP_WIDTH,
    STRIP_LENGTH,
    STRIP_REBAR,
    STRIP_TRADE,
    STRIP_BELTS,
    STRIP_ROW_BARS,
    SLAB_LENGTH,
    SLAB_WIDTH,
    SLAB_THICK,
    SLAB_STEP,
    SLAB_REBAR,
    SLAB_TRADE,
    PILE_DIAM,
    PILE_LEN,
    PILE_COUNT,
    PILE_REBAR,
    PILE_TRADE,
    AWAITING_FILE,
) = range(19)

BTN_STRIP = "Ленточный"
BTN_SLAB = "Плита"
BTN_PILES = "Сваи"
BTN_FILE = "Загрузить проект"
BTN_HELP = "Помощь"
BTN_CANCEL = "Отмена"

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [BTN_STRIP, BTN_SLAB],
        [BTN_PILES, BTN_FILE],
        [BTN_HELP],
    ],
    resize_keyboard=True,
)


def _parse_float(text: str) -> float:
    return float(text.replace(",", ".").strip())


def _parse_int(text: str) -> int:
    return int(_parse_float(text))


def _parse_auto_or_int(text: str) -> int | None:
    """None = автоматический расчёт."""
    t = text.strip().lower()
    if t in {"", "авто", "auto", "а", "-", "0"}:
        return None
    return _parse_int(text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "🏗 *Калькулятор арматуры 3.0*\n\n"
        f"_{DISCLAIMER}_\n\n"
        "Выберите тип расчёта или загрузите проект.\n"
        "В любой момент: /cancel — отмена, /start — меню.",
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD,
    )
    return ConversationHandler.END


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "*Как пользоваться*\n\n"
        "• *Ленточный* — пояса и прутки в ряду (авто или вручную)\n"
        "• *Плита* — двухслойная сетка\n"
        "• *Сваи* — вертикальная арматура (один тип за раз)\n"
        "• *Загрузить проект* — PDF, Excel, фото, DXF\n\n"
        "Ответы по метражу из проекта (ИИ) — в следующей версии.\n"
        "Сейчас бот показывает, *что прочитал* в файле.\n\n"
        "/start — главное меню",
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD,
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Отменено.", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END


# --- Ленточный ---

async def strip_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    context.user_data["flow"] = "strip"
    await update.message.reply_text(
        "Ленточный фундамент.\nВведите *высоту ленты, см* (например 60):",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return STRIP_HEIGHT


async def strip_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["height_cm"] = _parse_float(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число, например 60")
        return STRIP_HEIGHT
    await update.message.reply_text("Ширина ленты, *см* (например 40):", parse_mode="Markdown")
    return STRIP_WIDTH


async def strip_width(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["width_cm"] = _parse_float(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число, например 40")
        return STRIP_WIDTH
    await update.message.reply_text("Суммарная длина стен, *м* (например 74):", parse_mode="Markdown")
    return STRIP_LENGTH


async def strip_length(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["total_length_m"] = _parse_float(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число, например 74")
        return STRIP_LENGTH
    await update.message.reply_text("Диаметр арматуры, *мм* (6, 8, 10, 12 или 14):", parse_mode="Markdown")
    return STRIP_REBAR


async def strip_rebar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["rebar_d_mm"] = _parse_int(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите целое число, например 10")
        return STRIP_REBAR
    await update.message.reply_text("Длина прутка в продаже, *м* (например 6):", parse_mode="Markdown")
    return STRIP_TRADE


async def strip_trade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        trade = _parse_float(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число, например 6")
        return STRIP_TRADE

    context.user_data["trade_bar_length_m"] = trade
    height = context.user_data["height_cm"]
    auto_belts = calc_bars_per_height(height)
    await update.message.reply_text(
        f"Поясов по высоте — *{auto_belts}* (авто при {height:g} см).\n"
        "Введите своё число (например *4*) или «*авто*»:",
        parse_mode="Markdown",
    )
    return STRIP_BELTS


async def strip_belts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        belts = _parse_auto_or_int(update.message.text)
        if belts is not None and belts < 1:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Введите число от 1 (например 4) или «авто»")
        return STRIP_BELTS

    context.user_data["bars_per_height"] = belts
    width = context.user_data["width_cm"]
    auto_row = calc_bars_per_belt(width)
    await update.message.reply_text(
        f"Прутков в ряду (на пояс) — *{auto_row}* (авто при ширине {width:g} см).\n"
        "Введите своё число (например *6*) или «*авто*»:",
        parse_mode="Markdown",
    )
    return STRIP_ROW_BARS


async def strip_row_bars(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        row_bars = _parse_auto_or_int(update.message.text)
        if row_bars is not None and row_bars < 1:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Введите число от 1 (например 6) или «авто»")
        return STRIP_ROW_BARS

    d = context.user_data
    trade = d["trade_bar_length_m"]
    belts = d["bars_per_height"]
    auto_belts = calc_bars_per_height(d["height_cm"])
    auto_row = calc_bars_per_belt(d["width_cm"])

    notes: list[str] = []
    if belts is None:
        notes.append(f"Пояса: {auto_belts} шт. (авто по высоте {d['height_cm']:g} см)")
    else:
        notes.append(f"Пояса: {belts} шт. (вручную, авто было {auto_belts})")
    if row_bars is None:
        notes.append(f"Прутков в ряду: {auto_row} (авто по ширине {d['width_cm']:g} см)")
    else:
        notes.append(f"Прутков в ряду: {row_bars} (вручную, авто было {auto_row})")

    params = InputParams(
        foundation_type="strip",
        height_cm=d["height_cm"],
        width_cm=d["width_cm"],
        total_length_m=d["total_length_m"],
        rebar_d_mm=d["rebar_d_mm"],
        trade_bar_length_m=trade,
        bars_per_height=belts,
        bars_per_belt=row_bars,
        reserve_pct=DEFAULT_RESERVE_PCT,
    )
    try:
        result = calculate_strip(params)
    except Exception as exc:
        await update.message.reply_text(f"Ошибка расчёта: {exc}", reply_markup=MAIN_KEYBOARD)
        return ConversationHandler.END

    await update.message.reply_text(
        format_strip_result(result, trade, notes),
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD,
    )
    return ConversationHandler.END


# --- Плита ---

async def slab_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    context.user_data["flow"] = "slab"
    await update.message.reply_text(
        "Плитный фундамент.\nДлина плиты, *м* (например 10):",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return SLAB_LENGTH


async def slab_length(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["slab_length_m"] = _parse_float(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число")
        return SLAB_LENGTH
    await update.message.reply_text("Ширина плиты, *м*:", parse_mode="Markdown")
    return SLAB_WIDTH


async def slab_width(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["slab_width_m"] = _parse_float(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число")
        return SLAB_WIDTH
    await update.message.reply_text("Толщина плиты, *см* (например 30):", parse_mode="Markdown")
    return SLAB_THICK


async def slab_thick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["slab_thickness_cm"] = _parse_float(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число")
        return SLAB_THICK
    await update.message.reply_text("Шаг сетки армирования, *см* (например 20):", parse_mode="Markdown")
    return SLAB_STEP


async def slab_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["grid_step_cm"] = _parse_float(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число")
        return SLAB_STEP
    await update.message.reply_text("Диаметр арматуры, *мм*:", parse_mode="Markdown")
    return SLAB_REBAR


async def slab_rebar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["rebar_d_mm"] = _parse_int(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число")
        return SLAB_REBAR
    await update.message.reply_text("Длина прутка в продаже, *м*:", parse_mode="Markdown")
    return SLAB_TRADE


async def slab_trade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        trade = _parse_float(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число")
        return SLAB_TRADE

    d = context.user_data
    params = InputParams(
        foundation_type="slab",
        height_cm=d["slab_thickness_cm"],
        width_cm=d["slab_width_m"] * 100,
        total_length_m=(d["slab_length_m"] + d["slab_width_m"]) * 2,
        rebar_d_mm=d["rebar_d_mm"],
        trade_bar_length_m=trade,
        reserve_pct=DEFAULT_RESERVE_PCT,
    )
    try:
        result = calculate_slab(params, d["slab_length_m"], d["slab_width_m"], d["grid_step_cm"])
    except Exception as exc:
        await update.message.reply_text(f"Ошибка расчёта: {exc}", reply_markup=MAIN_KEYBOARD)
        return ConversationHandler.END

    await update.message.reply_text(
        format_slab_result(result, trade),
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD,
    )
    return ConversationHandler.END


# --- Сваи ---

async def piles_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    context.user_data["flow"] = "piles"
    await update.message.reply_text(
        "Сваи.\nДиаметр *бетонной* сваи, мм (200, 300 или 400):",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return PILE_DIAM


async def pile_diam(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["pile_diameter_mm"] = _parse_int(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число, например 300")
        return PILE_DIAM
    await update.message.reply_text("Длина сваи, *м* (например 1.95):", parse_mode="Markdown")
    return PILE_LEN


async def pile_len(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["pile_length_m"] = _parse_float(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число")
        return PILE_LEN
    await update.message.reply_text("Количество свай, *шт*:", parse_mode="Markdown")
    return PILE_COUNT


async def pile_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["pile_count"] = _parse_int(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите целое число")
        return PILE_COUNT
    await update.message.reply_text("Диаметр *арматуры* в свае, мм:", parse_mode="Markdown")
    return PILE_REBAR


async def pile_rebar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["rebar_d_mm"] = _parse_int(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число")
        return PILE_REBAR
    await update.message.reply_text("Длина прутка в продаже, *м*:", parse_mode="Markdown")
    return PILE_TRADE


async def pile_trade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        trade = _parse_float(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число")
        return PILE_TRADE

    d = context.user_data
    row = PileRowInput(
        pile_diameter_mm=d["pile_diameter_mm"],
        pile_length_m=d["pile_length_m"],
        pile_count=d["pile_count"],
        rebar_d_mm=d["rebar_d_mm"],
        trade_bar_length_m=trade,
    )
    try:
        result = calculate_piles([row], DEFAULT_RESERVE_PCT)
    except Exception as exc:
        await update.message.reply_text(f"Ошибка расчёта: {exc}", reply_markup=MAIN_KEYBOARD)
        return ConversationHandler.END

    await update.message.reply_text(
        format_piles_result(result),
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD,
    )
    return ConversationHandler.END


# --- Файлы ---

async def file_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    context.user_data["flow"] = "file"
    await update.message.reply_text(
        "Пришлите файл проекта (PDF, Excel, фото, DXF).\n"
        "Или /cancel — назад в меню.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return AWAITING_FILE


async def file_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message
    if message.document:
        doc = message.document
        filename = doc.file_name or "document"
        tg_file = await doc.get_file()
        data = bytes(await tg_file.download_as_bytearray())
    elif message.photo:
        photo = message.photo[-1]
        filename = "photo.jpg"
        tg_file = await photo.get_file()
        data = bytes(await tg_file.download_as_bytearray())
    else:
        await update.message.reply_text("Пришлите файл или фото документа.")
        return AWAITING_FILE

    inspection = inspect_bytes(filename, data)
    footer = (
        "\n\n_Автоответ по метражу из проекта — позже. "
        "Сейчас только разбор файла._"
    )
    await update.message.reply_text(
        inspection.summary + footer,
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD,
    )
    return ConversationHandler.END


async def fallback_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()
    if text == BTN_HELP:
        await help_cmd(update, context)
        return
    await update.message.reply_text(
        "Нажмите кнопку меню или /start",
        reply_markup=MAIN_KEYBOARD,
    )


def register_handlers(app: Application) -> None:
    strip_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{BTN_STRIP}$"), strip_start)],
        states={
            STRIP_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, strip_height)],
            STRIP_WIDTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, strip_width)],
            STRIP_LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, strip_length)],
            STRIP_REBAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, strip_rebar)],
            STRIP_TRADE: [MessageHandler(filters.TEXT & ~filters.COMMAND, strip_trade)],
            STRIP_BELTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, strip_belts)],
            STRIP_ROW_BARS: [MessageHandler(filters.TEXT & ~filters.COMMAND, strip_row_bars)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )

    slab_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{BTN_SLAB}$"), slab_start)],
        states={
            SLAB_LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, slab_length)],
            SLAB_WIDTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, slab_width)],
            SLAB_THICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, slab_thick)],
            SLAB_STEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, slab_step)],
            SLAB_REBAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, slab_rebar)],
            SLAB_TRADE: [MessageHandler(filters.TEXT & ~filters.COMMAND, slab_trade)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )

    piles_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{BTN_PILES}$"), piles_start)],
        states={
            PILE_DIAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, pile_diam)],
            PILE_LEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, pile_len)],
            PILE_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, pile_count)],
            PILE_REBAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, pile_rebar)],
            PILE_TRADE: [MessageHandler(filters.TEXT & ~filters.COMMAND, pile_trade)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )

    file_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{BTN_FILE}$"), file_start)],
        states={
            AWAITING_FILE: [
                MessageHandler(filters.Document.ALL | filters.PHOTO, file_received),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(strip_conv)
    app.add_handler(slab_conv)
    app.add_handler(piles_conv)
    app.add_handler(file_conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_text))
