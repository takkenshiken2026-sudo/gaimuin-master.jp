#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本文・FAQ 向けの軽量インライン markup（Markdown 風リンク）。"""

from __future__ import annotations

import html
import re

_MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_INLINE_TOKEN = re.compile(
    r"\[([^\]]+)\]\(([^)\s]+)\)|\*\*([^*\n]+?)\*\*"
)


def _link_html(label: str, url: str) -> str:
    if url.startswith("../") or url.startswith("/articles/"):
        return (
            f'<a class="related-link" href="{html.escape(url)}">{html.escape(label)}</a>'
        )
    return (
        f'<a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">'
        f"{html.escape(label)}</a>"
    )


def strip_md_bold(text: str) -> str:
    """JSON-LD 等プレーンテキスト向けに `**` を除去する。"""
    if not text or "**" not in text:
        return text
    cleaned = re.sub(r"\*\*([^*\n]+?)\*\*", r"\1", text)
    return cleaned.replace("**", "")


def render_inline_markup(text: str) -> str:
    """`[ラベル](URL)` と `**強調**` を HTML に変換する。"""
    if not text:
        return ""
    if "**" not in text and "[" not in text:
        return html.escape(text).replace("\n", "<br>")

    parts: list[str] = []
    last = 0
    for match in _INLINE_TOKEN.finditer(text):
        if match.start() > last:
            chunk = text[last : match.start()].replace("**", "")
            parts.append(html.escape(chunk))
        if match.group(3):
            parts.append(f"<strong>{html.escape(match.group(3))}</strong>")
        else:
            parts.append(_link_html(match.group(1), match.group(2)))
        last = match.end()
    tail = text[last:].replace("**", "")
    parts.append(html.escape(tail))
    return "".join(parts).replace("\n", "<br>")
