#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""index.html の INDEX_SEO / OGP を build 後に再適用する（用語ビルド後の保険）。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.brand_assets import inject_brand_head  # noqa: E402
from tools.index_seo_head import (  # noqa: E402
    INDEX_SEO_MARKER_END,
    INDEX_SEO_MARKER_START,
    inject_index_seo_head,
)


def main() -> int:
    index = ROOT / "index.html"
    if not index.is_file():
        print("repair_index_seo_head: index.html がありません", file=sys.stderr)
        return 0
    before = index.read_text(encoding="utf-8")
    text = inject_brand_head(before, Path("index.html"), site_root=ROOT)
    text = inject_index_seo_head(text)
    index.write_text(text, encoding="utf-8")
    if INDEX_SEO_MARKER_START not in text or INDEX_SEO_MARKER_END not in text:
        print(
            "repair_index_seo_head: INDEX_SEO マーカーを復元できませんでした",
            file=sys.stderr,
        )
        return 1
    head = text.split("</head>", 1)[0]
    if 'property="og:image"' not in head and 'name="twitter:image"' not in head:
        print("repair_index_seo_head: og:image を復元できませんでした", file=sys.stderr)
        return 1
    print("repair_index_seo_head: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
