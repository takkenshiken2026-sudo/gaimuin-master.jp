#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""証外マスター実践演習の解説品質監査（オリジナル解説ワークフロー用）。"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gaimuin_practice_explanation_texts import EXPLANATIONS  # noqa: E402
from tools.correct_answer_format import collect_choice_texts  # noqa: E402
from tools.q_explanation import (  # noqa: E402
    _is_generic_wrong_note,
    _is_substantive_choice_note,
    norm,
    parse_explanation_choices,
    question_ask_mode,
)

PRACTICE_CSV = ROOT / "data" / "practice_questions.csv"
BATCH_GLOB = "gaimuin_practice_tier2_batch*.py"

REQUIRED_KEYS = (
    "explanation",
    "explanation_summary",
    "explanation_correct",
    "explanation_point",
)

REQUIRED_KEYS_WITH_CHOICES = REQUIRED_KEYS + ("explanation_choices",)

FORBIDDEN_BODY_PHRASES = (
    "記述は正しいです",
    "記述は誤りです",
    "記述は誤った内容です",
    "設問の求め方と照らすと正答になりません",
    "基準と照らすと正答になりません",
    "定番の誤答",
)

THIN_CHOICE_MIN = 48


def _error(msg: str) -> None:
    print(f"[ERROR] {msg}")


def _warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def _wrong_choice_indices(row: dict) -> list[int]:
    correct_raw = norm(row.get("correct"))
    if not correct_raw.isdigit():
        return []
    correct = int(correct_raw)
    opts = collect_choice_texts(row)
    return [i for i in range(1, len(opts) + 1) if i != correct]


def _row_for_audit(row: dict | None) -> dict | None:
    """CSV 行が実践演習の現行形式と合うときだけ構造チェックに使う。"""
    if not row:
        return None
    qtype = norm(row.get("type"))
    opts = collect_choice_texts(row)
    if qtype == "marubatsu" and len(opts) == 2:
        return row
    if qtype == "single" and len(opts) >= 4:
        return row
    return None



def audit_explanation_fields(
    qno: str,
    fields: dict[str, str],
    *,
    row: dict | None = None,
) -> tuple[int, int]:
    errs = warns = 0
    label = f"EXPLANATIONS[{qno}]"

    if row:
        row = _row_for_audit(row)
    qtype = norm(row.get("type")) if row else ""
    is_marubatsu = qtype == "marubatsu"
    required = REQUIRED_KEYS if is_marubatsu else REQUIRED_KEYS_WITH_CHOICES

    for key in required:
        if not norm(fields.get(key)):
            _error(f"{label}: {key} が未入力")
            errs += 1

    for key in ("explanation", "explanation_summary", "explanation_correct", "explanation_point"):
        text = norm(fields.get(key))
        for phrase in FORBIDDEN_BODY_PHRASES:
            if phrase in text:
                _error(f"{label}.{key}: 禁止定型句「{phrase}」")
                errs += 1

    if is_marubatsu:
        return errs, warns

    choices_raw = norm(fields.get("explanation_choices"))
    parsed = parse_explanation_choices(choices_raw)
    if not parsed:
        _error(f"{label}: explanation_choices が空またはパース不可")
        return errs + 1, warns

    if row:
        wrong = _wrong_choice_indices(row)
        missing = [i for i in wrong if i not in parsed]
        extra = [i for i in parsed if i not in wrong]
        if missing:
            _error(f"{label}: 誤肢 {missing} の explanation_choices が未記入")
            errs += 1
        if extra:
            _error(f"{label}: 正答肢 {extra} を explanation_choices に含めない")
            errs += 1

    for num, note in parsed.items():
        if len(note) < THIN_CHOICE_MIN:
            _error(f"{label}: （{num}）の理由が短すぎます（{len(note)}字）→ 自動補完されます")
            errs += 1
        elif not _is_substantive_choice_note(note):
            _error(f"{label}: （{num}）の理由が薄いです → 自動補完されます")
            errs += 1
        if _is_generic_wrong_note(note):
            _error(f"{label}: （{num}）が汎用テンプレ相当です")
            errs += 1

    if row:
        stem = norm(row.get("stem"))
        if "最も適切でない" in stem:
            for num, note in parsed.items():
                if num == int(row.get("correct") or 0):
                    continue
                if "最も適切でない" not in note and "正答" not in note and "当たりません" not in note:
                    _warn(f"{label}: （{num}）に「最も適切でない」形式の言及が弱い")

    return errs, warns


def audit_csv_sync() -> tuple[int, int]:
    """正本と CSV の列内容が一致しているか（patch / apply 漏れ検出）。"""
    if not PRACTICE_CSV.is_file():
        _warn(f"{PRACTICE_CSV.name} がありません")
        return 0, 1
    warns = 0
    with PRACTICE_CSV.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for idx, row in enumerate(rows, start=2):
        qno = norm(row.get("question_no"))
        if not qno or norm(row.get("is_invalidated")).upper() == "TRUE":
            continue
        if qno not in EXPLANATIONS:
            _warn(f"{PRACTICE_CSV.name}:{idx} q{qno} が EXPLANATIONS に未登録")
            warns += 1
            continue
        fields = EXPLANATIONS[qno]
        qtype = norm(row.get("type"))
        sync_keys = REQUIRED_KEYS if qtype == "marubatsu" else REQUIRED_KEYS_WITH_CHOICES
        for key in sync_keys:
            if norm(row.get(key)) != norm(fields.get(key)):
                _warn(f"{PRACTICE_CSV.name}:{idx} q{qno}: {key} が正本と CSV で不一致（patch 未反映?）")
                warns += 1
    return 0, warns


def audit_orphan_explanations(csv_qnos: set[str]) -> tuple[int, int]:
    errs = warns = 0
    for qno in EXPLANATIONS:
        if qno not in csv_qnos:
            _warn(f"EXPLANATIONS[{qno}] が practice_questions.csv に無い（未適用?）")
            warns += 1
    return errs, warns


def audit_duplicate_points() -> tuple[int, int]:
    warns = 0
    seen: dict[str, list[str]] = {}
    for qno, fields in EXPLANATIONS.items():
        pt = norm(fields.get("explanation_point"))
        if pt:
            seen.setdefault(pt, []).append(qno)
    for pt, qnos in seen.items():
        if len(qnos) >= 3:
            _warn(f"explanation_point が {len(qnos)} 問で同一: {', '.join(qnos)}")
            warns += 1
    return 0, warns


def main() -> int:
    total_err = total_warn = 0

    csv_qnos: set[str] = set()
    if PRACTICE_CSV.is_file():
        with PRACTICE_CSV.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                qno = norm(row.get("question_no"))
                if qno and norm(row.get("is_invalidated")).upper() != "TRUE":
                    csv_qnos.add(qno)

    for qno, fields in sorted(EXPLANATIONS.items(), key=lambda x: int(x[0])):
        row = None
        if PRACTICE_CSV.is_file():
            with PRACTICE_CSV.open(encoding="utf-8-sig", newline="") as f:
                for r in csv.DictReader(f):
                    if norm(r.get("question_no")) == qno:
                        row = r
                        break
        e, w = audit_explanation_fields(qno, fields, row=row)
        total_err += e
        total_warn += w

    e, w = audit_orphan_explanations(csv_qnos)
    total_err += e
    total_warn += w

    e, w = audit_duplicate_points()
    total_err += e
    total_warn += w

    e, w = audit_csv_sync()
    total_err += e
    total_warn += w

    print(
        f"gaimuin practice explanation audit: {total_err} error(s), {total_warn} warning(s)"
    )
    return 1 if total_err else 0


if __name__ == "__main__":
    raise SystemExit(main())
