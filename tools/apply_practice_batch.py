#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""実践演習 batch（QUESTIONS リスト）を data/practice_questions.csv にマージする。"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_COLUMNS = [
    "question_no",
    "type",
    "category",
    "tags",
    "stem",
    "preamble",
    "statement_a",
    "statement_b",
    "statement_c",
    "statement_d",
    "choice_1",
    "choice_2",
    "choice_3",
    "choice_4",
    "choice_5",
    "correct",
    "explanation",
    "explanation_summary",
    "explanation_correct",
    "explanation_choices",
    "explanation_point",
    "is_invalidated",
]


def load_batch_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("practice_batch", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "QUESTIONS"):
        raise ValueError(f"{path} must define QUESTIONS list")
    return mod


def norm(value: object) -> str:
    return str(value or "").strip()


def truthy(value: object) -> bool:
    return norm(value).upper() in {"TRUE", "1", "YES"}


def merge_fieldnames(existing: list[str], rows: list[dict[str, str]]) -> list[str]:
    out = list(existing)
    for row in rows:
        for key in row:
            if key not in out:
                out.append(key)
    for col in DEFAULT_COLUMNS:
        if col not in out:
            out.append(col)
    return out


def apply_questions(
    csv_path: Path,
    questions: list[dict[str, str]],
    *,
    drop_invalidated: bool = True,
    dry_run: bool = False,
) -> tuple[int, int]:
    if not csv_path.is_file():
        base_rows: list[dict[str, str]] = []
        fieldnames = list(DEFAULT_COLUMNS)
    else:
        with csv_path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or DEFAULT_COLUMNS)
            base_rows = [dict(row) for row in reader]

    if drop_invalidated:
        kept = [r for r in base_rows if not truthy(r.get("is_invalidated"))]
        dropped = len(base_rows) - len(kept)
        base_rows = kept
    else:
        dropped = 0

    by_no: dict[int, dict[str, str]] = {}
    for row in base_rows:
        raw = norm(row.get("question_no"))
        if not raw:
            continue
        by_no[int(raw)] = row

    patched = 0
    for q in questions:
        qno = int(q["question_no"])
        row = {col: norm(q.get(col)) for col in merge_fieldnames(fieldnames, [q])}
        row["question_no"] = str(qno)
        if not row.get("is_invalidated"):
            row["is_invalidated"] = ""
        by_no[qno] = row
        patched += 1

    merged = [by_no[k] for k in sorted(by_no)]
    fieldnames = merge_fieldnames(fieldnames, merged)

    if dry_run:
        return patched, dropped

    if csv_path.is_file():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = csv_path.with_suffix(f".csv.bak-{stamp}")
        shutil.copy2(csv_path, backup)
        print(f"  バックアップ: {backup.name}")

    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(merged)

    return patched, dropped


def main() -> int:
    ap = argparse.ArgumentParser(description="実践演習 batch を practice_questions.csv に適用")
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--batch", type=Path, required=True, help="QUESTIONS を定義した .py")
    ap.add_argument("--keep-invalidated", action="store_true", help="is_invalidated 行を残す")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    csv_path = args.root.resolve() / "data" / "practice_questions.csv"
    mod = load_batch_module(args.batch.resolve())
    questions = getattr(mod, "QUESTIONS")
    if not isinstance(questions, list) or not questions:
        print("QUESTIONS が空です。", file=sys.stderr)
        return 1

    patched, dropped = apply_questions(
        csv_path,
        questions,
        drop_invalidated=not args.keep_invalidated,
        dry_run=args.dry_run,
    )
    mode = "would apply" if args.dry_run else "applied"
    print(f"{mode} {patched} questions → {csv_path}")
    if dropped:
        print(f"  dropped invalidated rows: {dropped}")
    print("続けて: python3 tools/validate_csv.py && python3 tools/build_all.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
