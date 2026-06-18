# -*- coding: utf-8 -*-
"""practiceTiers（一種・二種など）向けの振り分け・パスヘルパ。"""

from __future__ import annotations

from tools.build_past_question_pages import norm, parse_tags
from tools.q_content_quality import is_demo_practice_question_row
from tools.site_config import practice_tiers


def tier_index_rel_path(tier_id: str) -> str:
    return f"q/practice/{tier_id}/index.html"


def tier_display_label(tier: dict) -> str:
    return str(
        tier.get("label") or tier.get("shortLabel") or tier.get("tag") or tier.get("id") or ""
    ).strip()


def tier_list_breadcrumb_label(tier: dict) -> str:
    label = tier_display_label(tier)
    return f"{label}一覧" if label else "実践演習一覧"


def tier_id_from_tags_and_qno(*, tags: list[str], qno: int, tiers: list[dict]) -> str:
    tag_set = {str(t).strip() for t in tags if str(t).strip()}
    for tier in tiers:
        tg = str(tier.get("tag") or tier.get("shortLabel") or "").strip()
        if tg and tg in tag_set:
            return str(tier["id"])
    return "tier1" if qno >= 1000 else "tier2"


def page_tier_id(page: dict, tiers: list[dict] | None = None) -> str:
    tiers = tiers if tiers is not None else practice_tiers()
    return tier_id_from_tags_and_qno(
        tags=list(page.get("tags") or []),
        qno=int(page["qno"]),
        tiers=tiers,
    )


def row_tier_id(row: dict, tiers: list[dict] | None = None) -> str:
    tiers = tiers if tiers is not None else practice_tiers()
    qno_raw = norm(row.get("question_no"))
    qno = int(qno_raw) if qno_raw.isdigit() else 0
    return tier_id_from_tags_and_qno(
        tags=parse_tags(row.get("tags") or ""),
        qno=qno,
        tiers=tiers,
    )


def filter_pages_by_tier(
    pages: list[dict],
    tier_id: str,
    tiers: list[dict] | None = None,
) -> list[dict]:
    tiers = tiers if tiers is not None else practice_tiers()
    return [p for p in pages if page_tier_id(p, tiers) == tier_id]


def multi_tier_practice_enabled() -> bool:
    return len(practice_tiers()) >= 2


def csv_practice_count_by_tier(
    csv_path,
    tier_id: str,
    tiers: list[dict] | None = None,
) -> int:
    import csv
    from pathlib import Path

    tiers = tiers if tiers is not None else practice_tiers()
    path = Path(csv_path)
    if not path.is_file():
        return 0
    text = path.read_text(encoding="utf-8-sig")
    n = 0
    for row in csv.DictReader(text.splitlines()):
        if norm(row.get("is_invalidated", "")).upper() == "TRUE":
            continue
        if is_demo_practice_question_row(row):
            continue
        if row_tier_id(row, tiers) == tier_id:
            n += 1
    return n
