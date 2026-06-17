#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""証外マスター: glossary_terms.csv の article_title / article_lead を一括設定。

SEO 方針（docs/seo-article-guidelines.md）:
- 各タイトルに「証券外務員」を含める
- title タグは「{article_title}｜証外マスター」で 60 字以内
- importance でサフィックスを変え、同一パターンのカニバリを緩和
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BRAND = "証外マスター"
EXAM_KW = "証券外務員"
MAX_TAG_LEN = 60
TAG_SUFFIX_LEN = len(f"｜{BRAND}")

IMPORTANCE_SUFFIX = {
    "A": "証券外務員試験で頻出の要点",
    "B": "証券外務員試験の意味と論点",
    "C": "証券外務員試験の基礎用語",
    "S": "証券外務員試験の重要用語",
}


def make_title(term: str, importance: str) -> str:
    imp = (importance or "B").strip().upper()
    suffix = IMPORTANCE_SUFFIX.get(imp, IMPORTANCE_SUFFIX["B"])
    candidates = [
        f"{term}とは｜{suffix}",
        f"{term}とは｜証券外務員試験の要点",
        f"{term}｜証券外務員試験",
    ]
    max_title = MAX_TAG_LEN - TAG_SUFFIX_LEN
    for title in candidates:
        if len(title) <= max_title and EXAM_KW in title:
            return title
    return candidates[-1][:max_title]


def make_lead(term: str, gist: str, category: str) -> str:
    gist = (gist or "").strip()
    cat = (category or "").strip()
    base = (
        f"証券外務員試験で繰り返し問われる「{term}」の意味と論点を整理します。"
    )
    if gist:
        base += f"{gist}。"
    if cat:
        base += f"{cat}分野の過去問対策に使える要点と、混同しやすい点を解説します。"
    else:
        base += "試験対策に使える要点と、混同しやすい点を解説します。"
    return base


def gist_from_row(row: dict[str, str]) -> str:
    short = (row.get("short_def") or "").strip()
    if short:
        return short
    definition = (row.get("definition") or "").strip()
    if definition:
        return definition.split("。")[0] + "。"
    return ""


def seo_audit(rows: list[dict[str, str]]) -> list[str]:
    warnings: list[str] = []
    seen: dict[str, str] = {}
    for row in rows:
        term = (row.get("term") or "").strip()
        title = make_title(term, row.get("importance") or "B")
        if EXAM_KW not in title:
            warnings.append(f"{term}: missing exam keyword in title")
        if "とは" not in title and term not in title:
            warnings.append(f"{term}: title missing term or とは")
        tag_len = len(f"{title}｜{BRAND}")
        if tag_len > MAX_TAG_LEN:
            warnings.append(f"{term}: title tag {tag_len} chars (>60)")
        if title in seen:
            warnings.append(f"duplicate title: {term} and {seen[title]}")
        seen[title] = term
        lead = make_lead(term, gist_from_row(row), row.get("category") or "")
        if len(lead) < 60:
            warnings.append(f"{term}: article_lead short ({len(lead)} chars)")
    return warnings


def main() -> int:
    ap = argparse.ArgumentParser(description="証外用語 SEO タイトル・リード一括設定")
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--audit-only", action="store_true")
    args = ap.parse_args()

    root = args.root.resolve()
    csv_path = root / "data" / "glossary_terms.csv"
    if not csv_path.is_file():
        print(f"missing {csv_path}", file=sys.stderr)
        return 1

    rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))
    audit = seo_audit(rows)
    if audit:
        print("SEO audit warnings:")
        for msg in audit:
            print(f"  WARN {msg}")
    else:
        print("SEO audit: OK")

    if args.audit_only:
        return 1 if audit else 0

    if not rows:
        return 0

    fieldnames = list(rows[0].keys())
    changed_title = 0
    changed_lead = 0
    for row in rows:
        term = (row.get("term") or "").strip()
        if not term:
            continue
        new_title = make_title(term, row.get("importance") or "B")
        new_lead = make_lead(term, gist_from_row(row), row.get("category") or "")
        if (row.get("article_title") or "").strip() != new_title:
            row["article_title"] = new_title
            changed_title += 1
        if (row.get("article_lead") or "").strip() != new_lead:
            row["article_lead"] = new_lead
            changed_lead += 1

    if (changed_title or changed_lead) and not args.dry_run:
        with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)

    print(
        f"apply_gaimuin_glossary_titles: updated titles={changed_title}, leads={changed_lead} in {csv_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
