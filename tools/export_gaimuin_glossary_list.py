#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""証外マスター: glossary_terms.csv から用語マスター一覧 Markdown を生成する。

出力: sites/gaimuin-master/glossary-term-list.md
正本データ: data/glossary_terms.csv（シードは tools/seed_gaimuin_glossary.py）
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT_PATH = ROOT / "sites" / "gaimuin-master" / "glossary-term-list.md"

CATEGORY_ORDER = (
    "金融商品・サービス",
    "勧誘・販売規則",
    "金融商品取引法",
    "その他法令・業務",
)

IMPORTANCE_ORDER = ("A", "B", "C", "S")


def load_seed_terms() -> set[str]:
    try:
        from tools.seed_gaimuin_glossary import TERMS  # noqa: WPS433
    except ImportError:
        return set()
    return {t[0] for t in TERMS}


def esc_cell(text: str) -> str:
    return (text or "").replace("|", "／").replace("\n", " ").strip()


def audit_rows(rows: list[dict[str, str]], seed_terms: set[str]) -> list[str]:
    warnings: list[str] = []
    terms = [r["term"] for r in rows]
    dupes = [t for t, c in Counter(terms).items() if c > 1]
    if dupes:
        warnings.append(f"重複 term: {', '.join(dupes)}")
    if seed_terms:
        csv_set = set(terms)
        missing_in_csv = sorted(seed_terms - csv_set)
        extra_in_csv = sorted(csv_set - seed_terms)
        if missing_in_csv:
            warnings.append(f"シードにあって CSV にない ({len(missing_in_csv)}): {', '.join(missing_in_csv[:5])}…")
        if extra_in_csv:
            warnings.append(f"CSV にあってシードにない ({len(extra_in_csv)}): {', '.join(extra_in_csv[:5])}…")
    for imp in ("A", "B", "C"):
        n = sum(1 for r in rows if (r.get("importance") or "").strip() == imp)
        if n == 0:
            warnings.append(f"importance={imp} の用語が0件")
    return warnings


def render_markdown(rows: list[dict[str, str]], warnings: list[str]) -> str:
    today = date.today().isoformat()
    total = len(rows)
    imp_counts = Counter((r.get("importance") or "").strip() for r in rows)
    by_cat: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_cat[row.get("category") or "（未分類）"].append(row)

    lines: list[str] = [
        "# 証外マスター — 用語マスター一覧（300件）",
        "",
        f"自動生成日: {today}。正本は `data/glossary_terms.csv`。再生成:",
        "",
        "```bash",
        "python3 tools/export_gaimuin_glossary_list.py --root ~/Projects/gaimuin-master",
        "```",
        "",
        "## サマリー",
        "",
        f"| 項目 | 値 |",
        f"|------|-----|",
        f"| 総件数 | {total} |",
        f"| importance A（頻出） | {imp_counts.get('A', 0)} |",
        f"| importance B（標準） | {imp_counts.get('B', 0)} |",
        f"| importance C（補助） | {imp_counts.get('C', 0)} |",
        "",
        "### 分野別件数",
        "",
        "| 分野 | 件数 | A | B | C |",
        "|------|------|---|---|---|",
    ]
    for cat in CATEGORY_ORDER:
        sub = by_cat.get(cat, [])
        ic = Counter((r.get("importance") or "").strip() for r in sub)
        lines.append(
            f"| {cat} | {len(sub)} | {ic.get('A', 0)} | {ic.get('B', 0)} | {ic.get('C', 0)} |"
        )

    lines.extend(
        [
            "",
            "## 運用メモ",
            "",
            "- **シード正本:** `tools/seed_gaimuin_glossary.py` の `TERMS`（再シード時は CSV 全上書き）",
            "- **SEO タイトル:** `tools/apply_gaimuin_glossary_titles.py`",
            "- **本文バッチ:** A級93件から手書き品質で投入（`docs/glossary-term-template.md`）",
            "- **公開一覧:** `/terms/index.html`（検索・分野絞り込み）",
            "",
        ]
    )

    if warnings:
        lines.extend(["## 監査 WARN", ""])
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    for cat in CATEGORY_ORDER:
        sub = sorted(
            by_cat.get(cat, []),
            key=lambda r: (
                IMPORTANCE_ORDER.index((r.get("importance") or "B").strip())
                if (r.get("importance") or "B").strip() in IMPORTANCE_ORDER
                else 9,
                r.get("term") or "",
            ),
        )
        if not sub:
            continue
        lines.extend(
            [
                f"## {cat}（{len(sub)}件）",
                "",
                "| # | 用語 | 重要度 | タグ | 短い定義 | slug |",
                "|---|------|--------|------|----------|------|",
            ]
        )
        for i, row in enumerate(sub, 1):
            slug = (row.get("slug") or "").strip()
            if not slug:
                from tools.build_glossary_pages import lookup_key  # noqa: WPS433

                slug = f"g-{lookup_key(row['term'])}.html"
            short = esc_cell(row.get("short_def") or "")
            if len(short) > 48:
                short = short[:47] + "…"
            lines.append(
                "| {i} | {term} | {imp} | {tags} | {short} | `{slug}` |".format(
                    i=i,
                    term=esc_cell(row.get("term") or ""),
                    imp=esc_cell(row.get("importance") or ""),
                    tags=esc_cell(row.get("tags") or ""),
                    short=short,
                    slug=slug,
                )
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="証外用語マスター一覧 Markdown を生成")
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = args.root.resolve()
    csv_path = root / "data" / "glossary_terms.csv"
    if not csv_path.is_file():
        print(f"missing {csv_path}", file=sys.stderr)
        return 1

    rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))
    seed_terms = load_seed_terms()
    warnings = audit_rows(rows, seed_terms)
    md = render_markdown(rows, warnings)

    if warnings:
        print("audit warnings:")
        for w in warnings:
            print(f"  WARN {w}")
    else:
        print("audit: OK")

    if args.dry_run:
        print(f"dry-run: would write {len(rows)} terms -> {args.out}")
        return 0

    out = args.out if args.out.is_absolute() else root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"wrote {len(rows)} terms -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
