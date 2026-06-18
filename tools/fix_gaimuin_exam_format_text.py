#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""証外マスター：ガイド・用語内の試験形式数値を JSDA 公式（2025-06 確認）に揃える。"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 日本証券業協会 外務員資格試験案内（https://www.jsda.or.jp/gaimuin/shiken.html）
REPLACEMENTS: list[tuple[str, str]] = [
    ("一種100問120分・二種60問90分", "一種100問160分・二種70問120分"),
    ("一種は100問120分、二種は60問90分", "一種は100問160分、二種は70問120分"),
    ("一種は100問120分、二種は70問120分", "一種は100問160分、二種は70問120分"),
    ("一種は100問120", "一種は100問160"),
    ("二種は60問90分", "二種は70問120分"),
    ("二種60問90分", "二種70問120分"),
    ("一種100問120分", "一種100問160分"),
    ("100問120分", "100問160分"),
    ("一種120分・二種90分", "一種160分・二種120分"),
    ("二種60問", "二種70問"),
    ("60問中", "70問中"),
    ("100問120分（一種）", "100問160分（一種）"),
    ("100問120分を", "100問160分を"),
    ("100問120分を月2回", "100問160分を月2回"),
    ("最終4週で100問120分", "最終4週で100問160分"),
    ("CBT本番で100問120分", "CBT本番で100問160分"),
    ("一種はおおむね100問120分", "一種はおおむね100問160分"),
    ("一種100問・二種60問", "一種100問・二種70問"),
    ("→100問120分", "→100問160分"),
    ("100問120分の3段階", "100問160分の3段階"),
    ("一種なら100問120分", "一種なら100問160分"),
    ("一種50問／二種30問", "一種50問／二種35問"),
    ("二種30問", "二種35問"),
    ("60問90分のCBT", "70問120分のCBT"),
    ("60問90分", "70問120分"),
]


def apply_text(text: str) -> tuple[str, int]:
    out = text
    n = 0
    for old, new in REPLACEMENTS:
        if old in out:
            count = out.count(old)
            out = out.replace(old, new)
            n += count
    return out, n


def patch_csv(path: Path, *, dry_run: bool) -> int:
    if not path.is_file():
        return 0
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = [dict(r) for r in reader]

    changed_cells = 0
    for row in rows:
        for key in fieldnames:
            raw = row.get(key) or ""
            patched, hits = apply_text(raw)
            if hits:
                changed_cells += hits
                row[key] = patched

    if changed_cells and not dry_run:
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    print(f"{'would patch' if dry_run else 'patched'} {path.name}: {changed_cells} replacements")
    return changed_cells


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    root = args.root.resolve()
    total = 0
    for name in ("guide_articles.csv", "glossary_terms.csv"):
        total += patch_csv(root / "data" / name, dry_run=args.dry_run)
    if total:
        print("続けて: python3 tools/build_all.py")
    else:
        print("変更なし")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
