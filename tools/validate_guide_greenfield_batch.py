#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""greenfield batch（1記事·新規執筆）の apply 前検証。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.apply_guide_rewrite_batch import load_rewrites_module  # noqa: E402
from tools.guide_exam_facts import load_exam_facts, scan_row_forbidden  # noqa: E402
from tools.guide_greenfield_lib import patch_contains_placeholder  # noqa: E402
from tools.guide_law_facts import load_law_facts, scan_row_law_forbidden  # noqa: E402
from tools.validate_guide_hand_batch import validate_rewrites  # noqa: E402


def validate_greenfield_rewrites(
    rewrites: dict[str, dict[str, str]],
    *,
    root: Path,
    max_slugs: int = 1,
) -> list[str]:
    errors: list[str] = []
    if len(rewrites) > max_slugs:
        errors.append(f"greenfield batch must have at most {max_slugs} slug(s), got {len(rewrites)}")
    if len(rewrites) < 1:
        errors.append("greenfield batch is empty")

    try:
        facts = load_exam_facts(root)
    except FileNotFoundError as exc:
        errors.append(str(exc))
        facts = {}

    law_facts = load_law_facts(root)

    errors.extend(validate_rewrites(rewrites, root=root))

    for slug, patch in rewrites.items():
        prefix = f"{slug}:"
        for col in patch_contains_placeholder(patch):
            errors.append(f"{prefix} {col} still has greenfield placeholder text")
        if facts:
            pseudo = {"slug": slug, **patch}
            for hit in scan_row_forbidden(pseudo, facts):
                errors.append(f"{prefix} exam_facts forbidden: {hit}")
        if law_facts:
            pseudo = {"slug": slug, **patch}
            for hit in scan_row_law_forbidden(pseudo, law_facts):
                errors.append(f"{prefix} law_facts forbidden: {hit}")

    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate greenfield REWRITES (1 slug)")
    ap.add_argument("--batch", type=Path, required=True)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--max-slugs", type=int, default=1)
    args = ap.parse_args()
    mod = load_rewrites_module(args.batch.resolve())
    rewrites = getattr(mod, "REWRITES")
    errors = validate_greenfield_rewrites(
        rewrites, root=args.root.resolve(), max_slugs=args.max_slugs
    )
    print(
        f"validate_guide_greenfield_batch: {args.batch.name} "
        f"slugs={len(rewrites)} errors={len(errors)}"
    )
    for msg in errors[:50]:
        print(f"  ERROR {msg}")
    if len(errors) > 50:
        print(f"  ... and {len(errors) - 50} more")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
