#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-command build for exam-site projects (template and standard production sites)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def ensure_python_deps() -> None:
    """GitHub Actions 等で PyYAML が未導入のとき build を止めない。"""
    py = sys.executable
    try:
        import yaml  # noqa: F401
    except ImportError:
        subprocess.run([py, "-m", "pip", "install", "--quiet", "pyyaml"], check=True)


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def maybe_run_exam_schedule_page(py: str) -> None:
    script = ROOT / "tools" / "build_exam_schedule_page.py"
    schedule_csv = ROOT / "data" / "exam_schedule_otsu4.csv"
    if script.is_file() and schedule_csv.is_file():
        run([py, str(script)])


def repair_spa_index_head() -> None:
    """用語ビルド等が index.html の SEO マーカーを壊した場合の保険。"""
    index = ROOT / "index.html"
    if not index.is_file():
        return
    from tools.brand_assets import inject_brand_head
    from tools.index_seo_head import inject_index_seo_head

    text = index.read_text(encoding="utf-8")
    text = inject_index_seo_head(text)
    text = inject_brand_head(text, Path("index.html"), site_root=ROOT)
    index.write_text(text, encoding="utf-8")


def main() -> int:
    ensure_python_deps()
    py = sys.executable
    run([py, "tools/validate_csv.py"])
    run([py, "tools/validate_guide_exam_facts.py", "--skip-greenfield-pending"])
    run([py, "tools/validate_guide_law_facts.py", "--skip-greenfield-pending"])
    run([py, "tools/validate_question_explanations.py"])
    run([py, "tools/generate_brand_assets.py"])
    run([py, "tools/apply_site_config.py"])
    run([py, "tools/csv_to_exam_site_past_js.py"])
    run([py, "tools/csv_to_exam_site_ichimondou_js.py"])
    run([py, "tools/build_past_question_pages.py"])
    run([py, "tools/build_practice_ichimon_pages.py"])
    run([py, "tools/build_article_pages.py"])
    run([py, "tools/build_guide_retire_redirects.py"])
    maybe_run_exam_schedule_page(py)
    run([py, "tools/build_glossary_pages.py"])
    run([py, "tools/build_hub_retire_redirects.py"])
    run([py, "tools/build_sitemap.py"])
    run([py, "tools/validate_sitemap.py"])
    run([py, "tools/validate_generated_seo.py"])
    repair_spa_index_head()
    run([py, "tools/validate_site_integration.py"])
    run([py, "tools/validate_guide_index_picks.py"])
    run([py, "tools/validate_internal_links.py"])
    run([py, "tools/validate_public_content.py"])
    run(["bash", "tools/prepare_public_site.sh"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
