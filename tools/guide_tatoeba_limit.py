#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ガイド記事本文の「例えば」「たとえば」出現回数を記事単位で上限化する。"""

from __future__ import annotations

import re
from typing import Final

MAX_EXAMPLE_MARKERS_PER_ARTICLE: Final[int] = 2
# 後方互換（validate_generated_seo 等）
MAX_TATOEBA_PER_ARTICLE: Final[int] = MAX_EXAMPLE_MARKERS_PER_ARTICLE

EXAMPLE_MARKER_RE = re.compile(r"例えば|たとえば")
TATOEBA_RE = re.compile("たとえば")
ALT_MARKERS: Final[tuple[str, ...]] = ("具体例として", "一例として", "例として")

READER_PROSE_FIELD_KEYS: Final[tuple[str, ...]] = (
    "lead",
    "user_intent",
    *(f"section_{idx}_body" for idx in range(1, 9)),
    *(f"faq_{idx}_answer" for idx in range(1, 4)),
)

_READER_HTML_TAGS = ("p", "li", "td", "th", "h2", "h3", "h4", "dd", "div")


class ExampleMarkerBudget:
    """記事内で保持する「例えば」「たとえば」の残数。"""

    __slots__ = ("limit", "used", "_alt_idx")

    def __init__(self, limit: int = MAX_EXAMPLE_MARKERS_PER_ARTICLE) -> None:
        self.limit = max(0, limit)
        self.used = 0
        self._alt_idx = 0

    def process(self, text: str) -> str:
        if not text or not EXAMPLE_MARKER_RE.search(text):
            return text

        def repl(match: re.Match[str]) -> str:
            if self.used < self.limit:
                self.used += 1
                return match.group(0)
            alt = ALT_MARKERS[self._alt_idx % len(ALT_MARKERS)]
            self._alt_idx += 1
            return alt

        return EXAMPLE_MARKER_RE.sub(repl, text)


# 後方互換
TatoebaBudget = ExampleMarkerBudget


def count_example_markers(text: str) -> int:
    return len(EXAMPLE_MARKER_RE.findall(text or ""))


def count_tatoeba(text: str) -> int:
    return len(TATOEBA_RE.findall(text or ""))


def cap_article_tatoeba_fields(
    article: dict[str, str],
    *,
    limit: int = MAX_EXAMPLE_MARKERS_PER_ARTICLE,
) -> dict[str, str]:
    """読者向け prose 列を読み順どおりに処理し、記事全体で例示マーカーを上限以内に抑える。"""
    budget = ExampleMarkerBudget(limit)
    out = dict(article)
    for key in READER_PROSE_FIELD_KEYS:
        raw = out.get(key, "")
        if raw:
            out[key] = budget.process(raw)
    return out


def example_markers_in_reader_html(html: str) -> list[str]:
    """生成 HTML の <main> 内に残る「例えば」「たとえば」（監査用）。"""
    main_m = re.search(r"<main[^>]*>(.*)</main>", html, re.I | re.S)
    if not main_m:
        return []
    chunk = main_m.group(1)
    hits: list[str] = []
    tag_alt = "|".join(_READER_HTML_TAGS)
    for m in re.finditer(rf"<({tag_alt})[^>]*>(.*?)</\1>", chunk, re.I | re.S):
        plain = re.sub(r"<[^>]+>", "", m.group(2))
        hits.extend(EXAMPLE_MARKER_RE.findall(plain))
    return hits


def tatoeba_in_reader_html(html: str) -> list[str]:
    """後方互換。例えば/たとえばの合計ヒットを返す。"""
    return example_markers_in_reader_html(html)
