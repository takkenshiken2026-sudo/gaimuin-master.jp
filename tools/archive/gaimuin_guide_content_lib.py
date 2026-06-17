#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""証券外務員（一種・二種） 試験ガイド向けの本文・FAQ 生成（量産テンプレ差し替え用）。"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Callable

EXAM = "証券外務員（一種・二種）"
EXAM_SHORT = "証外"
OFFICIAL = "日本証券業協会の試験案内"
ORG = "日本証券業協会"
FOUR_FIELDS = (
    "金融商品・サービス",
    "勧誘・販売規則",
    "金融商品取引法",
    "その他法令・業務",
)

STUB_MARKERS = (
    "の観点で整理します",
    "まず公式要項で最新の制度を確認してください。本サイトでは過去問演習と用語解説で",
    "理解度を具体的に確かめられます",
    "このサイトでは過去問・用語解説・比較表を組み合わせ",
    "間違えた問題は理由を短くメモし、関連用語で定義",
)

META_STUB = "公式情報の確認方法と学習の進め方を整理します。受験前に押さえるべきポイントと、このサイトでの演習・用語解説の活用法を解説します"


def is_stub(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return True
    return any(m in t for m in STUB_MARKERS)


def two_paragraphs(p1: str, p2: str) -> str:
    return f"{p1.strip()}\n\n{p2.strip()}"


def ensure_min(text: str, min_len: int, tail: str) -> str:
    t = text.strip()
    if len(t) >= min_len:
        return t
    extra = tail
    while len(t + extra) < min_len:
        extra += " " + tail
    return (t.rstrip("。") + "。" + extra).strip()


def topic_from_row(row: dict[str, str]) -> str:
    title = (row.get("title") or "").strip()
    slug = (row.get("slug") or "").strip()
    if "｜" in title:
        parts = [p.strip() for p in title.split("｜") if p.strip()]
        for part in reversed(parts):
            if EXAM in part or EXAM_SHORT in part:
                part = re.sub(rf"^{re.escape(EXAM)}[の｜|]*", "", part)
                part = re.sub(rf"^{re.escape(EXAM_SHORT)}[の｜|]*", "", part).strip()
            part = re.sub(r"【[^】]+】$", "", part).strip()
            if len(part) >= 4 and not re.fullmatch(r"[a-z0-9 -]+", part, re.I):
                return part
    elif "|" in title:
        title = title.split("|", 1)[-1].strip()
    title = re.sub(r"^(.+?)【[^】]+】$", r"\1", title).strip()
    from tools.guide_topic_normalize import strip_exam_prefix

    title = strip_exam_prefix(title, EXAM, EXAM_SHORT)
    for prefix in (f"{EXAM}の", f"{EXAM}｜", f"{EXAM_SHORT}の"):
        if title.startswith(prefix):
            title = title[len(prefix) :].strip()
    if len(title) >= 4 and not title.startswith("証外"):
        return title
    from tools.archive.guide_catalog_batch import topic_from_row as _catalog_topic_from_row

    return _catalog_topic_from_row(row)


def field_name_from_slug(slug: str) -> str | None:
    m = re.match(r"field-([a-z0-9-]+)-", slug)
    if not m:
        return None
    fid = m.group(1)
    mapping = {
        "law": "金融商品取引法",
        "rights": "勧誘・販売規則",
        "limit": "金融商品・サービス",
        "products": "金融商品・サービス",
        "fil": "金融商品取引法",
        "solicitation": "勧誘・販売規則",
        "compliance": "その他法令・業務",
    }
    return mapping.get(fid, fid.replace("-", " "))


def _official_note() -> str:
    from tools.guide_content_shared import official_note_single

    return official_note_single(OFFICIAL)


def _practice_note(topic: str) -> str:
    return (
        f"演習で{topic}に関する設問を解いたら、正解理由と誤答肢の違いを短くメモし、"
        f"用語解説・比較表・よくある誤答タブで似た論点を比較表で整理すると定着しやすくなります。"
    )


# --- 見出し別本文（180字以上・具体性あり） ---


def _heading_よくある誤解(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"{topic}では、「適合性の原則＝元本保証」「一種と二種の業務範囲が同じ」"
        f"「5%ルールは投資家保護のための勧誘制限」など、現場イメージと制度のズレが誤答の温床になります。"
        f"特に適合性の原則と重要事項説明、有価証券とデリバティブの区分、金商法と販売規則の混同は四択で頻出です。",
        f"誤解を解くには、用語解説で定義を確認したうえで、比較表タブの「混同しやすい組み合わせ」を読み、"
        f"演習問題で引っかけ肢を体験してください。{_official_note()}",
    )


def _heading_独学前に公式情報を確認(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"独学を始める前に、{OFFICIAL}で受験資格・試験日程・出題範囲（4分野）・合格基準をメモしてください。"
        f"{topic}の学習計画は、外務員必携の章立てと一致させると、過去問の分野ラベルとも対応づけやすくなります。",
        f"ブログやSNSの「最新情報」は、必ず{ORG}のページと照合してから採用してください。"
        f"申込期限や受験料は年度ごとに変わるため、カレンダーに締切を入れてから教材を開く習慣が有効です。",
    )


def _heading_教材参考書(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return _heading_外務員必携(topic, _slug, _genre, _ctx)


def _heading_外務員必携(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"{topic}向けには、{ORG}発行の公式テキスト「外務員必携」を軸に置くのが基本です。"
        f"問題集は年度・版の表記を確認し、4分野すべてをカバーしているかを目次でチェックしてください。",
        f"教材を増やしすぎるより、外務員必携を2周してから演習問題・一問一答で穴を見つける方が、"
        f"証券会社での勧誘・販売の実務イメージもつきやすくなります。{_practice_note(topic)}",
    )


def _heading_過去問現在地(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"最初の過去問は、{topic}に限定せず1回分を通しで解き、4分野のうちどこで迷ったかを記録します。"
        f"たとえば「金融商品・サービス」と「金商法」の問題を取り違えた、など分野名でメモすると復習が楽です。",
        f"得点より「どの用語が弱いか」を把握することが目的です。"
        f"不正解の選択肢は、用語解説で定義と試験論点を確認してから同分野の演習へ戻ってください。",
    )


def _heading_復習計画(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"復習は「翌日・3日後・1週間後」の3回サイクルをカレンダーに先に入れておくと実行しやすくなります。"
        f"{topic}で間違えた問題は、正答番号ではなく「なぜ他の肢が違うか」まで言語化してから次へ進みます。",
        f"アプリのブックマークや復習機能に、分野タグ付きで残しておくと、"
        f"直前期に{topic}関連の弱点だけを絞り込めます。",
    )


def _review_focus_label(topic: str, slug: str) -> str:
    if slug.startswith("exam-day-") or any(
        x in topic for x in ("持ち物", "流れ", "時間配分", "トラブル", "CBT")
    ):
        return "演習で間違えた分野"
    return topic


def _heading_直前期絞り込み(topic: str, slug: str, _genre: str, _ctx: dict) -> str:
    focus = _review_focus_label(topic, slug)
    return two_paragraphs(
        f"試験直前は新しい参考書を増やさず、{focus}と頻出用語に絞ります。"
        f"4分野のうち得点率が低い領域を1つ選び、用語10語＋演習20問程度をセットで見直すのが目安です。",
        f"前日は暗記の詰め込みより、睡眠と当日の持ち物・会場確認を優先してください。"
        f"数値（合格点210点・70%、5%ルール、適合性の原則、開示期限など）は早見表タブで最終確認すると安心です。",
    )


def _heading_直前絞り込み見出し(topic: str, slug: str, genre: str, ctx: dict) -> str:
    return _heading_直前期絞り込み(topic, slug, genre, ctx)


def _heading_最終確認リスト(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    from tools.guide_content_shared import exam_day_forget_checklist_prose

    return exam_day_forget_checklist_prose(official=OFFICIAL, topic=topic)


def _heading_当日タイムライン(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    from tools.guide_content_shared import exam_day_timeline_prose

    return exam_day_timeline_prose(official=OFFICIAL, topic=topic)


def _heading_持ち物と時間配分(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    from tools.guide_content_shared import exam_day_items_and_time_prose

    return exam_day_items_and_time_prose(official=OFFICIAL, topic=topic)


def _heading_メンタルトラブル(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"当日の不安や体調不良は、深呼吸・水分補給・会場係員への相談で対処します。"
        f"問題が解けない場合も、300問全体の時間配分を崩さず次の設問へ進む判断が得点維持につながります。",
        f"会場でのトラブル（座席、画面操作、筆記用具など）は早めに係員へ声をかけてください。"
        f"{topic}の学習内容より、当日は冷静さと{OFFICIAL}の受験要項どおりの行動を優先します。",
    )


def _heading_制度改定(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"金融商品取引法・販売等の勧誘に関する規則・金融商品取引業等に関する内閣府令など、"
        f"{topic}の背景法令は改正やガイドライン更新があります。"
        f"試験は制度の「考え方」と外務員の対応原則が中心ですが、数値要件は外務員必携の版を確認してください。",
        f"学習中も月1回程度、{OFFICIAL}とテキストの改訂情報を見直す習慣をつけると、"
        f"古い問題集の解説とのズレに気づきやすくなります。",
    )


def _heading_分野位置づけ(topic: str, slug: str, _genre: str, _ctx: dict) -> str:
    field = field_name_from_slug(slug) or topic
    return two_paragraphs(
        f"外務員必携の4分野のうち、「{field}」は{topic}の理解に直結する部分です。"
        f"証券外務員試験では、顧客への勧誘・販売・説明・記録・法令遵守の判断場面として問われます。",
        f"他領域とのつながりを意識すると、事例問題の選択肢が読みやすくなります。"
        f"たとえば勧誘・販売規則の領域は、適合性の原則や重要事項説明とセットで出題されることが多いです。",
    )


def _heading_基礎知識(topic: str, slug: str, _genre: str, _ctx: dict) -> str:
    field = field_name_from_slug(slug) or topic
    return two_paragraphs(
        f"{field}の基礎として、キーワードの定義（適合性の原則、重要事項説明、有価証券、デリバティブ、"
        f"インサイダー取引、5%ルールなど）を用語解説で確認してください。"
        f"試験では長い定義文の一部が空欄になったり、似た語句と並べ替えられたりします。",
        f"暗記カードを作る場合は「誰が・いつ・何をするか」の3点セットでまとめると、"
        f"事例問題の主体（外務員／金融商品取引業者／投資家）を見分けやすくなります。{_practice_note(topic)}",
    )


def _heading_頻出論点(topic: str, slug: str, _genre: str, _ctx: dict) -> str:
    field = field_name_from_slug(slug) or topic
    return two_paragraphs(
        f"{field}では、外務員の具体的行動（顧客属性の確認、商品説明、重要事項の書面交付、"
        f"不適切勧誘の回避、記録保存）が正解になりやすいです。"
        f"逆に「元本保証と誤解させる説明」「適合性確認を省略する」などは誤答パターンとして繰り返し出ます。",
        f"演習問題の解説で頻出テーマをチェックし、同じ論点が別の言い回しで出ていないかを確認してください。"
        f"比較表・よくある誤答タブは、頻出の混同ペアを短時間で復習するのに向いています。",
    )


def _heading_過去問確認(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"{topic}の理解度は、関連する演習問題で確認するのが効率的です。"
        f"1問解くごとに「根拠は外務員必携のどの章か」をメモすると、復習時に該当ページへすぐ戻れます。",
        f"同じ問題を時間を空けて解き直し、言い換え選択肢でも正解できるかまで確認してください。"
        f"二回連続正解でも、条件を1語変えた肢で誤答する場合は、用語の定義がまだ曖昧なサインです。",
    )


def _heading_他分野関連(topic: str, slug: str, _genre: str, _ctx: dict) -> str:
    field = field_name_from_slug(slug) or topic
    return two_paragraphs(
        f"「{field}」は、金融商品取引法（インサイダー・開示）や勧誘・販売規則（適合性の原則）など、"
        f"他領域のキーワードとセットで事例が構成されることがあります。"
        f"関連用語リンクから隣接する用語を2〜3件読むと、長文問題の文脈がつかみやすくなります。",
        f"4分野をバランスよく学ぶため、弱点分野ばかりでなく、得意分野も月1回は演習で維持してください。"
        f"試験ガイドの学習計画記事と組み合わせると、領域配分の調整がしやすくなります。",
    )


def _heading_受験資格(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"{EXAM}の受験資格は、{OFFICIAL}の受験要項で確認します。"
        f"一種・二種それぞれの受験要件や、実務経験・在籍先の条件など、自分に該当するかをチェックリスト化してください。",
        f"資格要件は年度で文言が更新されることがあるため、申込前にもう一度要項PDFの更新日を確認してください。"
        f"不明点は{ORG}の問い合わせ窓口を利用し、非公式情報だけで判断しないようにします。",
    )


def _heading_年間スケジュール(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"試験は年複数回実施されるため、{OFFICIAL}で「申込期間→試験日→合格発表」の流れをカレンダーに転記します。"
        f"{topic}の学習期間を逆算する際は、申込締切の1〜2週間前までに主要領域の演習を1周終える目安が現実的です。",
        f"仕事繁忙期と試験日が重なる場合は、早めの回を選ぶか、学習計画記事を参考に週あたり時間を再配分してください。",
    )


def _heading_申込手数料(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return _heading_JSDA申込(topic, _slug, _genre, _ctx)


def _heading_JSDA申込(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"受験料・支払方法・申込方法は{OFFICIAL}（{ORG}）の受験案内で確認します。"
        f"JSDAの申込サイトでは、受験区分（一種／二種）、受験地、氏名・連絡先を正確に入力し、支払期限をカレンダーに登録してください。",
        f"申込後に受験票・会場案内が届くまでの流れも要項に記載があります。"
        f"直前に住所変更やキャンセル規定があるかも、申込時に確認しておいてください。",
    )


def _heading_申込手順会場(topic: str, slug: str, _genre: str, _ctx: dict) -> str:
    from tools.guide_content_shared import exam_application_venue_prose
    from tools.exam_venue_official_links import official_page_md_for_exam

    return exam_application_venue_prose(
        official=OFFICIAL,
        topic=topic,
        official_page_md=official_page_md_for_exam(EXAM, OFFICIAL),
    )


def _heading_申込前チェック(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    from tools.guide_content_shared import application_precheck_prose

    return application_precheck_prose(official=OFFICIAL, topic=topic)


def _heading_過去問年度別(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"過去問はまず1つの実施回を通しで解き、4分野ごとの正答率をざっくり把握します。"
        f"{topic}に関連する分野の問題数が多い回を選ぶより、全体の出題バランスを見る方が初期分析には有効です。",
        f"解説を読む際は、外務員の行動として正しいか／法令上の主体が誰か、を必ず確認してください。"
        f"同じ回を2周目以降は、時間を計って解くと本番のペース感がつかめます。",
    )


def _heading_模試一問(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"一問一答は、通勤時間などの隙間に4分野を短時間で確認するのに向いています。"
        f"模試形式の演習は、本番に近い問題数・時間配分の練習に使い、弱点が見えた分野は用語解説へ戻ります。",
        f"{topic}の学習では、一問一答で「用語の定義」、四択演習で「勧誘・販売の事例判断」の両方を回すとバランスが取れます。",
    )


def _heading_間違い分類(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"誤答の理由を「知識不足」「用語混同」「読み飛ばし」「主体の取り違え（外務員 vs 投資家 vs 業者）」"
        f"に分類すると、次の対策が決まります。混同が多い場合は比較表タブを優先してください。",
        f"ノートの1行例：「第○問／金商法／『開示義務の主体』を混同」。"
        f"この形式で{topic}関連の誤答を溜めると、直前の解き直しが効率的になります。",
    )


def _heading_解き直し(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"解き直しは、当日・3日後・1週間後の間隔を空けると記憶の定着を確認しやすくなります。"
        f"ブラウザの復習機能やブックマーク一覧を「{topic}関連」でフィルタし、優先順位を付けてください。",
        f"2回連続で正解できても、解説を読まずに選んだ問題は三回目も解き直し対象にします。"
        f"「なぜ正解か」を言語化できるまでが、本番レベルの理解です。",
    )


def _heading_用語分野学習(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"演習で分からなかった語句は、用語解説タブで定義・試験論点・よくある誤解まで確認します。"
        f"関連用語から2件以上読むと、{topic}の設問で並べられた選択肢の意図が見えやすくなります。",
        f"用語だけ暗記しても事例問題は解けないため、演習→用語→演習の往復を1セットとして回してください。",
    )


def _heading_外務員の役割(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"証券外務員は、{topic}の場面で「顧客理解・適合性確認・商品説明・重要事項の交付・記録保存・法令遵守」"
        f"のバランスを取る主体として問われます。投資判断の最終責任は投資家にあり、外務員が元本保証を約束する対応は誤りです。",
        f"演習では「何をすべきか／すべきでないか」の二択に見える問題でも、"
        f"勧誘と販売の手続、書面交付のタイミングの線引きがポイントになることが多いです。",
    )


def _heading_試験目的(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"{EXAM}は、証券会社等で外務員として顧客への勧誘・販売・説明を行うための"
        f"知識・態度を評価する試験です。金融商品の理解、法令遵守、顧客保護が中心テーマです。",
        f"4分野は外務員必携に沿って構成されています。"
        f"試験勉強は暗記だけでなく、「現場でどう対応するか」の判断練習として演習問題を活用してください。",
    )


def _heading_試験形式(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return _heading_CBT(topic, _slug, _genre, _ctx)


def _heading_CBT(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"証券外務員試験はCBT（Computer Based Testing）方式で実施されます。"
        f"300問・300点満点・合格基準は一般に210点（70%）ですが、最新の問題数・制限時間・合格点は{OFFICIAL}で必ず確認してください。",
        f"画面操作に慣れるため、演習でも時間を計って解く習慣を早めに身につけてください。"
        f"長文の事例問題は後半に条件が書かれることが多いので、1問あたりの目安時間を意識した練習が有効です。",
    )


def _heading_合格点(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"証券外務員試験は300点満点で、合格点は210点（70%）が一般的な基準です。"
        f"分野別の足切りは設けられていないため、得意分野で得点を稼ぎつつ弱点分野を底上げする戦略が取りやすくなります。",
        f"合格率や合格点の正式な数値は{OFFICIAL}の統計・要項で確認し、"
        f"自分の演習得点（何割正解か）と照らし合わせて学習計画を調整してください。",
    )


def _heading_4分野(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    items = "\n".join(f"- {f}" for f in FOUR_FIELDS)
    return two_paragraphs(
        f"出題範囲は外務員必携に沿った次の4分野です。\n{items}",
        f"領域横断の事例問題も出るため、分野別に学んだあと、通しの演習で領域をまたぐ問題にも慣れておくと安心です。"
        f"{_practice_note(topic)}",
    )


def _heading_金商法(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"金融商品取引法（金商法）は、有価証券の発行・取引、開示、インサイダー取引規制、"
        f"相場操縦の禁止など、証券市場の根幹を定める法令として{topic}の理解に直結します。",
        f"条文の主体（発行者・金融商品取引業者・投資家）と要件（いつ・何を開示・禁止するか）を"
        f"外務員必携の該当章と演習問題でセット学習してください。{_official_note()}",
    )


def _heading_適合性の原則(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"適合性の原則は、顧客の知識・経験・財産状況・投資目的に照らし、"
        f"不適切な勧誘・販売を行わないよう金融商品取引業者に求められる原則です。"
        f"元本保証や必ず儲かると誤解させる説明は、この原則に反する典型例として問われます。",
        f"試験では顧客属性（プロ・一般・適格機関投資家など）と勧誘可能な商品の組み合わせが"
        f"四択で頻出です。用語解説と比較表で整理してから演習に戻してください。",
    )


def _heading_5パーセントルール(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"5%ルール（大量保有報告制度）は、上場株式等を発行会社の発行済株式総数の5%を超えて取得した場合に、"
        f"一定の報告・公表義務が生じる制度です。取得割合・報告期限・届出先の数値が問われます。",
        f"インサイダー取引規制やTOB制度と混同しやすいため、"
        f"用語解説で「誰が・いつ・何を報告するか」を表にまとめ、演習で言い換え問題にも対応してください。",
    )


def _heading_一種二種の違い(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"証券外務員一種は、有価証券の価値等の分析に基づく投資勧誘（いわゆるアドバイザリー業務）が中心で、"
        f"二種は値段の告知・注文の受付などの業務が中心です。受験区分・業務範囲・試験の出題範囲の違いは{OFFICIAL}で確認してください。",
        f"試験では「一種なら可能／二種なら不可」といった業務区分の判断が事例問題で出ます。"
        f"自分が受験・登録する区分を先に決め、外務員必携の該当章と演習の分野タグを合わせて学習すると迷いません。",
    )


def _heading_サイト学習(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        "このサイトでのおすすめの流れ：①試験ガイドで制度の全体像 ②用語解説で重要語を章ごとに確認 "
        "③一問一答で知識の穴を洗い出し ④演習問題一覧から分野別に四択演習 ⑤間違えた問題は復習機能に残す。",
        f"直前期は新しい教材を増やしすぎず、{topic}で誤答した分野と頻出用語に絞って解き直してください。"
        f"比較表・数値早見・よくある誤答タブは、短時間の確認向きです。",
    )


def _heading_用語ハブ1(topic: str, slug: str, _genre: str, ctx: dict) -> str:
    term = ctx.get("term_name") or topic
    short = ctx.get("term_short") or ""
    p1 = (
        f"{EXAM}では、{term}の定義と試験での引っかけ（主体の取り違え・数値・手順の順序）がセットで問われます。"
    )
    if short:
        p1 += f" 短い定義：{short.rstrip('。')}。"
    return two_paragraphs(
        p1,
        f"詳細な定義・試験論点・FAQは用語解説「{term}」のページで確認してください。"
        f"本記事（試験ガイド）は、用語を学んだあと演習・比較表へ進む導線として使います。"
        f"{_practice_note(term)}",
    )


def _heading_用語ハブ2(topic: str, slug: str, _genre: str, ctx: dict) -> str:
    term = ctx.get("term_name") or topic
    return two_paragraphs(
        f"用語解説は「{term}とは何か」を答える場所です。"
        f"勉強の進め方・申込・直前対策・再受験は試験ガイド一覧で扱い、役割を分けて読むと迷いません。",
        f"定義を読んだら、弱点分野のガイド記事か演習問題へ進み、"
        f"選択肢で迷った論点だけ用語ページに戻る往復が効率的です。",
    )


def _heading_用語ハブ3(topic: str, slug: str, _genre: str, ctx: dict) -> str:
    term = ctx.get("term_name") or topic
    return two_paragraphs(
        f"おすすめの学習順：①用語解説で{term}の定義と誤答パターンを確認 "
        f"②関連用語リンクから混同語を比較表で整理 ③演習問題で該当分野を解き、間違えた選択肢を用語解説で照合 "
        f"④必要なら学習計画・分野別ガイドへ。",
        f"比較表タブに{term}が登場する場合は、似た制度・用語との違いを表形式で確認してから演習に戻してください。",
    )


def _heading_出題範囲確認(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"{topic}の出題範囲は、{OFFICIAL}の受験案内と外務員必携の目次で確認します。"
        f"4分野の名称と配点・出題比率は年度で微調整されることがあるため、学習開始時と申込前に最新版を照合してください。",
        f"サイト内の演習・用語は site-config の分野設定に沿って整理されています。"
        f"公式テキストの章番号と分野タグをメモしておくと、弱点復習が効率化します。",
    )


def _heading_科目配点(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"証券外務員試験は300問・300点満点で、4分野からおおむね均等に出題されます。"
        f"分野別の配点・出題数の正式な内訳は{OFFICIAL}と外務員必携で確認し、学習時間の配分に反映してください。",
        f"得意分野で得点を確保しつつ、苦手分野は外務員必携＋演習20問セットで底上げするのが現実的な戦略です。",
    )


def _heading_合格率統計(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"合格率・受験者数は{OFFICIAL}の統計資料で公表されます。"
        f"数字だけで難易度を判断せず、自分の演習正答率と弱点分野を合わせて見積もってください。",
        f"{topic}の学習時間は、4分野のバランスと仕事の繁忙期を考慮して設定します。"
        f"合格点210点（70%）を演習でも目標ラインにすると、本番のイメージがつかみやすくなります。",
    )


HEADING_MAP: dict[str, Callable[..., str]] = {
    "よくある誤解": _heading_よくある誤解,
    "独学前に公式情報を確認": _heading_独学前に公式情報を確認,
    "教材・参考書の選び方": _heading_教材参考書,
    "過去問で現在地を確認": _heading_過去問現在地,
    "復習を計画に入れる": _heading_復習計画,
    "直前期の絞り込み": _heading_直前期絞り込み,
    "制度・出題の改定": _heading_制度改定,
    "合格後の手続き": lambda t, s, g, c: two_paragraphs(
        f"合格後の手続き（合格証の交付、社内報告、外務員登録の申請など）は{OFFICIAL}と受験要項で確認します。"
        f"所属する金融商品取引業者のコンプライアンス部門のルールと併せて、必要書類の保管期間もチェックしてください。",
        f"{t}に合格した場合も、社内研修や業務規程の更新が別途必要なことがあります。"
        f"試験合格＝現場対応の完成ではない点も、外務員必携後半の章で確認しておきましょう。",
    ),
    "不合格後の立て直し": lambda t, s, g, c: two_paragraphs(
        f"不合格の場合は、分野別の弱点分析から再計画を立てます。"
        f"演習の得点記録と誤答ノートを見返し、4分野のうち正答率が低い領域を2つに絞って1ヶ月集中する方法が有効です。",
        f"再受験の申込期間をカレンダーに入れ、同じミス（用語混同・主体の誤り）を比較表タブで潰してください。",
    ),
    "公式情報の優先": lambda t, s, g, c: two_paragraphs(
        f"{topic_from_stub(t)}に関する情報は、{ORG}の{OFFICIAL}を最優先にしてください。"
        f"受験要項・テキスト改訂・合格発表の案内は、非公式サイトより公式ページが正です。",
        f"学習中に見つけた数値（合格点、5%ルール、報告期限など）は、数値早見表と外務員必携で二重確認する習慣をつけましょう。",
    ),
    "分野の位置づけ": _heading_分野位置づけ,
    "押さえる基礎知識": _heading_基礎知識,
    "頻出論点": _heading_頻出論点,
    "過去問での確認方法": _heading_過去問確認,
    "他分野との関連": _heading_他分野関連,
    "受験資格の確認": _heading_受験資格,
    "年間スケジュール": _heading_年間スケジュール,
    "申込期間と手数料": _heading_申込手数料,
    "申込手順と会場": _heading_申込手順会場,
    "申込前チェックリスト": _heading_申込前チェック,
    "最初は年度別に解く": _heading_過去問年度別,
    "模試・一問一答の位置づけ": _heading_模試一問,
    "間違いの理由を分類する": _heading_間違い分類,
    "解き直しのタイミング": _heading_解き直し,
    "用語・分野別学習へ戻る": _heading_用語分野学習,
    "外務員の役割": _heading_外務員の役割,
    "試験の目的と位置づけ": _heading_試験目的,
    "試験形式と合格基準（公式で再確認）": _heading_試験形式,
    "出題範囲4分野の全体像": _heading_4分野,
    "出題範囲4科目の全体像": _heading_4分野,
    "全体像を分野に分ける": _heading_4分野,
    "このサイトでの学習の進め方": _heading_サイト学習,
    "このサイトでできること": _heading_サイト学習,
    "用語解説で確認する内容": _heading_用語ハブ1,
    "試験ガイドとの使い分け": _heading_用語ハブ2,
    "おすすめの学習順": _heading_用語ハブ3,
    "直前1〜2週間の絞り込み": _heading_直前絞り込み見出し,
    "最終確認リスト": _heading_最終確認リスト,
    "当日のタイムライン": _heading_当日タイムライン,
    "持ち物と時間配分": _heading_持ち物と時間配分,
    "メンタル・トラブル対応": _heading_メンタルトラブル,
    "まず確認する公式情報": _heading_独学前に公式情報を確認,
    "出題範囲の確認先": _heading_出題範囲確認,
    "範囲の全体像と改定": _heading_制度改定,
    "科目・配点": _heading_科目配点,
    "制限時間と出題形式": _heading_CBT,
    "過去問との対応": _heading_過去問確認,
    "合格率の確認先": _heading_合格率統計,
    "合格点・基準の意味": _heading_合格点,
    "難易度の考え方": _heading_合格率統計,
    "統計の読み方": _heading_合格率統計,
    "学習計画への反映": _heading_復習計画,
}


def topic_from_stub(topic: str) -> str:
    return topic


def _keyword_fallback(heading: str, topic: str, slug: str, genre: str) -> str:
    """未登録見出し向けのキーワードベース生成。"""
    h = heading
    checks: list[tuple[tuple[str, ...], Callable[..., str]]] = [
        (("CBT", "コンピュータ", "画面"), _heading_CBT),
        (("合格点", "210", "70%", "300点"), _heading_合格点),
        (("外務員必携", "公式テキスト", "テキスト"), _heading_外務員必携),
        (("金商法", "金融商品取引法"), _heading_金商法),
        (("適合性",), _heading_適合性の原則),
        (("5%", "5％", "パーセント"), _heading_5パーセントルール),
        (("一種", "二種", "種別"), _heading_一種二種の違い),
        (("JSDA", "日本証券業協会", "申込"), _heading_JSDA申込),
        (("公式", "要項", "確認"), _heading_独学前に公式情報を確認),
        (("過去問", "演習"), _heading_過去問確認),
        (("復習", "解き直"), _heading_解き直し),
        (("外務員",), _heading_外務員の役割),
        (("用語", "用語集"), _heading_用語分野学習),
        (("合格", "難易度", "合格率"), _heading_合格率統計),
        (("持参", "必ず持", "持ち物"), _heading_持ち物と時間配分),
        (("禁止", "持込", "持ち込み"), _heading_持ち物と時間配分),
        (("タイムライン",), _heading_当日タイムライン),
        (("チェックリスト", "忘れ物"), _heading_最終確認リスト),
        (("直前", "当日", "試験前"), _heading_直前期絞り込み),
        (("睡眠", "健康", "体調"), lambda t, s, g, c: two_paragraphs(
            f"試験直前は睡眠を削りすぎないことが得点維持に効きます。"
            f"暗記の詰め込みより、誤答ノートの確認と持ち物・会場の準備を優先してください。",
            f"{topic}で不安な領域は、用語10語だけピックアップして見直す程度に留めるとメンタル面も安定しやすいです。",
        )),
    ]
    for keys, fn in checks:
        if any(k in h or k in topic or k in slug for k in keys):
            return fn(topic, slug, genre, {})
    from tools.guide_content_shared import keyword_fallback_default

    return keyword_fallback_default(
        heading,
        topic,
        exam=EXAM,
        exam_short=EXAM_SHORT,
        official=OFFICIAL,
        official_note_fn=_official_note,
        practice_note_fn=_practice_note,
        two_paragraphs_fn=two_paragraphs,
    )


def section_body_for(heading: str, topic: str, slug: str, genre: str, ctx: dict) -> str:
    fn = HEADING_MAP.get(heading.strip())
    if fn:
        body = fn(topic, slug, genre, ctx)
    else:
        body = _keyword_fallback(heading, topic, slug, genre)
    from tools.guide_content_shared import section_body_min_filler

    return ensure_min(body, 180, section_body_min_filler(heading, topic, OFFICIAL))


def faq_answer_for(question: str, topic: str, slug: str, row: dict[str, str], faq_index: int = 1) -> str:
    q = (question or "").strip().rstrip("？?")
    if not q:
        return ""
    text = ""
    if faq_index == 1:
        if ("一種" in q or "二種" in q) and ("違い" in q or "どちら" in q):
            text = (
                "一種は分析に基づく投資勧誘、二種は価格告知・注文受付などの業務が中心です。"
                "受験区分と登録後の業務範囲は日本証券業協会の試験案内と外務員必携で確認してください。"
            )
        elif "合格点" in q or "210" in q or "何点" in q:
            text = (
                "証券外務員試験は300点満点で、合格点は一般的に210点（70%）です。"
                f"最新の合格基準は{OFFICIAL}の受験要項で必ず確認してください。"
            )
        elif "公式" in q or "どこで" in q:
            text = (
                f"{OFFICIAL}（{ORG}）で最新情報を確認してください。"
                f"受験要項・テキスト改訂・合格発表は公式ページが正本です。"
                f"{topic}に関する数値や期限も、非公式まとめではなく公式資料と照合してください。"
            )
        else:
            from tools.guide_content_shared import faq_official_verify_answer

            text = faq_official_verify_answer(q, topic, EXAM, EXAM_SHORT, OFFICIAL)
    elif faq_index == 2:
        if "適合性" in q:
            text = (
                "適合性の原則では、顧客の知識・経験・財産・目的に照らし不適切な勧誘・販売を避けます。"
                "元本保証や必ず儲かると誤解させる説明は禁止され、顧客属性に応じた商品選定が要点です。"
            )
        elif "独学" in q:
            text = (
                f"独学でも対策可能です。外務員必携＋演習問題＋用語解説の3点セットで進め、"
                f"弱点は比較表・よくある誤答タブで補強してください。"
            )
        else:
            text = (
                f"「{topic}」は{EXAM}の出題範囲に含まれる論点です。"
                f"外務員必携の該当章と{OFFICIAL}の受験要項を照合し、"
                f"演習で誤答パターン（適合性・書面交付・説明義務など）を確認してください。"
            )
    else:
        if "おすすめ" in q or "進め方" in q or "何に使" in q:
            text = (
                f"①用語解説でキーワードを確認 ②{topic}関連の演習を解く "
                f"③誤答を比較表で整理 ④数日後に同じ設問を解き直し、"
                f"というサイクルが効率的です。外務員必携の該当章を並行して読んでください。"
            )
        elif "過去問" in q:
            text = (
                "過去問・演習問題は出題傾向把握と弱点発見に有効です。"
                "解きっぱなしにせず、用語解説へ戻る解き直しをセットにします。"
            )
        else:
            text = (
                f"読了後は、{topic}に関連する演習を5問以上解き、"
                f"間違えた選択肢を用語解説で確認してから関連ガイドへ進んでください。"
                f"解き直し日をカレンダーに入れると定着しやすくなります。"
            )
    return ensure_min(
        text,
        100,
        f"数値・主体・手順は{ORG}の最新案内と照合してください。",
    )


def action_items_for(topic: str, slug: str, genre: str) -> str:
    from tools.guide_content_shared import action_items_prose

    return action_items_prose(topic, EXAM, EXAM_SHORT, OFFICIAL, slug, genre)


def lead_for(row: dict[str, str], topic: str) -> str:
    from tools.guide_topic_normalize import exam_topic_clause

    genre = row.get("genre") or ""
    clause = exam_topic_clause(EXAM, topic, EXAM_SHORT)
    base = (
        f"{clause}、証券外務員試験で問われやすい論点と"
        f"学習の進め方を整理する記事です。"
    )
    if genre == "用語ハブ活用法":
        base += "用語解説で定義を確認したあと、演習と比較表で理解を深める流れを示します。"
    elif genre == "試験概要":
        base += "4分野の全体像と公式情報の確認方法から学習を始めたい人向けです。"
    else:
        base += f"外務員必携と{OFFICIAL}を参照しながら、演習・用語解説で弱点を補強する進め方をまとめます。"
    return ensure_min(base, 80, "本記事では試験本番で得点につながる理解の順序を示します。")


def meta_description_for(row: dict[str, str], topic: str) -> str:
    from tools.guide_topic_normalize import exam_topic_clause, topic_label

    genre = row.get("genre") or ""
    label = topic_label(topic, EXAM, EXAM_SHORT)
    if genre == "用語ハブ活用法":
        return (
            f"{EXAM}の「{label}」を試験対策向けに整理。"
            f"用語解説・演習・比較表との学習順と、外務員が押さえる論点を解説します。"
        )[:165]
    if genre == "試験概要":
        return (
            f"{EXAM}の概要・4分野・合格基準の確認方法。"
            f"公式情報の見方と、このサイトでの演習・用語解説の使い方をまとめます。"
        )[:165]
    if genre == "受験・申込":
        return (
            f"{EXAM}の受験資格・日程・申込手続きの確認ポイント。"
            f"申込前チェックリストと、学習開始までの流れを整理します。"
        )[:165]
    return (
        f"{exam_topic_clause(EXAM, topic, EXAM_SHORT)}、証券外務員試験で問われる論点と学習の進め方を解説。"
        f"公式情報の確認ポイントと演習・用語解説の活用法をまとめます。"
    )[:165]


def user_intent_for(topic: str, genre: str) -> str:
    from tools.guide_content_shared import user_intent_prose

    return user_intent_prose(topic, EXAM, EXAM_SHORT, OFFICIAL, genre)


def key_points_for(row: dict[str, str], topic: str) -> str:
    items: list[str] = []
    for i in range(1, 6):
        h = (row.get(f"section_{i}_heading") or "").strip()
        if h and len(h) <= 40:
            items.append(h)
    if len(items) < 3:
        items = [
            f"{topic}の試験論点を整理する",
            f"{OFFICIAL}で最新情報を確認する",
            "演習と用語解説で理解を確認する",
        ]
    return ";".join(items[:5])


def load_glossary_index(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    by_term: dict[str, dict[str, str]] = {}
    for r in rows:
        term = (r.get("term") or "").strip()
        if term:
            by_term[term] = r
    return by_term


def term_for_hub_slug(slug: str, title: str, glossary: dict[str, dict[str, str]]) -> tuple[str, str]:
    """slug/title から用語名と short_def を推定。"""
    t = title
    if "｜" in t:
        t = t.split("｜", 1)[-1]
    t = re.sub(r"とは[？?]?.*", "", t).strip()
    t = re.sub(r"（.*?）", "", t).strip()
    for term in sorted(glossary.keys(), key=len, reverse=True):
        if term in title or term in t:
            return term, (glossary[term].get("short_def") or glossary[term].get("definition") or "")[:120]
    slug_map = {
        "suitability-principle": "適合性の原則",
        "insider-trading": "インサイダー取引",
        "five-percent-rule": "5%ルール",
        "financial-instruments-exchange-act": "金融商品取引法",
        "important-matters-explanation": "重要事項説明",
        "gaimuin-license": "証券外務員",
    }
    if slug in slug_map:
        term = slug_map[slug]
        g = glossary.get(term, {})
        return term, (g.get("short_def") or "")[:120]
    return t or slug.replace("-", " "), ""
