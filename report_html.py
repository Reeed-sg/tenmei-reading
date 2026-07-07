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
* { margin:0; padding:0; box-sizing:border-box; }
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
.c-catch { font-size:11.5pt; font-weight:300; line-height:2.2; color:var(--text); max-width:128mm; }
.c-astro { font-size:7pt; color:#999; margin-top:8mm; line-height:2.4; letter-spacing:.02em; }
.c-edition { font-family:'Cormorant Garamond',serif; font-size:8pt; letter-spacing:.55em; color:#c0a870; margin-top:3mm; }

/* ── チャプター共通 ── */
.chapter {
  width:210mm; min-height:297mm; background:white;
  padding:18mm 18mm 14mm;
  margin:0 auto 8mm; box-shadow:0 4px 20px rgba(0,0,0,.12);
}
.ch-num { font-family:'Cormorant Garamond',serif; font-size:8pt; letter-spacing:.5em; color:#ccc; text-align:center; margin-bottom:3mm; }
.ch-title { font-size:24pt; font-weight:400; text-align:center; color:var(--dark); margin-bottom:2mm; }
.ch-sub { font-size:9pt; text-align:center; color:#888; margin-bottom:4mm; line-height:1.8; }
.ch-divider { width:28mm; height:2px; background:var(--gold); margin:0 auto 8mm; }

/* ── 本文 ── */
.ch-body p { font-size:9.5pt; line-height:2.15; margin-bottom:3.5mm; }
.ch-body ul { margin:3mm 0 3mm 2mm; }
.ch-body li { font-size:9.5pt; line-height:2; margin-bottom:2mm; list-style:none; padding-left:5mm; position:relative; }
.ch-body li::before { content:'◇'; color:var(--gold); position:absolute; left:0; }
.ch-body strong { color:var(--gold-d); font-weight:600; }
.box-key { background:var(--box-key); border-left:3px solid var(--purple); padding:4mm 6mm; border-radius:0 4px 4px 0; margin:5mm 0; font-size:9pt; line-height:2.1; }
.ch-heading { font-size:10.5pt; font-weight:600; color:var(--dark); margin:6mm 0 2mm; border-bottom:1px solid #e8d5a3; padding-bottom:1.5mm; }

/* ── Chapter 1 専用：ダークシテシスボックス ── */
.thesis-box {
  background:var(--navy); color:white;
  border-radius:4px; padding:8mm 10mm; margin:6mm 0 8mm;
  text-align:center;
}
.thesis-label { font-family:'Cormorant Garamond',serif; font-size:7.5pt; letter-spacing:.5em; color:var(--gold); margin-bottom:4mm; }
.thesis-catch { font-size:13pt; font-weight:300; line-height:2.0; color:#f5f0e8; }
.thesis-sub { font-size:9pt; font-style:italic; color:#c5a84b; margin-top:3mm; line-height:1.8; }

/* ── Chapter 1 専用：星術カード ── */
.astro-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:3mm; margin:6mm 0 8mm; }
.astro-card { padding:4mm 3mm; border-radius:3px; text-align:center; }
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
    <div class="sig-writer">{{SIGNER_TITLE}} &nbsp;{{SENDER}}</div>
  </div>
  <div class="sig-footer">
    <div class="sig-footer-edition">{{EDITION}} ✦ {{NAME}}様</div>
    <div class="sig-footer-info">{{DOC_TITLE}} &nbsp;｜&nbsp; 鑑定士：{{SIGNER_TITLE}} {{SENDER}}</div>
    <div class="sig-footer-copy">{{FOOTER_COPY}}<br>内容の無断転載・転用を禁じます。</div>
  </div>
</div>
</body>
</html>"""
