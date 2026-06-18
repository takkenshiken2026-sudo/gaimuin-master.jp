# 試験ガイド：ゼロから執筆（greenfield）

**目的:** 旧稿を使わず、**1記事ずつ**本文をすべて新規執筆する。リライト batch（`*_rewrite_batch*.py` / `tools/rewrites/`）は使わない。

**前提:** [guide-portfolio-rewrite-workflow.md](./guide-portfolio-rewrite-workflow.md) のフェーズ0〜1（50本整理・退役）と `init_guide_greenfield.py` による旧稿クリアが済んでいること。

**品質ルーブリック:** 本文の書き方は引き続き [guide-expert-rewrite-program.md](./guide-expert-rewrite-program.md) §3（180字·表·FAQ·具体アンカー）。違いは「旧 CSV / 旧 rewrites をコピーしない」ことだけ。

---

## 正本ファイル（サイト別）

| ファイル | 役割 |
|----------|------|
| `sites/<site-id>/guide_exam_facts.json` | 試験形式の正本（問数·配点·合格基準·禁止句） |
| `sites/<site-id>/guide_greenfield_catalog.json` | タイトル修正·見出し案·`write_priority` |
| `data/guide_seo_keep_slugs.txt` | 残す slug 一覧（init が出力） |
| `data/guide_articles.csv` | 公開正本（`revision_note: greenfield執筆待ち` = 未執筆） |
| `tools/greenfield/<site-id>/<slug>.py` | **1記事＝1ファイル**の執筆 batch |

---

## フェーズ A：初期化（1回だけ）

```bash
cd ~/Projects/exam-site-shell   # または本番サイト root

python3 tools/init_guide_greenfield.py --root ~/Projects/<site> --dry-run
python3 tools/init_guide_greenfield.py --root ~/Projects/<site> --apply --retire
python3 tools/build_all.py
```

- keep 記事は本文がプレースホルダーになり `greenfield執筆待ち` になる
- merge 記事は archived + 301

---

## フェーズ B：1記事ずつ執筆（繰り返し）

### 1. 次に書く slug を決める

```bash
python3 tools/scaffold_guide_greenfield_batch.py --root ~/Projects/<site> --list-pending
# または write_priority の先頭
python3 tools/scaffold_guide_greenfield_batch.py --root ~/Projects/<site> --next
```

### 2. 雛形 batch を生成（1 slug のみ）

```bash
python3 tools/scaffold_guide_greenfield_batch.py \
  --root ~/Projects/eisei1shu-master \
  --slug exam-format-overview
```

→ `tools/greenfield/<site-id>/exam-format-overview.py` ができる（`section_*_body` は空）。

### 3. 本文を**すべて**手で書く

- **禁止:** `tools/rewrites/<slug>.py` や旧 `*_rewrite_batch*.py` からのコピペ
- **必須:** `guide_exam_facts.json` の数値と一致（100問系などサイト誤表記を入れない）
- 各節 180字以上·パイプ表1つ以上·FAQ3·`related_links` 内部3件
- `例えば/たとえば` は記事全体で最大2回（[guide-expert-rewrite-program.md](./guide-expert-rewrite-program.md) §3.1.1）

### 4. 検証 → CSV 反映

```bash
python3 tools/validate_guide_greenfield_batch.py \
  --batch tools/greenfield/<site-id>/exam-format-overview.py \
  --root ~/Projects/<site>

python3 tools/run_guide_greenfield_batch.py \
  --batch tools/greenfield/<site-id>/exam-format-overview.py \
  --root ~/Projects/<site>
```

成功すると `revision_note` が `greenfield完了（試験ファクト照合·新規執筆）` になる。

### 5. ビルド・デプロイ

```bash
python3 tools/build_all.py
# 本番へ push（ユーザー指示時）
```

**1記事完了ごとに 2〜5 を繰り返す。** 5本まとめ batch は使わない。

---

## 執筆優先順（一衛の例）

`sites/eisei1shu-master/guide_greenfield_catalog.json` の `write_priority`:

1. `exam-format-overview`（形式）
2. `goukaku-kijun`（合格基準）
3. `pass-score`
4. `exam-scope-overview` / `subject-breakdown`
5. `study-plan-working`
6. 以降、keep 一覧を順に

---

## リライトとの違い

| | 旧リライト | greenfield |
|--|-----------|------------|
| 本文ソース | 旧稿·rewrites/ | 空 batch から新規 |
| batch 単位 | 5本 | **1本** |
| 完了ラベル | `編集合格` | `greenfield完了` |
| 試験ファクト | 手動 | `guide_exam_facts.json` + `validate_guide_exam_facts.py` |
| 正本ドキュメント | guide-expert-rewrite-program | **本ファイル** + expert §3 |

---

## サイト展開チェックリスト

各サイトで greenfield を始める前に:

- [ ] `sites/<id>/guide_exam_facts.json` を作成
- [ ] `init_guide_greenfield.py --apply --retire`
- [ ] （任意）`guide_greenfield_catalog.json` で見出し·優先順
- [ ] テンプレから `sync_from_template.py` で greenfield ツールを同期

現状 **greenfield 初期化済みは一衛（eisei1shu-master）のみ**。他サイトは従来の公開旧稿のまま。
