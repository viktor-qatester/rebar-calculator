"""Поиск упоминаний арматуры в тексте проектов (без ИИ)."""

from __future__ import annotations

import re

# Типовые обозначения в КЖ: 12S400, 6 S240, сетки, каркасы
REBAR_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"арматур", re.IGNORECASE),
    re.compile(r"армирован", re.IGNORECASE),
    re.compile(r"\bарм\.?", re.IGNORECASE),
    re.compile(r"\b[аa][- ]?500", re.IGNORECASE),
    re.compile(r"\b[аa][- ]?400", re.IGNORECASE),
    re.compile(r"\b[аa][- ]?240", re.IGNORECASE),
    re.compile(r"\d{1,2}\s*[sс]\s*\d{3}", re.IGNORECASE),
    re.compile(r"\b[sс]\s*\d{3}\b", re.IGNORECASE),
    re.compile(r"[øØφф]\s*\d{1,2}\b", re.IGNORECASE),
    re.compile(r"\b[ds]\d{1,2}\b", re.IGNORECASE),
    re.compile(r"сетк[аи]", re.IGNORECASE),
    re.compile(r"\b1[cс]\b", re.IGNORECASE),
    re.compile(r"каркас", re.IGNORECASE),
    re.compile(r"стержн", re.IGNORECASE),
    re.compile(r"прут", re.IGNORECASE),
    re.compile(r"\bкж\b", re.IGNORECASE),
    re.compile(r"гост\s*5781", re.IGNORECASE),
    re.compile(r"стб\s*\d+", re.IGNORECASE),
    re.compile(r"\bL\s*=\s*\d+", re.IGNORECASE),
    re.compile(r"железобетон", re.IGNORECASE),
)


def normalize_project_text(text: str) -> str:
    """Схлопывает лишние пробелы — PDF часто рвёт слова."""
    return re.sub(r"\s+", " ", text)


def line_has_rebar(line: str) -> bool:
    return any(p.search(line) for p in REBAR_PATTERNS)


def count_rebar_mentions(text: str) -> int:
    normalized = normalize_project_text(text)
    return sum(len(p.findall(normalized)) for p in REBAR_PATTERNS)


def find_rebar_snippets(text: str, limit: int = 8) -> list[str]:
    hits: list[str] = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln or not line_has_rebar(ln):
            continue
        snippet = ln[:140] + ("…" if len(ln) > 140 else "")
        hits.append(snippet)
        if len(hits) >= limit:
            break
    return hits


def find_rebar_snippets_by_page(pages: list[str], limit: int = 8) -> list[str]:
    hits: list[str] = []
    for page_no, page_text in enumerate(pages, start=1):
        for ln in page_text.splitlines():
            ln = ln.strip()
            if not ln or not line_has_rebar(ln):
                continue
            snippet = ln[:120] + ("…" if len(ln) > 120 else "")
            hits.append(f"стр. {page_no}: {snippet}")
            if len(hits) >= limit:
                return hits
    return hits
