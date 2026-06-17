#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""証外マスター: guide_articles.csv の title のみ一括設定（本文は後から）。

SEO 方針（docs/seo-article-guidelines.md）:
- 各タイトルに「証券外務員試験」または「外務員」を自然に含める
- 30〜45文字前後・検索意図ごとに差別化（カニバリ回避）
- title タグは「{title}｜証外マスター」で 60 字以内
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BRAND = "証外マスター"
EXAM_KW = ("証券外務員", "外務員")

# slug → 読者向けタイトル（50本・重複なし・SEO 見直し版）
GUIDE_TITLES: dict[str, str] = {
    # 試験概要
    "exam-overview": "証券外務員試験の概要と4分野の出題範囲",
    "official-info-sources": "証券外務員試験・公式情報の確認先と手順",
    "first-time-exam-guide": "証券外務員試験を初めて受ける人向けガイド",
    # 受験・申込
    "exam-eligibility": "証券外務員試験の受験資格の確認方法と要件",
    "exam-schedule": "証券外務員試験の日程・申込・合格発表",
    "exam-application-flow": "証券外務員試験の申込手順・必要書類と流れ",
    "exam-venue-and-region": "証券外務員試験・CBT会場の選び方と当日アクセス",
    "exemption-system": "証券外務員試験の免除制度の対象と確認手順",
    # 出題・形式
    "exam-format-overview": "証券外務員試験の出題形式と問題数の目安",
    "exam-scope-overview": "証券外務員試験の出題範囲と外務員必携の読み方",
    "cbt-computer-exam": "証券外務員試験のCBT形式と本番での攻略法",
    "weight-by-topic": "証券外務員試験・4分野の配点と勉強の優先順位",
    # 合格・難易度
    "pass-rate": "証券外務員試験の合格率と難易度の目安",
    "pass-score": "証券外務員試験の合格点・合格基準の確認",
    "difficulty-for-beginners": "証券外務員試験は初心者・未経験でも受かるか",
    "pass-rate-how-to-read": "証券外務員試験・合格率の数字の読み方",
    # 学習計画
    "study-plan": "証券外務員試験の勉強計画の立て方と週次の組み方",
    "study-plan-3months": "証券外務員試験の3か月勉強計画の立て方",
    "study-plan-working": "証券外務員試験・仕事と両立する勉強計画",
    "first-30-days-plan": "証券外務員試験・最初の30日でやること",
    # 独学対策
    "self-study-roadmap": "証券外務員試験の独学合格ロードマップ",
    "self-study-start": "証券外務員試験を独学で始めるときの準備と手順",
    "textbook-selection": "証券外務員試験のテキスト・外務員必携の選び方",
    "self-study-mistakes": "証券外務員試験・独学でよくある失敗と対策",
    "affiliate-textbooks-recommend": "証券外務員試験のおすすめテキスト比較",
    "affiliate-problem-books": "証券外務員試験のおすすめ問題集の選び方",
    # 過去問活用
    "past-question-strategy": "証券外務員試験の過去問・模試の使い方",
    "past-questions-by-year": "証券外務員試験・年度別過去問の進め方",
    "mock-exam-how-to": "証券外務員試験の模擬試験の使い方とタイミング",
    "timed-practice": "証券外務員試験・時間配分と制限時間演習",
    "past-questions-wrong-reasons": "証券外務員試験・過去問の誤答分析と復習",
    "affiliate-mock-exam-materials": "証券外務員試験のおすすめ模試・問題集",
    # 分野別対策（legacy slug → 証外4分野）
    "field-law-basics": "証券外務員試験・金融商品取引法の基礎対策",
    "field-law-past-question-focus": "証券外務員試験・金商法の過去問出題傾向",
    "field-rights-basics": "証券外務員試験・勧誘・販売規則の基礎対策",
    "field-rights-past-question-focus": "証券外務員試験・勧誘規則の過去問傾向",
    "field-limit-basics": "証券外務員試験・金融商品・サービスの基礎対策",
    "field-limit-past-question-focus": "証券外務員試験・商品分野の過去問出題傾向",
    # 用語ハブ活用法
    "glossary-how-to": "証券外務員試験・用語解説での知識整理",
    "glossary-study-method": "証券外務員試験の用語集の効率的な使い方",
    "confusing-terms": "証券外務員試験で混同しやすい用語の整理",
    # 復習・苦手克服
    "review-cycle-spaced": "証券外務員試験の間隔反復復習のやり方",
    "mistake-notebook": "証券外務員試験の誤答ノートの作り方と活用法",
    # 直前・当日
    "final-week-prep": "証券外務員試験・直前1週間の勉強法と見直し",
    "exam-day-flow": "証券外務員試験当日の流れと時間配分のコツ",
    "mental-prep-exam-day": "証券外務員試験・本番当日のメンタル対策",
    "final-day-checklist": "証券外務員試験・前日・当日の持ち物リスト",
    # 注意点・更新
    "exam-changes": "証券外務員試験の制度・出題範囲の変更点",
    "common-misconceptions": "証券外務員試験のよくある誤解と正しい理解",
    "after-pass-procedure": "証券外務員試験合格後の登録手続きの流れ",
}


def seo_audit(titles: dict[str, str]) -> list[str]:
    """タイトル辞書の SEO 簡易監査。"""
    warnings: list[str] = []
    seen: dict[str, str] = {}
    for slug, title in titles.items():
        if not any(kw in title for kw in EXAM_KW):
            warnings.append(f"{slug}: missing exam keyword in title")
        n = len(title)
        if n < 16:
            warnings.append(f"{slug}: title too short ({n} chars, min 16)")
        elif n > 48:
            warnings.append(f"{slug}: title long ({n} chars, aim 30-45)")
        tag_len = len(f"{title}｜{BRAND}")
        if tag_len > 60:
            warnings.append(f"{slug}: title tag {tag_len} chars (>60): {title}")
        if title in seen:
            warnings.append(f"duplicate title: {slug} and {seen[title]}")
        seen[title] = slug
    return warnings


def main() -> int:
    ap = argparse.ArgumentParser(description="証外ガイド記事タイトル一括設定")
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--audit-only", action="store_true")
    args = ap.parse_args()

    audit = seo_audit(GUIDE_TITLES)
    if audit:
        print("SEO audit warnings:")
        for msg in audit:
            print(f"  WARN {msg}")
    else:
        print("SEO audit: OK")

    if args.audit_only:
        return 1 if audit else 0

    root = args.root.resolve()
    csv_path = root / "data" / "guide_articles.csv"
    if not csv_path.is_file():
        print(f"missing {csv_path}", file=sys.stderr)
        return 1

    rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))
    if not rows:
        return 0
    fieldnames = list(rows[0].keys())
    slugs = {(r.get("slug") or "").strip() for r in rows}
    missing = sorted(slugs - set(GUIDE_TITLES))
    extra = sorted(set(GUIDE_TITLES) - slugs)
    if missing:
        print("WARN: CSV slugs without title mapping:", ", ".join(missing), file=sys.stderr)
    if extra:
        print("WARN: title map slugs not in CSV:", ", ".join(extra), file=sys.stderr)

    changed = 0
    for row in rows:
        slug = (row.get("slug") or "").strip()
        if slug not in GUIDE_TITLES:
            continue
        new_title = GUIDE_TITLES[slug]
        if (row.get("title") or "").strip() != new_title:
            row["title"] = new_title
            changed += 1

    if changed and not args.dry_run:
        with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)

    print(f"apply_gaimuin_guide_titles: updated {changed} titles in {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
