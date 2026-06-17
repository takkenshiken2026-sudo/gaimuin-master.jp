#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""証券外務員サイト: 全ガイドに gaimuin_guide_content_lib を適用し、非アフィリエイトを published にする。

  python3 tools/seed_gaimuin_guides.py --root ~/Projects/gaimuin-master
  python3 tools/seed_gaimuin_guides.py --root ~/Projects/gaimuin-master --dry-run
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.apply_site_guide_content_lib import upgrade_meta_row  # noqa: E402
from tools.editorial_quality import norm  # noqa: E402
from tools.fix_guide_duplicate_bodies import (  # noqa: E402
    load_site_lib,
    patch_row_sections,
    repair_coherence_faqs,
)
from tools.rewrite_guide_boilerplate import _csv_fieldnames  # noqa: E402

TODAY = date.today().isoformat()


def is_affiliate_row(row: dict[str, str]) -> bool:
    tags = row.get("tags") or ""
    return "アフィリエイト" in tags


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--keep-draft",
        action="store_true",
        help="content のみ適用し published にしない",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    guide_path = root / "data" / "guide_articles.csv"
    if not guide_path.is_file():
        print(f"missing {guide_path}", file=sys.stderr)
        return 1

    lib = load_site_lib(root)
    with guide_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    touched = 0
    published = 0
    for row in rows:
        slug = norm(row.get("slug"))
        if not slug:
            continue
        before = {k: row.get(k) for k in row}
        topic = lib.topic_from_row(row)
        slug = norm(row.get("slug"))
        genre = norm(row.get("genre"))
        row["meta_description"] = lib.meta_description_for(row, topic)
        row["user_intent"] = lib.user_intent_for(topic, genre)
        row["action_items"] = lib.action_items_for(topic, slug, genre)
        row["lead"] = lib.lead_for(row, topic)
        if hasattr(lib, "key_points_for"):
            row["key_points"] = lib.key_points_for(row, topic)
        upgrade_meta_row(row, lib)
        patch_row_sections(row, fieldnames, lib)
        if not args.keep_draft and not is_affiliate_row(row):
            row["content_status"] = "published"
            published += 1
        row["revision_note"] = (
            f"{TODAY}: gaimuin content-lib 初回シード（手書きbatchで品質仕上げ予定）"
        )
        if before != {k: row.get(k) for k in row}:
            touched += 1

    repair_coherence_faqs(rows, fieldnames, lib)

    if args.dry_run:
        print(f"dry-run: would touch {touched} rows, publish {published} non-affiliate guides")
        return 0

    fieldnames = _csv_fieldnames(fieldnames, rows)
    with guide_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    print(f"seed_gaimuin_guides: updated {touched} rows, published {published} guides in {guide_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
