#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""greenfield 新規執筆: common-misconceptions

よくある誤解の横断整理。試験骨格の正本は exam-overview、
各論点の詳細は関連 slug へ接続。

  python3 tools/validate_guide_greenfield_batch.py --batch tools/greenfield/gaimuin-master/common-misconceptions.py --root ~/Projects/gaimuin-master
  python3 tools/run_guide_greenfield_batch.py --batch tools/greenfield/gaimuin-master/common-misconceptions.py --root ~/Projects/gaimuin-master
"""

from __future__ import annotations

REWRITES: dict[str, dict[str, str]] = {
    "common-misconceptions": {
        "title": "証券外務員試験のよくある誤解と正しい理解【6典型】",
        "meta_description": (
            "証券外務員試験の6大誤解を要項ベースで整理。"
            "年2回CBT·合格率70％·分野足切り·"
            "合格=登録·公式過去問などの正誤表と確認先を解説します。"
        ),
        "lead": (
            "外務員資格試験はCBT移行後も、"
            "紙試験時代の口コミ·他資格の情報が"
            "検索結果に混ざりやすい試験です。"
            "11月15日CBT·二種70問120分を"
            "想定して調べる場合、"
            "たとえば「合格率70％だから簡単」"
            "「年2回の試験日がある」"
            "「合格すればすぐ外務員として働ける」"
            "は、いずれも要項と照合すると"
            "修正が必要な典型です。"
            "本記事は6つの誤解を1枚の正誤表にまとめ、"
            "詳細は exam-overview と"
            "各関連ガイドへ接続します。"
            "正本は日本証券業協会「外務員資格試験」"
            "ページと受験要項です。"
        ),
        "user_intent": (
            "本記事を読むと、たとえば"
            "「二種70問を先に取らないと一種100問不可」"
            "「金商法が弱いと210点未満で足切り」"
            "などの誤解を表で修正し、"
            "次に読むべき正本記事"
            "（exam-schedule · pass-score 等）"
            "まで1行で分岐できるようになります。"
        ),
        "action_items": (
            "日証協試験ページでCBT·210点/308点·足切りなしを確認;"
            "誤解表の各行について関連ガイドを1本ずつ開く;"
            "口コミの数字は要項·プロメトリック案内と照合;"
            "一種直受験·一般受験可は exam-eligibility で再確認;"
            "学習計画は study-plan · past-question-strategy へ"
        ),
        "section_1_heading": "外務員試験の6大誤解一覧（正誤対比）",
        "section_1_body": (
            "ネット·古い教材で見かける誤解を"
            "要項ベースで対比します。"
            "詳細は各行の関連記事が正本です。"
            "例えば6月19日に本表を保存し、"
            "予約前·演習計画前に"
            "1行ずつチェックすると"
            "学習の取り違えを防げます。"
            "\n\n"
            "| # | 誤解 | 正しい理解 | 詳細 |\n"
            "| --- | --- | --- | --- |\n"
            "| 1 | 年2回一斉試験 | 通年CBT随時予約 | exam-schedule |\n"
            "| 2 | 合格率70％=簡単 | 個人の210点/308点 | pass-rate |\n"
            "| 3 | 分野別足切りあり | 総合7割のみ | pass-score |\n"
            "| 4 | 二種必須→一種 | 一種直受験可 | exam-eligibility |\n"
            "| 5 | 合格=即勤務可 | 登録は別手続 | after-pass-procedure |\n"
            "| 6 | 公式過去問PDF | 非公開·必携正本 | past-questions-by-year |"
        ),
        "section_2_heading": "試験形式·日程の誤解（CBT·マークシート·結果）",
        "section_2_body": (
            "誤解1：「春·秋の年2回試験」"
            "→一般受験はプロメトリック経由の"
            "通年CBT（平日中心·随時予約）。"
            "誤解2：「マークシート·鉛筆持参」"
            "→PC入力·筆記用具不要"
            "（final-day-checklist）。"
            "誤解3：「合格発表は数週間後」"
            "→終了画面に正解率表示·"
            "一般受験者へメール通知"
            "（exam-day-flow · 日証協案内）。"
            "たとえば11月15日（金）10:00開始·"
            "二種70問120分なら、"
            "9月16日頃から予約窗口、"
            "12:00頃終了後に画面結果、"
            "という流れが現行です。"
            "紙試験型スケジュールで"
            "逆算すると予約を逃しやすいです。"
            "\n\n"
            "| 誤解 | 現行CBT | 確認 |\n"
            "| --- | --- | --- |\n"
            "| 年2回 | 通年 | exam-schedule |\n"
            "| マークシート | PC入力 | exam-format-overview |\n"
            "| 後日発表のみ | 当日画面 | exam-day-flow |\n"
            "| 予約 | 60日前〜5営業日前 | 要項 |"
        ),
        "section_3_heading": "合格基準·合格率の誤解（210点·足切りなし）",
        "section_3_body": (
            "誤解4：「合格率68〜73％だから"
            "勉強しなくても7割取れる」"
            "→合格率は母集団統計、"
            "個人は210点/308点（総合7割）"
            "を演習で確認（pass-rate）。"
            "誤解5：「金商法が弱いと不合格」"
            "→分野別最低ラインはなく、"
            "総合得点のみが判定"
            "（weight-by-topic · pass-score）。"
            "誤解6：「正解率70％=合格確定」"
            "→五肢配点10点の内訳で"
            "得点は変動·210点換算が必要。"
            "例えば第8週日曜·二種70問通し192点"
            "（210点まで−18点）なら、"
            "合格率68％より得点改善を優先、"
            "と pass-rate-how-to-read が"
            "整理しています。"
            "\n\n"
            "| 概念 | 誤解 | 正本 |\n"
            "| --- | --- | --- |\n"
            "| 合格率 | 個人の確率 | 年度統計 |\n"
            "| 合格基準 | 分野足切り | 210点/308点 |\n"
            "| 演習 | 正答率のみ | 得点換算 |\n"
            "| 二種例 | 210点/300点 | 要項 |"
        ),
        "section_4_heading": "受験資格·免除·合格後の誤解",
        "section_4_body": (
            "誤解7：「証券会社員でないと受験不可」"
            "→一般受験は年齢·学歴·"
            "実務経験制限なし（exam-eligibility）。"
            "誤解8：「二種合格後でないと一種不可」"
            "→一種直受験可。"
            "誤解9：「FP·基礎試験で試験免除」"
            "→科目免除なし·"
            "2026年は返還措置のみ"
            "（exemption-system）。"
            "誤解10：「合格証をもらえば"
            "独学で外務員業務OK」"
            "→資格取得と外務員登録は別·"
            "登録は所属会社経由"
            "（after-pass-procedure）。"
            "たとえば11月15日CBT合格·"
            "二種210点の学生でも、"
            "入社後に人事が登録申請、"
            "が現実的な流れです。"
            "\n\n"
            "| 誤解 | 正解 | 記事 |\n"
            "| --- | --- | --- |\n"
            "| 受験資格 | 一般可 | exam-eligibility |\n"
            "| 一種 | 直受験可 | 同上 |\n"
            "| 免除 | 原則なし | exemption-system |\n"
            "| 勤務 | 登録必要 | after-pass-procedure |"
        ),
        "section_5_heading": "学習法の誤解と exam-overview との使い分け",
        "section_5_body": (
            "学習面の典型誤解も整理します。"
            "①「公式過去問PDFだけで足りる」"
            "→本番問題の年度別一括公開なし·"
            "必携+市販問題集+演習"
            "（past-questions-by-year）。"
            "②「過去問を年度順に全部解く」"
            "→4分野1周+解き直しサイクルが現実的"
            "（past-question-strategy）。"
            "③「プロ投資家=説明不要」"
            "→試験では37条/40条混同の"
            "誤答肢が定番（演習タグ参照）。"
            "exam-overview は試験骨格の"
            "ポジティブな入口、"
            "本記事は誤解の横断チェック、"
            "という役割分担です。"
            "例えば7月1日（火）を学習開始日に"
            "設定した独学者なら、"
            "第1週日曜に exam-overview を読み、"
            "第2週に本表6行を1行ずつ確認、"
            "疑問行だけ関連記事へ、"
            "という2段階が定番です。"
            "\n\n"
            "| 記事 | 役割 |\n"
            "| --- | --- |\n"
            "| exam-overview | 試験全体像 |\n"
            "| common-misconceptions | 誤解整理 |\n"
            "| past-question-strategy | 演習サイクル |\n"
            "| official-info-sources | 公式URL |"
        ),
        "faq_1_question": "外務員試験は年2回ですか？",
        "faq_1_answer": (
            "一般受験の一種·二種は"
            "通年CBT·随時予約です。"
            "年2回·一斉合格発表型は"
            "現行の一般受験ではありません。"
            "たとえば11月15日（金）受験なら"
            "9月16日頃から予約窗口が開き、"
            "プロメトリックで日時を選びます。"
            "詳細は exam-schedule が正本です。"
        ),
        "faq_2_question": "合格率70％台なら簡単に合格できますか？",
        "faq_2_answer": (
            "いいえ。合格率は一般受験者全体の"
            "統計で、個人の合格保証ではありません。"
            "合格基準は二種210点/300点·"
            "一種308点/440点（総合7割）です。"
            "例えば演習192点なら"
            "合格率68.1％より"
            "−18点改善を優先してください。"
            "pass-rate · pass-score を参照。"
        ),
        "faq_3_question": "exam-overview との違いは？",
        "faq_3_answer": (
            "exam-overview は試験の目的·"
            "問数·CBT·登録までの"
            "全体像（入口）が正本、"
            "本記事は口コミ·古い情報の"
            "誤解を正誤表で横断整理します。"
            "たとえば初めて調査するときは"
            "exam-overview →"
            "疑問行は common-misconceptions →"
            "詳細記事、"
            "の順が効率的です。"
        ),
        "primary_sources": "日本証券業協会（公式）|https://www.jsda.or.jp/",
        "related_links": (
            "exam-overview:試験全体像;"
            "exam-schedule:通年CBT予約;"
            "pass-score:210点/308点;"
            "exam-eligibility:受験資格"
        ),
    },
}
