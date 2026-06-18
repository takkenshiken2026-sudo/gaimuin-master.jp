#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch ファイルの解説列を gaimuin_practice_explanation_texts.py の内容で上書きする。"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gaimuin_practice_explanation_texts import EXPLANATIONS  # noqa: E402

BATCH_DIR = ROOT / "tools" / "batches"
BATCH_GLOB = "gaimuin_practice_tier2_batch*.py"


def load_batch(path: Path):
    spec = importlib.util.spec_from_file_location("batch", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod.QUESTIONS


def patch_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    count = 0
    for qno, fields in EXPLANATIONS.items():
        if f'"question_no": "{qno}"' not in text:
            continue
        block_start = text.index(f'"question_no": "{qno}"')
        next_match = re.search(r'\n    \{\n        "question_no":', text[block_start + 1 :])
        block_end = block_start + 1 + next_match.start() if next_match else len(text)
        block = text[block_start:block_end]
        for key, value in fields.items():
            pattern = rf'("{key}": )"[^"]*(?:"[^"]*"[^"]*)*"'
            # simpler: replace line by line within block
            line_pat = rf'^        "{key}": ".*",$'
            new_line = f'        "{key}": "{value}",'
            new_block, n = re.subn(line_pat, new_line, block, count=1, flags=re.MULTILINE)
            if n:
                block = new_block
        if block != text[block_start:block_end]:
            text = text[:block_start] + block + text[block_end:]
            count += 1
    path.write_text(text, encoding="utf-8")
    return count


def main() -> None:
    total = 0
    for path in sorted(BATCH_DIR.glob(BATCH_GLOB)):
        n = patch_file(path)
        print(f"{path.name}: {n} questions patched")
        total += n
    print(f"total: {total} questions")


if __name__ == "__main__":
    main()
