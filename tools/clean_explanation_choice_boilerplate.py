#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""explanation_choices / explanation_correct から重複定型句を除去する。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STRIP_PATTERNS = [
    re.compile(r"。?「(?:正しいもの|誤っているもの|最も適切でないもの)」の正答（\d+）には当たりません"),
    re.compile(r"。?誤りです。「(?:正しいもの|誤っているもの|最も適切でないもの)」の正答（\d+）には当たりません"),
    re.compile(r"。?本問の正答（\d+）とは別の誤り肢です"),
    re.compile(
        r"。?「[^」]{4,}」は設問の趣旨に照らすと誤った記述ではなく、"
        r"本問で選ぶ正答肢とは別の論点として正しい整理です。"
    ),
    re.compile(r"（\d+）の[^。]+も誤りですが、本問「[^」]+」の正答は（\d+）です。"),
    re.compile(r"本問「[^」]+」の正答は（\d+）です。"),
]


def clean_text(text: str) -> str:
    out = text
    for pat in STRIP_PATTERNS:
        out = pat.sub("", out)
    out = re.sub(r"。{2,}", "。", out)
    out = re.sub(r"；+", ";", out)
    return out.strip(" 。;")


def clean_file(path: Path) -> int:
    raw = path.read_text(encoding="utf-8")
    count = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        inner = clean_text(m.group(1))
        if inner != m.group(1):
            count += 1
        return f'{m.group(0)[: m.start(1) - m.start(0)]}{inner}{m.group(0)[m.end(1) - m.start(0) :][:0]}'

    new = raw
    for key in ("explanation_choices", "explanation_correct"):
        pat = re.compile(rf'("{key}": ")([^"]*)(")', re.MULTILINE)

        def sub(m: re.Match[str]) -> str:
            nonlocal count
            inner = clean_text(m.group(2))
            if inner != m.group(2):
                count += 1
            escaped = inner.replace("\\", "\\\\").replace('"', '\\"')
            return f'{m.group(1)}{escaped}{m.group(3)}'

        new = pat.sub(sub, new)
    if new != raw:
        path.write_text(new, encoding="utf-8")
    return count


def main() -> None:
    targets: list[Path] = []
    if "--tier1" in sys.argv:
        targets.append(ROOT / "tools" / "gaimuin_practice_tier1_explanation_texts.py")
    if "--tier2" in sys.argv or not targets:
        targets.append(ROOT / "tools" / "gaimuin_practice_explanation_texts.py")

    total = 0
    for path in targets:
        if not path.is_file():
            print(f"skip (missing): {path.name}")
            continue
        n = clean_file(path)
        print(f"{path.name}: {n} field(s) cleaned")
        total += n
    print(f"total: {total}")


if __name__ == "__main__":
    main()
