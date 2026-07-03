from bot.rebar_patterns import count_rebar_mentions, find_rebar_snippets, line_has_rebar

SAMPLE_KZH = """
Спецификация на монолитный фундамент Фм1
1C (12S400-200(100)/12S400-200(100)) 584x280
6 S240 СТБ 1704-2012 L=340
"""


def test_detects_s400_not_only_word_armatura():
    assert line_has_rebar("12S400-200(100)")
    assert count_rebar_mentions(SAMPLE_KZH) >= 3
    hits = find_rebar_snippets(SAMPLE_KZH)
    assert any("12S400" in h for h in hits)
