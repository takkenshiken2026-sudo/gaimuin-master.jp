#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用語編集合格 batch を apply → validate_csv。"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.apply_gaimuin_glossary_batch import apply_rewrites, load_rewrites_module  # noqa: E402
from tools.build_glossary_pages import lookup_key  # noqa: E402
from tools.glossary_expert_rewrite_rules import validate_expert_rewrites  # noqa: E402
from tools.validate_glossary_expert_batch import guide_slugs  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="用語編集合格 batch 適用パイプライン")
    ap.add_argument("--batch", type=Path, required=True)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--skip-apply", action="store_true")
    args = ap.parse_args()
    root = args.root.resolve()
    batch = args.batch.resolve()
    mod = load_rewrites_module(batch)
    rewrites = getattr(mod, "REWRITES")
    terms = sorted(rewrites.keys())
    csv_path = root / "data" / "glossary_terms.csv"
    base_rows = {
        (r.get("term") or "").strip(): r
        for r in csv.DictReader(csv_path.open(encoding="utf-8-sig"))
    }
    term_lookup = {lookup_key(t): t for t in base_rows}

    pre = validate_expert_rewrites(
        rewrites,
        base_rows=base_rows,
        term_lookup=term_lookup,
        guide_slugs=guide_slugs(root),
    )
    if pre:
        print("batch validation failed:", file=sys.stderr)
        for msg in pre[:20]:
            print(f"  {msg}", file=sys.stderr)
        return 1

    if not args.skip_apply:
        n = apply_rewrites(csv_path, rewrites)
        print(f"applied {n} terms from {batch.name}")

    py = sys.executable
    cmd = [py, "tools/validate_csv.py", "--scope", "glossary"]
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=root, check=True)
    print(f"OK: expert batch {batch.name} ({len(terms)} terms): {', '.join(terms)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
