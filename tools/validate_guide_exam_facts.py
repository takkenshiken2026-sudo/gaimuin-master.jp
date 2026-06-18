#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公開ガイド記事に試験ファクト誤表記（100問系）が無いか検証する。"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.editorial_quality import is_published_guide, norm  # noqa: E402
from tools.guide_exam_facts import load_exam_facts, scan_row_forbidden  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate guide articles against exam facts forbidden phrases")
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--include-draft", action="store_true", help="draft も検査対象にする")
    ap.add_argument("--only-slugs", help="カンマ区切り slug のみ検査")
    ap.add_argument(
        "--skip-greenfield-pending",
        action="store_true",
        help="revision_note に greenfield執筆待ち がある行はスキップ",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    only = {norm(s) for s in (args.only_slugs or "").split(",") if norm(s)}
    csv_path = root / "data" / "guide_articles.csv"
    if not csv_path.is_file():
        print(f"Missing {csv_path}", file=sys.stderr)
        return 1

    try:
        facts = load_exam_facts(root)
    except FileNotFoundError as exc:
        print(f"SKIP: {exc}")
        return 0

    rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))
    errors: list[str] = []
    checked = 0
    for row in rows:
        status = norm(row.get("content_status")).lower()
        if status == "archived":
            continue
        if not args.include_draft and not is_published_guide(row):
            continue
        slug = norm(row.get("slug"))
        if only and slug not in only:
            continue
        if args.skip_greenfield_pending and "greenfield執筆待ち" in norm(row.get("revision_note")):
            continue
        checked += 1
        hits = scan_row_forbidden(row, facts)
        for hit in hits:
            errors.append(f"{slug}: {hit}")

    if errors:
        print(f"FAIL: {len(errors)} forbidden phrase hit(s) in {checked} row(s)", file=sys.stderr)
        for line in errors[:40]:
            print(f"  {line}", file=sys.stderr)
        if len(errors) > 40:
            print(f"  ... +{len(errors) - 40} more", file=sys.stderr)
        return 1

    print(f"OK: {checked} guide row(s) — no forbidden exam-format phrases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
