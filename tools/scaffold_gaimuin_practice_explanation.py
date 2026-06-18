#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gaimuin_practice_explanation_texts.py に追記する EXPLANATIONS 雛形を出力する。"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BATCH_DIR = ROOT / "tools" / "batches"


def tier_paths(tier: str) -> tuple[Path, str]:
    if tier == "1":
        return ROOT / "data" / "practice_tier1_blueprint.csv", "gaimuin_practice_tier1_batch"
    return ROOT / "data" / "practice_tier2_blueprint.csv", "gaimuin_practice_tier2_batch"


def load_batch_questions(batch_num: int, *, tier: str = "2") -> list[dict[str, str]]:
    _, batch_prefix = tier_paths(tier)
    path = BATCH_DIR / f"{batch_prefix}{batch_num}.py"
    if not path.is_file():
        raise SystemExit(f"batch ファイルがありません: {path}")
    spec = importlib.util.spec_from_file_location("batch", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod.QUESTIONS


def blueprint_map(*, tier: str = "2") -> dict[str, dict[str, str]]:
    blueprint, _ = tier_paths(tier)
    if not blueprint.is_file():
        return {}
    with blueprint.open(encoding="utf-8-sig", newline="") as f:
        return {row["question_no"]: row for row in csv.DictReader(f)}


def scaffold_entry(q: dict[str, str], bp: dict[str, str]) -> str:
    qno = q["question_no"]
    qtype = q.get("type", bp.get(qno, {}).get("format", "marubatsu"))
    term = bp.get(qno, {}).get("source_term", "")
    stem = q.get("stem", "（問題文）")
    correct = q.get("correct", "?")

    if qtype == "marubatsu":
        choices_hint = ""
    else:
        choices_hint = (
            '        "explanation_choices": "'
            "1:（肢1が正答でない理由）;2:…;（正答肢は除く）"
            '",\n'
        )

    return f'''    "{qno}": {{
        "explanation": "（結論1〜2文。{term}）",
        "explanation_summary": "（15〜30字）",
        "explanation_correct": "（正答={correct} の理由。設問: {stem[:40]}…）",
{choices_hint}        "explanation_point": "（復習の具体アクション。他問と被らないこと）",
    }},'''


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--batch", type=int, help="batch 番号（例: 6）")
    ap.add_argument("--question-nos", help="カンマ区切り問番（例: 51,52,53）")
    ap.add_argument(
        "--tier1",
        action="store_true",
        help="一種（question_no 1001〜、tier1 blueprint / batch）",
    )
    ap.add_argument(
        "--tier2",
        action="store_true",
        help="二種（既定）",
    )
    args = ap.parse_args()

    if not args.batch and not args.question_nos:
        ap.error("--batch または --question-nos を指定してください")

    tier = "1" if args.tier1 else "2"
    bp = blueprint_map(tier=tier)
    questions: list[dict[str, str]] = []

    if args.batch:
        questions = load_batch_questions(args.batch, tier=tier)
    elif args.question_nos:
        want = {x.strip() for x in args.question_nos.split(",") if x.strip()}
        for n in range(1, 100):
            try:
                for q in load_batch_questions(n, tier=tier):
                    if q["question_no"] in want:
                        questions.append(q)
            except SystemExit:
                break
        missing = want - {q["question_no"] for q in questions}
        if missing:
            for qno in sorted(missing, key=int):
                row = bp.get(qno, {})
                questions.append(
                    {
                        "question_no": qno,
                        "type": row.get("format", "single"),
                        "stem": f"（batch未作成・用語: {row.get('source_term', '')}）",
                        "correct": "?",
                    }
                )

    mod = "gaimuin_practice_tier1_explanation_texts" if tier == "1" else "gaimuin_practice_explanation_texts"
    print(f"# {mod}.py の EXPLANATIONS に追記")
    print("# 手書きで（）を埋めてから patch → audit → apply してください\n")
    for q in sorted(questions, key=lambda x: int(x["question_no"])):
        print(scaffold_entry(q, bp))
        print()


if __name__ == "__main__":
    main()
