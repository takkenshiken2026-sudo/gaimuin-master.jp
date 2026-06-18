# 証外マスター（gaimuin-master）

## 本番

| 項目 | 値 |
|------|-----|
| サイトID | `gaimuin-master` |
| ブランド名 | 証外マスター |
| 試験名 | 証券外務員（一種・二種） |
| 公開 URL | https://gaimuin-master.jp（**取得・DNS 設定前** — CNAME / GitHub Pages カスタムドメインは取得後に有効化） |
| GitHub Pages（暫定） | https://takkenshiken2026-sudo.github.io/gaimuin-master/ |
| Git | https://github.com/takkenshiken2026-sudo/gaimuin-master |
| ローカル | `/Users/otedaiki/Projects/gaimuin-master` |

## デプロイ

| 項目 | 値 |
|------|-----|
| 方式 | GitHub Actions（[DEPLOY.md](../../docs/DEPLOY.md) 標準） |
| ワークフロー | `.github/workflows/deploy-pages.yml` |
| トリガー | `main` push / `workflow_dispatch` |
| GitHub 設定 | Settings → Pages → **Source: GitHub Actions** |
| ビルド | `python3 tools/build_all.py` → `public_site/` |

## 新規サイト初回セットアップ

2026-06-16: `exam-site-shell` からコピーして初期化。

```bash
cd ~/Projects/gaimuin-master
python3 tools/generate_brand_assets.py
python3 tools/apply_site_config.py
python3 tools/build_all.py
python3 tools/validate_site_integration.py
```

**ドメイン:** `gaimuin-master.jp`（`site-config.json` / ルート `CNAME` に記載済み）。レジストラ取得・DNS・GitHub Pages カスタムドメインは取得後に有効化してください。

## 同期（テンプレ root で実行）

```bash
cd ~/Projects/exam-site-shell
python3 tools/check_template_drift.py --target ~/Projects/gaimuin-master
python3 tools/sync_from_template.py --target ~/Projects/gaimuin-master --dry-run
python3 tools/sync_from_template.py --target ~/Projects/gaimuin-master --build
```

- 契約・検証: [docs/integration-checklist.md](../../docs/integration-checklist.md)
- 横断一覧: [docs/site-registry.md](../../docs/site-registry.md)

## サイト固有メモ

- 対象: **証券外務員一種・二種**（内部管理責任者は別サイト検討）
- `site-config.json` の `fields` は JSDA 公式テキストの大分類に合わせて 4 分野（商品・勧誘・金商法・その他法令/業務）
- 過去問 CSV・用語 300 件・ガイド 50 本以内はこれから拡充
- CBT 対応: マークシート形式（`extendedCorrectAnswers` は未使用）

## コンテンツ TODO

| 項目 | 目標 | 状態 |
|------|------|------|
| `glossary_terms.csv` | 300+ | **300件・v0済**／**編集合格 155/300**（expert batch1〜31 適用・フェーズ2進行中） |
| `guide_articles.csv` | 50以内 | **47本 published**（通常ガイド手書き完了）／アフィリエイト3本は **draft** |
| 実践演習（二種） | 70問（本番相当）→拡充490 | **490問ローカル完了**（〇×320＋五肢170）／本番150問／[作問手順](practice-tier2-workflow.md) |
| 過去問 | 年度別 | 非表示（hidePast） |
| アフィリエイト | ~10 本 | **未着手**（雛形3 slug のみ・brief は textbooks 雛形のみ） |

## 試験形式（公式・2025-06 確認）

| 区分 | 問数 | 時間 |
|------|------|------|
| 二種 | 70問（〇×50＋五肢20） | 2時間 |
| 一種 | 100問（〇×70＋五肢30） | 2時間40分 |

正本: https://www.jsda.or.jp/gaimuin/shiken.html

## 最終同期

- 日付: 2026-06-18
- 備考: 二種実践演習 Phase2 完了（490問・batch1〜49）。`build_all.py`・`audit_gaimuin_practice_explanations.py`（ERROR 0）通過済み。本番 push は未実施。
