#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""greenfield 用・1 slug ずつの執筆 batch 雛形を生成（旧 rewrites/ は使わない）。

使い方:
  python3 tools/scaffold_guide_greenfield_batch.py --root ~/Projects/eisei1shu-master --slug exam-format-overview
  python3 tools/scaffold_guide_greenfield_batch.py --root ~/Projects/eisei1shu-master --next
  python3 tools/scaffold_guide_greenfield_batch.py --root ~/Projects/eisei1shu-master --list-pending
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.editorial_quality import norm  # noqa: E402
from tools.guide_greenfield_lib import (  # noqa: E402
    next_write_slug,
    pending_slugs,
    scaffold_patch,
    site_id_from_root,
)


def py_literal(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def render_batch_py(site_id: str, slug: str, patch: dict[str, str]) -> str:
    lines = [
        "#!/usr/bin/env python3",
        "# -*- coding: utf-8 -*-",
        f'"""greenfield 新規執筆: {slug}',
        "",
        "旧 tools/rewrites/ や *_rewrite_batch*.py は参照しない。",
        "本文をすべて記入してから:",
        f"  python3 tools/validate_guide_greenfield_batch.py --batch tools/greenfield/{site_id}/{slug}.py",
        f"  python3 tools/run_guide_greenfield_batch.py --batch tools/greenfield/{site_id}/{slug}.py",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "REWRITES: dict[str, dict[str, str]] = {",
        f'    "{slug}": {{',
    ]
    for key in sorted(patch.keys()):
        val = patch[key]
        lines.append(f"        {key!r}: {py_literal(val)},")
    lines.extend(
        [
            "    },",
            "}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="greenfield 1記事 batch 雛形")
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--slug", help="対象 slug（1記事）")
    ap.add_argument("--next", action="store_true", help="write_priority の次の未執筆 slug")
    ap.add_argument("--list-pending", action="store_true", help="greenfield執筆待ち slug 一覧")
    ap.add_argument("--force", action="store_true", help="既存 batch を上書き")
    args = ap.parse_args()
    root = args.root.resolve()
    site_id = site_id_from_root(root)

    if args.list_pending:
        slugs = pending_slugs(root)
        print(f"pending ({len(slugs)}):")
        for s in slugs:
            print(f"  {s}")
        nxt = next_write_slug(root)
        if nxt:
            print(f"next recommended: {nxt}")
        return 0

    slug = norm(args.slug)
    if args.next:
        slug = next_write_slug(root) or ""
        if not slug:
            print("No greenfield pending slugs.", file=sys.stderr)
            return 1
        print(f"next slug: {slug}")

    if not slug:
        ap.error("Specify --slug or --next")

    patch = scaffold_patch(root, slug)
    out_dir = ROOT / "tools" / "greenfield" / site_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slug}.py"
    if out_path.is_file() and not args.force:
        print(f"Already exists: {out_path}  (use --force)", file=sys.stderr)
        return 1
    out_path.write_text(render_batch_py(site_id, slug, patch), encoding="utf-8")
    print(f"written: {out_path}")
    print("Fill all section_*_body / faq_* / action_items, then validate + run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
