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
        "name": name, "reading": reading,
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
・占術的根拠を各所に簡潔に添えてください"""

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

def call_part1(client, info):
    print("  📡 第1〜5章を生成中（1〜2分）...")
    prompt = base_info(info) + """

以下のXMLタグで出力してください：

<catchphrase>その人の本質と使命を表す印象的なキャッチコピー（20〜40文字・1〜2文）</catchphrase>

<chapter1>
第1章：天命の全体像（約500文字）
天命キーワード・魂のテーマ・数秘×四柱×星座の統合解釈・オーラの色と波動
</chapter1>

<chapter2>
第2章：使命と才能の詳細分析（約600文字）
3大才能と発揮方法・ユニークな強み・魂が喜ぶ活動・社会への役割
</chapter2>

<chapter3>
第3章：今の時代背景と天命の接点（約600文字）
2026〜2028年の時代の流れ（AI・経済・社会変化）・天命が今輝く理由・社会課題との交差・時代が求める役割
</chapter3>

<chapter4>
第4章：3年間の天命ロードマップ（約800文字）
2026年（今すぐ始めること：30日・3ヶ月・1年のアクション）
2027年（飛躍への助走：やること・避けること・チャンスの窓）
2028年（天命開花の年：使命が花開く具体的シナリオ）
</chapter4>

<chapter5>
第5章：今日からのアクションプラン20選（約1000文字）
仕事・キャリア5個／人間関係4個／学び4個／健康4個／お金3個
各アクションに占術的根拠を1行添える
</chapter5>"""
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8192,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text

def call_part2(client, info):
    print("  📡 第6〜11章を生成中（1〜2分）...")
    prompt = base_info(info) + """

以下のXMLタグで出力してください：

<chapter6>
第6章：ラッキー風水＆パワースポット（約500文字）
ラッキーカラー3色（使い方）・ラッキーナンバー3つ・国内パワースポット5箇所（具体的地名）・海外パワースポット3箇所・ラッキーアイテム3つ
吉方位・避けるべき方位は【算出済み占術データ】の吉方位・凶方位をそのまま使用し、再計算しないこと
</chapter6>

<chapter7>
第7章：人間関係と天命の仲間（約500文字）
相性の良い生まれ年・星座タイプ・出会うべきキーパーソン3タイプ・注意すべきパターン・理想のチーム像
</chapter7>

<chapter8>
第8章：魂の課題と乗り越え方（約500文字）
繰り返しやすいカルマのパターン・天命を妨げる3つのブロックと解除法・過去世テーマと今世での昇華・ネガティブサイクル脱出ワーク
</chapter8>

<chapter9>
第9章：月別・季節別の吉凶カレンダー（約600文字）
2026〜2027年の月別：エネルギーが高まる月3ヶ月・休息の月2ヶ月・新しいことを始めるベストタイミング・注意の時期と対処法
</chapter9>

<chapter10>
第10章：天命宣言文＆メッセージ（約400文字）
オリジナル天命宣言文（毎朝のアファメーション）・守護存在からのスピリチュアルメッセージ・10年後のビジョンレター・鑑定師からの最後の言葉
</chapter10>

<chapter11>
第11章：SNS戦略＆プロデューサー鑑定（約600文字）
最適なSNS媒体と理由（Instagram/note/YouTube/TikTok等）・発信コンセプト・世界観の方向性・フォロワーゼロからマネタイズへのステップ・月収100万円ロードマップ・向いているビジネスモデル
</chapter11>"""
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8192,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text

def parse_tag(text, tag):
    m = re.search(rf'<{tag}>(.*?)</{tag}>', text, re.DOTALL)
    return m.group(1).strip() if m else ""


# ── テキスト→HTML変換 ─────────────────────────────────────────

def text_to_html(text):
    blocks = re.split(r'\n{2,}', text.strip())
    html = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.split('\n')
        first = lines[0]

        if first.startswith('【要点】') or first.startswith('【'):
            inner = '<br>'.join(l for l in lines if l.strip())
            html.append(f'<div class="box-key">{inner}</div>')
        elif all(l.startswith('・') for l in lines if l.strip()):
            items = [l.lstrip('・ ') for l in lines if l.strip()]
            lis = ''.join(f'<li>{i}</li>' for i in items)
            html.append(f'<ul>{lis}</ul>')
        else:
            for line in lines:
                if line.strip():
                    html.append(f'<p>{line}</p>')
    return '\n'.join(html)


# ── HTML生成 ─────────────────────────────────────────────────

CHAPTER_META = {
    1:  ("天命の全体像",          "この人が生まれ持った天命と魂のテーマ"),
    2:  ("使命と才能の詳細分析",   "「私の天職は何か？」── 天命的な明確な答え"),
    3:  ("今の時代背景と天命の接点","2026年── 時代の波に乗る天命の輝き"),
    4:  ("3年間の天命ロードマップ", "2026〜2028 ｜ 天命開花への道筋"),
    5:  ("今日からのアクションプラン","今すぐできる20の具体的行動"),
    6:  ("ラッキー風水＆パワースポット","天命を加速させる場所・色・数字"),
    7:  ("人間関係と天命の仲間",    "天命を共に生きるキーパーソン"),
    8:  ("魂の課題と乗り越え方",    "カルマのパターンと解除法"),
    9:  ("月別・季節別 吉凶カレンダー","2026〜2027年のベストタイミング"),
    10: ("天命宣言文＆メッセージ",  "あなただけのオリジナル宣言"),
    11: ("SNS戦略＆プロデューサー鑑定","天命×SNS×ビジネスの最適解"),
}

def build_html(info, data):
    chapters_html = ""
    for i in range(1, 12):
        title, subtitle = CHAPTER_META[i]
        body = text_to_html(data.get(f"chapter{i}", "（内容を取得できませんでした）"))
        chapters_html += f"""
<div class="chapter page">
  <div class="ch-num">CHAPTER {i:02d}</div>
  <h2 class="ch-title">{title}</h2>
  <p class="ch-sub">{subtitle}</p>
  <div class="ch-divider"></div>
  <div class="ch-body">{body}</div>
</div>"""

    astro = (
        f"{info['bdate']}生&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"{info['zodiac']}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"LifePath {info['lifepath']}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"{info['kyusei']}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"年柱：{info['year_pillar']}&nbsp;"
        f"月柱：{data.get('month_pillar','—')}&nbsp;"
        f"日柱：{data.get('day_pillar','—')}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"総格：{info['soukaku']}画"
    )
    catch = data.get('catchphrase', '').replace('\n', '<br>')

    return HTML_TEMPLATE.replace("{{NAME}}", info['name']) \
                        .replace("{{READING}}", info['reading']) \
                        .replace("{{CATCH}}", catch) \
                        .replace("{{ASTRO}}", astro) \
                        .replace("{{CHAPTERS}}", chapters_html)


# ── HTMLテンプレート ──────────────────────────────────────────

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>天命鑑定書</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=Noto+Serif+JP:wght@300;400;600&display=swap" rel="stylesheet">
<style>
:root {
  --gold:    #C5A84B;
  --gold-l:  #E8D5A3;
  --bg:      #FAFAF7;
  --dark:    #1A1A1A;
  --text:    #2C2C2C;
  --purple:  #4B2D7F;
  --box-key: #F3EFF8;
}
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'Noto Serif JP',serif; background:#ece8e0; color:var(--text); }

@media print {
  body { background:white; }
  @page { size:A4 portrait; margin:0; }
  .page { page-break-after:always; box-shadow:none !important; }
}

/* ── Cover ── */
.cover {
  width:210mm; min-height:297mm;
  background:var(--bg);
  display:flex; flex-direction:column;
  align-items:center;
  margin:0 auto 8mm;
  box-shadow:0 4px 20px rgba(0,0,0,.15);
}
.gold-rule {
  width:100%; height:5px;
  background:linear-gradient(90deg,transparent 5%,var(--gold) 20%,var(--gold) 80%,transparent 95%);
}
.cover-inner {
  flex:1; display:flex; flex-direction:column;
  align-items:center; justify-content:center;
  padding:22mm 18mm; gap:5mm; text-align:center;
}
.c-header { font-family:'Cormorant Garamond',serif; font-size:8pt; letter-spacing:.5em; color:#999; }
.c-diamond { color:var(--gold); font-size:22pt; line-height:1; }
.c-label { font-size:9.5pt; letter-spacing:.65em; color:#aaa; }
.c-name {
  font-size:44pt; font-weight:300; letter-spacing:.35em;
  color:var(--dark); line-height:1.15; margin:4mm 0;
}
.c-reading { font-size:9pt; letter-spacing:.35em; color:var(--gold); }
.c-line { width:55mm; height:1px; background:var(--gold); margin:5mm auto; }
.c-catch { font-size:12pt; font-weight:300; line-height:2.3; color:var(--text); max-width:130mm; }
.c-astro { font-size:7.5pt; color:#888; margin-top:7mm; line-height:2.2; }
.c-edition { font-family:'Cormorant Garamond',serif; font-size:8pt; letter-spacing:.5em; color:#bbb; margin-top:4mm; }

/* ── Chapter ── */
.chapter {
  width:210mm; min-height:297mm;
  background:white;
  padding:20mm 18mm 16mm;
  margin:0 auto 8mm;
  box-shadow:0 4px 20px rgba(0,0,0,.12);
}
.ch-num {
  font-family:'Cormorant Garamond',serif;
  font-size:8pt; letter-spacing:.5em; color:#ccc;
  text-align:center; margin-bottom:4mm;
}
.ch-title {
  font-size:22pt; font-weight:400;
  text-align:center; color:var(--dark); margin-bottom:2.5mm;
}
.ch-sub {
  font-size:9pt; text-align:center; color:#999; margin-bottom:5mm;
}
.ch-divider {
  width:28mm; height:2px; background:var(--gold);
  margin:0 auto 9mm;
}

/* Content */
.ch-body p { font-size:9.5pt; line-height:2.1; margin-bottom:3mm; }
.ch-body ul { margin:4mm 0 4mm 2mm; }
.ch-body li {
  font-size:9.5pt; line-height:2; margin-bottom:2mm;
  list-style:none; padding-left:5mm; position:relative;
}
.ch-body li::before { content:'◇'; color:var(--gold); position:absolute; left:0; }

.box-key {
  background:var(--box-key);
  border-left:3px solid var(--purple);
  padding:5mm 7mm; border-radius:0 4px 4px 0;
  margin:5mm 0; font-size:9.5pt; line-height:2.1;
}
</style>
</head>
<body>

<div class="cover page">
  <div class="gold-rule"></div>
  <div class="cover-inner">
    <div class="c-header">CELESTIAL DESTINY READING &nbsp;✦&nbsp; PREMIUM EDITION</div>
    <div class="c-diamond">✦</div>
    <div class="c-label">天　命　鑑　定　書</div>
    <div class="c-name">{{NAME}}</div>
    <div class="c-reading">{{READING}}&nbsp;様</div>
    <div class="c-line"></div>
    <div class="c-catch">{{CATCH}}</div>
    <div class="c-astro">{{ASTRO}}</div>
    <div class="c-edition">CELESTIAL DESTINY EDITION</div>
  </div>
  <div class="gold-rule"></div>
</div>

{{CHAPTERS}}

</body>
</html>"""


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

    data = {"month_pillar": info["month_pillar"], "day_pillar": info["day_pillar"]}
    all_tags = ["catchphrase"] + [f"chapter{i}" for i in range(1,12)]
    for tag in all_tags:
        data[tag] = parse_tag(resp1, tag) or parse_tag(resp2, tag)

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
