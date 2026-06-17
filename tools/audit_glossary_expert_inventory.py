#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用語詳細の編集合格インベントリ（v0 最低ライン / v1 expert_pass）。"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_glossary_pages import lookup_key  # noqa: E402
from tools.editorial_quality import GLOSSARY_EXPERT, norm, split_semicolon  # noqa: E402
from tools.glossary_expert_rewrite_rules import (  # noqa: E402
    OPERATOR_BATCH_REF_RE,
    expert_tag_present,
    validate_expert_row,
)


def audit_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    term_lookup = {lookup_key((r.get("term") or "").strip()): (r.get("term") or "").strip() for r in rows}
    out: list[dict[str, str]] = []
    for row in rows:
        term = norm(row.get("term"))
        if not term:
            continue
        body_len = len(norm(row.get("term_detail_body")))
        imp = norm(row.get("importance"))
        batch_leak = any(
            OPERATOR_BATCH_REF_RE.search(norm(row.get(c)) or "")
            for c in (
                "term_detail_body",
                "common_mistakes",
                "explanation",
                "article_lead",
                *(f"faq_{i}_answer" for i in range(1, 5)),
            )
        )
        expert_errors = validate_expert_row(row, term_lookup=term_lookup, guide_slugs=None)
        if expert_tag_present(norm(row.get("tags"))) and not expert_errors:
            status = "expert_pass"
        elif body_len < GLOSSARY_EXPERT["term_detail_body"] or batch_leak:
            status = "needs_upgrade"
        else:
            status = "v0_ok"
        out.append(
            {
                "term": term,
                "category": norm(row.get("category")),
                "importance": imp,
                "status": status,
                "body_len": str(body_len),
                "batch_leak": "yes" if batch_leak else "no",
                "expert_tag": "yes" if expert_tag_present(norm(row.get("tags"))) else "no",
                "issue_count": str(len(expert_errors)),
                "issue_sample": expert_errors[0][:80] if expert_errors else "",
            }
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="用語編集合格インベントリ")
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("-o", "--output", type=Path, help="CSV 出力先")
    ap.add_argument("--needs-upgrade", action="store_true", help="要改善のみ表示")
    args = ap.parse_args()
    csv_path = args.root.resolve() / "data" / "glossary_terms.csv"
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))
    audited = audit_rows(rows)
    if args.needs_upgrade:
        audited = [r for r in audited if r["status"] != "expert_pass"]

    counts: dict[str, int] = {}
    batch_leaks = sum(1 for r in audited if r["batch_leak"] == "yes")
    for r in audited:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    print(f"用語数: {len(audited)}")
    print(f"  expert_pass: {counts.get('expert_pass', 0)}")
    print(f"  v0_ok: {counts.get('v0_ok', 0)}")
    print(f"  needs_upgrade: {counts.get('needs_upgrade', 0)}")
    print(f"  batch参照残存: {batch_leaks}")

    if args.output:
        fieldnames = list(audited[0].keys()) if audited else []
        with args.output.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            w.writeheader()
            w.writerows(audited)
        print(f"wrote {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
