#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""退役ガイド記事の articles/{slug}/ へ noindex リダイレクト HTML を書く（正本: guide_retired.json）。"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.editorial_quality import norm  # noqa: E402

REDIRECT_HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="0;url={url}">
<link rel="canonical" href="{url}">
<meta name="robots" content="noindex, follow">
<title>記事移動中…</title>
<script>location.replace({url_js});</script>
</head>
<body>
<p>新しい記事へ移動します。<a href="{url}">こちら</a></p>
</body>
</html>
"""


def load_retired_map(root: Path) -> dict[str, str]:
    retired_json = root / "data" / "guide_retired.json"
    if not retired_json.is_file():
        return {}
    data = json.loads(retired_json.read_text(encoding="utf-8"))
    return {
        norm(slug): norm(target)
        for slug, target in (data.get("redirects") or {}).items()
        if norm(slug) and norm(target)
    }


def article_redirect_href(target: str) -> str:
    """articles/{slug}/index.html からの相対 URL を組み立てる。"""
    t = norm(target)
    if t.startswith(("http://", "https://")):
        return t
    if t.startswith("../"):
        base = t.rstrip("/")
        if base.endswith(".html"):
            return base
        return f"{base}/index.html"
    slug = t.rstrip("/")
    return f"../{slug}/index.html"


def write_redirect(articles_dir: Path, slug: str, target_slug: str) -> None:
    out_dir = articles_dir / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    rel = article_redirect_href(target_slug)
    esc = html.escape(rel, quote=True)
    (out_dir / "index.html").write_text(
        REDIRECT_HTML.format(url=esc, url_js=repr(rel)),
        encoding="utf-8",
    )
    marker = out_dir / ".generated-by-exam-site"
    if marker.is_file():
        marker.unlink()


def build_retire_redirects(root: Path) -> int:
    mapping = load_retired_map(root)
    articles_dir = root / "articles"
    articles_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for slug, target in sorted(mapping.items()):
        if not target:
            continue
        write_redirect(articles_dir, slug, target)
        count += 1
    print(f"Wrote {count} retired guide redirect(s) under articles/")
    return count


def main() -> int:
    ap = argparse.ArgumentParser(description="退役ガイドの 301 stub を articles/ に生成")
    ap.add_argument("--root", type=Path, default=ROOT, help="サイトルート")
    args = ap.parse_args()
    root = args.root.resolve()
    import os

    os.environ["EXAM_SITE_ROOT"] = str(root)
    build_retire_redirects(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
