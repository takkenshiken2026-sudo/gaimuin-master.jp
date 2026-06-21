#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用語手書きリライト batch を glossary_terms.csv に適用（term をキーにする）。"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import sys
from datetime import date
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TODAY = date.today().isoformat()


def load_rewrites_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("glossary_rewrite_batch", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "REWRITES"):
        raise ValueError(f"{path} must define REWRITES dict")
    return mod


def apply_rewrites(
    csv_path: Path,
    rewrites: dict[str, dict[str, str]],
    *,
    dry_run: bool = False,
) -> int:
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))
    if not rows:
        return 0
    fieldnames = list(rows[0].keys())
    patched = 0
    for row in rows:
        term = (row.get("term") or "").strip()
        if term not in rewrites:
            continue
        patch = rewrites[term]
        for key, value in patch.items():
            if key not in fieldnames:
                fieldnames.append(key)
            row[key] = value
        patched += 1
    if patched and not dry_run:
        with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    return patched


def all_patches(mod: ModuleType) -> dict[str, dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for key in ("PEER_SHORT_UPDATES", "REWRITES"):
        block = getattr(mod, key, None)
        if not block:
            continue
        for term, patch in block.items():
            merged.setdefault(term, {}).update(patch)
    if not merged:
        raise ValueError(f"{getattr(mod, '__file__', mod)} must define REWRITES dict")
    return merged


def main() -> int:
    ap = argparse.ArgumentParser(description="用語手書き batch を CSV に適用")
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--batch", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    csv_path = args.root.resolve() / "data" / "glossary_terms.csv"
    mod = load_rewrites_module(args.batch.resolve())
    rewrites = all_patches(mod)
    terms = list(rewrites.keys())
    n = apply_rewrites(csv_path, rewrites, dry_run=args.dry_run)
    mode = "would patch" if args.dry_run else "patched"
    print(f"{mode} {n} rows: {', '.join(terms)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
