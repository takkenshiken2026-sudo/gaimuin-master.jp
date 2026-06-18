#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""試験ガイド greenfield（ゼロから執筆）の共通ヘルパ。"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from tools.editorial_quality import is_published_guide, norm
from tools.guide_exam_facts import GREENFIELD_PLACEHOLDER, lead_anchor, load_exam_facts

ROOT = Path(__file__).resolve().parents[1]


def site_id_from_root(root: Path) -> str:
    cfg = root / "site-config.json"
    if cfg.is_file():
        data = json.loads(cfg.read_text(encoding="utf-8"))
        sid = norm(data.get("siteId") or data.get("site_id"))
        if sid:
            return sid
    return root.name


def catalog_path_for_root(root: Path) -> Path | None:
    sid = site_id_from_root(root)
    for base in (root, ROOT):
        p = base / "sites" / sid / "guide_greenfield_catalog.json"
        if p.is_file():
            return p
    return None


def load_greenfield_catalog(root: Path) -> dict:
    path = catalog_path_for_root(root)
    if not path:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def keep_slugs_path(root: Path) -> Path:
    return root / "data" / "guide_seo_keep_slugs.txt"


def load_keep_slugs(root: Path) -> set[str]:
    path = keep_slugs_path(root)
    if path.is_file():
        return {norm(line) for line in path.read_text(encoding="utf-8").splitlines() if norm(line)}
    catalog = load_greenfield_catalog(root)
    priority = catalog.get("write_priority") or []
    return {norm(s) for s in priority if norm(s)}


def load_guide_rows(root: Path) -> list[dict[str, str]]:
    csv_path = root / "data" / "guide_articles.csv"
    return list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))


def row_by_slug(root: Path, slug: str) -> dict[str, str] | None:
    for row in load_guide_rows(root):
        if norm(row.get("slug")) == norm(slug):
            return row
    return None


def is_greenfield_pending(row: dict[str, str]) -> bool:
    return "greenfield執筆待ち" in norm(row.get("revision_note"))


def pending_slugs(root: Path) -> list[str]:
    keep = load_keep_slugs(root)
    out: list[str] = []
    for row in load_guide_rows(root):
        slug = norm(row.get("slug"))
        if not slug:
            continue
        if keep and slug not in keep:
            continue
        if is_greenfield_pending(row):
            out.append(slug)
    return out


def next_write_slug(root: Path) -> str | None:
    catalog = load_greenfield_catalog(root)
    pending = set(pending_slugs(root))
    for slug in catalog.get("write_priority") or []:
        s = norm(slug)
        if s in pending:
            return s
    return pending_slugs(root)[0] if pending else None


def section_headings_for_slug(root: Path, slug: str, row: dict[str, str], catalog: dict) -> list[str]:
    headings_map = catalog.get("section_headings") or {}
    if slug in headings_map:
        return [norm(h) for h in headings_map[slug] if norm(h)][:7]
    out: list[str] = []
    for i in range(1, 8):
        h = norm(row.get(f"section_{i}_heading"))
        if h and "greenfield" not in h.lower() and "執筆待ち" not in h:
            out.append(h)
        elif h and "本文セクション" in h:
            continue
    if out:
        return out[:7]
    return [
        "読者が最初に確認すること",
        "試験ファクトの整理",
        "具体的な進め方",
        "よくある誤解",
        "次に読むページ",
    ]


def title_for_slug(slug: str, row: dict[str, str], catalog: dict) -> str:
    fixes = catalog.get("title_fixes") or {}
    if slug in fixes:
        return fixes[slug]
    return norm(row.get("title"))


def meta_for_slug(title: str, facts: dict) -> str:
    short = title.split("【")[0].strip() or title
    fmt = facts.get("exam_format") or {}
    return (
        f"{short}について、公式要項を起点に整理します。"
        f"本試験は全{fmt.get('question_count', '')}問·"
        f"{fmt.get('total_points', '')}点満点です。"
    )


def scaffold_patch(root: Path, slug: str) -> dict[str, str]:
    row = row_by_slug(root, slug)
    if not row:
        raise KeyError(f"slug not in guide_articles.csv: {slug}")
    facts = load_exam_facts(root)
    catalog = load_greenfield_catalog(root)
    title = title_for_slug(slug, row, catalog)
    short = title.split("【")[0].strip() or title
    anchor = lead_anchor(facts)
    patch: dict[str, str] = {
        "title": title,
        "meta_description": meta_for_slug(title, facts),
        "lead": anchor or norm(row.get("lead")),
        "user_intent": (
            f"本記事を読むと、{short}の確認ポイントと次の行動が分かります。"
            "公式要項と照合したうえで試験対策を進められます。"
        ),
        "action_items": "",
    }
    for i, heading in enumerate(section_headings_for_slug(root, slug, row, catalog), start=1):
        if i > 7:
            break
        patch[f"section_{i}_heading"] = heading
        patch[f"section_{i}_body"] = ""
    for i in range(1, 4):
        patch.setdefault(f"faq_{i}_question", "")
        patch.setdefault(f"faq_{i}_answer", "")
    return patch


def patch_contains_placeholder(patch: dict[str, str]) -> list[str]:
    needle = "greenfield 執筆待ち"
    hits: list[str] = []
    cols = [k for k in patch if k.endswith("_body") or k.endswith("_answer") or k in ("lead", "user_intent")]
    for col in cols:
        if needle in norm(patch.get(col)):
            hits.append(col)
    if any(x in GREENFIELD_PLACEHOLDER for x in [norm(patch.get(c)) for c in cols if norm(patch.get(c))]):
        pass
    for col in cols:
        body = norm(patch.get(col))
        if body and body.startswith("【greenfield 執筆待ち】"):
            hits.append(col)
    return hits
