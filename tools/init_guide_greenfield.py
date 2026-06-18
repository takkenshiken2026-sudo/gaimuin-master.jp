#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""試験ガイドのグリーンフィールド初期化（keep を draft 化·本文クリア、merge を退役候補に）。

使い方:
  python3 tools/init_guide_greenfield.py --root ~/Projects/eisei1shu-master --dry-run
  python3 tools/init_guide_greenfield.py --root ~/Projects/eisei1shu-master --apply --retire

正本:
  sites/<site-id>/guide_exam_facts.json
  sites/<site-id>/guide_greenfield_catalog.json（任意）
  data/guide_seo_candidates.csv（keep / merge 判定）
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.editorial_quality import is_published_guide, norm  # noqa: E402
from tools.guide_exam_facts import (  # noqa: E402
    GREENFIELD_PLACEHOLDER,
    lead_anchor,
    load_exam_facts,
)
from tools.guide_retire_catalog import redirect_target  # noqa: E402
from tools.retire_guide_articles import apply_retire  # noqa: E402


def catalog_path_for_root(root: Path) -> Path | None:
    sid = root.name
    cfg = root / "site-config.json"
    if cfg.is_file():
        data = json.loads(cfg.read_text(encoding="utf-8"))
        sid = norm(data.get("siteId") or data.get("site_id") or sid)
    for base in (root, ROOT):
        p = base / "sites" / sid / "guide_greenfield_catalog.json"
        if p.is_file():
            return p
    return None


def load_catalog(root: Path) -> dict:
    path = catalog_path_for_root(root)
    if not path:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def candidate_decision(row: dict[str, str]) -> str:
    manual = norm(row.get("manual_decision"))
    return manual or norm(row.get("auto_decision"))


def load_candidates(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(encoding="utf-8-sig")))


def build_keep_set(candidates: list[dict[str, str]], catalog: dict) -> set[str]:
    keep: set[str] = set()
    for row in candidates:
        if row.get("content_status") != "published":
            continue
        if candidate_decision(row) == "keep":
            keep.add(norm(row["slug"]))
    for slug in catalog.get("promote_keep") or []:
        s = norm(slug)
        if s:
            keep.add(s)
    for slug in catalog.get("demote_keep") or []:
        keep.discard(norm(slug))
    return keep


def build_retire_map(
    candidates: list[dict[str, str]],
    keep: set[str],
    published_slugs: set[str],
) -> dict[str, str]:
    retiring: dict[str, str] = {}
    for row in candidates:
        if row.get("content_status") != "published":
            continue
        slug = norm(row["slug"])
        if slug in keep:
            continue
        decision = candidate_decision(row)
        if decision not in {"merge", "retire", "replace"}:
            continue
        hint = norm(row.get("merge_target"))
        if hint and hint in keep:
            target = hint
        else:
            target = redirect_target(
                slug,
                published_slugs=published_slugs,
                retiring=set(retiring),
                hint=hint or None,
            )
        if target == slug or target not in keep:
            for fallback in (
                hint,
                "exam-format-overview",
                "goukaku-kijun",
                "past-questions-by-field",
                "textbook-selection",
                "study-plan-working",
            ):
                fb = norm(fallback)
                if fb and fb in keep:
                    target = fb
                    break
            else:
                target = sorted(keep)[0]
        retiring[slug] = target
    return retiring


def placeholder_body(facts: dict, organizer: str | None = None) -> str:
    fmt = facts.get("exam_format") or {}
    org = organizer or norm(facts.get("organizer"))
    tier2 = (
        f"二種{fmt.get('question_count', 44)}問·{fmt.get('duration_minutes', 120)}分·"
        f"{fmt.get('total_points', 300)}点満点"
    )
    first = facts.get("first_kind_reference") or {}
    if first.get("question_count"):
        format_summary = (
            f"{tier2}（一種は{first['question_count']}問·{first['duration_minutes']}分·"
            f"{first['total_points']}点満点）"
        )
    else:
        format_summary = tier2
    pass_pct = fmt.get("pass_overall_percent", 60)
    pass_pts = fmt.get("pass_overall_points", 240)
    per_range = fmt.get("pass_per_range_percent")
    if per_range not in (None, ""):
        pass_criteria = (
            f"総合{pass_pct}％（{pass_pts}点）以上かつ各出題範囲{per_range}％以上"
        )
    else:
        note = norm(facts.get("pass_criteria_note"))
        if note.startswith("合否は"):
            note = note[3:].lstrip("、").strip()
        pass_criteria = note or f"総合{pass_pct}％（{pass_pts}点）以上"
    return GREENFIELD_PLACEHOLDER.format(
        organizer=org,
        format_summary=format_summary,
        pass_criteria=pass_criteria,
    )


def apply_headings(row: dict[str, str], headings: list[str]) -> None:
    for i in range(1, 8):
        key = f"section_{i}_heading"
        if i <= len(headings):
            row[key] = headings[i - 1]
        elif norm(row.get(key)):
            row[key] = f"（greenfield 見出し待ち {i}）"


from tools.related_links import parse_related_link_token  # noqa: E402


def strip_related_to_keep(related: str, keep: set[str]) -> str:
    kept: list[str] = []
    for item in [x.strip() for x in norm(related).split(";") if x.strip()]:
        target, _label = parse_related_link_token(item)
        if target and target not in keep:
            continue
        kept.append(item)
    return ";".join(kept)


def greenfield_reset_row(
    row: dict[str, str],
    *,
    facts: dict,
    catalog: dict,
    keep: set[str],
    today: str,
) -> None:
    slug = norm(row.get("slug"))
    overrides = catalog.get("title_fixes") or {}
    headings_map = catalog.get("section_headings") or {}

    if slug in overrides:
        row["title"] = overrides[slug]
        short = overrides[slug].split("【")[0].strip() or overrides[slug]
        row["meta_description"] = (
            f"{short}について、公式要項を起点に整理します。"
            f"本試験は全{facts['exam_format']['question_count']}問·"
            f"{facts['exam_format']['total_points']}点満点です。"
        )

    anchor = lead_anchor(facts)
    if anchor:
        row["lead"] = anchor + " 本記事は greenfield 執筆待ちのたたき台です。本文は順次差し替えます。"

    if slug in headings_map:
        apply_headings(row, headings_map[slug])
    else:
        for i in range(1, 8):
            row[f"section_{i}_heading"] = f"本文セクション{i}（greenfield 執筆待ち）"

    for i in range(1, 8):
        row[f"section_{i}_body"] = placeholder_body(facts)

    for i in range(1, 4):
        fmt = facts.get("exam_format") or {}
        org = norm(facts.get("organizer"))
        if i == 1:
            per_range = fmt.get("pass_per_range_percent")
            if per_range not in (None, ""):
                pass_note = f"各科目{per_range}％足切り"
            else:
                note = norm(facts.get("pass_criteria_note") or "総合得点のみ")
                if note.startswith("合否は"):
                    note = note[3:].lstrip("、").strip()
                pass_note = note
            row["faq_1_question"] = "この記事はいつ本番の内容に差し替わりますか？"
            row["faq_1_answer"] = (
                "greenfield 執筆プログラムの優先順（write_priority）に沿って順次公開します。"
                f"試験形式は二種{fmt.get('question_count')}問·{fmt.get('total_points')}点満点·"
                f"{pass_note}を正本とし、{org}の公式要項で都度確認します。"
            )
        else:
            row[f"faq_{i}_question"] = ""
            row[f"faq_{i}_answer"] = ""

    row["action_items"] = ""
    row["key_points"] = ""
    title_for_intent = overrides.get(slug) or norm(row.get("title"))
    short_title = title_for_intent.split("【")[0].strip() or title_for_intent
    row["user_intent"] = (
        f"本記事を読むと、{short_title}の確認ポイントと次の行動が分かります。"
        "（greenfield 執筆待ち·本文は順次差し替え）"
    )

    row["content_status"] = "published"
    row["revision_note"] = f"{today}: greenfield執筆待ち（旧稿破棄·試験ファクト正本で新規執筆）"
    row["fact_checked_at"] = today
    row["related_links"] = strip_related_to_keep(norm(row.get("related_links")), keep)
    note = norm(row.get("original_note"))
    tag = "greenfield_reset"
    row["original_note"] = f"{note};{tag}".strip(";") if note else tag


def run_init(
    root: Path,
    *,
    dry_run: bool,
    do_retire: bool,
    force: bool,
) -> int:
    csv_path = root / "data" / "guide_articles.csv"
    cand_path = root / "data" / "guide_seo_candidates.csv"
    if not cand_path.is_file():
        cand_path = ROOT / "sites" / root.name / "guide-seo-candidates.csv"
    if not csv_path.is_file():
        print(f"Missing {csv_path}", file=sys.stderr)
        return 1
    if not cand_path.is_file():
        print(f"Missing candidates CSV ({cand_path})", file=sys.stderr)
        return 1

    facts = load_exam_facts(root)
    catalog = load_catalog(root)
    candidates = load_candidates(cand_path)
    keep = build_keep_set(candidates, catalog)

    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    published_slugs = {norm(r["slug"]) for r in rows if is_published_guide(r)}
    retire_map = build_retire_map(candidates, keep, published_slugs)

    # 候補に無い公開記事は退役（安全側）
    for slug in sorted(published_slugs - keep - set(retire_map)):
        retire_map[slug] = redirect_target(
            slug, published_slugs=published_slugs, retiring=set(keep) | set(retire_map)
        )

    today = date.today().isoformat()
    stats = {"keep_reset": 0, "already_draft": 0, "retire": len(retire_map)}

    for row in rows:
        slug = norm(row.get("slug"))
        if slug in keep:
            rev = norm(row.get("revision_note"))
            if not force and "greenfield執筆待ち" in rev and is_published_guide(row):
                stats["already_draft"] += 1
                continue
            if not dry_run:
                greenfield_reset_row(row, facts=facts, catalog=catalog, keep=keep, today=today)
            stats["keep_reset"] += 1

    print(f"site: {root.name}")
    print(f"keep (draft reset): {len(keep)} slugs")
    print(f"  reset rows: {stats['keep_reset']}  already greenfield draft: {stats['already_draft']}")
    print(f"retire/merge: {len(retire_map)} slugs")
    if catalog.get("write_priority"):
        print("write priority:", ", ".join(catalog["write_priority"][:8]), "...")

    if dry_run:
        print("\n[dry-run] CSV / retire は未書き込み")
        for slug in sorted(retire_map)[:12]:
            print(f"  retire {slug} -> {retire_map[slug]}")
        if len(retire_map) > 12:
            print(f"  ... +{len(retire_map) - 12} more")
        return 0

    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    keep_path = root / "data" / "guide_seo_keep_slugs.txt"
    retire_path = root / "data" / "guide_seo_retire_slugs.txt"
    redirect_path = root / "data" / "guide_greenfield_retire_redirects.json"
    keep_path.write_text("\n".join(sorted(keep)) + "\n", encoding="utf-8")
    retire_path.write_text("\n".join(sorted(retire_map)) + "\n", encoding="utf-8")
    redirect_path.write_text(
        json.dumps({"updated": today, "redirects": retire_map}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote: {keep_path} ({len(keep)})")
    print(f"wrote: {retire_path} ({len(retire_map)})")
    print(f"wrote: {redirect_path}")

    if do_retire and retire_map:
        candidates_list = [
            (slug, "greenfield", target) for slug, target in sorted(retire_map.items())
        ]
        rstats = apply_retire(root, candidates_list, dry_run=False, phase=1)
        print(
            f"retired: archived={rstats.get('archived', rstats.get('removed', 0))} "
            f"related_patched={rstats['related_patched']}"
        )

    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="試験ガイド greenfield 初期化")
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--force", action="store_true", help="既に greenfield 済みの keep も再初期化")
    ap.add_argument("--retire", action="store_true", help="merge 記事を archived + 301 登録")
    args = ap.parse_args()
    if not args.apply and not args.dry_run:
        print("Specify --dry-run or --apply", file=sys.stderr)
        return 1
    return run_init(args.root.resolve(), dry_run=args.dry_run, do_retire=args.retire and args.apply, force=args.force)


if __name__ == "__main__":
    raise SystemExit(main())
