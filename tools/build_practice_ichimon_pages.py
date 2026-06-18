#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data/practice_questions.csv / data/ichimon_questions.csv から静的 SEO ページを生成。

  - q/practice/p{no:03d}/index.html … 実践演習（各問）
  - q/practice/index.html … 実践演習一覧（practiceTiers 時は hub）
  - q/practice/tier{N}/index.html … 試験種別別一覧（practiceTiers 時）
  - q/ichimon/y{年}/i{月:02d}-{連番}/index.html … 一問一答（各問）
  - q/ichimon/index.html … 一問一答一覧

過去問ビルド（build_past_question_pages.py）は q/past/ のみ削除する。
本スクリプトは q/practice/ と q/ichimon/ のみ再生成する。
"""

from __future__ import annotations

import csv
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.q_explanation import build_explanation_html, build_ichimon_explanation_html  # noqa: E402
from tools.q_content_quality import (  # noqa: E402
    build_ichimon_primary_ids,
    ichimon_robots_meta,
    is_demo_practice_question_row,
    set_ichimon_primary_ids,
)
from tools.q_similar_questions import build_similar_questions_html, load_question_catalog  # noqa: E402
from tools.build_past_question_pages import (  # noqa: E402
    HEAD_FONTS,
    Q_INDEX_CSS_VER,
    ROBOTS_INDEX_FOLLOW,
    q_index_filter_chip_btn,
    build_stem_html,
    glossary_links_for_tags,
    guide_links_for_page,
    load_glossary_lookup,
    load_guide_articles,
    meta_description,
    normalize_glossary_href,
    norm,
    parse_correct,
    parse_tags,
    public_url,
    rel_css,
    rel_href,
    rel_theme_css,
    stem_preview,
    text_to_html,
)
from tools.html_footer import (  # noqa: E402
    breadcrumb_html,
    q_hub_links_html,
    q_index_filters_details_html,
    q_index_stats_line,
    q_index_tools_close_html,
    q_index_tools_open_html,
    q_practice_tier_tabs_html,
    shell_body_class,
    site_page_footer,
    site_page_header,
    site_page_wrap_close,
    site_page_wrap_open,
)
from tools.q_page_seo import (
    index_lead,
    index_meta_description,
    index_search_index_suffix,
    index_search_placeholder,
    question_meta_description,
    study_modes_note_html,
)
from tools.site_config import brand_name, category_order, clean_origin, exam_name, ichimon_enabled, practice_tiers
from tools.seo_editorial_chrome import seo_brand_asset_tags

PRACTICE_CSV = ROOT / "data" / "practice_questions.csv"
ICHIMON_CSV = ROOT / "data" / "ichimon_questions.csv"
Q_ROOT = ROOT / "q"
BASE_DEFAULT = clean_origin()

from tools.ichimon_paths import ichimon_path_info, ichimon_rel_path  # noqa: E402

PRACTICE_ID_BASE = 900_000

INDEX_CONFIG: dict[str, dict] = {
    "practice": {
        "variant": "practice",
        "groupBy": "category",
        "groupPrefix": "group",
        "groupLabel": "分野",
        "searchInputLabel": "実践演習検索",
        "searchPlaceholder": "例：第1問、分野名、問題文…",
        "emptyTitle": "条件に一致する実践演習がありません",
        "emptyHint": "検索語を短くするか、分野・学習状況を「すべて」に戻してお試しください。",
        "appLinkTemplate": "../index.html#orig",
        "appLinkLabel": "アプリで解く",
        "rowLabelField": "qno",
        "statusFilters": ["wrong", "bookmark"],
        "answerKind": "choice",
    },
    "ichimon": {
        "variant": "ichimon",
        "groupBy": "category",
        "groupPrefix": "group",
        "groupLabel": "分野",
        "searchInputLabel": "一問一答検索",
        "searchPlaceholder": "例：2026-01-1、分野名、問題文…",
        "emptyTitle": "条件に一致する一問一答がありません",
        "emptyHint": "検索語を短くするか、分野・学習状況を「すべて」に戻してお試しください。",
        "appLinkTemplate": "../index.html#ichimondou",
        "appLinkLabel": "アプリで解く",
        "rowLabelField": "id",
        "statusFilters": ["wrong", "bookmark"],
        "answerKind": "marubatsu",
    },
}


def group_slug(key: str) -> str:
    """HTML id / アンカー用（中黒・記号はハイフンに）。"""
    s = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", str(key)).strip("-")
    return s or "other"


def sort_category_keys(keys: list[str]) -> list[str]:
    """site-config.json の fields 順で分野名を並べる。"""
    order = category_order()
    rank = {name: i for i, name in enumerate(order)}
    return sorted(keys, key=lambda k: (rank.get(k, len(order)), k))


def category_rank(cat: str) -> int:
    order = category_order()
    try:
        return order.index(cat)
    except ValueError:
        return len(order)


def practice_rel_path(qno: int) -> str:
    return f"q/practice/p{qno:03d}/index.html"


def _rel_root_asset(rel_path: Path, filename: str) -> str:
    depth = len(rel_path.parent.parts)
    prefix = "/".join([".."] * depth)
    return f"{prefix}/{filename}" if prefix else filename


def _practice_question_nav(page: dict) -> tuple[list[tuple[str, str | None]], str | None, str]:
    """パンくず（tier 対応）と tier タブ用 id、一覧 JSON-LD 用ラベル。"""
    from tools.practice_tier import (
        multi_tier_practice_enabled,
        page_tier_id,
        tier_index_rel_path,
        tier_list_breadcrumb_label,
    )

    heading_tail = f"第{page['qno']}問"
    if not multi_tier_practice_enabled():
        return (
            [("トップ", "index.html"), ("実践演習一覧", "q/practice/index.html"), (heading_tail, None)],
            None,
            "実践演習一覧",
        )
    tiers = practice_tiers()
    tid = page_tier_id(page, tiers)
    tier = next(t for t in tiers if str(t.get("id") or "") == tid)
    list_label = tier_list_breadcrumb_label(tier)
    return (
        [
            ("トップ", "index.html"),
            ("実践演習", "q/practice/index.html"),
            (list_label, tier_index_rel_path(tid)),
            (heading_tail, None),
        ],
        tid,
        list_label,
    )


def parse_marubatsu_answer(raw: str) -> bool:
    s = norm(raw)
    if s in ("○", "〇"):
        return True
    if s in ("×", "✕", "╳"):
        return False
    raise ValueError(f"想定外の answer 列: {raw!r}")


def marubatsu_label(correct_answer: bool) -> str:
    return "○" if correct_answer else "×"


def load_practice_rows() -> list[dict]:
    if not PRACTICE_CSV.is_file():
        return []
    return list(csv.DictReader(PRACTICE_CSV.read_text(encoding="utf-8-sig").splitlines()))


def load_ichimon_rows() -> list[dict]:
    if not ICHIMON_CSV.is_file():
        return []
    return list(csv.DictReader(ICHIMON_CSV.read_text(encoding="utf-8-sig").splitlines()))


def practice_page_dict(row: dict, line_no: int) -> dict:
    if norm(row.get("is_invalidated", "")).upper() == "TRUE":
        raise ValueError(f"practice line {line_no}: 無効行はスキップ対象")
    from tools.correct_answer_format import collect_choice_texts, practice_min_choice_count
    from tools.site_config import extended_correct_answers

    qno = int(row["question_no"])
    opts = collect_choice_texts(row)
    min_choices = practice_min_choice_count(row)
    if len(opts) < min_choices:
        raise ValueError(f"practice line {line_no}: 選択肢欠け no={qno}")
    cor = parse_correct(row.get("correct"), max_choice=len(opts))
    if cor is None:
        raise ValueError(f"practice line {line_no}: 正答なし no={qno}")
    cat = norm(row.get("category"))
    stem_plain = norm(row.get("stem"))
    return {
        "qno": qno,
        "category": cat,
        "type": norm(row.get("type")) or "single",
        "stem_html": build_stem_html(row),
        "stem_plain": stem_plain,
        "opts": opts,
        "correct": cor,
        "exp": norm(row.get("explanation")) or "（解説は未入力です。）",
        "tags": parse_tags(norm(row.get("tags"))),
        "rel_path": practice_rel_path(qno),
        "href_rel": f"p{qno:03d}/index.html",
    }


def ichimon_page_dict(row: dict, line_no: int) -> dict:
    rid = norm(row.get("id"))
    if not rid:
        raise ValueError(f"ichimon line {line_no}: id が空")
    cat = norm(row.get("category"))
    statement = norm(row.get("question"))
    correct = parse_marubatsu_answer(norm(row.get("answer")))
    paths = ichimon_path_info(rid)
    return {
        "id": rid,
        "year": int(paths["year"]),
        "category": cat,
        "statement": statement,
        "statement_html": f"<p>{text_to_html(statement)}</p>" if statement else "<p>（問題文なし）</p>",
        "correct_answer": correct,
        "exp": norm(row.get("explanation")) or "（解説は未入力です。）",
        "source": norm(row.get("source")),
        "tags": parse_tags(norm(row.get("tags"))),
        "rel_path": str(paths["rel_path"]),
        "href_rel": str(paths["href_rel"]),
    }


def build_practice_related_html(
    page: dict,
    rel_path: Path,
    all_pages: list[dict],
    glossary_lookup: dict[str, str],
    guides: list[dict[str, str]],
) -> str:
    from tools.build_glossary_pages import field_hub_slug
    from tools.knowledge_hub_seo import field_hub_page_exists
    from tools.practice_tier import (
        multi_tier_practice_enabled,
        page_tier_id,
        tier_index_rel_path,
        tier_list_breadcrumb_label,
    )

    links: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(href: str, label: str) -> None:
        if href in seen:
            return
        seen.add(href)
        links.append((href, label))

    if multi_tier_practice_enabled():
        tiers = practice_tiers()
        tid = page_tier_id(page, tiers)
        tier = next(t for t in tiers if str(t.get("id") or "") == tid)
        add(rel_href(rel_path, tier_index_rel_path(tid)), tier_list_breadcrumb_label(tier))
        same_tier = sorted(
            [p for p in all_pages if page_tier_id(p, tiers) == tid],
            key=lambda x: x["qno"],
        )
        qnos = [p["qno"] for p in same_tier]
        idx = qnos.index(page["qno"])
        for j in (idx - 1, idx + 1):
            if 0 <= j < len(same_tier):
                pg = same_tier[j]
                add(rel_href(rel_path, pg["rel_path"]), f"実践演習 第{pg['qno']}問")
    else:
        add(rel_href(rel_path, "q/practice/index.html"), "実践演習一覧")
        qno = page["qno"]
        by_no = {p["qno"]: p for p in all_pages}
        for other in (qno - 1, qno + 1):
            pg = by_no.get(other)
            if pg:
                add(rel_href(rel_path, pg["rel_path"]), f"実践演習 第{other}問")

    for gl in glossary_links_for_tags(page.get("tags") or [], glossary_lookup):
        add(rel_href(rel_path, normalize_glossary_href(gl["href"])), gl["label"])

    cat = page.get("category") or ""
    if field_hub_page_exists(cat):
        hub = field_hub_slug(cat)
        add(rel_href(rel_path, f"terms/{hub}/index.html"), f"{cat}の用語一覧")

    for href_rel, title in guide_links_for_page(page.get("category") or "", guides):
        add(rel_href(rel_path, href_rel), title)

    add(rel_href(rel_path, "q/index.html"), "過去問一覧")
    add(rel_href(rel_path, "q/ichimon/index.html"), "一問一答一覧")
    add(rel_href(rel_path, "index.html#orig"), "アプリで演習する")

    link_html = "".join(
        f'<a class="related-link" href="{html.escape(h)}">{html.escape(l)}</a>'
        for h, l in links[:8]
    )
    return (
        '<section class="q-block q-related" aria-labelledby="q-related-h">'
        '<h2 id="q-related-h" class="q-h2">関連ページ</h2>'
        '<div class="related-box"><div class="related-links">'
        f"{link_html}</div></div></section>"
    )


def build_ichimon_related_html(
    page: dict,
    rel_path: Path,
    all_pages: list[dict],
    glossary_lookup: dict[str, str],
    guides: list[dict[str, str]],
) -> str:
    from tools.build_glossary_pages import field_hub_slug
    from tools.knowledge_hub_seo import field_hub_page_exists

    links: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(href: str, label: str) -> None:
        if href in seen:
            return
        seen.add(href)
        links.append((href, label))

    add(rel_href(rel_path, "q/ichimon/index.html"), "一問一答一覧")
    ordered = sorted(all_pages, key=lambda p: p["id"])
    ids = [p["id"] for p in ordered]
    idx = ids.index(page["id"])
    for j in (idx - 1, idx + 1):
        if 0 <= j < len(ordered):
            pg = ordered[j]
            add(rel_href(rel_path, pg["rel_path"]), f"一問一答 {pg['id']}")

    for gl in glossary_links_for_tags(page.get("tags") or [], glossary_lookup):
        add(rel_href(rel_path, normalize_glossary_href(gl["href"])), gl["label"])

    cat = page.get("category") or ""
    if field_hub_page_exists(cat):
        hub = field_hub_slug(cat)
        add(rel_href(rel_path, f"terms/{hub}/index.html"), f"{cat}の用語一覧")

    for href_rel, title in guide_links_for_page(page.get("category") or "", guides):
        add(rel_href(rel_path, href_rel), title)

    add(rel_href(rel_path, "q/index.html"), "過去問一覧")
    add(rel_href(rel_path, "q/practice/index.html"), "実践演習一覧")
    add(rel_href(rel_path, "index.html#ichimondou"), "アプリで演習する")

    link_html = "".join(
        f'<a class="related-link" href="{html.escape(h)}">{html.escape(l)}</a>'
        for h, l in links[:8]
    )
    return (
        '<section class="q-block q-related" aria-labelledby="q-related-h">'
        '<h2 id="q-related-h" class="q-h2">関連ページ</h2>'
        '<div class="related-box"><div class="related-links">'
        f"{link_html}</div></div></section>"
    )


def build_practice_question_html(
    page: dict,
    row: dict,
    rel_path: Path,
    base_url: str,
    *,
    all_pages: list[dict],
    glossary_lookup: dict[str, str],
    guides: list[dict[str, str]],
    question_catalog: list[dict],
) -> str:
    from tools.q_page_seo import (
        question_h1,
        question_meta_headline,
        question_page_title,
    )

    practice_tags = page.get("tags") or []
    heading = question_h1(
        "practice",
        qno=page["qno"],
        category=page["category"],
        tags=practice_tags,
    )
    title = question_page_title(
        "practice",
        qno=page["qno"],
        category=page["category"],
        tags=practice_tags,
    )
    stem = page.get("stem_plain") or ""
    desc = question_meta_description(
        "practice",
        headline=question_meta_headline(
            "practice", qno=page["qno"], tags=practice_tags
        ),
        category=page["category"],
        body=stem,
        answer_tail=str(page["correct"]) if page.get("correct") is not None else "",
    )
    study_modes_note = study_modes_note_html()
    canonical = public_url(base_url, page["rel_path"])
    lead_html = ""
    opts_html = "".join(
        f'<li class="q-opt"><span class="q-opt-num">（{i}）</span> {html.escape(o)}</li>'
        for i, o in enumerate(page["opts"], start=1)
    )
    ans_block = f'<p>正答は <strong>（{page["correct"]}）</strong> です。</p>'
    exp_html = build_explanation_html(
        {
            **page,
            "year": 0,
            "is_invalidated": False,
            "is_exempt": False,
        },
        row,
    )
    similar_html = build_similar_questions_html(
        page,
        rel_path,
        question_catalog,
        mode="practice",
        rel_href=rel_href,
        publish_root=ROOT,
    )
    related_html = build_practice_related_html(
        page, rel_path, all_pages, glossary_lookup, guides
    )
    from tools.practice_tier import tier_index_rel_path  # noqa: E402

    crumb_items, tier_tab_id, list_json_label = _practice_question_nav(page)
    list_json_href = (
        tier_index_rel_path(tier_tab_id) if tier_tab_id else "q/practice/index.html"
    )
    json_ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": canonical + "#webpage",
                "url": canonical,
                "name": title,
                "description": desc,
                "inLanguage": "ja-JP",
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "トップ", "item": public_url(base_url, "index.html")},
                    *(
                        [
                            {
                                "@type": "ListItem",
                                "position": 2,
                                "name": "実践演習",
                                "item": public_url(base_url, "q/practice/index.html"),
                            },
                            {
                                "@type": "ListItem",
                                "position": 3,
                                "name": list_json_label,
                                "item": public_url(base_url, list_json_href),
                            },
                            {"@type": "ListItem", "position": 4, "name": heading, "item": canonical},
                        ]
                        if tier_tab_id
                        else [
                            {
                                "@type": "ListItem",
                                "position": 2,
                                "name": list_json_label,
                                "item": public_url(base_url, "q/practice/index.html"),
                            },
                            {"@type": "ListItem", "position": 3, "name": heading, "item": canonical},
                        ]
                    ),
                ],
            },
        ],
    }
    site_header = site_page_header(rel_path, current="practice")
    site_breadcrumb = breadcrumb_html(rel_path, crumb_items)
    tier_tabs_html = q_practice_tier_tabs_html(rel_path, current_tier_id=tier_tab_id)
    site_footer = site_page_footer(rel_path, current="practice")

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
{seo_brand_asset_tags(rel_path)}
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
{ROBOTS_INDEX_FOLLOW}
<link rel="canonical" href="{html.escape(canonical)}">
<meta property="og:type" content="article">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{html.escape(canonical)}">
<meta name="twitter:card" content="summary_large_image">
{HEAD_FONTS}
<link rel="stylesheet" href="{html.escape(rel_css(rel_path))}">
<link rel="stylesheet" href="{html.escape(rel_theme_css(rel_path))}">
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
</head>
<body class="{shell_body_class('q-static-page')}">
{site_page_wrap_open()}
{site_header}
<main class="q-static-main">
  {site_breadcrumb}
  {study_modes_note}
  {q_hub_links_html(rel_path, current="practice")}
  {tier_tabs_html}
  <p class="q-meta-line">実践演習 · {html.escape(page["category"])}</p>
  <h1 class="q-h1">{html.escape(heading)}</h1>
  {lead_html}
  <section class="q-block" aria-labelledby="q-stem-h">
    <h2 id="q-stem-h" class="q-h2">問題</h2>
    <div class="q-stem">{page["stem_html"]}</div>
  </section>
  <section class="q-block" aria-labelledby="q-opts-h">
    <h2 id="q-opts-h" class="q-h2">選択肢</h2>
    <ol class="q-opts">{opts_html}</ol>
  </section>
  <section class="q-block q-answer" aria-labelledby="q-ans-h">
    <h2 id="q-ans-h" class="q-h2">正答</h2>
    {ans_block}
  </section>
  <section class="q-block" aria-labelledby="q-exp-h">
    <h2 id="q-exp-h" class="q-h2">解説</h2>
    {exp_html}
  </section>
  {similar_html}
  {related_html}
  <p class="q-app-link"><a href="{html.escape(rel_href(rel_path, 'index.html#orig'))}">アプリで演習する</a></p>
</main>
{site_footer}
{site_page_wrap_close()}
</body>
</html>
"""


def build_ichimon_question_html(
    page: dict,
    row: dict,
    rel_path: Path,
    base_url: str,
    *,
    all_pages: list[dict],
    glossary_lookup: dict[str, str],
    guides: list[dict[str, str]],
    question_catalog: list[dict],
) -> str:
    from tools.q_page_seo import (
        ichimon_meta_snippet,
        question_h1,
        question_meta_headline,
        question_page_title,
    )

    heading = question_h1(
        "ichimon", question_id=page["id"], category=page["category"]
    )
    title = question_page_title(
        "ichimon", question_id=page["id"], category=page["category"]
    )
    stmt = page.get("statement") or ""
    ans = marubatsu_label(page["correct_answer"])
    desc = question_meta_description(
        "ichimon",
        headline=question_meta_headline("ichimon", question_id=page["id"]),
        category=page["category"],
        body=ichimon_meta_snippet(stmt),
        answer_tail=ans,
    )
    study_modes_note = study_modes_note_html()
    canonical = public_url(base_url, page["rel_path"])
    source_line = (
        f'<p class="q-meta-line">{html.escape(page["source"])}</p>'
        if page.get("source")
        else ""
    )
    similar_html = build_similar_questions_html(
        page,
        rel_path,
        question_catalog,
        mode="ichimon",
        rel_href=rel_href,
        publish_root=ROOT,
    )
    related_html = build_ichimon_related_html(
        page, rel_path, all_pages, glossary_lookup, guides
    )
    json_ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": canonical + "#webpage",
                "url": canonical,
                "name": title,
                "description": desc,
                "inLanguage": "ja-JP",
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "トップ", "item": public_url(base_url, "index.html")},
                    {"@type": "ListItem", "position": 2, "name": "一問一答一覧", "item": public_url(base_url, "q/ichimon/index.html")},
                    {"@type": "ListItem", "position": 3, "name": heading, "item": canonical},
                ],
            },
        ],
    }
    site_header = site_page_header(rel_path, current="ichimon")
    site_breadcrumb = breadcrumb_html(
        rel_path,
        [
            ("トップ", "index.html"),
            ("一問一答一覧", "q/ichimon/index.html"),
            (heading, None),
        ],
    )
    site_footer = site_page_footer(rel_path, current="ichimon")
    exp_html = build_ichimon_explanation_html(page, row)
    robots_meta = ichimon_robots_meta(page["id"])

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
{seo_brand_asset_tags(rel_path)}
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
{robots_meta}
<link rel="canonical" href="{html.escape(canonical)}">
<meta property="og:type" content="article">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{html.escape(canonical)}">
<meta name="twitter:card" content="summary_large_image">
{HEAD_FONTS}
<link rel="stylesheet" href="{html.escape(rel_css(rel_path))}">
<link rel="stylesheet" href="{html.escape(rel_theme_css(rel_path))}">
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
</head>
<body class="{shell_body_class('q-static-page')}">
{site_page_wrap_open()}
{site_header}
<main class="q-static-main">
  {site_breadcrumb}
  {study_modes_note}
  {q_hub_links_html(rel_path, current="ichimon")}
  <p class="q-meta-line">一問一答 · {html.escape(page["category"])}</p>
  {source_line}
  <h1 class="q-h1">{html.escape(heading)}</h1>
  <section class="q-block" aria-labelledby="q-stem-h">
    <h2 id="q-stem-h" class="q-h2">問題</h2>
    <div class="q-stem q-stem-ichimon">{page["statement_html"]}</div>
  </section>
  <section class="q-block q-answer" aria-labelledby="q-ans-h">
    <h2 id="q-ans-h" class="q-h2">正答</h2>
    <p class="q-ichimon-answer">答えは <strong class="q-marubatsu">{html.escape(ans)}</strong> です。</p>
  </section>
  <section class="q-block" aria-labelledby="q-exp-h">
    <h2 id="q-exp-h" class="q-h2">解説</h2>
    {exp_html}
  </section>
  {similar_html}
  {related_html}
  <p class="q-app-link"><a href="{html.escape(rel_href(rel_path, 'index.html#ichimondou'))}">アプリで演習する</a></p>
</main>
{site_footer}
{site_page_wrap_close()}
</body>
</html>
"""


def build_group_blocks(
    pages: list[dict],
    *,
    mode: str,
    group_by: str,
) -> tuple[str, str, int]:
    """過去問一覧と同型の折りたたみブロック＋ジャンプリンク HTML。"""
    row_builder = build_practice_index_table_row if mode == "practice" else build_ichimon_index_table_row
    groups: dict[str, list[dict]] = {}
    for pg in pages:
        if group_by == "year":
            key = str(pg.get("year") or 0)
        else:
            key = pg["category"]
        groups.setdefault(key, []).append(pg)

    sorted_keys = (
        sorted(groups.keys(), reverse=True)
        if group_by == "year"
        else sort_category_keys(list(groups.keys()))
    )
    open_keys = set(sorted_keys[:2])
    blocks: list[str] = []
    jump_links: list[str] = []

    for key in sorted_keys:
        items = groups[key]
        if mode == "practice":
            items.sort(key=lambda x: x["qno"])
        else:
            items.sort(key=lambda x: x["id"])
        rows_html = "".join(row_builder(pg) for pg in items)
        if group_by == "year":
            block_id = f"year-{key}"
            heading = f"{key}年"
            jump_label = heading
        else:
            slug = group_slug(key)
            block_id = f"group-{slug}"
            heading = key
            jump_label = key
        prefix = "year" if group_by == "year" else "group"
        expanded = "true" if key in open_keys else "false"
        collapsed = "" if key in open_keys else " is-collapsed"
        jump_links.append(
            f'<a class="q-index-filter-opt q-index-year-link" href="#{block_id}" '
            f'data-group="{html.escape(key, quote=True)}">'
            f'{html.escape(jump_label)}<span class="q-index-filter-count">（{len(items)}）</span></a>'
        )
        blocks.append(
            f'<section class="q-index-year-block{collapsed}" id="{block_id}" data-group-prefix="{prefix}">'
            f'<div class="q-index-year-head">'
            f'<div class="q-index-year-head-main">'
            f'<button type="button" class="q-index-year-toggle" aria-expanded="{expanded}" '
            f'aria-controls="body-{block_id}"><span class="q-index-year-chevron" aria-hidden="true"></span></button>'
            f'<h2 id="{block_id}-heading">{html.escape(heading)}</h2>'
            f"</div>"
            f'<span class="q-index-year-count" data-total="{len(items)}">{len(items)}問</span>'
            f"</div>"
            f'<div class="q-year-table-wrap" id="body-{block_id}">'
            f'<table class="q-year-table" aria-labelledby="{block_id}-heading">'
            "<thead><tr>"
            '<th scope="col">問</th><th scope="col">分野</th>'
            '<th scope="col">問題文（抜粋）</th>'
            "</tr></thead>"
            f"<tbody>{rows_html}</tbody>"
            "</table></div></section>"
        )
    return "".join(blocks), "".join(jump_links), len(groups)


def build_practice_hub_index(
    *,
    tiers: list[dict],
    tier_counts: dict[str, int],
    base_url: str,
    total_count: int,
) -> str:
    """practiceTiers があるサイトの実践演習 hub（試験種別の入口）。"""
    from tools.practice_tier import tier_display_label, tier_index_rel_path
    from tools.q_page_seo import (
        index_h1,
        index_page_title,
        practice_hub_lead,
        practice_hub_meta_description,
    )

    rel_path = Path("q/practice/index.html")
    h1 = index_h1("practice")
    page_title = index_page_title("practice")
    lead = practice_hub_lead()
    desc = practice_hub_meta_description(total_count=total_count)
    canonical_rel = "q/practice/index.html"

    cards: list[str] = []
    for tier in tiers:
        tid = str(tier.get("id") or "").strip()
        if not tid:
            continue
        label = tier_display_label(tier)
        subtitle = str(tier.get("subtitle") or "").strip()
        count = tier_counts.get(tid, 0)
        href = "/" + tier_index_rel_path(tid).lstrip("/")
        subtitle_html = (
            f'<p class="q-practice-tier-card-lead">{html.escape(subtitle)}</p>'
            if subtitle
            else ""
        )
        cards.append(
            f'<section class="q-practice-tier-card">'
            f'<h2 class="q-practice-tier-card-title">{html.escape(label)}</h2>'
            f"{subtitle_html}"
            f'<p class="q-practice-tier-card-count">{count}問</p>'
            f'<p class="q-practice-tier-card-action">'
            f'<a class="site-btn site-btn--primary" href="{html.escape(href)}">一覧を見る</a>'
            f"</p></section>"
        )

    header = site_page_header(rel_path, current="practice")
    breadcrumb = breadcrumb_html(rel_path, [("トップ", "index.html"), (f"{h1}一覧", None)])
    footer = site_page_footer(rel_path, current="practice")
    css_href = rel_css(rel_path)
    theme_href = rel_theme_css(rel_path)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
{seo_brand_asset_tags(rel_path)}
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(page_title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta property="og:title" content="{html.escape(page_title)}">
<meta property="og:description" content="{html.escape(desc)}">
{ROBOTS_INDEX_FOLLOW}
<link rel="canonical" href="{html.escape(public_url(base_url, canonical_rel))}">
{HEAD_FONTS}
<link rel="stylesheet" href="{html.escape(css_href)}">
<link rel="stylesheet" href="{html.escape(theme_href)}">
</head>
<body class="{shell_body_class('q-index-page q-practice-hub-page')}">
{site_page_wrap_open()}
{header}
<main class="site-page-main">
  {breadcrumb}
  <h1>{html.escape(h1)}</h1>
  <p class="site-page-lead">{html.escape(lead)}</p>
  {study_modes_note_html()}
  {q_hub_links_html(rel_path, current="practice")}
  <div class="q-practice-tier-hub" aria-label="試験種別を選ぶ">
    {"".join(cards)}
  </div>
  <p class="q-practice-hub-total">全{total_count}問（試験種別ごとに分野別一覧から探せます）</p>
</main>
{footer}
{site_page_wrap_close()}
</body>
</html>
"""


def _practice_pages_for_tier_index(pages: list[dict], rel_path: Path) -> list[dict]:
    """tier 別一覧は q/practice/pNNN/ への相対 href が ../ 付きになるよう補正する。"""
    out: list[dict] = []
    for pg in pages:
        patched = dict(pg)
        patched["href_rel"] = rel_href(rel_path, pg["rel_path"])
        out.append(patched)
    return out


def build_mode_index(
    *,
    mode: str,
    pages: list[dict],
    base_url: str,
    rel_path: Path,
    practice_tier: dict | None = None,
) -> str:
    """実践演習 / 一問一答の一覧（過去問 q/index.html と同型 UI）。"""
    cfg = {**INDEX_CONFIG[mode], "categoryOrder": category_order()}
    study_modes_note = study_modes_note_html()
    search_placeholder = index_search_placeholder(mode)

    if mode == "practice":
        current = "practice"
        from tools.practice_tier import tier_index_rel_path, tier_list_breadcrumb_label
        from tools.q_page_seo import index_h1, index_page_title

        page_title = index_page_title("practice", tier=practice_tier)
        h1 = index_h1("practice", tier=practice_tier)
        lead = index_lead("practice", tier=practice_tier)
        desc = index_meta_description("practice", count=len(pages), tier=practice_tier)
        if practice_tier:
            tid = str(practice_tier.get("id") or "")
            canonical_rel = tier_index_rel_path(tid)
        else:
            canonical_rel = "q/practice/index.html"
        pages_for_index = (
            _practice_pages_for_tier_index(pages, rel_path) if practice_tier else pages
        )
        index_items = [practice_index_item_dict(pg) for pg in pages_for_index]
        group_by = "category"
        filter_hint = "分野・学習状況"
        show_category_row = False
        year_row_label = "分野へ"
        tier_tab_id = str(practice_tier.get("id") or "") if practice_tier else None
        tier_tabs_html = q_practice_tier_tabs_html(rel_path, current_tier_id=tier_tab_id)
        if practice_tier:
            breadcrumb_items: list[tuple[str, str | None]] = [
                ("トップ", "index.html"),
                ("実践演習", "q/practice/index.html"),
                (tier_list_breadcrumb_label(practice_tier), None),
            ]
        else:
            breadcrumb_items = [("トップ", "index.html"), (f"{h1}一覧", None)]
    else:
        current = "ichimon"
        from tools.q_page_seo import index_h1, index_page_title

        page_title = index_page_title("ichimon")
        h1 = index_h1("ichimon")
        lead = index_lead("ichimon")
        desc = index_meta_description("ichimon", count=len(pages))
        canonical_rel = "q/ichimon/index.html"
        index_items = [ichimon_index_item_dict(pg) for pg in pages]
        group_by = "category"
        filter_hint = "分野・学習状況"
        show_category_row = False
        year_row_label = "分野へ"
        tier_tabs_html = ""
        breadcrumb_items = [("トップ", "index.html"), (f"{h1}一覧", None)]

    by_category: dict[str, int] = {}
    for pg in pages:
        by_category[pg["category"]] = by_category.get(pg["category"], 0) + 1

    group_blocks_html, group_jump_html, group_count = build_group_blocks(
        pages_for_index if mode == "practice" and practice_tier else pages,
        mode=mode,
        group_by=group_by,
    )

    status_defs = [
        ("all", "すべて", True),
        ("wrong", "不正解", False),
        ("bookmark", "ブックマーク", False),
        ("exempt", "免除", False),
        ("invalid", "無効", False),
    ]
    status_chips = []
    for sid, label, default_on in status_defs:
        if sid != "all" and sid not in cfg["statusFilters"]:
            continue
        status_chips.append(
            q_index_filter_chip_btn(
                "q-index-status-btn",
                "data-status",
                sid,
                label,
                on=default_on,
            )
        )
    category_chips = [
        q_index_filter_chip_btn("q-index-chip-btn", "data-cat", "all", "すべて", on=True)
    ]
    for cat in sort_category_keys(list(by_category.keys())):
        count = by_category[cat]
        category_chips.append(
            q_index_filter_chip_btn("q-index-chip-btn", "data-cat", cat, cat, count=count)
        )

    json_data = json.dumps(index_items, ensure_ascii=False)
    json_config = json.dumps(cfg, ensure_ascii=False)
    group_label = cfg["groupLabel"]

    header = site_page_header(rel_path, current=current)
    breadcrumb = breadcrumb_html(rel_path, breadcrumb_items)
    footer = site_page_footer(rel_path, current=current)
    list_aria = f"{group_label}別{h1}"
    css_href = rel_css(rel_path)
    theme_href = rel_theme_css(rel_path)
    index_js_href = _rel_root_asset(rel_path, "site-q-index.js")

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
{seo_brand_asset_tags(rel_path)}
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(page_title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta property="og:title" content="{html.escape(page_title)}">
<meta property="og:description" content="{html.escape(desc)}">
{ROBOTS_INDEX_FOLLOW}
<link rel="canonical" href="{html.escape(public_url(base_url, canonical_rel))}">
{HEAD_FONTS}
<link rel="stylesheet" href="{html.escape(css_href)}">
<link rel="stylesheet" href="{html.escape(theme_href)}">
</head>
<body class="{shell_body_class('q-index-page')}">
{site_page_wrap_open()}
{header}
<main class="site-page-main">
  {breadcrumb}
  <h1>{html.escape(h1)}</h1>
  <p class="site-page-lead">{html.escape(lead)}</p>
  {study_modes_note}
  {q_hub_links_html(rel_path, current=current)}
  {tier_tabs_html}
  <section class="past-index-panel" aria-labelledby="mode-index-heading">
    <div class="past-index-head">
      <div>
        <h2 id="mode-index-heading">{html.escape(h1)}一覧</h2>
        <p>{html.escape(q_index_stats_line(question_count=len(pages), mode=mode, year_count=len({p.get("year") for p in pages}), category_count=len(by_category)))}。キーワード検索と絞り込みで探せます。</p>
      </div>
    </div>
    {q_index_tools_open_html(
        search_label=cfg["searchInputLabel"],
        search_placeholder=search_placeholder,
        hit_text=f"{len(pages)} / {len(pages)} 問",
    )}
      {q_index_filters_details_html(
          year_row_label=year_row_label if mode == "practice" else group_label,
          year_jump_html=group_jump_html,
          category_chips_html="".join(category_chips),
          status_chips_html="".join(status_chips),
          show_category_row=show_category_row,
          filters_hint=filter_hint,
      )}
    {q_index_tools_close_html()}
    <div class="q-index-empty-panel hide" id="q-index-empty" role="status">
      <p class="q-index-empty-title">{html.escape(cfg["emptyTitle"])}</p>
      <p class="q-index-empty-hint">{html.escape(cfg["emptyHint"])}</p>
      <button type="button" class="q-index-reset" id="q-index-empty-reset">条件をクリア</button>
    </div>
    <div class="q-index-layout">
      <div class="q-index-content">
        <section class="q-index-years q-index-view-panel" id="q-index-view-year" aria-label="{html.escape(list_aria)}">{group_blocks_html}</section>
        <section class="q-index-view-panel hide" id="q-index-view-cat" aria-label="分野別一覧"><div id="q-index-cat-mount"></div></section>
        <section class="q-index-view-panel hide" id="q-index-view-flat" aria-label="一覧（フラット）">
          <div class="q-year-table-wrap">
            <table class="q-year-table">
              <thead><tr>
                <th scope="col">問</th><th scope="col">分野</th>
                <th scope="col">問題文（抜粋）</th>
              </tr></thead>
              <tbody id="q-index-flat-body"></tbody>
            </table>
          </div>
        </section>
        <nav class="q-index-pagination hide" id="q-index-pagination" aria-label="ページ送り"></nav>
      </div>
    </div>
  </section>
</main>
{footer}
{site_page_wrap_close()}
<button type="button" class="q-index-top" id="q-index-top" aria-label="ページ上部へ">↑</button>
<script type="application/json" id="q-index-config">{json_config}</script>
<script type="application/json" id="q-index-data">{json_data}</script>
<script defer src="{html.escape(index_js_href)}"></script>
</body>
</html>
"""


def build_practice_index_table_row(page: dict) -> str:
    """実践一覧の表行（操作列なし。フィルタは #q-index-data + site-q-index.js）。"""
    href = html.escape(page["href_rel"])
    label = f"第{page['qno']}問"
    preview = stem_preview(page.get("stem_plain") or "")
    preview_cell = (
        html.escape(preview)
        if preview
        else '<span class="q-year-table-desc--empty">問題文は各ページで確認できます</span>'
    )
    return (
        '<tr class="q-year-table-row" tabindex="0"'
        f' data-app-id="{page["app_id"]}"'
        f' data-href="{html.escape(page["href_rel"], quote=True)}"'
        f' data-category="{html.escape(page["category"], quote=True)}">'
        f'<td class="q-year-table-no" data-label="問"><a href="{href}">{html.escape(label)}</a></td>'
        f'<td class="q-year-table-cat" data-label="分野">{html.escape(page["category"])}</td>'
        f'<td class="q-year-table-desc" data-label="問題文">{preview_cell}</td>'
        "</tr>"
    )


def build_ichimon_index_table_row(page: dict) -> str:
    href = html.escape(page["href_rel"])
    label = html.escape(page["id"])
    app_id = html.escape(page["id"], quote=True)
    preview = stem_preview(page.get("statement") or "")
    preview_cell = (
        html.escape(preview)
        if preview
        else '<span class="q-year-table-desc--empty">問題文は各ページで確認できます</span>'
    )
    return (
        '<tr class="q-year-table-row" tabindex="0"'
        f' data-app-id="{app_id}"'
        f' data-href="{html.escape(page["href_rel"], quote=True)}"'
        f' data-category="{html.escape(page["category"], quote=True)}">'
        f'<td class="q-year-table-no" data-label="ID"><a href="{href}">{label}</a></td>'
        f'<td class="q-year-table-cat" data-label="分野">{html.escape(page["category"])}</td>'
        f'<td class="q-year-table-desc" data-label="問題文">{preview_cell}</td>'
        "</tr>"
    )


def _patch_index_rows_for_ichimon(pages: list[dict]) -> None:
    """一覧テーブル用に stem_plain を補う。"""
    for pg in pages:
        pg["stem_plain"] = stem_preview(pg.get("statement") or "")


def practice_index_item_dict(page: dict) -> dict:
    preview = stem_preview(page.get("stem_plain") or "")
    tags = page.get("tags") or []
    qno = page["qno"]
    search_bits = [
        f"第{qno}問",
        page["category"],
        preview,
        *tags,
    ]
    return {
        "appId": PRACTICE_ID_BASE + qno,
        "year": 0,
        "qno": qno,
        "label": f"第{qno}問",
        "category": page["category"],
        "href": page["href_rel"],
        "preview": preview,
        "tags": tags,
        "exempt": False,
        "invalidated": False,
        "correct": page.get("correct"),
        "search": " ".join(
            x for x in (*search_bits, index_search_index_suffix()) if x
        ),
    }


def ichimon_index_item_dict(page: dict) -> dict:
    preview = stem_preview(page.get("statement") or "")
    tags = page.get("tags") or []
    rid = page["id"]
    year = int(page.get("year") or 0)
    if not year and "-" in rid:
        head = rid.split("-", 1)[0]
        if head.isdigit():
            year = int(head)
    search_bits = [rid, page["category"], str(year), preview, *tags]
    return {
        "appId": rid,
        "year": year,
        "qno": 0,
        "label": rid,
        "category": page["category"],
        "href": page["href_rel"],
        "preview": preview,
        "tags": tags,
        "exempt": False,
        "invalidated": False,
        "correctAnswer": page.get("correct_answer"),
        "search": " ".join(
            x for x in (*search_bits, index_search_index_suffix()) if x
        ),
    }


def _patch_index_rows_for_practice(pages: list[dict]) -> None:
    for pg in pages:
        pg["app_id"] = PRACTICE_ID_BASE + pg["qno"]


def build_ichimon_redirect_index(*, base_url: str) -> str:
    """hideIchimon 時: 旧一問一答一覧 URL を実践演習へ転送。"""
    dest = "../practice/index.html"
    title = html.escape(f"実践演習一覧｜{brand_name()}")
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="0;url={html.escape(dest)}">
<meta name="robots" content="noindex, follow">
<title>{title}</title>
<link rel="canonical" href="{html.escape(public_url(base_url, "q/practice/index.html"))}">
</head>
<body>
<p><a href="{html.escape(dest)}">実践演習一覧へ移動</a></p>
</body>
</html>
"""


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=BASE_DEFAULT)
    args = ap.parse_args()
    base = args.base_url.rstrip("/")

    glossary_lookup = load_glossary_lookup()
    guides = load_guide_articles()
    question_catalog = load_question_catalog(ROOT)

    for sub in ("practice", "ichimon"):
        target = Q_ROOT / sub
        if target.is_dir():
            shutil.rmtree(target)

    practice_rows = load_practice_rows()
    practice_pages: list[dict] = []
    practice_rows_valid: list[dict] = []
    for i, row in enumerate(practice_rows, start=2):
        if norm(row.get("is_invalidated", "")).upper() == "TRUE":
            continue
        if is_demo_practice_question_row(row):
            continue
        practice_pages.append(practice_page_dict(row, i))
        practice_rows_valid.append(row)
    _patch_index_rows_for_practice(practice_pages)

    for p, row in zip(practice_pages, practice_rows_valid):
        rel = Path(p["rel_path"])
        out = ROOT / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            build_practice_question_html(
                p,
                row,
                out.relative_to(ROOT),
                base,
                all_pages=practice_pages,
                glossary_lookup=glossary_lookup,
                guides=guides,
                question_catalog=question_catalog,
            ),
            encoding="utf-8",
        )

    idx = Q_ROOT / "practice" / "index.html"
    idx.parent.mkdir(parents=True, exist_ok=True)
    tiers = practice_tiers()
    if len(tiers) >= 2:
        from tools.practice_tier import filter_pages_by_tier, tier_index_rel_path

        tier_counts = {
            str(tier["id"]): len(filter_pages_by_tier(practice_pages, str(tier["id"]), tiers))
            for tier in tiers
            if str(tier.get("id") or "").strip()
        }
        idx.write_text(
            build_practice_hub_index(
                tiers=tiers,
                tier_counts=tier_counts,
                base_url=base,
                total_count=len(practice_pages),
            ),
            encoding="utf-8",
        )
        for tier in tiers:
            tid = str(tier.get("id") or "").strip()
            if not tid:
                continue
            filtered = filter_pages_by_tier(practice_pages, tid, tiers)
            tier_idx = Q_ROOT / "practice" / tid / "index.html"
            tier_idx.parent.mkdir(parents=True, exist_ok=True)
            tier_idx.write_text(
                build_mode_index(
                    mode="practice",
                    pages=filtered,
                    base_url=base,
                    rel_path=Path(tier_index_rel_path(tid)),
                    practice_tier=tier,
                ),
                encoding="utf-8",
            )
    else:
        idx.write_text(
            build_mode_index(
                mode="practice",
                pages=practice_pages,
                base_url=base,
                rel_path=Path("q/practice/index.html"),
            ),
            encoding="utf-8",
        )

    ichimon_rows = load_ichimon_rows()
    if ichimon_enabled():
        set_ichimon_primary_ids(build_ichimon_primary_ids(ichimon_rows))
        ichimon_pairs: list[tuple[dict, dict]] = []
        for i, row in enumerate(ichimon_rows, start=2):
            ichimon_pairs.append((ichimon_page_dict(row, i), row))
        ichimon_pairs.sort(key=lambda pr: (category_rank(pr[0]["category"]), pr[0]["id"]))
        ichimon_pages = [p for p, _ in ichimon_pairs]
        ichimon_rows = [r for _, r in ichimon_pairs]
        _patch_index_rows_for_ichimon(ichimon_pages)

        for p, row in zip(ichimon_pages, ichimon_rows):
            rel = Path(p["rel_path"])
            out = ROOT / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(
                build_ichimon_question_html(
                    p,
                    row,
                    out.relative_to(ROOT),
                    base,
                    all_pages=ichimon_pages,
                    glossary_lookup=glossary_lookup,
                    guides=guides,
                    question_catalog=question_catalog,
                ),
                encoding="utf-8",
            )

        if ichimon_pages:
            idx = Q_ROOT / "ichimon" / "index.html"
            idx.parent.mkdir(parents=True, exist_ok=True)
            idx.write_text(
                build_mode_index(
                    mode="ichimon",
                    pages=ichimon_pages,
                    base_url=base,
                    rel_path=Path("q/ichimon/index.html"),
                ),
                encoding="utf-8",
            )
    else:
        ichimon_pages = []
        idx = Q_ROOT / "ichimon" / "index.html"
        idx.parent.mkdir(parents=True, exist_ok=True)
        idx.write_text(build_ichimon_redirect_index(base_url=base), encoding="utf-8")

    print(
        f"Wrote practice: {len(practice_pages)} pages"
        + (", index" if practice_pages else "")
    )
    print(
        f"Wrote ichimon: {len(ichimon_pages)} pages"
        + (", index" if ichimon_pages else "")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
