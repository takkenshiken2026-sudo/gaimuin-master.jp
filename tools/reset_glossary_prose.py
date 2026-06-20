#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用語詳細の執筆列を一括リセット（編集合格タグ除去・準備中スタブへ）。

全300語をゼロから書き直す前段として、本文・FAQ 等を最小スタブに差し替えます。
必ず data/backups/ に CSV バックアップを取ってから --confirm で実行してください。
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.editorial_quality import GLOSSARY_EXPERT, norm, split_semicolon  # noqa: E402
from tools.glossary_term_rules import check_glossary_row  # noqa: E402
from tools.build_glossary_pages import lookup_key  # noqa: E402
from tools.site_config import exam_name  # noqa: E402

GLOSSARY_CSV = ROOT / "data" / "glossary_terms.csv"
BACKUP_DIR = ROOT / "data" / "backups"

EXPERT_TAG = GLOSSARY_EXPERT["expert_tag"]
PREPARING_TAG = "準備中"

PROSE_COLUMNS: tuple[str, ...] = (
    "short_def",
    "definition",
    "explanation",
    "article_title",
    "article_lead",
    "term_detail_body",
    "exam_points",
    "common_mistakes",
    "memory_tip",
    "example_question",
    "example_answer",
    "faq_1_question",
    "faq_1_answer",
    "faq_2_question",
    "faq_2_answer",
    "faq_3_question",
    "faq_3_answer",
    "faq_4_question",
    "faq_4_answer",
)

DATE_COLUMNS: tuple[str, ...] = (
    "fact_checked_at",
    "last_reviewed_at",
    "source_checked_at",
)


def reset_tags(tags: str) -> str:
    kept = [t for t in split_semicolon(tags) if t != EXPERT_TAG]
    if PREPARING_TAG not in kept:
        kept.append(PREPARING_TAG)
    return ";".join(kept)


def stub_prose(term: str, *, exam: str, category: str) -> dict[str, str]:
    """validate_csv ERROR を避ける最小スタブ（雛形マーカーなし）。"""
    title = f"{term}とは｜{exam}の意味と論点"
    return {
        "short_def": f"{term}は{exam}で問われる{category}分野の用語です。",
        "definition": (
            f"{term}は{exam}の学習範囲で押さえる概念です。"
            f"定義、数値、主体の違いを公式情報に沿って整理する必要があります。"
            f"詳細解説は順次公開予定です。"
        ),
        "explanation": (
            f"{term}が出る四択では、定義の言い換え、似た用語との混同、"
            f"例外条件の有無が問われやすいです。"
            f"たとえば二種は70問120分·300点満点·210点合格、"
            f"一種は100問160分·440点満点·308点合格が前提になります。"
        ),
        "article_title": title,
        "article_lead": (
            f"{exam}の用語「{term}」は{category}分野で頻出です。"
            f"本記事は現在、定義·試験論点·混同注意を専門家監修の下で執筆中です。"
            f"公開まで関連用語と演習で予習してください。"
        ),
        "term_detail_body": (
            f"{term}の詳細解説は現在作成中です。"
            f"{exam}では4分野の選択肢の中で、定義·数値·主体の区別が定番です。"
            f"日本証券業協会の公式要項と演習解説をあわせて確認してください。\n\n"
            f"公開前のページでは要点のみ表示しています。"
            f"制度や数値は年度で変わるため、受験前は必ず一次情報を再確認してください。"
            f"{term}は関連用語3語とセットで覚えると得点が安定しやすくなります。"
        ),
        "exam_points": (
            f"{term}の定義と条件を声に出して確認する;"
            f"似た用語との違いを2列表で整理する;"
            f"演習10問で誤答理由を4分類する"
        ),
        "common_mistakes": (
            f"{term}では、定義の言い換え肢や似た用語との混同が典型です。"
            f"たとえば主体（誰が）と時点（いつ）を読み飛ばすと誤答しやすくなります。"
        ),
        "memory_tip": (
            f"{term}は関連用語3語と1行メモでセット暗記。"
            f"演習でタグ付け復習。"
        ),
        "example_question": f"{term}に関する次の記述として、正しいものはどれか。",
        "example_answer": "×",
        "faq_1_question": f"{term}とは何ですか？",
        "faq_1_answer": (
            f"{term}は{exam}の{category}分野で扱う概念です。"
            f"詳細な定義と具体例は記事執筆完了後に公開します。"
            f"たとえば二種70問120分·210点合格、一種100問160分·308点合格の"
            f"形式理解とあわせて学習してください。"
        ),
        "faq_2_question": f"{term}でよくある誤解は？",
        "faq_2_answer": (
            f"似た用語との混同、定義の言い換えへの引っかかり、"
            f"数値·期限の読み飛ばしが{term}周辺の典型です。"
            f"演習では「混同」「数値」「主体」の3タグを付けて誤答を分類すると"
            f"弱点が見えやすくなります。公式要項の該当箇所も併せて確認してください。"
        ),
        "faq_3_question": f"{term}は試験でどう問われますか？",
        "faq_3_answer": (
            f"四択では{term}の定義確認、例外の有無、関連制度との組み合わせが"
            f"出題されやすいです。たとえば「{term}は常に〜である」型の"
            f"断定肢は条件の見落としが引っかけになります。"
            f"公式要項で最新の制度を確認してから演習に入ってください。"
        ),
        "faq_4_question": f"{term}を学んだあとに何を確認しますか？",
        "faq_4_answer": (
            f"関連用語3語を白紙に書き、{term}との違いを1行ずつメモしてください。"
            f"次に演習10問で{term}タグ付きの問題を解き、"
            f"誤答は必携該当章へ戻る流れを1周固定すると定着します。"
            f"記事公開後は本ページの詳細解説で復習してください。"
        ),
    }


def backup_csv(csv_path: Path) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = date.today().isoformat()
    dest = BACKUP_DIR / f"glossary_terms_pre_reset_{stamp}.csv"
    if dest.is_file():
        n = 2
        while dest.is_file():
            dest = BACKUP_DIR / f"glossary_terms_pre_reset_{stamp}_{n}.csv"
            n += 1
    shutil.copy2(csv_path, dest)
    return dest


def reset_row(row: dict[str, str], *, exam: str) -> dict[str, str]:
    term = norm(row.get("term"))
    category = norm(row.get("category")) or "試験範囲"
    out = dict(row)
    out.update(stub_prose(term, exam=exam, category=category))
    out["tags"] = reset_tags(norm(row.get("tags")))
    for col in DATE_COLUMNS:
        out[col] = ""
    return out


def validate_rows(rows: list[dict[str, str]]) -> list[str]:
    term_lookup = {lookup_key(norm(r.get("term"))): norm(r.get("term")) for r in rows}
    errors: list[str] = []
    for row in rows:
        term = norm(row.get("term"))
        for issue in check_glossary_row(row, term_lookup=term_lookup):
            if issue.level == "ERROR":
                errors.append(f"{term}: {issue.message}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="用語詳細執筆列の一括リセット")
    ap.add_argument("--dry-run", action="store_true", help="変更内容のみ表示")
    ap.add_argument(
        "--confirm",
        action="store_true",
        help="バックアップ後に glossary_terms.csv を上書き",
    )
    args = ap.parse_args()

    if not GLOSSARY_CSV.is_file():
        print(f"missing {GLOSSARY_CSV}", file=sys.stderr)
        return 1
    if not args.dry_run and not args.confirm:
        print("Specify --dry-run or --confirm", file=sys.stderr)
        return 1

    exam = exam_name()
    with GLOSSARY_CSV.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    before_expert = sum(1 for r in rows if EXPERT_TAG in split_semicolon(norm(r.get("tags"))))
    reset_rows = [reset_row(r, exam=exam) for r in rows]
    after_expert = sum(1 for r in reset_rows if EXPERT_TAG in split_semicolon(norm(r.get("tags"))))
    after_preparing = sum(1 for r in reset_rows if PREPARING_TAG in split_semicolon(norm(r.get("tags"))))

    print(f"terms: {len(rows)}")
    print(f"  編集合格 before: {before_expert} → after: {after_expert}")
    print(f"  準備中 after: {after_preparing}")

    val_errors = validate_rows(reset_rows)
    if val_errors:
        print("validate_csv preview failed:", file=sys.stderr)
        for msg in val_errors[:15]:
            print(f"  {msg}", file=sys.stderr)
        return 1

    if args.dry_run:
        print("dry-run OK (no file written)")
        return 0

    backup_path = backup_csv(GLOSSARY_CSV)
    print(f"backup: {backup_path}")

    with GLOSSARY_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(reset_rows)

    print(f"reset {len(reset_rows)} terms → {GLOSSARY_CSV}")
    print("next: python3 tools/build_all.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
