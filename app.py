import os, re, json
from datetime import datetime, date
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

try:
    from anthropic import Anthropic
except ImportError:
    st.error("pip install anthropic を実行してください")
    st.stop()

# ── ページ設定 ───────────────────────────────────────────────

st.set_page_config(
    page_title="天命鑑定書 生成システム",
    page_icon="✦",
    layout="centered",
)

# ── セキュリティ設定 ─────────────────────────────────────────
# Streamlit Cloud の場合: st.secrets["APP_PASSWORD"] / st.secrets["DAILY_LIMIT"]
# ローカルの場合: .env の APP_PASSWORD / DAILY_LIMIT

def get_secret(key, default=None):
    """Streamlit Secrets → .env の順で取得"""
    try:
        return st.secrets[key]
    except Exception:
        return os.environ.get(key, default)

APP_PASSWORD = get_secret("APP_PASSWORD", "")       # 空の場合は認証スキップ
DAILY_LIMIT  = int(get_secret("DAILY_LIMIT", "50")) # 1日の最大生成数
COUNTER_FILE = Path(__file__).parent / ".usage_counter.json"

def load_counter():
    today = date.today().isoformat()
    if COUNTER_FILE.exists():
        data = json.loads(COUNTER_FILE.read_text())
        if data.get("date") == today:
            return data.get("count", 0)
    return 0

def increment_counter():
    today = date.today().isoformat()
    count = load_counter() + 1
    COUNTER_FILE.write_text(json.dumps({"date": today, "count": count}))
    return count

def sanitize(text: str, max_len: int = 500) -> str:
    """入力値のサニタイズ：制御文字除去・長さ制限"""
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text[:max_len].strip()

# ── パスワード認証 ───────────────────────────────────────────

if APP_PASSWORD:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.markdown('<div class="main-title">✦ 天命鑑定書</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-title">CELESTIAL DESTINY READING SYSTEM</div>', unsafe_allow_html=True)
        st.markdown("---")
        pw = st.text_input("アクセスコードを入力してください", type="password")
        if st.button("認証"):
            if pw == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("アクセスコードが正しくありません")
        st.stop()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@300;400;600&display=swap');

html, body, [class*="css"] { font-family: 'Noto Serif JP', serif; }

.main-title {
    text-align: center;
    font-size: 2rem;
    font-weight: 300;
    letter-spacing: 0.4em;
    color: #1A1A1A;
    margin-bottom: 0.2rem;
}
.sub-title {
    text-align: center;
    font-size: 0.85rem;
    letter-spacing: 0.3em;
    color: #C5A84B;
    margin-bottom: 2rem;
}
.gold-line {
    height: 2px;
    background: linear-gradient(90deg, transparent, #C5A84B, transparent);
    margin: 1.5rem 0;
}
.section-label {
    font-size: 0.8rem;
    letter-spacing: 0.2em;
    color: #888;
    margin-bottom: 0.5rem;
}
.stButton > button {
    width: 100%;
    background: #1A1A1A !important;
    color: white !important;
    border: none !important;
    padding: 0.8rem 2rem !important;
    font-size: 1rem !important;
    letter-spacing: 0.2em !important;
    border-radius: 4px !important;
    font-family: 'Noto Serif JP', serif !important;
}
.stButton > button:hover {
    background: #C5A84B !important;
}
.result-box {
    background: #FAFAF7;
    border: 1px solid #E8D5A3;
    border-radius: 8px;
    padding: 1.5rem;
    margin-top: 1rem;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ── ヘッダー ─────────────────────────────────────────────────

st.markdown('<div class="main-title">✦ 天命鑑定書</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">CELESTIAL DESTINY READING SYSTEM</div>', unsafe_allow_html=True)
st.markdown('<div class="gold-line"></div>', unsafe_allow_html=True)

# ── 占術計算 ─────────────────────────────────────────────────

STEMS    = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
STARS    = ["一白水星","二黒土星","三碧木星","四緑木星","五黄土星",
            "六白金星","七赤金星","八白土星","九紫火星"]
ZODIAC   = [
    (1,19,"山羊座 ♑"),(2,18,"水瓶座 ♒"),(3,20,"魚座 ♓"),
    (4,19,"牡羊座 ♈"),(5,20,"牡牛座 ♉"),(6,21,"双子座 ♊"),
    (7,22,"蟹座 ♋"),  (8,22,"獅子座 ♌"),(9,22,"乙女座 ♍"),
    (10,22,"天秤座 ♎"),(11,21,"蠍座 ♏"),(12,21,"射手座 ♐"),
    (12,31,"山羊座 ♑"),
]

def digit_reduce(n):
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n

def calc_lifepath(y, m, d):
    n = digit_reduce(y) + digit_reduce(m) + digit_reduce(d)
    while n not in (11, 22, 33) and n > 9:
        n = sum(int(x) for x in str(n))
    return n

def calc_zodiac(m, d):
    for cm, cd, sign in ZODIAC:
        if m < cm or (m == cm and d <= cd):
            return sign
    return "山羊座 ♑"

def calc_kyusei(y, m, d):
    adj = y if (m > 2 or (m == 2 and d >= 4)) else y - 1
    n   = digit_reduce(sum(int(c) for c in str(adj)))
    idx = (11 - n) % 9
    return STARS[idx - 1 if idx > 0 else 8]

def calc_year_pillar(y):
    return STEMS[(y - 4) % 10] + BRANCHES[(y - 4) % 12]

# ── Claude API ───────────────────────────────────────────────

SYSTEM = """あなたは東洋・西洋の占術を統合した世界最高峰の天命鑑定師です。
指示された章のみを、必ず以下のXMLタグで囲んで出力してください。
・テキストのみで記述し、HTMLタグは一切使わないでください
・段落は空行で区切ってください
・箇条書きは「・」で始めてください
・各章の冒頭に【要点】として3行サマリーを必ず入れてください
・対象者への語りかけ口調（〜ですよ、〜ですね）で書いてください
・占術的根拠を各所に簡潔に添えてください"""

def base_info(f):
    return f"""氏名：{f['name']}／{f['reading']}
生年月日：{f['bdate']}（{f['gender']}・{f['place']}出身）
職業・状況：{f['job']}
悩み・課題：{f['concerns']}
目標・夢：{f['goals']}
SNS・ビジネス目標：{f['sns']}

【算出済み占術データ】
西洋星座：{f['zodiac']}／LifePath：{f['lifepath']}／九星気学：{f['kyusei']}／年柱：{f['year_pillar']}
月柱・日柱は正確に算出して記載してください。"""

def call_part1(client, f):
    prompt = base_info(f) + """

<catchphrase>その人の本質と使命を表す印象的なキャッチコピー（20〜40文字・1〜2文）</catchphrase>
<month_pillar>月柱（漢字2文字のみ）</month_pillar>
<day_pillar>日柱（漢字2文字のみ）</day_pillar>

<chapter1>第1章：天命の全体像（約500文字）
天命キーワード・魂のテーマ・数秘×四柱×星座の統合解釈・オーラの色と波動</chapter1>

<chapter2>第2章：使命と才能の詳細分析（約600文字）
3大才能と発揮方法・ユニークな強み・魂が喜ぶ活動・社会への役割</chapter2>

<chapter3>第3章：今の時代背景と天命の接点（約600文字）
2026〜2028年の時代の流れ（AI・経済・社会変化）・天命が今輝く理由・社会課題との交差</chapter3>

<chapter4>第4章：3年間の天命ロードマップ（約800文字）
2026年（30日・3ヶ月・1年のアクション）／2027年（やること・避けること）／2028年（天命開花シナリオ）</chapter4>

<chapter5>第5章：今日からのアクションプラン20選（約1000文字）
仕事5・人間関係4・学び4・健康4・お金3（各アクションに占術的根拠を1行）</chapter5>"""
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8192,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text

def call_part2(client, f):
    prompt = base_info(f) + """

<chapter6>第6章：ラッキー風水＆パワースポット（約500文字）
ラッキーカラー3色・ラッキーナンバー3つ・国内5箇所・海外3箇所・ラッキーアイテム3つ・吉方位</chapter6>

<chapter7>第7章：人間関係と天命の仲間（約500文字）
相性の良いタイプ・キーパーソン3タイプ・注意パターン・理想のチーム像</chapter7>

<chapter8>第8章：魂の課題と乗り越え方（約500文字）
カルマのパターン・3つのブロックと解除法・過去世テーマ・脱出ワーク</chapter8>

<chapter9>第9章：月別・季節別の吉凶カレンダー（約600文字）
2026〜2027年の月別：エネルギーが高まる月・休息の月・ベストタイミング・注意の時期</chapter9>

<chapter10>第10章：天命宣言文＆メッセージ（約400文字）
天命宣言文（アファメーション）・守護存在からのメッセージ・10年後ビジョンレター・最後の言葉</chapter10>

<chapter11>第11章：SNS戦略＆プロデューサー鑑定（約600文字）
最適SNS媒体と理由・発信コンセプト・マネタイズステップ・月収100万円ロードマップ・向いているビジネスモデル</chapter11>"""
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

# ── テキスト→HTML ────────────────────────────────────────────

def text_to_html(text):
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
        elif all(l.startswith('・') for l in lines if l.strip()):
            lis = ''.join(f'<li>{l.lstrip("・ ")}</li>' for l in lines if l.strip())
            html.append(f'<ul>{lis}</ul>')
        else:
            for line in lines:
                if line.strip():
                    html.append(f'<p>{line}</p>')
    return '\n'.join(html)

# ── HTML生成 ─────────────────────────────────────────────────

CHAPTER_META = {
    1:  ("天命の全体像",            "この人が生まれ持った天命と魂のテーマ"),
    2:  ("使命と才能の詳細分析",     "「私の天職は何か？」── 天命的な明確な答え"),
    3:  ("今の時代背景と天命の接点", "2026年── 時代の波に乗る天命の輝き"),
    4:  ("3年間の天命ロードマップ",  "2026〜2028 ｜ 天命開花への道筋"),
    5:  ("今日からのアクションプラン","今すぐできる20の具体的行動"),
    6:  ("ラッキー風水＆パワースポット","天命を加速させる場所・色・数字"),
    7:  ("人間関係と天命の仲間",      "天命を共に生きるキーパーソン"),
    8:  ("魂の課題と乗り越え方",      "カルマのパターンと解除法"),
    9:  ("月別・季節別 吉凶カレンダー","2026〜2027年のベストタイミング"),
    10: ("天命宣言文＆メッセージ",    "あなただけのオリジナル宣言"),
    11: ("SNS戦略＆プロデューサー鑑定","天命×SNS×ビジネスの最適解"),
}

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>天命鑑定書 - {{NAME}}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=Noto+Serif+JP:wght@300;400;600&display=swap" rel="stylesheet">
<style>
:root {
  --gold:#C5A84B; --gold-l:#E8D5A3;
  --bg:#FAFAF7; --dark:#1A1A1A; --text:#2C2C2C;
  --purple:#4B2D7F; --box-key:#F3EFF8;
}
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'Noto Serif JP',serif; background:#ece8e0; color:var(--text); }
@media print {
  body { background:white; }
  @page { size:A4 portrait; margin:0; }
  .page { page-break-after:always; box-shadow:none !important; }
}
.cover {
  width:210mm; min-height:297mm; background:var(--bg);
  display:flex; flex-direction:column; align-items:center;
  margin:0 auto 8mm; box-shadow:0 4px 20px rgba(0,0,0,.15);
}
.gold-rule { width:100%; height:5px; background:linear-gradient(90deg,transparent 5%,var(--gold) 20%,var(--gold) 80%,transparent 95%); }
.cover-inner {
  flex:1; display:flex; flex-direction:column;
  align-items:center; justify-content:center;
  padding:22mm 18mm; gap:5mm; text-align:center;
}
.c-header { font-family:'Cormorant Garamond',serif; font-size:8pt; letter-spacing:.5em; color:#999; }
.c-diamond { color:var(--gold); font-size:22pt; line-height:1; }
.c-label { font-size:9.5pt; letter-spacing:.65em; color:#aaa; }
.c-name { font-size:44pt; font-weight:300; letter-spacing:.35em; color:var(--dark); line-height:1.15; margin:4mm 0; }
.c-reading { font-size:9pt; letter-spacing:.35em; color:var(--gold); }
.c-line { width:55mm; height:1px; background:var(--gold); margin:5mm auto; }
.c-catch { font-size:12pt; font-weight:300; line-height:2.3; color:var(--text); max-width:130mm; }
.c-astro { font-size:7.5pt; color:#888; margin-top:7mm; line-height:2.2; }
.c-edition { font-family:'Cormorant Garamond',serif; font-size:8pt; letter-spacing:.5em; color:#bbb; margin-top:4mm; }
.chapter {
  width:210mm; min-height:297mm; background:white;
  padding:20mm 18mm 16mm;
  margin:0 auto 8mm; box-shadow:0 4px 20px rgba(0,0,0,.12);
}
.ch-num { font-family:'Cormorant Garamond',serif; font-size:8pt; letter-spacing:.5em; color:#ccc; text-align:center; margin-bottom:4mm; }
.ch-title { font-size:22pt; font-weight:400; text-align:center; color:var(--dark); margin-bottom:2.5mm; }
.ch-sub { font-size:9pt; text-align:center; color:#999; margin-bottom:5mm; }
.ch-divider { width:28mm; height:2px; background:var(--gold); margin:0 auto 9mm; }
.ch-body p { font-size:9.5pt; line-height:2.1; margin-bottom:3mm; }
.ch-body ul { margin:4mm 0 4mm 2mm; }
.ch-body li { font-size:9.5pt; line-height:2; margin-bottom:2mm; list-style:none; padding-left:5mm; position:relative; }
.ch-body li::before { content:'◇'; color:var(--gold); position:absolute; left:0; }
.box-key { background:var(--box-key); border-left:3px solid var(--purple); padding:5mm 7mm; border-radius:0 4px 4px 0; margin:5mm 0; font-size:9.5pt; line-height:2.1; }
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

def build_html(f, data):
    chapters_html = ""
    for i in range(1, 12):
        title, subtitle = CHAPTER_META[i]
        body = text_to_html(data.get(f"chapter{i}", ""))
        chapters_html += f"""
<div class="chapter page">
  <div class="ch-num">CHAPTER {i:02d}</div>
  <h2 class="ch-title">{title}</h2>
  <p class="ch-sub">{subtitle}</p>
  <div class="ch-divider"></div>
  <div class="ch-body">{body}</div>
</div>"""

    astro = (
        f"{f['bdate']}生&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"{f['zodiac']}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"LifePath {f['lifepath']}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"{f['kyusei']}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"年柱：{f['year_pillar']}&nbsp;"
        f"月柱：{data.get('month_pillar','—')}&nbsp;"
        f"日柱：{data.get('day_pillar','—')}"
    )
    catch = data.get('catchphrase', '').replace('\n', '<br>')
    return (HTML_TEMPLATE
            .replace("{{NAME}}", f['name'])
            .replace("{{READING}}", f['reading'])
            .replace("{{CATCH}}", catch)
            .replace("{{ASTRO}}", astro)
            .replace("{{CHAPTERS}}", chapters_html))

# ── フォーム UI ──────────────────────────────────────────────

with st.form("reading_form"):
    st.markdown('<p class="section-label">▸ 基本情報</p>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        name    = st.text_input("お名前（フルネーム）*", placeholder="田中まりこ")
        bdate   = st.text_input("生年月日*", placeholder="1984年2月19日")
        place   = st.text_input("出生地（都道府県）*", placeholder="沖縄県")
    with col2:
        reading = st.text_input("ふりがな*", placeholder="たなか まりこ")
        gender  = st.selectbox("性別*", ["女性", "男性", "その他"])
        job     = st.text_input("現在の職業・状況*", placeholder="育休中・コーチング準備中")

    st.markdown('<div class="gold-line"></div>', unsafe_allow_html=True)
    st.markdown('<p class="section-label">▸ 鑑定内容</p>', unsafe_allow_html=True)

    concerns = st.text_area("現在の悩みや課題*", placeholder="なかなか動けない。自分に自信が持てない。", height=80)
    goals    = st.text_area("目標や夢*", placeholder="沖縄の女性を元気にしたい。コーチとして独立したい。", height=80)
    sns      = st.text_input("SNS・ビジネス目標（任意）", placeholder="Instagramで月収100万円を目指したい")

    submitted = st.form_submit_button("✦ 天命鑑定書を生成する")

# ── 生成処理 ─────────────────────────────────────────────────

if submitted:
    # ── レート制限チェック ──
    current_count = load_counter()
    if current_count >= DAILY_LIMIT:
        st.error(f"本日の生成上限（{DAILY_LIMIT}件）に達しました。明日またお試しください。")
        st.stop()

    # ── 1セッション1回制限 ──
    if st.session_state.get("already_generated"):
        st.warning("1セッションにつき1回のみ生成できます。再生成する場合はページを再読み込みしてください。")
        st.stop()

    errors = []
    if not name:    errors.append("お名前")
    if not reading: errors.append("ふりがな")
    if not bdate:   errors.append("生年月日")
    if not place:   errors.append("出生地")
    if not job:     errors.append("職業・状況")
    if not concerns: errors.append("悩みや課題")
    if not goals:   errors.append("目標や夢")

    if errors:
        st.error(f"未入力の必須項目があります：{', '.join(errors)}")
    else:
        # ── 入力サニタイズ ──
        name     = sanitize(name, 50)
        reading  = sanitize(reading, 50)
        place    = sanitize(place, 50)
        job      = sanitize(job, 200)
        concerns = sanitize(concerns, 500)
        goals    = sanitize(goals, 500)
        sns      = sanitize(sns, 200)

        m = re.search(r'(\d{4})[年/\-](\d{1,2})[月/\-](\d{1,2})', bdate)
        if not m:
            st.error("生年月日の形式を確認してください（例: 1984年2月19日）")
        else:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            info = {
                "name": name, "reading": reading,
                "bdate": f"{y}年{mo}月{d}日",
                "gender": gender, "place": place,
                "job": job, "concerns": concerns,
                "goals": goals, "sns": sns or "なし",
                "lifepath":   calc_lifepath(y, mo, d),
                "zodiac":     calc_zodiac(mo, d),
                "kyusei":     calc_kyusei(y, mo, d),
                "year_pillar": calc_year_pillar(y),
            }

            st.info(f"🔮 {name} 様の占術データ：{info['zodiac']} ／ LifePath {info['lifepath']} ／ {info['kyusei']} ／ 年柱 {info['year_pillar']}")

            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                st.error("ANTHROPIC_API_KEY が設定されていません。管理者にお問い合わせください。")
            else:
                client = Anthropic(api_key=api_key)
                data   = {}

                progress = st.progress(0, text="✦ 天命の声を聴いています…")

                try:
                    progress.progress(10, text="📖 第1〜5章を生成中（1〜2分）…")
                    resp1 = call_part1(client, info)
                    progress.progress(55, text="📖 第6〜11章を生成中（1〜2分）…")
                    resp2 = call_part2(client, info)
                    progress.progress(90, text="📄 鑑定書を組み立て中…")

                    all_tags = ["catchphrase","month_pillar","day_pillar"] + [f"chapter{i}" for i in range(1,12)]
                    for tag in all_tags:
                        data[tag] = parse_tag(resp1, tag) or parse_tag(resp2, tag)

                    html = build_html(info, data)
                    progress.progress(100, text="✅ 完成！")

                    increment_counter()
                    st.session_state.already_generated = True
                    st.success(f"✦ {name} 様の天命鑑定書が完成しました！")
                    st.markdown(f"""
<div class="result-box">
    <p style="font-size:1.1rem; color:#C5A84B; letter-spacing:0.1em;">{data.get('catchphrase','').replace(chr(10),'<br>')}</p>
</div>
""", unsafe_allow_html=True)

                    ts = datetime.now().strftime("%Y%m%d_%H%M")
                    st.download_button(
                        label="📥 鑑定書をダウンロード（HTML）",
                        data=html.encode("utf-8"),
                        file_name=f"tenmei_{name}_{ts}.html",
                        mime="text/html",
                    )
                    st.caption("ダウンロードしたHTMLをChromeで開き、印刷→PDFに保存すると完成です。")

                except Exception as e:
                    progress.empty()
                    st.error(f"生成中にエラーが発生しました：{e}")
