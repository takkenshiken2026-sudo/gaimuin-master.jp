#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用語「編集合格」batch の REWRITES を検証。"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_glossary_pages import lookup_key  # noqa: E402
from tools.glossary_expert_rewrite_rules import validate_expert_rewrites  # noqa: E402
from tools.validate_gaimuin_glossary_batch import load_batch  # noqa: E402


def guide_slugs(root: Path) -> set[str]:
    path = root / "data" / "guide_articles.csv"
    if not path.is_file():
        return set()
    return {
        (r.get("slug") or "").strip()
        for r in csv.DictReader(path.open(encoding="utf-8-sig"))
        if (r.get("slug") or "").strip()
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="用語編集合格 batch 機械チェック")
    ap.add_argument("--batch", type=Path, required=True)
    ap.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args()
    root = args.root.resolve()
    rewrites = load_batch(args.batch.resolve())
    csv_path = root / "data" / "glossary_terms.csv"
    base_rows = {
        (r.get("term") or "").strip(): r
        for r in csv.DictReader(csv_path.open(encoding="utf-8-sig"))
    }
    term_lookup = {lookup_key(t): t for t in base_rows}
    errors = validate_expert_rewrites(
        rewrites,
        base_rows=base_rows,
        term_lookup=term_lookup,
        guide_slugs=guide_slugs(root),
    )
    if errors:
        print("validation failed:", file=sys.stderr)
        for msg in errors[:30]:
            print(f"  {msg}", file=sys.stderr)
        if len(errors) > 30:
            print(f"  ... and {len(errors) - 30} more", file=sys.stderr)
        return 1
    print(f"OK: expert batch {len(rewrites)} terms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
