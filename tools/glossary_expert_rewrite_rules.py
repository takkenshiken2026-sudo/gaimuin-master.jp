#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用語詳細「編集合格」batch の機械チェック（SEO・読者価値）。"""

from __future__ import annotations

import re

from tools.editorial_quality import (
    GLOSSARY_EXPERT,
    boilerplate_issues,
    concreteness_issues,
    duplicate_faq_answers,
    long_sentence_issues,
    norm,
    split_paragraphs,
    split_semicolon,
)
from tools.glossary_term_rules import check_glossary_row
from tools.guide_concrete_rewrite_rules import EXAMPLE_MARKERS_RE

OPERATOR_BATCH_REF_RE = re.compile(r"batch\s*\d+", re.I)

PROSE_COLS = (
    "short_def",
    "definition",
    "article_lead",
    "term_detail_body",
    "explanation",
    "common_mistakes",
    "memory_tip",
    *(f"faq_{n}_answer" for n in range(1, 5)),
)


def operator_leak_issues(text: str, column: str) -> list[str]:
    if OPERATOR_BATCH_REF_RE.search(text):
        return [f"{column}: 運用メモ「batch N」が読者向け本文に残っています"]
    return []


def expert_tag_present(tags: str) -> bool:
    return GLOSSARY_EXPERT["expert_tag"] in split_semicolon(tags)


def _text_is_concrete(text: str) -> bool:
    if EXAMPLE_MARKERS_RE.search(text):
        return True
    return bool(re.search(r"\d|第\d+条|％", text))


def count_concrete_faq_answers(row: dict[str, str]) -> int:
    return sum(
        1
        for i in range(1, 5)
        if _text_is_concrete(norm(row.get(f"faq_{i}_answer")))
    )


def validate_expert_row(
    row: dict[str, str],
    *,
    term_lookup: dict[str, str],
    guide_slugs: set[str] | None = None,
) -> list[str]:
    """1用語分の expert_pass チェック。ERROR 相当の文字列リスト。"""
    errors: list[str] = []
    term = norm(row.get("term"))
    if not term:
        return ["term が空です"]

    for issue in check_glossary_row(row, term_lookup=term_lookup):
        if issue.level == "ERROR":
            errors.append(f"{term}: {issue.message}")

    tags = norm(row.get("tags"))
    if not expert_tag_present(tags):
        errors.append(
            f"{term}: tags に「{GLOSSARY_EXPERT['expert_tag']}」を含めてください"
        )

    mins = GLOSSARY_EXPERT
    for col, min_len in (
        ("article_lead", mins["article_lead"]),
        ("term_detail_body", mins["term_detail_body"]),
        ("definition", mins["definition"]),
        ("explanation", mins["explanation"]),
        ("common_mistakes", mins["common_mistakes"]),
        ("memory_tip", mins["memory_tip"]),
    ):
        val = norm(row.get(col))
        if len(val) < min_len:
            errors.append(f"{term}: {col} は {min_len} 字以上（現在 {len(val)} 字）")

    body = norm(row.get("term_detail_body"))
    if len(split_paragraphs(body)) < mins["paragraphs_in_body"]:
        errors.append(f"{term}: term_detail_body は空行区切りで {mins['paragraphs_in_body']} 段落以上")

    for col in PROSE_COLS:
        text = norm(row.get(col))
        if not text:
            continue
        for msg in operator_leak_issues(text, col):
            errors.append(f"{term}: {msg}")
        for issue in boilerplate_issues(text, col):
            if issue.level == "ERROR":
                errors.append(f"{term}: {issue.message}")

    for i in range(1, 5):
        ans = norm(row.get(f"faq_{i}_answer"))
        if len(ans) < mins["faq_answer"]:
            errors.append(
                f"{term}: faq_{i}_answer は {mins['faq_answer']} 字以上（現在 {len(ans)} 字）"
            )

    exam_points = split_semicolon(norm(row.get("exam_points")))
    imp = norm(row.get("importance"))
    need_ep = mins["exam_points_as"] if imp in {"A", "S"} else mins["exam_points_min"]
    if len(exam_points) < need_ep:
        errors.append(f"{term}: exam_points は {need_ep} 項目以上")

    related = split_semicolon(norm(row.get("related_terms")))
    if len(related) < mins["related_terms"]:
        errors.append(f"{term}: related_terms は {mins['related_terms']} 件以上")

    if guide_slugs is not None:
        related_links = split_semicolon(norm(row.get("related_links")))
        internal = 0
        for item in related_links:
            target = item.split(":", 1)[0].strip() if ":" in item else item.strip()
            if target and not target.startswith(("http://", "https://")) and target in guide_slugs:
                internal += 1
        if internal < mins["related_links_min"]:
            errors.append(
                f"{term}: related_links に試験ガイド slug を {mins['related_links_min']} 件以上"
            )

    if not _text_is_concrete(body):
        errors.append(f"{term}: term_detail_body に具体例・数値・条文のいずれかが必要です")

    if count_concrete_faq_answers(row) < mins["min_faq_concrete"]:
        errors.append(
            f"{term}: FAQ 回答のうち {mins['min_faq_concrete']} 件以上に具体例・数値を入れてください"
        )

    faq_answers = [norm(row.get(f"faq_{i}_answer")) for i in range(1, 5)]
    for issue in duplicate_faq_answers([a for a in faq_answers if a]):
        errors.append(f"{term}: {issue.message}")

    title = norm(row.get("article_title"))
    if title and term not in title and "とは" not in title:
        errors.append(f"{term}: article_title に用語名または「とは」を含めてください")

    return errors


def validate_expert_rewrites(
    rewrites: dict[str, dict[str, str]],
    *,
    base_rows: dict[str, dict[str, str]],
    term_lookup: dict[str, str],
    guide_slugs: set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    for term, patch in rewrites.items():
        if term not in base_rows:
            errors.append(f"{term}: not in glossary_terms.csv")
            continue
        merged = dict(base_rows[term])
        merged.update(patch)
        errors.extend(
            validate_expert_row(
                merged,
                term_lookup=term_lookup,
                guide_slugs=guide_slugs,
            )
        )
    return errors
