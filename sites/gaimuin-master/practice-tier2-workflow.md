# 二種実践演習 作問ワークフロー（証外マスター）

正本: [日本証券業協会 外務員資格試験](https://www.jsda.or.jp/gaimuin/shiken.html)（2025-06 確認）  
出題範囲の目次: [外務員必携](https://www.jsda.or.jp/gaimuin/)（要項参照）

## 公式スペック

| 区分 | 総問数 | 〇× | 五肢 | 試験時間 | 合格基準 |
|------|--------|-----|------|----------|----------|
| 二種 | **70問** | 50問（各2点） | 20問（各10点） | **2時間** | 300点満点の7割（210点） |
| 一種 | 100問 | 70問 | 30問 | 2時間40分 | 440点満点の7割（308点） |

## 二種のレベル・範囲（作問の前提）

JSDA 要項より:

- **知識水準**: 出題科目についての**基礎的知識**（一種は実務的・専門的）
- **職務イメージ**: 店頭における外務業務（第二種外務員・第二種業が中心）
- **デリバティブ**: 二種の職務範囲外だが、**株式・債券等の関連科目に基礎として含めて出題**
- **コンプラ**: 基本的かつ重要な事項を必ずカバー
- **出題形式**: 〇×（正誤1文）＋五肢（語句選択・**計算は少数**）

### 作問で優先する論点

| 分野 | 典型テーマ（外務員必携・用語記事と対応） |
|------|------------------------------------------|
| 金融商品・サービス | 有価証券の範囲、株・債・投信・ETF、元本非保証、商品の仕組み |
| 勧誘・販売規則 | 37条説明・40条適合、投資家区分、前後書面、自己責任原則 |
| 金融商品取引法 | 第一種業／第二種業、外務員一種・二種、顧客資産（分別管理）、インサイダー等 |
| その他法令・業務 | 金販法（クーリング・オフ）、反社排除、顧客本位、業界規則 |

### 作問で控える・引っかけに使う論点

- **第一種専用業務**（引受・自己の計算による売買等）を「二種でも常に可能」とする誤肢
- **条文番号・制度の入れ替え**（37＝適合、説明＝結果保証 等）
- **投資家区分の混同**（一般・特定・プロ、緩和＝免除）
- 一種レベルの深い計算・デリバティブの応用単独問題（基礎の文脈に留める）

## 70問ブループリント（Phase 1）

`data/practice_tier2_blueprint.csv` に番号・形式・分野・用語・batch を管理。

| 分野 | 〇×目標 | 五肢目標 | 小計 |
|------|---------|----------|------|
| 金融商品・サービス | 13 | 5 | 18 |
| 勧誘・販売規則 | 13 | 5 | 18 |
| 金融商品取引法 | 12 | 5 | 17 |
| その他法令・業務 | 12 | 5 | 17 |
| **計** | **50** | **20** | **70** |

Phase 2（約490問）は同じ配分比率で拡充し、同一用語の言い換え・関連論点を追加。

### Phase 2 の運用（10問バッチ）

| batch | 問番 | 形式 | 備考 |
|-------|------|------|------|
| 8 | 71〜80 | 〇×10 | Phase2 開始（未使用用語中心） |
| 9 | 81〜90 | 〇×10 | 同上 |
| … | … | … | 71〜350 は〇×、351〜490 は五肢 |

- **1バッチ＝常に10問**。Phase1 の batch6（5問）・batch7（15問）は例外。
- スロットは `practice_tier2_blueprint.csv` に先に追加し、`status: planned` → 適用後 `done`。
- 解説は `gaimuin_practice_explanation_texts.py` に手書き → patch → audit → apply。

## 1問あたりの品質基準

### 問題文

- **〇×**: 1文・40〜80字・正誤が一意（「場合による」だけの曖昧文は不可）
- **五肢**: 「次の記述のうち、正しい／誤っている／最も適切でないものはどれか」形式
- 過去問の**丸写し禁止**。用語記事の定義・誤解パターンを根拠にオリジナル作成

### 誤答肢（五肢）

- 用語記事の `exam_trap_patterns` / 試験頻出の誤解を1肢ずつ反映
- 「すべて」「必ず」「不要」「同一」などの**絶対語**で引っかけを作る（本試験と同型）
- 正解肢と同程度の文量

### 解説（必須列）

| 列 | 内容 |
|----|------|
| `explanation` | 1〜2文の結論（問ごとに切り口・文体を変える） |
| `explanation_summary` | 15〜30字の記憶フック |
| `explanation_correct` | 正答理由（なぜ正しい／なぜその肢が正解か） |
| `explanation_choices` | **他の選択肢**（五肢のみ必須） | 〇×は不要（表示しない）。五肢は `番号:理由;...` 形式 |
| `explanation_point` | 復習の次アクション（用語・条文・比較表） |

**オリジナル解説の手順（正本・監査・反映）** → [docs/gaimuin-practice-explanation-workflow.md](../../docs/gaimuin-practice-explanation-workflow.md)

**オリジナル性（GSC・重複回避）**

- 問ごとに文体・導入・復習アクションを変える。全問同型のテンプレ文は使わない。
- 避ける定型句: `記述は正しいです` / `記述は誤りです`、`設問の求め方と照らすと…`（未記入時の自動補完文を CSV に入れない）
- 正本: `tools/gaimuin_practice_explanation_texts.py` → `patch_practice_explanations.py` → **`audit_gaimuin_practice_explanations.py`（ERROR 0）** → batch / CSV

### タグ

- 必須: `二種`
- 形式: `〇×` または `五肢`
- 用語・論点: 用語名・条文テーマ（サイト内検索・フィルタ用）

## データ正本

| ファイル | 役割 |
|----------|------|
| `data/practice_questions.csv` | 実践演習の正本 |
| `data/practice_tier2_blueprint.csv` | 70問スロット・用語・進捗 |
| `data/practice_tier2_plan.csv` | 粗いフェーズ計画（レガシー） |
| `tools/batches/gaimuin_practice_tier2_batchN.py` | 10問単位の投入データ |

## 作業手順

```bash
cd ~/Projects/gaimuin-master

# 1. ブループリントで次の10問スロットを確認
#    data/practice_tier2_blueprint.csv

# 2. batch を書く（tools/batches/gaimuin_practice_tier2_batchN.py）
#    根拠: data/glossary_terms.csv の該当用語（編集合格済み優先）

# 3. 解説を手書き（正本）
#    tools/gaimuin_practice_explanation_texts.py
#    雛形: python3 tools/scaffold_gaimuin_practice_explanation.py --batch N

# 4. 正本 → batch 反映・監査
python3 tools/patch_practice_explanations.py
python3 tools/audit_gaimuin_practice_explanations.py   # ERROR 0 必須

# 5. CSV にマージ
python3 tools/apply_practice_batch.py --batch tools/batches/gaimuin_practice_tier2_batchN.py

# 6. 検証・生成
python3 tools/validate_csv.py
python3 tools/build_all.py
```

詳細: [docs/gaimuin-practice-explanation-workflow.md](../../docs/gaimuin-practice-explanation-workflow.md)

## 進捗

| Phase | 目標 | 状態 |
|-------|------|------|
| 0 | 〇×UI・数値統一 | 完了 |
| 1 smoke | 10問 | batch1 適用済み |
| 1 本番相当 | 70問（〇×50＋五肢20） | **完了**（batch1〜7 適用済み） |
| 2 拡充（〇×） | 71〜350問 | **完了**（batch8〜35） |
| 2 拡充（五肢） | 351〜490問 | **完了**（batch36〜49） |
| 3 五肢未作成用語 | 491〜620問 | **進行中**（130問スロット・batch50 適用済み 500問） |

## Phase 2 完了サマリー（2026-06-18）

| 区分 | 問数 | batch |
|------|------|-------|
| 〇× | 320問（1〜350） | batch1〜35 |
| 五肢 | 170問（1〜70＋351〜490） | batch1〜7, 36〜49 |
| **計** | **490問** | |

- ブループリント `practice_tier2_blueprint.csv`：490行すべて `done`（Phase2）
- 本番（GitHub Pages）：**490問**デプロイ済み（2026-06-18）

## Phase 3（491問以降）

| 項目 | 内容 |
|------|------|
| 目的 | 〇×のみ・未使用の用語に **五肢** を追加（用語カバレッジ完成） |
| 目標 | **130問**（491〜620）／batch50〜62 |
| 形式 | すべて五肢（`single`） |
| 状態 | batch50（491〜500）**適用済み** → ローカル **500問** |

### Phase 3 運用

- スロットは `practice_tier2_blueprint.csv` に 491〜620 を `planned` で追加済み
- 10問バッチ単位で batch51 以降を作成・適用
- 解説正本: `gaimuin_practice_explanation_texts.py` → patch → audit（ERROR 0）→ apply → build
