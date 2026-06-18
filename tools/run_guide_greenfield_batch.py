#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""greenfield batch を CSV に適用（1記事ずつ·ゼロから執筆した本文のみ）。"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.apply_guide_rewrite_batch import apply_rewrites, load_rewrites_module  # noqa: E402
from tools.rewrite_guide_boilerplate import _csv_fieldnames  # noqa: E402
from tools.editorial_quality import norm  # noqa: E402
from tools.strip_generic_guide_padding import strip_row  # noqa: E402
from tools.validate_guide_greenfield_batch import validate_greenfield_rewrites  # noqa: E402

TODAY = date.today().isoformat()
GREENFIELD_REVISION = f"{TODAY}: greenfield完了（試験ファクト照合·新規執筆）"


def _max_section_in_patch(patch: dict[str, str]) -> int:
    mx = 0
    for key, value in patch.items():
        if not key.startswith("section_") or not norm(value):
            continue
        parts = key.split("_")
        if len(parts) >= 3 and parts[1].isdigit():
            mx = max(mx, int(parts[1]))
    return mx


def _clear_unused_sections(row: dict[str, str], patch: dict[str, str]) -> None:
    mx = _max_section_in_patch(patch)
    for i in range(mx + 1, 8):
        row[f"section_{i}_heading"] = ""
        row[f"section_{i}_body"] = ""
    for i in range(1, 5):
        if f"faq_{i}_question" not in patch:
            row[f"faq_{i}_question"] = ""
        if f"faq_{i}_answer" not in patch:
            row[f"faq_{i}_answer"] = ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply one greenfield guide article batch")
    ap.add_argument("--batch", type=Path, required=True)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--skip-apply", action="store_true", help="validate/strip のみ")
    ap.add_argument("--max-slugs", type=int, default=1)
    args = ap.parse_args()
    root = args.root.resolve()
    batch = args.batch.resolve()
    mod = load_rewrites_module(batch)
    rewrites = getattr(mod, "REWRITES")
    slugs = set(rewrites.keys())

    pre = validate_greenfield_rewrites(rewrites, root=root, max_slugs=args.max_slugs)
    if pre:
        print("greenfield validation failed:", file=sys.stderr)
        for msg in pre[:25]:
            print(f"  {msg}", file=sys.stderr)
        return 1

    csv_path = root / "data" / "guide_articles.csv"
    if not args.skip_apply:
        n = apply_rewrites(csv_path, rewrites, revision=GREENFIELD_REVISION)
        print(f"applied {n} slug(s) from {batch.name}")

        rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))
        fieldnames = list(rows[0].keys()) if rows else []
        for row in rows:
            if (row.get("slug") or "").strip() not in slugs:
                continue
            _clear_unused_sections(row, rewrites[(row.get("slug") or "").strip()])
            note = (row.get("original_note") or "").strip()
            if "greenfield_done" not in note:
                row["original_note"] = f"{note};greenfield_done".strip(";") if note else "greenfield_done"
            row["content_status"] = "published"
        fieldnames = _csv_fieldnames(fieldnames, rows)
        with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)

    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    changed = 0
    for row in rows:
        if (row.get("slug") or "").strip() in slugs and strip_row(row):
            changed += 1
    if changed:
        fieldnames = _csv_fieldnames(fieldnames, rows)
        with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    print(f"stripped padding on {changed} row(s)")

    py = sys.executable
    slug_arg = ",".join(sorted(slugs))
    steps: list[tuple[list[str], Path]] = [
        ([py, "tools/validate_csv.py", "--scope", "guide", "--only-slugs", slug_arg], root),
        (
            [py, str(ROOT / "tools/validate_guide_exam_facts.py"), "--root", str(root), "--only-slugs", slug_arg],
            ROOT,
        ),
        (
            [py, str(ROOT / "tools/validate_guide_law_facts.py"), "--root", str(root), "--only-slugs", slug_arg],
            ROOT,
        ),
        (
            [py, str(ROOT / "tools/audit_guide_prose_quality.py"), "--root", str(root), "--strict", "--only-slugs", slug_arg],
            ROOT,
        ),
    ]
    for cmd, cwd in steps:
        print("+", " ".join(cmd))
        subprocess.run(cmd, cwd=cwd, check=True)
    print(f"OK: greenfield batch {batch.name} ({len(slugs)} slug) passed gates")
    print("Next: python3 tools/build_all.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
