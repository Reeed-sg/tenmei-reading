#!/usr/bin/env python3
"""
天命鑑定書 自動生成スクリプト
Usage: python generate_reading.py
"""

import os, re, sys
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from anthropic import Anthropic
except ImportError:
    print("pip install anthropic python-dotenv を実行してください")
    sys.exit(1)

# ── 占術計算 ────────────────────────────────────────────────
# 年柱・月柱・日柱・九星気学は fortune_calc.py で確定計算する（節気ベース）

from fortune_calc import lifepath, zodiac_sign, kyusei, year_pillar, month_pillar, day_pillar, lucky_directions, five_kaku


# ── 入力 ────────────────────────────────────────────────────

def ask(prompt, required=True):
    while True:
        v = input(f"  {prompt}: ").strip()
        if v or not required:
            return v
        print("  ※ 必須項目です")

def get_input():
    print("\n" + "═"*50)
    print("  天命鑑定書 生成システム")
    print("═"*50 + "\n")
    sei      = ask("姓")
    mei      = ask("名")
    name     = sei + mei
    reading  = ask("ふりがな")
    bdate    = ask("生年月日（例: 1984年2月19日）")
    gender   = ask("性別（女性/男性）")
    place    = ask("出生地（都道府県）")
    job      = ask("現在の職業・状況")
    concerns = ask("現在の悩みや課題")
    goals    = ask("目標や夢")
    sns      = ask("SNS・ビジネス目標（任意）", required=False)

    m = re.search(r'(\d{4})[年/\-](\d{1,2})[月/\-](\d{1,2})', bdate)
    if not m:
        print("\n❌ 生年月日の形式が認識できませんでした（例: 1984年2月19日）")
        sys.exit(1)
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))

    kyusei_star = kyusei(y, mo, d)
    directions  = lucky_directions(kyusei_star, datetime.now().year)
    kaku = five_kaku(sei, mei)

    astro = {
        "lifepath":    lifepath(y, mo, d),
        "zodiac":      zodiac_sign(mo, d),
        "kyusei":      kyusei_star,
        "year_pillar": year_pillar(y, mo, d),
        "month_pillar": month_pillar(y, mo, d),
        "day_pillar":   day_pillar(y, mo, d),
        "directions":  directions,
        "directions_text": (
            f"今年（{datetime.now().year}年）の吉方位：{'・'.join(directions['吉方位']) or 'なし'}／"
            f"避けるべき方位：五黄殺{directions['五黄殺'] or 'なし'}・"
            f"暗剣殺{directions['暗剣殺'] or 'なし'}・歳破{directions['歳破']}・"
            f"本命殺{directions['本命殺'] or 'なし'}・本命的殺{directions['本命的殺'] or 'なし'}"
        ),
        "tenkaku": kaku["天格"], "jinkaku": kaku["人格"], "chikaku": kaku["地格"],
        "gaikaku": kaku["外格"], "soukaku": kaku["総格"],
        "soukaku_missing": kaku["missing"],
    }
    if kaku["missing"]:
        print(f"  ⚠ 姓名判断：画数不明の文字があります（{''.join(kaku['missing'])}）。値は不完全な可能性があります。")

    return {
        "name": name, "sei": sei, "mei": mei, "reading": reading,
        "bdate": f"{y}年{mo}月{d}日",
        "gender": gender, "place": place,
        "job": job, "concerns": concerns,
        "goals": goals, "sns": sns or "なし",
        **astro,
    }


# ── Claude API ───────────────────────────────────────────────

SYSTEM = """あなたは東洋・西洋の占術を統合した世界最高峰の天命鑑定師です。
指示された章のみを、必ず以下のXMLタグで囲んで出力してください。
・テキストのみで記述し、HTMLタグは一切使わないでください
・段落は空行で区切ってください
・箇条書きは「・」で始めてください
・各章の冒頭に【要点】として3行サマリーを必ず入れてください
・対象者への語りかけ口調（〜ですよ、〜ですね）で書いてください
・占術的根拠を各所に簡潔に添えてください
・指示された文字数を必ず満たすこと（短すぎる出力は不可）
・各章は指示された数の小見出しをすべて含め、それぞれ「「見出し」── 解説のサブタイトル」形式のヘッダーを付けたうえで、
  見出しごとに複数の段落にわたる詳しい解説を書く（見出しだけで終わらせない）"""

def base_info(info):
    return f"""氏名：{info['name']}／{info['reading']}
生年月日：{info['bdate']}（{info['gender']}・{info['place']}出身）
職業・状況：{info['job']}
悩み・課題：{info['concerns']}
目標・夢：{info['goals']}
SNS・ビジネス目標：{info['sns']}

【算出済み占術データ】（すでに正確に算出済みのため、再計算せずそのまま使用してください）
西洋星座：{info['zodiac']}／LifePath：{info['lifepath']}／九星気学：{info['kyusei']}
年柱：{info['year_pillar']}／月柱：{info['month_pillar']}／日柱：{info['day_pillar']}
{info['directions_text']}
姓名判断（五格）：天格{info['tenkaku']}／人格{info['jinkaku']}／地格{info['chikaku']}／外格{info['gaikaku']}／総格{info['soukaku']}"""

def _roadmap_years():
    """現在日時を基準にロードマップの3年間を返す（例：2026年7月起点なら 2026後半/2027/2028）"""
    now = datetime.now()
    return now.year, now.year + 1, now.year + 2, now.month

def call_part1(client, info):
    print("  📡 第1〜2章を生成中（1〜2分）...")
    first_name = info['mei']
    y1, y2, y3, m1 = _roadmap_years()
    prompt = base_info(info) + f"""

呼びかける名前：{first_name}さん
今日の時点：{y1}年{m1}月（占いの起点は必ずここから。{y1}年の前半にはもう触れず「{y1}年後半」として語ること）

<catchphrase>その人の本質と使命を表す印象的なキャッチコピー（20〜40文字・1〜2文。名前は入れない）</catchphrase>
<edition_name>その人のエネルギーを表す英語2〜3語のエディション名（例：OCEAN EMBER EDITION / SILENT FIRE EDITION）大文字のみ</edition_name>

<chapter1>第1章：天命概論（約750文字）
冒頭は「{first_name}さん、」で始める。以下4つの小見出しをすべて含める：
「魂のテーマとこの世に生まれた根本理由」── 生年月日の背景と占術データから、なぜこの魂として生まれてきたのかを解き明かす
「数秘術×四柱推命・九星気学の視点」── LifePathと年柱・月柱・日柱・九星気学の組み合わせが示す性質
「西洋占星術の視点」── 星座が示す本質
「オーラの色と波動の特徴」── 色・周波数帯・周囲に与える印象</chapter1>

<chapter2>第2章：才能と使命（約900文字）
以下4つの小見出しをすべて含める：
「3大天賦の才能」── 「才能名」── 占術的根拠 の形式で3つ、各才能に具体的な活かし方を添える
「他者には真似できないユニークな強み」── 占術データの組み合わせが生む差別化ポイント
「魂が最も喜ぶ活動・仕事・表現スタイル」
「社会に対して果たすべき具体的な役割」</chapter2>"""
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8192,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text

def call_part2(client, info):
    print("  📡 第3〜5章を生成中（1〜2分）...")
    first_name = info['mei']
    y1, y2, y3, m1 = _roadmap_years()
    prompt = base_info(info) + f"""

呼びかける名前：{first_name}さん（必ずこの名前で統一すること）
今日の時点：{y1}年{m1}月（3年ロードマップは「{y1}年後半」「{y2}年」「{y3}年」の3期間で構成すること。{y1}年の前半には触れない）

<chapter3>第3章：時代文脈（約900文字）
以下3つの小見出しをすべて含める：
「{y1}〜{y3}年の時代の大きな流れ」── AI・経済・社会変化の具体的トレンドとその人の天命の交差点
「なぜ今こそこの人の天命が輝くのか」── 占術データ（年齢・命式）と時代の一致を具体的に
「時代が求めているこの人の役割」</chapter3>

<chapter4>第4章：3年ロードマップ（約1200文字）
「{y1}年後半」「{y2}年」「{y3}年」の3つの見出しに分け、各年について
・その年の占術的テーマ（九星気学・干支等）
・具体的にやるべきこと
・避けるべきこと
・月収目標の目安
を書く。{y1}年後半は今日から始められる30日以内・3ヶ月以内のアクションを含める</chapter4>

<chapter5>第5章：今日からの行動（約1500文字）
仕事・キャリア／人間関係・コミュニティ／学び・スキルアップ／健康・エネルギー管理／お金・豊かさ
の5カテゴリすべてに小見出しを立て、各カテゴリ3〜4個・合計約20個の具体的アクションを列挙する。各アクションに占術的根拠を1行添える</chapter5>"""
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8192,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text

def call_part3(client, info):
    print("  📡 第6〜8章を生成中（1〜2分）...")
    first_name = info['mei']
    prompt = base_info(info) + f"""

呼びかける名前：{first_name}さん（必ずこの名前で統一すること）

<chapter6>第6章：ラッキー風水＆パワースポット（約750文字）
以下4つの小見出しをすべて含める：
「ラッキーカラー・ナンバー・アイテム」── 3色とその使い方、ラッキーナンバー、アイテムの意味
「国内パワースポット5箇所」── 具体的な地名と、なぜその人に合うのかの占術的理由を各1〜2文で
「海外パワースポット3箇所」── 同様に
「吉方位・凶方位」── 【算出済み占術データ】の吉方位・凶方位をそのまま使用し、再計算しないこと。方位ごとの活用法を添える</chapter6>

<chapter7>第7章：人間関係と天命の仲間（約750文字）
以下3つの小見出しをすべて含める：
「天命を加速させる相性」── 相性の良い生まれ年タイプ・星座タイプを具体的に
「出会うべきキーパーソン3タイプ」── 各タイプに名前を付けて簡潔に説明
「注意すべき人間関係のパターン」── この人が陥りやすい関係性の癖と対処法</chapter7>

<chapter8>第8章：魂の課題と乗り越え方（約750文字）
以下3つの小見出しをすべて含める：
「繰り返しやすいカルマのパターン」
「天命を妨げる3つのブロックと解除法」── ブロックごとに解除法をセットで
「過去世のテーマと今世での昇華方法」</chapter8>"""
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8192,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text

def call_part4(client, info):
    print("  📡 第9〜11章を生成中（1〜2分）...")
    first_name = info['mei']
    y1, y2, y3, m1 = _roadmap_years()
    prompt = base_info(info) + f"""

呼びかける名前：{first_name}さん（必ずこの名前で統一すること）
今日の時点：{y1}年{m1}月（吉凶カレンダーは{y1}年{m1}月〜{y2}年12月の期間で書くこと。{y1}年の{m1}月より前の月には触れない）

<chapter9>第9章：月別・季節別の吉凶カレンダー（約900文字）
{y1}年{m1}月から{y2}年12月までを対象に、季節・四半期ごとに小見出しを立てて
エネルギーが高まる時期・休息推奨の時期・新しいことを始めるベストタイミング・注意すべき時期と対処法を書く</chapter9>

<chapter10>第10章：天命宣言文＆メッセージ（約600文字）
以下3つの小見出しをすべて含める：
「天命宣言文」── 毎朝声に出して読むアファメーション形式（5〜7行）
「守護存在からのスピリチュアルメッセージ」
「10年後のビジョンレター」── 10年後の自分から今の{first_name}さんへの手紙形式（簡潔に）</chapter10>

<chapter11>第11章：SNS戦略＆プロデューサー鑑定（約900文字）
以下4つの小見出しをすべて含める：
「最適なSNS媒体と理由」── Instagram/note/YouTube/TikTok等から具体的に選び占術的根拠を添える
「発信コンセプト・世界観の方向性」
「フォロワーゼロからマネタイズへのステップ」── 具体的な段階を{y1}年後半〜{y3}年で
「向いているビジネスモデル」</chapter11>

""" + f"""<from_message>鑑定師から{first_name}さんへの個人的なメッセージ（400〜500文字）。
・「{first_name}さん、」で書き始める
・その人が書いた悩みや言葉を引用しながら、天命から見たポジティブな真実を伝える
・動けていない・自信がないといった課題を、占術的根拠で肯定的に解釈し直す
・具体的な最初の一歩を1つだけ提案する
・温かく背中を押す言葉で締める
・重要な気づきや励ましの言葉は **このように** ダブルアスタリスクで囲む（3〜4箇所）</from_message>"""
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8192,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text

# ── HTML生成（テンプレート・変換ロジックは report_html.py に共通化） ──

from report_html import HTML_TEMPLATE, text_to_html, parse_tag, build_astro_cards

CHAPTER_META = {
    1:  ("天命概論",               ""),
    2:  ("才能と使命",             "「私の天職は何か？」── 天命的な明確な答え"),
    3:  ("時代文脈",               "時代の波に乗る天命の輝き"),
    4:  ("3年ロードマップ",         "天命開花への道筋"),
    5:  ("今日からの行動",          "今すぐできる具体的アクション"),
    6:  ("ラッキー風水＆パワースポット","天命を加速させる場所・色・数字"),
    7:  ("人間関係と天命の仲間",     "天命を共に生きるキーパーソン"),
    8:  ("魂の課題と乗り越え方",     "カルマのパターンと解除法"),
    9:  ("吉凶カレンダー",          "ベストタイミングを知る"),
    10: ("天命宣言文",              "あなただけのオリジナル宣言"),
    11: ("SNS＆ビジネス戦略",       "天命×SNS×ビジネスの最適解"),
}

def build_html(info, data, sender="YURI（結梨嘉望）"):
    chapters_html = ""
    for i in range(1, 12):
        title, subtitle = CHAPTER_META[i]
        body = text_to_html(data.get(f"chapter{i}", ""))

        prefix = ""
        if i == 1:
            catch_fmt = data.get('catchphrase', '').replace('\n', '<br>')
            prefix = f"""
<div class="thesis-box">
  <div class="thesis-label">✦ YOUR CELESTIAL THESIS ✦</div>
  <div class="thesis-catch">{catch_fmt}</div>
</div>
{build_astro_cards(info, data)}"""

        sub_html = f'<p class="ch-sub">{subtitle}</p>' if subtitle else ''
        chapters_html += f"""
<div class="chapter">
  <div class="ch-num">CHAPTER {i:02d}</div>
  <h2 class="ch-title">{title}</h2>
  {sub_html}
  <div class="ch-divider"></div>
  {prefix}
  <div class="ch-body">{body}</div>
</div>"""

    mp = data.get('month_pillar', '—')
    dp = data.get('day_pillar', '—')
    astro = (
        f"{info['bdate']}生&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"{info['zodiac']}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"LifePath {info['lifepath']}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"{info['kyusei']}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"年柱：{info['year_pillar']}&nbsp;月柱：{mp}&nbsp;日柱：{dp}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"総格：{info['soukaku']}画"
    )
    catch   = data.get('catchphrase', '').replace('\n', '<br>')
    edition = data.get('edition_name', 'CELESTIAL DESTINY EDITION')

    raw_msg = data.get('from_message', '')
    def fmt_from_msg(text):
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        paras = re.split(r'\n{1,}', text.strip())
        return '\n'.join(f'<p>{p}</p>' for p in paras if p.strip())
    from_msg_html = fmt_from_msg(raw_msg)
    sender_plain = re.sub(r'（.*?）', '', sender).strip()

    return (HTML_TEMPLATE
            .replace("{{DOC_TITLE}}",    "天命鑑定書")
            .replace("{{DOC_LABEL}}",    "天　命　鑑　定　書")
            .replace("{{HEADER_EN}}",    "CELESTIAL DESTINY READING &nbsp;✦&nbsp; PREMIUM EDITION")
            .replace("{{SIGNER_TITLE}}", "天命鑑定士")
            .replace("{{FOOTER_COPY}}",  "本鑑定書は占術・数秘術・算命学・九星気学・姓名判断を統合した天命鑑定です。")
            .replace("{{NAME}}",         info['name'])
            .replace("{{READING}}",      info['reading'])
            .replace("{{CATCH}}",        catch)
            .replace("{{ASTRO}}",        astro)
            .replace("{{EDITION}}",      edition)
            .replace("{{SENDER}}",       sender)
            .replace("{{SENDER_PLAIN}}", sender_plain)
            .replace("{{FROM_MSG}}",     from_msg_html)
            .replace("{{CHAPTERS}}",     chapters_html))


# ── メイン ───────────────────────────────────────────────────

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY が設定されていません。.env ファイルを確認してください。")
        sys.exit(1)

    client = Anthropic(api_key=api_key)
    info   = get_input()

    print(f"\n✨ {info['name']} 様の鑑定書を生成します...")
    print(f"   {info['zodiac']} ／ LifePath {info['lifepath']} ／ {info['kyusei']} ／ "
          f"年柱：{info['year_pillar']} 月柱：{info['month_pillar']} 日柱：{info['day_pillar']}\n")

    resp1 = call_part1(client, info)
    resp2 = call_part2(client, info)
    resp3 = call_part3(client, info)
    resp4 = call_part4(client, info)

    responses = [resp1, resp2, resp3, resp4]
    data = {"month_pillar": info["month_pillar"], "day_pillar": info["day_pillar"]}
    all_tags = ["catchphrase", "edition_name", "from_message"] + [f"chapter{i}" for i in range(1,12)]
    for tag in all_tags:
        data[tag] = next((v for r in responses if (v := parse_tag(r, tag))), "")

    print("  📄 HTML生成中...")
    html = build_html(info, data)

    out_dir = Path(__file__).parent / "output"
    out_dir.mkdir(exist_ok=True)
    ts       = datetime.now().strftime("%Y%m%d_%H%M")
    out_path = out_dir / f"tenmei_{info['name']}_{ts}.html"
    out_path.write_text(html, encoding="utf-8")

    print(f"\n✅ 完成！")
    print(f"   → {out_path}")
    print("   Chromeで開いて「印刷 → PDFに保存」で完成です。\n")

if __name__ == "__main__":
    main()
