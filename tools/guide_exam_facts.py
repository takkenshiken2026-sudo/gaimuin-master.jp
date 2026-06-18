#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""試験ガイド用の試験ファクト正本（サイト別 JSON）の読み込みと検証。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tools.editorial_quality import norm

DEFAULT_FACTS_REL = Path("sites") / "{site_id}" / "guide_exam_facts.json"


def site_id_from_root(root: Path) -> str:
    cfg_path = root / "site-config.json"
    if cfg_path.is_file():
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        sid = norm(data.get("siteId") or data.get("site_id"))
        if sid:
            return sid
    return root.name


def facts_path_for_root(root: Path) -> Path:
    sid = site_id_from_root(root)
    p = root / "sites" / sid / "guide_exam_facts.json"
    if p.is_file():
        return p
    tpl = root.parent / "exam-site-shell" / "sites" / sid / "guide_exam_facts.json"
    if tpl.is_file():
        return tpl
    here = Path(__file__).resolve().parents[1]
    p2 = here / "sites" / sid / "guide_exam_facts.json"
    if p2.is_file():
        return p2
    return root / "data" / "guide_exam_facts.json"


def load_exam_facts(root: Path) -> dict[str, Any]:
    path = facts_path_for_root(root)
    if not path.is_file():
        raise FileNotFoundError(f"guide_exam_facts.json not found for {root} ({path})")
    return json.loads(path.read_text(encoding="utf-8"))


def lead_anchor(facts: dict[str, Any]) -> str:
    fmt = facts.get("exam_format") or {}
    tpl = norm(facts.get("lead_anchor_template"))
    if not tpl:
        return ""
    return tpl.format(
        question_count=fmt.get("question_count", ""),
        total_points=fmt.get("total_points", ""),
        duration_minutes=fmt.get("duration_minutes", ""),
        pass_overall_percent=fmt.get("pass_overall_percent", ""),
        pass_overall_points=fmt.get("pass_overall_points", ""),
        pass_per_range_percent=fmt.get("pass_per_range_percent", ""),
    )


def forbidden_phrases(facts: dict[str, Any]) -> list[str]:
    raw = facts.get("forbidden_phrases") or []
    return [norm(x) for x in raw if norm(x)]


def scan_forbidden_text(text: str, facts: dict[str, Any]) -> list[str]:
    hits: list[str] = []
    body = norm(text)
    if not body:
        return hits
    for phrase in forbidden_phrases(facts):
        if phrase in body:
            hits.append(phrase)
    return hits


def scan_row_forbidden(row: dict[str, str], facts: dict[str, Any]) -> list[str]:
    prose_cols = [
        "title",
        "meta_description",
        "lead",
        "user_intent",
        *(f"section_{i}_body" for i in range(1, 8)),
        *(f"faq_{i}_answer" for i in range(1, 5)),
    ]
    hits: list[str] = []
    for col in prose_cols:
        for phrase in scan_forbidden_text(row.get(col, ""), facts):
            label = f"{col}:{phrase}"
            if label not in hits:
                hits.append(label)
    return hits


GREENFIELD_PLACEHOLDER = (
    "【greenfield 執筆待ち】{organizer}の公式要項で最新を確認したうえで、本節の本文を新規執筆します。"
    "試験形式の正本は全{question_count}問（{total_points}点満点）·{duration_minutes}分·五肢択一で、"
    "合格は総合{pass_overall_percent}％（{pass_overall_points}点）以上かつ"
    "各出題範囲{pass_per_range_percent}％以上です。"
    "旧稿にあった100問·5科目×各20問·1.8分/問などの表記は採用しません。"
    "執筆完了後に事実確認日と参照元を更新して公開します。"
)
