#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""greenfield 新規執筆: first-time-exam-guide

初受験者向けオンボーディング。全体像は exam-overview、
週次計画は study-plan、独学Day1は self-study-start が正本。

  python3 tools/validate_guide_greenfield_batch.py --batch tools/greenfield/gaimuin-master/first-time-exam-guide.py --root ~/Projects/gaimuin-master
  python3 tools/run_guide_greenfield_batch.py --batch tools/greenfield/gaimuin-master/first-time-exam-guide.py --root ~/Projects/gaimuin-master
"""

from __future__ import annotations

REWRITES: dict[str, dict[str, str]] = {
    "first-time-exam-guide": {
        "title": "証券外務員試験·初めて受ける人向けガイド【7ステップ·最初の2週間】",
        "meta_description": (
            "証券外務員試験を初めて受ける人向けガイド。"
            "要項確認から区分決定·CBT予約·必携·演習まで7ステップ、"
            "初受験で混同しやすい点と最初の2週間の読む順序を表付きで解説します。"
        ),
        "lead": (
            "外務員資格試験を初めて受ける方は、"
            "「年2回のペーパー試験」「合格すればその場で外務員」"
            "など古い情報と混同しやすいです。"
            "一般受験の正本はCBT通年·プロメトリック予約·"
            "二種70問120分·210点合格（一種100問160分·308点）です。"
            "たとえば6月19日（木）に初めて調べ始めるなら、"
            "週末90分で7ステップのうち①要項②区分③形式まで、"
            "を終えるのが本記事の骨格です。"
            "2週間後は self-study-start → first-30-days-plan へ進みます。"
        ),
        "user_intent": (
            "本記事を読むと、初受験の最初の週末を"
            "土曜19:00要項30分·19:30区分20分·20:00形式20分·"
            "20:20演習5問、と90分カレンダーに書き、"
            "次に読むガイドの順序まで具体化できます。"
        ),
        "action_items": (
            "日証協「外務員資格試験」ページで要項PDFを保存する;"
            "一種/二種を exam-eligibility で1行決める;"
            "CBT·210点/308点·足切りなしを exam-format-overview で確認する;"
            "外務員必携4巻の発注可否を会社·予算で判断する;"
            "演習5問と正答数を1行記録し2週間後に first-30-days-plan へ移る"
        ),
        "section_1_heading": "初受験者の7ステップ（最初の週末で③まで）",
        "section_1_body": (
            "初めて受験する方は、次の7ステップを順に進めます。"
            "最初の週末90分で①〜③まで終えるのが現実的です。"
            "①要項PDF保存（official-info-sources）、"
            "②一種/二種決定（exam-eligibility）、"
            "③形式·合格点確認（exam-format-overview）、"
            "④4分野地図（exam-scope-overview）、"
            "⑤必携4巻発注（textbook-selection）、"
            "⑥演習10問ベースライン（q/practice/）、"
            "⑦受験日の予約窗口確認（exam-application-flow）。"
            "例えば6月21日（土）19:00〜20:30で"
            "要項·区分·形式まで終え、"
            "6月22日（日）に演習5問を解く、"
            "という2日分割が続きやすいです。"
            "\n\n"
            "| ステップ | 内容 | 正本ガイド |\n"
            "| --- | --- | --- |\n"
            "| ① | 要項PDF | official-info-sources |\n"
            "| ② | 一種/二種 | exam-eligibility |\n"
            "| ③ | 70問/100問 | exam-format-overview |\n"
            "| ④ | 4分野 | exam-scope-overview |\n"
            "| ⑤ | 必携4巻 | textbook-selection |\n"
            "| ⑥ | 演習5問 | pass-score |\n"
            "| ⑦ | 予約窗口 | exam-application-flow |"
        ),
        "section_2_heading": "初受験で混同しやすい5点",
        "section_2_body": (
            "検索や口コミで古い情報と混ざりやすい点を"
            "先に5行で固定します。"
            "\n\n"
            "| 混同 | 正本 | 誤解 |\n"
            "| --- | --- | --- |\n"
            "| 開催 | CBT通年 | 年2回一斉 |\n"
            "| 合格後 | 登録は別手続 | その場で外務員 |\n"
            "| 合否 | 総合7割のみ | 分野別足切り |\n"
            "| 過去問 | 市販·演習 | 年度別一括公開 |\n"
            "| 必携 | 協会テキスト | 法律そのもの |\n"
            "\n"
            "たとえば第1週日曜·演習5問中"
            "「合格=登録」系の誤答が1問あれば、"
            "after-pass-procedure を10分だけ読み、"
            "「試験合格≠登録完了」をノート表紙に書きます。"
            "CBT予約は受験日の60日前〜5営業日前"
            "（プロメトリック·要項で再確認）です。"
        ),
        "section_3_heading": "最初の週末90分チェックリスト",
        "section_3_body": (
            "初受験で教材を増やしすぎると止まります。"
            "最初の週末は次の90分テンプレだけ実行してください。"
            "通信講座·予備校は必須ではありません。"
            "\n\n"
            "| 時刻 | 作業 | 成果物 |\n"
            "| --- | --- | --- |\n"
            "| 0-30分 | 要項PDF保存 | フォルダ1件 |\n"
            "| 30-50分 | 一種/二種決定 | 表紙1行 |\n"
            "| 50-70分 | 形式·210点確認 | メモ3行 |\n"
            "| 70-80分 | 必携発注判断 | 発注 or 保留 |\n"
            "| 80-90分 | 演習5問 | 正答数1行 |\n"
            "\n"
            "例えば6月21日（土）19:00開始·二種決定·"
            "演習5問3/5なら、"
            "6月23日（月）から平日30分×週3を"
            "self-study-start の最小ルートで開始します。"
            "必携未到着週は当サイト演習10問だけでも"
            "学習は始められます。"
        ),
        "section_4_heading": "最初の2週間：読むガイドの順序",
        "section_4_body": (
            "初受験の2週間は「全体像→区分→形式→独学開始」"
            "の順が迷いにくいです。"
            "16週の週次表は2週目以降で十分です。"
            "\n\n"
            "| 週 | 読むガイド | やること |\n"
            "| --- | --- | --- |\n"
            "| 1前半 | exam-overview | 骨格把握 |\n"
            "| 1後半 | exam-eligibility | 区分決定 |\n"
            "| 2前半 | exam-format-overview | 210点/308点 |\n"
            "| 2後半 | self-study-start | Day1-2週 |\n"
            "\n"
            "たとえば6月19日調査開始なら、"
            "7月3日までに上記4本を読み、"
            "7月5日（土）から first-30-days-plan の"
            "30日カレンダーに移行します。"
            "会社指定で二種70問なら、"
            "一種の検討時間は割かず演習量を確保してください。"
        ),
        "section_5_heading": "2週間後に進む次のガイド",
        "section_5_body": (
            "2週間で7ステップの①〜⑥が終わったら、"
            "次の順で深掘りします。"
            "exam-scope-overview → study-plan →"
            "field-limit-basics（第1週=商品）→"
            "past-question-strategy。"
            "予約可能期間に入ったら exam-application-flow と"
            "exam-venue-and-region をセットで読みます。"
            "例えば11月15日CBT受験なら、"
            "9月16日頃から予約窗口を監視します。"
            "4分野1周が終わる段階（試験まで約12週）で"
            "仮の受験日を確定するのが定番です。"
            "直前は final-day-checklist → exam-day-flow です。"
            "\n\n"
            "| フェーズ | ガイド | 目標 |\n"
            "| --- | --- | --- |\n"
            "| 2-4週 | first-30-days-plan | 演習40問 |\n"
            "| 1-4週 | study-plan | 16週表 |\n"
            "| 通し | pass-score | 210点記録 |\n"
            "| 申込 | exam-application-flow | 予約完了 |"
        ),
        "faq_1_question": "初めてでも一種から受けられますか？",
        "faq_1_answer": (
            "一般受験者は二種合格なしで一種を直接受験できます"
            "（要項·exam-eligibility で再確認）。"
            "ただし100問160分·308点合格は学習量が増え、"
            "デリバティブも出題されます。"
            "未経験·独学初学者は二種70問120分から始める判断が多いです。"
            "たとえば会社指示が二種なら70問、"
            "指示なしで80〜150時間確保できるなら"
            "一種も選択肢、と1行で決めてください。"
        ),
        "faq_2_question": "いつCBT予約を入れるべきですか？",
        "faq_2_answer": (
            "一般受験者は受験希望日の60日前から予約可能、"
            "5営業日前が目安の締切です"
            "（プロメトリック·要項で再確認）。"
            "初受験は学習2〜4週目で形式·210点を確認し、"
            "4分野のベースライン演習が始まってから"
            "仮の受験日を決めるとブレにくくなります。"
            "例えば10月に16週プラン開始なら、"
            "11月末〜12月受験の予約を視野に入れてください。"
        ),
        "faq_3_question": "study-plan との違いは？",
        "faq_3_answer": (
            "本記事は初受験者の最初の2週間·7ステップに特化、"
            "study-plan は16週の週次配分表の正本です。"
            "初めて調べた週末は本記事と exam-overview から始め、"
            "区分決定と演習5問が終わったら study-plan へ移る、"
            "という順がおすすめです。"
            "独学Day1の90分テンプレは self-study-start が"
            "より詳しい正本です。"
        ),
        "primary_sources": "日本証券業協会（公式）|https://www.jsda.or.jp/",
        "related_links": (
            "exam-overview:試験の全体像;"
            "exam-eligibility:一種/二種の決め方;"
            "self-study-start:独学Day1-2週;"
            "exam-application-flow:CBT予約手順"
        ),
    },
}
