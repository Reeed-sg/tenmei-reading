"""
鑑定書HTML生成の共通部品（天命鑑定書・ビジネス鑑定書で共用）

紺×ゴールドのビジュアルテンプレートと、AI出力テキスト→HTML変換ロジックをまとめている。
書類名（天命鑑定書／ビジネス鑑定書）はテンプレート内のプレースホルダーで差し替える。
"""
import re

ZODIAC_DESC = {
    "山羊座 ♑": "粘り強さ・現実的野心・責任感",
    "水瓶座 ♒": "革新・自由・先見性",
    "魚座 ♓":   "共感・直感・スピリチュアル感受性",
    "牡羊座 ♈": "情熱・先駆・行動力",
    "牡牛座 ♉": "安定・美・現実的豊かさ",
    "双子座 ♊": "好奇心・コミュニケーション・多才",
    "蟹座 ♋":   "感受性・守護・家族愛",
    "獅子座 ♌": "創造・表現・リーダーシップ",
    "乙女座 ♍": "分析・奉仕・完璧主義",
    "天秤座 ♎": "調和・美・対話",
    "蠍座 ♏":   "変容・洞察・深い情熱",
    "射手座 ♐": "自由・探求・哲学",
}
LIFEPATH_DESC = {
    1: "先駆者・リーダー", 2: "協調・直感", 3: "創造・喜び・表現",
    4: "基盤・構築・忍耐", 5: "自由・変化・冒険", 6: "愛・責任・調和",
    7: "探求・内省・哲学", 8: "権力・豊かさ", 9: "奉仕・慈悲・完成",
    11: "直感・啓示（マスター）", 22: "大建設家（マスター）", 33: "愛と癒しの師（マスター）",
}
KYUSEI_DESC = {
    "一白水星": "柔軟・適応・深い内省",  "二黒土星": "母性・勤勉・包容力",
    "三碧木星": "行動・若さ・突破力",    "四緑木星": "成長・信頼・人脈",
    "五黄土星": "カリスマ・中心・帝王運", "六白金星": "誠実・完璧・高貴",
    "七赤金星": "喜び・口才・社交性",    "八白土星": "変革・節目・山の力",
    "九紫火星": "直感・美・輝く知性",
}


def parse_tag(text, tag):
    m = re.search(rf'<{tag}>(.*?)</{tag}>', text, re.DOTALL)
    return m.group(1).strip() if m else ""


def parse_table_tag(text, tag):
    """<tag>\nfield1|field2|field3\n...\n</tag> → [[field1,field2,field3], ...]"""
    raw = parse_tag(text, tag)
    rows = []
    for line in raw.strip().split('\n'):
        line = line.strip().strip('|')
        if not line:
            continue
        rows.append([c.strip() for c in line.split('|')])
    return rows


def text_to_html(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)  # AIが使う**強調**をHTML化
    blocks = re.split(r'\n{2,}', text.strip())
    html = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.split('\n')
        first = lines[0]
        if first.startswith('【'):
            inner = '<br>'.join(l for l in lines if l.strip())
            html.append(f'<div class="box-key">{inner}</div>')
        elif re.match(r'^「.+」', first):
            # 「見出し」── サブタイトル 形式
            html.append(f'<div class="ch-heading">{first}</div>')
            rest = '\n'.join(lines[1:]).strip()
            if rest:
                for line in rest.split('\n'):
                    if line.strip():
                        if line.strip().startswith('・'):
                            html.append(f'<ul><li>{line.lstrip("・ ")}</li></ul>')
                        else:
                            html.append(f'<p>{line}</p>')
        elif all(l.strip().startswith('・') for l in lines if l.strip()):
            lis = ''.join(f'<li>{l.lstrip("・ ")}</li>' for l in lines if l.strip())
            html.append(f'<ul>{lis}</ul>')
        else:
            for line in lines:
                if line.strip():
                    html.append(f'<p>{line}</p>')
    return '\n'.join(html)


def build_astro_cards(f, data, extra_cards=None):
    mp = data.get('month_pillar', '—')
    dp = data.get('day_pillar', '—')
    z  = f['zodiac']
    lp = f['lifepath']
    ky = f['kyusei']
    yp = f['year_pillar']
    cards = [
        ("WESTERN",     "ac-w", z,              ZODIAC_DESC.get(z, "")),
        ("NUMEROLOGY",  "ac-n", f"LifePath {lp}", LIFEPATH_DESC.get(lp, "")),
        ("九星気学",    "ac-k", ky,             KYUSEI_DESC.get(ky, "")),
        ("年柱",        "ac-y", yp,             ""),
        ("月柱",        "ac-m", mp,             ""),
        ("日柱 ★",     "ac-d", dp,             ""),
        ("姓名判断",    "ac-s", f"総格 {f['soukaku']}画",
         (f"天格{f['tenkaku']}・人格{f['jinkaku']}・地格{f['chikaku']}・外格{f['gaikaku']}"
          if f.get('tenkaku') is not None else "")),
    ]
    if extra_cards:
        cards += extra_cards
    html = '<div class="astro-grid">'
    for label, cls, title, desc in cards:
        html += f'''<div class="astro-card {cls}">
  <div class="ac-label">{label}</div>
  <div class="ac-title">{title}</div>
  {"<div class='ac-desc'>"+desc+"</div>" if desc else ""}
</div>'''
    html += '</div>'
    return html


def build_swatches(colors):
    """colors: [(name, hex), ...] 4色程度のラッキーカラー帯"""
    if not colors:
        return ""
    html = '<div class="swatch-row">'
    for name, hexcode in colors:
        html += f'''<div class="swatch-item">
  <div class="swatch-color" style="background:{hexcode}"></div>
  <div class="swatch-name">{name}</div>
  <div class="swatch-hex">{hexcode}</div>
</div>'''
    html += '</div>'
    return html


def build_info_grid(cards, columns=3):
    """cards: [{"label":..., "title":..., "desc":..., "badge":...(optional)}]"""
    if not cards:
        return ""
    html = f'<div class="info-grid" style="grid-template-columns:repeat({columns},1fr)">'
    for c in cards:
        badge_html = f'<div class="info-badge">{c["badge"]}</div>' if c.get("badge") else ''
        desc_html = f'<div class="info-desc">{c["desc"]}</div>' if c.get("desc") else ''
        html += f'''<div class="info-card">
  {badge_html}
  <div class="info-label">{c.get("label","")}</div>
  <div class="info-title">{c.get("title","")}</div>
  {desc_html}
</div>'''
    html += '</div>'
    return html


def build_table(headers, rows, highlight_last=False):
    """headers: [str,...] / rows: [[str,...], ...]"""
    if not rows:
        return ""
    html = '<table class="report-table"><thead><tr>'
    for h in headers:
        html += f'<th>{h}</th>'
    html += '</tr></thead><tbody>'
    for i, row in enumerate(rows):
        cls = ' class="table-highlight"' if highlight_last and i == len(rows) - 1 else ''
        html += f'<tr{cls}>' + ''.join(f'<td>{cell}</td>' for cell in row) + '</tr>'
    html += '</tbody></table>'
    return html


def build_score_bars(items):
    """items: [(label, score:int0-100, desc), ...]"""
    if not items:
        return ""
    html = '<div class="score-bars">'
    for label, score, desc in items:
        try:
            score_i = max(0, min(100, int(re.sub(r'[^0-9]', '', str(score)) or 0)))
        except ValueError:
            score_i = 0
        html += f'''<div class="score-bar-item">
  <div class="score-bar-head"><span class="score-bar-label">{label}</span><span class="score-bar-num">{score_i}点</span></div>
  <div class="score-bar-track"><div class="score-bar-fill" style="width:{score_i}%"></div></div>
  <div class="score-bar-desc">{desc}</div>
</div>'''
    html += '</div>'
    return html


def build_calendar_grid(months):
    """months: [(month_label, stars:int1-5, desc), ...]"""
    if not months:
        return ""
    html = '<div class="cal-grid">'
    for label, stars, desc in months:
        try:
            stars_i = max(1, min(5, int(re.sub(r'[^0-9]', '', str(stars)) or 3)))
        except ValueError:
            stars_i = 3
        star_str = '★' * stars_i + '☆' * (5 - stars_i)
        html += f'''<div class="cal-card">
  <div class="cal-month">{label}</div>
  <div class="cal-stars">{star_str}</div>
  <div class="cal-desc">{desc}</div>
</div>'''
    html += '</div>'
    return html


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>{{DOC_TITLE}} - {{NAME}}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=Noto+Serif+JP:wght@300;400;600&display=swap" rel="stylesheet">
<style>
:root {
  --gold:#C5A84B; --gold-l:#E8D5A3; --gold-d:#A8862E;
  --bg:#FAFAF7; --dark:#1A1A1A; --text:#2C2C2C;
  --purple:#4B2D7F; --navy:#1a1a3a; --box-key:#F3EFF8;
}
* { margin:0; padding:0; box-sizing:border-box; -webkit-print-color-adjust:exact; print-color-adjust:exact; color-adjust:exact; }
body { font-family:'Noto Serif JP',serif; background:#e8e4de; color:var(--text); }

@media print {
  body { background:white; }
  @page { size:A4 portrait; margin:0; }
  .cover { page-break-after:always !important; box-shadow:none !important; }
  .chapter { page-break-before:always !important; box-shadow:none !important; }
  .sig-page { page-break-before:always !important; box-shadow:none !important; }
}

/* ── カバー ── */
.cover {
  width:210mm; height:297mm;
  background:var(--bg);
  display:flex; flex-direction:column; align-items:center;
  margin:0 auto 8mm; box-shadow:0 4px 24px rgba(0,0,0,.18);
  overflow:hidden;
}
.gold-rule { width:100%; height:6px; flex-shrink:0;
  background:linear-gradient(90deg,transparent 3%,var(--gold-d) 15%,var(--gold) 50%,var(--gold-d) 85%,transparent 97%); }
.cover-inner {
  flex:1; display:flex; flex-direction:column;
  align-items:center; justify-content:center;
  padding:16mm 20mm; gap:4mm; text-align:center;
  min-height:0;
}
.c-header { font-family:'Cormorant Garamond',serif; font-size:7.5pt; letter-spacing:.55em; color:#b0a090; }
.c-diamond { color:var(--gold); font-size:26pt; line-height:1; margin:2mm 0; }
.c-label { font-size:8.5pt; letter-spacing:.8em; color:#c0b090; margin-bottom:2mm; }
.c-name { font-size:46pt; font-weight:300; letter-spacing:.4em; color:var(--dark); line-height:1.2; }
.c-reading { font-size:9pt; letter-spacing:.4em; color:var(--gold); margin-top:1mm; }
.c-line { width:52mm; height:1px; background:var(--gold); margin:5mm auto; }
.c-catch { font-size:13.5pt; font-weight:300; line-height:2.2; color:var(--text); max-width:128mm; }
.c-astro { font-size:8pt; color:#999; margin-top:8mm; line-height:2.4; letter-spacing:.02em; }
.c-edition { font-family:'Cormorant Garamond',serif; font-size:8pt; letter-spacing:.55em; color:#c0a870; margin-top:3mm; }

/* ── チャプター共通 ── */
.chapter {
  width:210mm; min-height:297mm; background:white;
  padding:18mm 18mm 14mm;
  margin:0 auto 8mm; box-shadow:0 4px 20px rgba(0,0,0,.12);
  /* 章が複数ページにまたがる場合、ページの継続部分にも上下paddingを複製する
     （これがないと1ページ目以降の継続ページは上余白ゼロで文章が用紙端から始まってしまう） */
  box-decoration-break: clone;
  -webkit-box-decoration-break: clone;
}
.ch-num { font-family:'Cormorant Garamond',serif; font-size:8.7pt; letter-spacing:.5em; color:#ccc; text-align:center; margin-bottom:3mm; }
.ch-title { font-size:17.5pt; font-weight:600; text-align:center; color:var(--dark); margin-bottom:2mm; }
.ch-sub { font-size:10.7pt; text-align:center; color:#888; margin-bottom:4mm; line-height:1.8; }
.ch-divider { width:28mm; height:2px; background:var(--gold); margin:0 auto 8mm; }

/* ── 本文（ページ内収まり調整のため本文10.8pt・行間2.0に微調整） ── */
/* 見出し・箇条書き・要点ボックスは1ページに収まりきらない場合、
   途中で分割せず塊ごと次ページへ送る（page-break-inside回避） */
.ch-body p { font-size:10.8pt; line-height:2.0; margin-bottom:4mm; break-inside:avoid; page-break-inside:avoid; }
.ch-body ul { margin:3.5mm 0 3.5mm 2mm; }
.ch-body li { font-size:10.8pt; line-height:1.9; margin-bottom:2.5mm; list-style:none; padding-left:5mm; position:relative; break-inside:avoid; page-break-inside:avoid; }
.ch-body li::before { content:'◇'; color:var(--gold); position:absolute; left:0; }
.ch-body strong { color:var(--gold-d); font-weight:600; }
.box-key { background:var(--box-key); border-left:3px solid var(--purple); padding:4.5mm 6.5mm; border-radius:0 4px 4px 0; margin:5.5mm 0; font-size:10.3pt; line-height:2.0; break-inside:avoid; page-break-inside:avoid; }
.ch-heading { font-size:12.7pt; font-weight:600; color:var(--dark); margin:7mm 0 2.5mm; border-bottom:1px solid #e8d5a3; padding-bottom:1.5mm; break-after:avoid; page-break-after:avoid; break-inside:avoid; page-break-inside:avoid; }

/* ── Chapter 1 専用：ダークシテシスボックス ── */
.thesis-box {
  background:var(--navy); color:white;
  border-radius:4px; padding:6mm 10mm; margin:4mm 0 6mm;
  text-align:center;
  break-inside:avoid; page-break-inside:avoid;
}
.thesis-label { font-family:'Cormorant Garamond',serif; font-size:7.5pt; letter-spacing:.5em; color:var(--gold); margin-bottom:3mm; }
.thesis-catch { font-size:14.5pt; font-weight:300; line-height:1.9; color:#f5f0e8; }
.thesis-sub { font-size:10pt; font-style:italic; color:#c5a84b; margin-top:2mm; line-height:1.7; }

/* ── Chapter 1 専用：姓名判断・五格リーディング ── */
.gokaku-box { background:#F3EFF8; border:1px solid #e0d5ec; border-radius:4px; padding:5mm 7mm; margin:0 0 6mm; break-inside:avoid; page-break-inside:avoid; }
.gokaku-label { font-family:'Cormorant Garamond',serif; font-size:7.5pt; letter-spacing:.4em; color:var(--purple); text-align:center; margin-bottom:2.5mm; }
.gokaku-box p { font-size:9.7pt; line-height:1.75; color:var(--text); margin-bottom:2mm; }
.gokaku-box p:last-child { margin-bottom:0; }

/* ── Chapter 1 専用：星術カード ── */
.astro-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:3mm; margin:4mm 0 6mm; break-inside:avoid; page-break-inside:avoid; }
.astro-card { padding:3mm 3mm; border-radius:3px; text-align:center; }
.ac-w  { background:#fce8e8; }
.ac-n  { background:#fff0dc; }
.ac-k  { background:#e8eeff; }
.ac-y  { background:#f5f5f5; border:1px solid #ddd; }
.ac-m  { background:#f0f5ff; border:1px solid #dde; }
.ac-d  { background:#1a1a3a; color:white; }
.ac-s  { background:#f3eff8; border:1px solid #e0d5ec; }
.ac-label { font-family:'Cormorant Garamond',serif; font-size:6.5pt; letter-spacing:.35em; color:#999; margin-bottom:1.5mm; }
.ac-d .ac-label { color:#9090b0; }
.ac-title { font-size:13pt; font-weight:600; line-height:1.3; }
.ac-d .ac-title { color:#e0d8f0; }
.ac-desc { font-size:7.5pt; line-height:1.6; color:#666; margin-top:1.5mm; }
.ac-d .ac-desc { color:#a0a0c0; }

/* ── ラッキーカラー・スウォッチ ── */
.swatch-row { display:grid; grid-template-columns:repeat(4,1fr); gap:3mm; margin:5mm 0 7mm; break-inside:avoid; page-break-inside:avoid; }
.swatch-item { text-align:center; }
.swatch-color { width:100%; height:16mm; border-radius:3px; margin-bottom:2mm; box-shadow:inset 0 0 0 1px rgba(0,0,0,.06); }
.swatch-name { font-size:8.5pt; font-weight:600; color:var(--text); }
.swatch-hex { font-family:'Cormorant Garamond',serif; font-size:7.5pt; color:#999; letter-spacing:.05em; }

/* ── 汎用情報カードグリッド（ラッキーアイテム・パワースポット・天職案・肩書き案・ベンチマーク） ── */
.info-grid { display:grid; gap:3mm; margin:4mm 0 5mm; }
.info-card { background:#FAFAF7; border:1px solid #ece5d8; border-radius:4px; padding:4mm 4mm; position:relative; break-inside:avoid; page-break-inside:avoid; }
.info-badge { display:inline-block; font-family:'Cormorant Garamond',serif; font-size:7pt; letter-spacing:.12em; color:var(--gold-d); background:var(--gold-l); border-radius:2px; padding:.8mm 2.2mm; margin-bottom:2mm; }
.info-label { font-family:'Cormorant Garamond',serif; font-size:7pt; letter-spacing:.25em; color:#aaa; margin-bottom:1mm; }
.info-title { font-size:11.5pt; font-weight:600; color:var(--dark); margin-bottom:1.5mm; line-height:1.4; }
.info-desc { font-size:8.7pt; line-height:1.7; color:#666; }

/* ── テーブル（収益モデル等） ── */
.report-table { width:100%; border-collapse:collapse; margin:4mm 0 6mm; font-size:9.4pt; }
.report-table th { background:var(--navy); color:#f0ece0; text-align:left; padding:2.4mm 3.5mm; font-weight:500; letter-spacing:.03em; }
.report-table td { padding:2.2mm 3.5mm; border-bottom:1px solid #ece5d8; }
.report-table tr { break-inside:avoid; page-break-inside:avoid; }
.report-table tr:nth-child(even) td { background:#FAFAF7; }
.report-table .table-highlight td { background:var(--gold-l); font-weight:600; color:var(--gold-d); border-top:1.5px solid var(--gold); }

/* ── スコアバー（SNS戦略等） ── */
.score-bars { margin:4mm 0 6mm; }
.score-bar-item { margin-bottom:3.5mm; break-inside:avoid; page-break-inside:avoid; }
.score-bar-head { display:flex; justify-content:space-between; align-items:baseline; margin-bottom:1.2mm; }
.score-bar-label { font-size:10.3pt; font-weight:600; color:var(--dark); }
.score-bar-num { font-family:'Cormorant Garamond',serif; font-size:11pt; color:var(--gold-d); font-weight:600; }
.score-bar-track { width:100%; height:2.4mm; background:#ece5d8; border-radius:2mm; overflow:hidden; margin-bottom:1.4mm; }
.score-bar-fill { height:100%; background:linear-gradient(90deg,var(--gold-d),var(--gold)); border-radius:2mm; }
.score-bar-desc { font-size:8.3pt; line-height:1.55; color:#666; }

/* ── 運勢カレンダー（12ヶ月グリッド） ── */
.cal-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:2.8mm; margin:5mm 0 7mm; break-inside:avoid; page-break-inside:avoid; }
.cal-card { background:#FAFAF7; border:1px solid #ece5d8; border-radius:4px; padding:3.5mm 2.5mm; text-align:center; }
.cal-month { font-size:9.3pt; font-weight:600; color:var(--dark); margin-bottom:1.2mm; }
.cal-stars { color:var(--gold-d); font-size:9.5pt; letter-spacing:.1em; margin-bottom:1.5mm; }
.cal-desc { font-size:7.3pt; line-height:1.55; color:#777; }

/* ── FROM ページ ── */
.sig-page {
  width:210mm; height:297mm; background:var(--bg);
  display:flex; flex-direction:column;
  margin:0 auto; box-shadow:0 4px 20px rgba(0,0,0,.12);
  overflow:hidden;
}
.sig-body {
  flex:1; display:flex; flex-direction:column;
  align-items:center; justify-content:center;
  padding:16mm 22mm; text-align:center; gap:0;
}
.sig-header { font-family:'Cormorant Garamond',serif; font-size:8pt; letter-spacing:.55em; color:var(--gold); margin-bottom:10mm; }
.sig-msg { font-size:10.5pt; line-height:2.3; color:var(--text); text-align:left; max-width:148mm; }
.sig-msg p { margin-bottom:5mm; }
.sig-msg strong { color:var(--gold); font-weight:600; }
.sig-writer { font-size:12pt; letter-spacing:.25em; color:var(--dark); margin-top:10mm; text-align:center; width:100%; }
.sig-footer {
  background:#2a2240; color:#c0b8d0; padding:7mm 22mm;
  text-align:center; flex-shrink:0;
}
.sig-footer-edition { font-family:'Cormorant Garamond',serif; font-size:9pt; letter-spacing:.4em; color:var(--gold); margin-bottom:2.5mm; }
.sig-footer-info { font-size:8pt; color:#a098b8; line-height:2; margin-bottom:2mm; }
.sig-footer-copy { font-size:7pt; color:#706080; line-height:1.8; margin-top:3mm; }
</style>
</head>
<body>
<div class="cover">
  <div class="gold-rule"></div>
  <div class="cover-inner">
    <div class="c-header">{{HEADER_EN}}</div>
    <div class="c-diamond">✦</div>
    <div class="c-label">{{DOC_LABEL}}</div>
    <div class="c-name">{{NAME}}</div>
    <div class="c-reading">{{READING}}&nbsp;様</div>
    <div class="c-line"></div>
    <div class="c-catch">{{CATCH}}</div>
    <div class="c-astro">{{ASTRO}}</div>
    <div class="c-edition">{{EDITION}}</div>
  </div>
  <div class="gold-rule"></div>
</div>
{{CHAPTERS}}
<div class="sig-page">
  <div class="sig-body">
    <div class="sig-header">✦ &nbsp; F R O M &nbsp; {{SENDER_PLAIN}} &nbsp; ✦</div>
    <div class="sig-msg">{{FROM_MSG}}</div>
    <div class="sig-writer">{{SENDER}}</div>
  </div>
  <div class="sig-footer">
    <div class="sig-footer-edition">{{EDITION}} ✦ {{NAME}}様</div>
    <div class="sig-footer-info">{{DOC_TITLE}} &nbsp;｜&nbsp; 鑑定士：{{SENDER}}</div>
    <div class="sig-footer-copy">{{FOOTER_COPY}}<br>内容の無断転載・転用を禁じます。</div>
  </div>
</div>
</body>
</html>"""
