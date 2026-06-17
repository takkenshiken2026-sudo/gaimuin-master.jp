#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用語手書き batch の REWRITES を glossary_term_rules で検証。"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_glossary_pages import lookup_key  # noqa: E402
from tools.glossary_term_rules import (  # noqa: E402
    GLOSSARY_MIN_LENGTHS,
    check_glossary_row,
)


def load_batch(path: Path) -> dict[str, dict[str, str]]:
    spec = importlib.util.spec_from_file_location("glossary_batch", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "REWRITES")


def validate_rewrites(
    rewrites: dict[str, dict[str, str]],
    *,
    root: Path,
) -> list[str]:
    csv_path = root / "data" / "glossary_terms.csv"
    base_rows = {
        (r.get("term") or "").strip(): r
        for r in csv.DictReader(csv_path.open(encoding="utf-8-sig"))
    }
    term_lookup = {lookup_key(t): t for t in base_rows}
    errors: list[str] = []
    for term, patch in rewrites.items():
        if term not in base_rows:
            errors.append(f"{term}: not in glossary_terms.csv")
            continue
        merged = dict(base_rows[term])
        merged.update(patch)
        for col, min_len in GLOSSARY_MIN_LENGTHS.items():
            val = (merged.get(col) or "").strip()
            if len(val) < min_len:
                errors.append(f"{term}: {col} too short ({len(val)} < {min_len})")
        for issue in check_glossary_row(merged, term_lookup=term_lookup):
            if issue.level == "ERROR":
                errors.append(f"{term}: {issue.message}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="用語 batch 機械チェック")
    ap.add_argument("--batch", type=Path, required=True)
    ap.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args()
    rewrites = load_batch(args.batch.resolve())
    errors = validate_rewrites(rewrites, root=args.root.resolve())
    if errors:
        print("validation failed:", file=sys.stderr)
        for msg in errors:
            print(f"  {msg}", file=sys.stderr)
        return 1
    print(f"OK: {len(rewrites)} terms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
