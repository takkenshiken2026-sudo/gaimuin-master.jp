#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""試験ガイド用の法令数値ファクト（サイト別 JSON）の読み込みと検証。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.editorial_quality import norm
from tools.guide_exam_facts import site_id_from_root

PROSE_COLS = [
    "title",
    "meta_description",
    "lead",
    "user_intent",
    *(f"section_{i}_body" for i in range(1, 8)),
    *(f"faq_{i}_answer" for i in range(1, 5)),
]


def law_facts_path_for_root(root: Path) -> Path:
    sid = site_id_from_root(root)
    for base in (root, Path(__file__).resolve().parents[1]):
        p = base / "sites" / sid / "guide_law_facts.json"
        if p.is_file():
            return p
    return root / "sites" / sid / "guide_law_facts.json"


def load_law_facts(root: Path) -> dict[str, Any] | None:
    path = law_facts_path_for_root(root)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def forbidden_law_phrases(facts: dict[str, Any]) -> list[str]:
    raw = facts.get("forbidden_phrases") or []
    return [norm(x) for x in raw if norm(x)]


def scan_law_forbidden_text(text: str, facts: dict[str, Any]) -> list[str]:
    hits: list[str] = []
    body = norm(text)
    if not body:
        return hits
    for phrase in forbidden_law_phrases(facts):
        if phrase in body:
            hits.append(phrase)
    return hits


def scan_row_law_forbidden(row: dict[str, str], facts: dict[str, Any]) -> list[str]:
    hits: list[str] = []
    for col in PROSE_COLS:
        for phrase in scan_law_forbidden_text(row.get(col, ""), facts):
            label = f"{col}:{phrase}"
            if label not in hits:
                hits.append(label)
    return hits
