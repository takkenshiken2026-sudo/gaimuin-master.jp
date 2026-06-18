# 証外マスター — 実践演習「オリジナル解説」手順

二種実践演習の解説は **機械生成・一括テンプレ禁止**。問題と同様、問ごとに手書きする。

関連: [practice-tier2-workflow.md](../sites/gaimuin-master/practice-tier2-workflow.md)（作問全体） / [question-static-pages.md](./question-static-pages.md)（CSV 列仕様）

---

## 解説の構成（1問あたり5列）

| 列 | 役割 | 書き方の要点 |
|----|------|--------------|
| `explanation` | 結論1〜2文 | 問ごとに切り口・文体を変える。設問文の丸写しは不可 |
| `explanation_summary` | 15〜30字の記憶フック | 他問と被らない短い言い回し |
| `explanation_correct` | 正答の理由 | 〇×は「なぜ正しい／誤っているか」、五肢は「なぜその肢か」 |
| `explanation_choices` | **他の選択肢**（五肢のみ必須） | 下記「他の選択肢の書き方」参照。〇×は**表示しない**ため不要 |
| `explanation_point` | 復習の次アクション | 用語・条文・比較・実務シーンなど、問ごとに異なる動作 |

### 禁止する定型句（GSC 重複・読者不信）

- `記述は正しいです` / `記述は誤りです`
- `定番の誤答` / `用語「…」と…を整理してください` の機械的繰り返し
- `設問の求め方と照らすと正答になりません`（未記入時の自動補完文 — **CSV に入れない**）
- 全問同じ `explanation_point`（例: 毎回「用語解説で確認してください」だけ）

---

## 「他の選択肢」（`explanation_choices`）の書き方

**五肢（`type: single`）のみ必須**。〇×（`type: marubatsu`）は選択肢が「正しい／誤っている」のみのため、**ページに「他の選択肢」セクションは出さない** — `explanation_choices` は書かなくてよい（正本・CSV とも空で可）。

### 形式

```
番号:理由文;番号:理由文
```

例: `1:預金は…「正しい」は選べません。;3:…`

- 正答肢の番号は**含めない**
- 1肢あたり **48文字以上**（推奨72文字以上）。短いと自動補完に置き換わる
- 選択肢本文のキーワードを1つ以上含め、「なぜその肢が誤りか／正答でないか」を明示

### 〇×（`type: marubatsu`）

`explanation_correct` に正誤の理由を書けば十分。**`explanation_choices` は不要**（表示されない）。

### 五肢（`type: single`）

設問の求め方で書き分ける。

| 設問 | 各肢の解説の趣旨 |
|------|------------------|
| 正しいものはどれか | 誤肢ごとに「なぜ誤った記述か」 |
| 誤っているものはどれか | 正しい記述の肢に「なぜ本問の正答（誤り）ではないか」 |
| 最も適切でないものはどれか | 適切な肢に「なぜ最も不適切ではないか」＋正答肢との対比 |

---

## 正本と反映の流れ

```
data/practice_tier2_blueprint.csv  … スロット・用語・難易度
        ↓
tools/batches/gaimuin_practice_tier2_batchN.py  … 問題文・選択肢・正答
        ↓
tools/gaimuin_practice_explanation_texts.py  … 解説5列の正本（手書き）
        ↓
tools/patch_practice_explanations.py  … 正本 → batch へ反映
        ↓
tools/audit_gaimuin_practice_explanations.py  … 品質ゲート（ERROR 0）
        ↓
tools/apply_practice_batch.py --batch …  … CSV へマージ
        ↓
validate_csv.py + build_all.py
```

**原則:** batch に解説を直接書かず、まず `gaimuin_practice_explanation_texts.py` に書いてから patch する。  
（問題だけ先に batch に書き、解説は後から正本追加でも可）

---

## 1バッチ（10問）の作業手順

### 1. スロット確認

```bash
# data/practice_tier2_blueprint.csv で batch N の question_no・用語・難易度を確認
```

### 2. 問題を書く

`tools/batches/gaimuin_practice_tier2_batchN.py`

- 根拠: `data/glossary_terms.csv`（編集合格済み優先）の定義・`exam_trap_patterns`
- batch5以降は `standard`（引っかけ・条文混同・絶対語）
- この段階では解説列は空でも可

### 3. 解説の雛形を出す（任意）

```bash
python3 tools/scaffold_gaimuin_practice_explanation.py --batch N
```

`gaimuin_practice_explanation_texts.py` に追記する dict の骨組みが stdout に出る。

### 4. 解説を手書き

`tools/gaimuin_practice_explanation_texts.py` の `EXPLANATIONS["問番"]` に5列を記入。

**チェックリスト（1問終わるごと）**

- [ ] 他問と文体が被っていない
- [ ] 五肢なら `explanation_choices` が全誤肢をカバーしている
- [ ] 各 choice 理由が48字以上・選択肢内容に触れている（五肢のみ）
- [ ] 禁止定型句がない
- [ ] `explanation_point` が具体的（「確認してください」だけで終わらない）

### 5. 反映と監査

```bash
python3 tools/patch_practice_explanations.py
python3 tools/audit_gaimuin_practice_explanations.py   # ERROR 0 必須
python3 tools/apply_practice_batch.py --batch tools/batches/gaimuin_practice_tier2_batchN.py
python3 tools/validate_csv.py
python3 tools/build_all.py
```

### 6. 目視スポットチェック

生成後、次をブラウザまたは HTML で2〜3問確認する。

- 「正解の理由」が正答と一致しているか
- 「他の選択肢」に汎用テンプレが出ていないか
- 五肢で誤肢ごとに理由が分かれているか

### 7. デプロイ（本番）

```bash
cd ~/Projects/gaimuin-master
git add … && git commit && git push
```

`practice_tier2_blueprint.csv` の `status` を `done` に更新してコミット。

---

## ツール一覧

| ツール | 用途 |
|--------|------|
| `gaimuin_practice_explanation_texts.py` | 解説正本（dict） |
| `patch_practice_explanations.py` | 正本 → batch 反映 |
| `audit_gaimuin_practice_explanations.py` | 未記入・薄い解説・禁止句の監査 |
| `scaffold_gaimuin_practice_explanation.py` | 新規問の EXPLANATIONS 雛形出力 |
| `apply_practice_batch.py` | batch → `practice_questions.csv` |
| `validate_question_explanations.py` | 全サイト共通の解説監査（build_all 内） |

---

## 既存50問のメンテ

解説だけ直す場合:

1. `gaimuin_practice_explanation_texts.py` を編集
2. `patch_practice_explanations.py` → `audit` → `apply`（全 batch）→ `build_all`
3. 本番 sync / push

batch ファイルを手編集した解説は、次回 patch で上書きされる。**正本は常に `gaimuin_practice_explanation_texts.py`**。
