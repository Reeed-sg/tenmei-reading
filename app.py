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

APP_PASSWORD  = get_secret("APP_PASSWORD", "")       # 空の場合は認証スキップ
DAILY_LIMIT   = int(get_secret("DAILY_LIMIT", "50")) # 1日の最大生成数
COUNTER_FILE  = Path(__file__).parent / ".usage_counter.json"
READINGS_DIR  = Path(__file__).parent / "output" / "readings"
READINGS_DIR.mkdir(parents=True, exist_ok=True)

def save_reading(info: dict, data: dict, sender: str) -> Path:
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = re.sub(r'[^\w぀-鿿]', '_', info['name'])
    path = READINGS_DIR / f"{ts}_{name}.json"
    path.write_text(json.dumps(
        {"info": info, "data": data, "sender": sender, "created_at": datetime.now().isoformat()},
        ensure_ascii=False, indent=2
    ), encoding="utf-8")
    # 古いファイルは最新30件だけ保持
    files = sorted(READINGS_DIR.glob("*.json"), reverse=True)
    for old in files[30:]:
        old.unlink(missing_ok=True)
    return path

def list_readings() -> list[dict]:
    files = sorted(READINGS_DIR.glob("*.json"), reverse=True)
    result = []
    for f in files:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            result.append({
                "path": f,
                "label": f"{d['info']['name']}様　{d['created_at'][:16].replace('T',' ')}",
                "info": d["info"],
                "data": d["data"],
                "sender": d.get("sender", ""),
            })
        except Exception:
            pass
    return result

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

【文体・口調のルール】
・必ず対象者の名前（氏名のうち名）を冒頭と要所で使う（例：「真理子さん、」）
・「あなた」は使わず「○○さん」で統一する
・語りかけ口調（〜ですよ、〜ですね、〜なのです）で書く
・具体的なエピソード・数字・占術的根拠を必ず入れる
・太鼓判を押すように断定的に、かつ温かみのある文体で

【形式のルール】
・テキストのみで記述し、HTMLタグは一切使わない
・段落は空行で区切る
・箇条書きは「・」で始める
・各章の冒頭に【要点】として3行サマリーを必ず入れる
・章内の各テーマには「「見出し」── 解説のサブタイトル」形式でヘッダーを付ける"""

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
    first_name = f['reading'].split()[0] if ' ' in f['reading'] else f['reading']
    prompt = base_info(f) + f"""

名前の読み（呼びかけ用）：{first_name}さん

<catchphrase>その人の本質と使命を表す印象的なキャッチコピー（20〜40文字・1〜2文。名前は入れない）</catchphrase>
<edition_name>その人のエネルギーを表す英語2〜3語のエディション名（例：OCEAN EMBER EDITION / SILENT FIRE EDITION）大文字のみ</edition_name>
<month_pillar>月柱（漢字2文字のみ）</month_pillar>
<day_pillar>日柱（漢字2文字のみ）</day_pillar>

<chapter1>第1章：天命概論（約600文字）
冒頭は「{first_name}さん、」で始める。天命キーワード・魂のテーマ・数秘×四柱×星座の統合解釈・オーラの色と波動。各テーマに「「見出し」── サブタイトル」形式のヘッダーを付ける</chapter1>

<chapter2>第2章：才能と使命（約700文字）
3大才能を「「才能名」── 占術的根拠」形式で展開。ユニークな強み・魂が喜ぶ活動・社会への役割。各才能に具体的な活かし方を添える</chapter2>

<chapter3>第3章：時代文脈（約600文字）
2026〜2028年の時代の流れ（AI・経済・社会変化）×その人の天命。「今がまさにその時である理由」を占術データと時代背景から断定的に語る</chapter3>

<chapter4>第4章：3年ロードマップ（約800文字）
2026年（今日・30日・3ヶ月・1年のアクション）／2027年（やること・避けること）／2028年（天命開花シナリオ）。月柱・日柱も含めた具体的な指針</chapter4>

<chapter5>第5章：今日からの行動（約1000文字）
今日からできる具体的アクション20選。仕事5・人間関係4・学び4・健康4・お金3の各カテゴリに（占術的根拠）を添える</chapter5>"""
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8192,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text

def call_part2(client, f):
    first_name = f['reading'].split()[0] if ' ' in f['reading'] else f['reading']
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
最適SNS媒体と理由・発信コンセプト・マネタイズステップ・月収100万円ロードマップ・向いているビジネスモデル</chapter11>

""" + f"""<from_message>鑑定師から{first_name}さんへの個人的なメッセージ（300〜400文字）。
・「{first_name}さん、」で書き始める
・その人が書いた悩みや言葉を引用しながら、天命から見たポジティブな真実を伝える
・動けていない・自信がないといった課題を、占術的根拠で肯定的に解釈し直す
・具体的な最初の一歩を1つだけ提案する
・温かく背中を押す言葉で締める
・重要な気づきや励ましの言葉は **このように** ダブルアスタリスクで囲む（2〜3箇所）</from_message>"""
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

# ── HTML生成 ─────────────────────────────────────────────────

CHAPTER_META = {
    1:  ("天命概論",               ""),
    2:  ("才能と使命",             "「私の天職は何か？」── 天命的な明確な答え"),
    3:  ("時代文脈",               "2026年── 時代の波に乗る天命の輝き"),
    4:  ("3年ロードマップ",         "2026〜2028 ｜ 天命開花への道筋"),
    5:  ("今日からの行動",          "今すぐできる20の具体的アクション"),
    6:  ("ラッキー風水＆パワースポット","天命を加速させる場所・色・数字"),
    7:  ("人間関係と天命の仲間",     "天命を共に生きるキーパーソン"),
    8:  ("魂の課題と乗り越え方",     "カルマのパターンと解除法"),
    9:  ("吉凶カレンダー",          "2026〜2027年のベストタイミング"),
    10: ("天命宣言文",              "あなただけのオリジナル宣言"),
    11: ("SNS＆ビジネス戦略",       "天命×SNS×ビジネスの最適解"),
}

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

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>天命鑑定書 - {{NAME}}</title>
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

/* ── Chapter 1 専用：6枚星術カード ── */
.astro-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:3mm; margin:6mm 0 8mm; }
.astro-card { padding:4mm 3mm; border-radius:3px; text-align:center; }
.ac-w  { background:#fce8e8; }
.ac-n  { background:#fff0dc; }
.ac-k  { background:#e8eeff; }
.ac-y  { background:#f5f5f5; border:1px solid #ddd; }
.ac-m  { background:#f0f5ff; border:1px solid #dde; }
.ac-d  { background:#1a1a3a; color:white; }
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
    <div class="c-header">CELESTIAL DESTINY READING &nbsp;✦&nbsp; PREMIUM EDITION</div>
    <div class="c-diamond">✦</div>
    <div class="c-label">天　命　鑑　定　書</div>
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
    <div class="sig-writer">天命鑑定士 &nbsp;{{SENDER}}</div>
  </div>
  <div class="sig-footer">
    <div class="sig-footer-edition">{{EDITION}} ✦ {{NAME}}様</div>
    <div class="sig-footer-info">天命鑑定書 &nbsp;｜&nbsp; 鑑定士：天命鑑定士 {{SENDER}}</div>
    <div class="sig-footer-copy">本鑑定書は占術・数秘術・算命学・九星気学・姓名判断を統合した天命鑑定です。<br>内容の無断転載・転用を禁じます。</div>
  </div>
</div>
</body>
</html>"""

def build_astro_cards(f, data):
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
    ]
    html = '<div class="astro-grid">'
    for label, cls, title, desc in cards:
        html += f'''<div class="astro-card {cls}">
  <div class="ac-label">{label}</div>
  <div class="ac-title">{title}</div>
  {"<div class='ac-desc'>"+desc+"</div>" if desc else ""}
</div>'''
    html += '</div>'
    return html

def build_html(f, data, sender="YURI（結梨嘉望）"):
    chapters_html = ""
    for i in range(1, 12):
        title, subtitle = CHAPTER_META[i]
        body = text_to_html(data.get(f"chapter{i}", ""))

        # Chapter 1 専用：ダークシテシスボックス＋星術カード
        prefix = ""
        if i == 1:
            catch_fmt = data.get('catchphrase', '').replace('\n', '<br>')
            prefix = f"""
<div class="thesis-box">
  <div class="thesis-label">✦ YOUR CELESTIAL THESIS ✦</div>
  <div class="thesis-catch">{catch_fmt}</div>
</div>
{build_astro_cards(f, data)}"""

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
        f"{f['bdate']}生&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"{f['zodiac']}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"LifePath {f['lifepath']}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"{f['kyusei']}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"年柱：{f['year_pillar']}&nbsp;月柱：{mp}&nbsp;日柱：{dp}"
    )
    catch   = data.get('catchphrase', '').replace('\n', '<br>')
    edition = data.get('edition_name', 'CELESTIAL DESTINY EDITION')

    # FROM メッセージ：**text** → <strong>text</strong>、改行→段落
    raw_msg = data.get('from_message', '')
    def fmt_from_msg(text):
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        paras = re.split(r'\n{1,}', text.strip())
        return '\n'.join(f'<p>{p}</p>' for p in paras if p.strip())

    from_msg_html = fmt_from_msg(raw_msg)

    # 差出人：表示用（括弧あり）とヘッダー用（括弧なし・英字部分のみ）
    sender_plain = re.sub(r'（.*?）', '', sender).strip()  # "YURI" だけ

    return (HTML_TEMPLATE
            .replace("{{NAME}}",         f['name'])
            .replace("{{READING}}",      f['reading'])
            .replace("{{CATCH}}",        catch)
            .replace("{{ASTRO}}",        astro)
            .replace("{{EDITION}}",      edition)
            .replace("{{SENDER}}",       sender)
            .replace("{{SENDER_PLAIN}}", sender_plain)
            .replace("{{FROM_MSG}}",     from_msg_html)
            .replace("{{CHAPTERS}}",     chapters_html))

def regenerate_chapter(client, f, data, chapter_num, feedback):
    """指定した章だけをフィードバックに基づいて再生成"""
    if chapter_num == 0:
        prompt = base_info(f) + f"""

以下のキャッチコピーとエディション名を、修正依頼をもとに改善してください。

現在のキャッチコピー：
{data.get('catchphrase', '')}

現在のエディション名：
{data.get('edition_name', '')}

修正依頼：
{feedback}

<catchphrase>修正後のキャッチコピー</catchphrase>
<edition_name>修正後のエディション名</edition_name>"""
    else:
        title, _ = CHAPTER_META[chapter_num]
        prompt = base_info(f) + f"""

第{chapter_num}章「{title}」を修正依頼をもとに改善・修正してください。
文体・口調は元の内容に準じ、{f['reading'].split()[0] if ' ' in f['reading'] else f['reading']}さんへの語りかけ形式を維持してください。

現在の内容：
{data.get(f'chapter{chapter_num}', '')}

修正依頼：
{feedback}

修正後の内容のみを以下のタグで囲んで出力してください（他のタグは不要）：
<chapter{chapter_num}>修正後の内容</chapter{chapter_num}>"""

    resp = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=4096,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    ).content[0].text
    return resp

# ── 過去の鑑定を読み込む ─────────────────────────────────────

past = list_readings()
if past and not st.session_state.get("reading_data"):
    with st.expander("📂 過去の鑑定書を読み込んで修正する"):
        labels = [r["label"] for r in past]
        sel = st.selectbox("鑑定を選択", labels, key="past_sel")
        if st.button("読み込む", key="load_past"):
            chosen = past[labels.index(sel)]
            st.session_state.reading_info   = chosen["info"]
            st.session_state.reading_data   = chosen["data"]
            st.session_state.reading_sender = chosen["sender"]
            st.rerun()

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

    st.markdown('<div class="gold-line"></div>', unsafe_allow_html=True)
    st.markdown('<p class="section-label">▸ 署名（最終ページ）</p>', unsafe_allow_html=True)
    sender = st.text_input("差出人名", value="YURI（結梨嘉望）", placeholder="YURI（結梨嘉望）")

    submitted = st.form_submit_button("✦ 天命鑑定書を生成する")

# ── 生成処理 ─────────────────────────────────────────────────

if submitted:
    # ── レート制限チェック ──
    current_count = load_counter()
    if current_count >= DAILY_LIMIT:
        st.error(f"本日の生成上限（{DAILY_LIMIT}件）に達しました。明日またお試しください。")
        st.stop()

    # ── 1セッション1回制限（修正依頼は別途可能）──
    if st.session_state.get("already_generated"):
        st.warning("新規生成は1セッション1回です。修正は下の「修正依頼フォーム」から行ってください。")
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

                    all_tags = ["catchphrase","edition_name","month_pillar","day_pillar","from_message"] + [f"chapter{i}" for i in range(1,12)]
                    for tag in all_tags:
                        data[tag] = parse_tag(resp1, tag) or parse_tag(resp2, tag)

                    html = build_html(info, data, sender=sender or "YURI（結梨嘉望）")
                    progress.progress(100, text="✅ 完成！")

                    increment_counter()
                    save_reading(info, data, sender or "YURI（結梨嘉望）")
                    st.session_state.already_generated = True
                    st.session_state.reading_info   = info
                    st.session_state.reading_data   = data
                    st.session_state.reading_sender = sender or "YURI（結梨嘉望）"
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

# ── 修正依頼セクション ────────────────────────────────────────

if st.session_state.get("reading_data"):
    st.markdown('<div class="gold-line"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="main-title" style="font-size:1.4rem; margin-top:1rem;">✏️ 修正依頼</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-title" style="margin-bottom:1rem;">REVISION REQUEST</div>',
        unsafe_allow_html=True,
    )

    chapter_options = {"表紙・キャッチコピー / エディション名": 0}
    chapter_options.update({
        f"CHAPTER {i:02d}　{CHAPTER_META[i][0]}": i for i in range(1, 12)
    })
    chapter_options["署名ページ（FROM）の差出人名を変更"] = 99

    with st.form("revision_form"):
        sel_label = st.selectbox("修正したい箇所", list(chapter_options.keys()))
        feedback  = st.text_area(
            "どう修正したいですか？",
            placeholder="例：最後の段落をもっと具体的な行動指針に変えてほしい / アクションプランを職業に合わせてほしい",
            height=100,
        )
        new_sender = st.text_input(
            "差出人名（署名変更の場合のみ入力）",
            value=st.session_state.get("reading_sender", ""),
        )
        rev_submit = st.form_submit_button("✦ この箇所を修正する")

    if rev_submit:
        chapter_num = chapter_options[sel_label]
        if not feedback and chapter_num != 99:
            st.warning("修正内容を入力してください。")
        else:
            _info   = st.session_state.reading_info
            _data   = dict(st.session_state.reading_data)
            _sender = st.session_state.reading_sender

            if chapter_num == 99:
                # 署名だけ変更
                _sender = new_sender or _sender
                st.session_state.reading_sender = _sender
                st.success("署名ページを更新しました。")
            else:
                api_key = os.environ.get("ANTHROPIC_API_KEY")
                if not api_key:
                    st.error("ANTHROPIC_API_KEY が設定されていません。")
                else:
                    with st.spinner(f"「{sel_label}」を修正中（30〜60秒）…"):
                        try:
                            client = Anthropic(api_key=api_key)
                            resp = regenerate_chapter(client, _info, _data, chapter_num, feedback)

                            if chapter_num == 0:
                                new_catch   = parse_tag(resp, "catchphrase")
                                new_edition = parse_tag(resp, "edition_name")
                                if new_catch:   _data["catchphrase"]   = new_catch
                                if new_edition: _data["edition_name"]  = new_edition
                            else:
                                new_body = parse_tag(resp, f"chapter{chapter_num}")
                                if new_body:
                                    _data[f"chapter{chapter_num}"] = new_body
                                else:
                                    st.warning("修正内容を取得できませんでした。フィードバックを変えてもう一度お試しください。")

                            st.session_state.reading_data = _data
                            st.success(f"「{sel_label}」の修正が完了しました！下からダウンロードしてください。")
                        except Exception as e:
                            st.error(f"修正中にエラーが発生しました：{e}")

            # 修正済み HTML を生成してダウンロードボタン表示
            _data   = st.session_state.reading_data
            _sender = st.session_state.reading_sender
            html_rev = build_html(_info, _data, sender=_sender)
            ts_rev   = datetime.now().strftime("%Y%m%d_%H%M")
            st.download_button(
                label="📥 修正済み鑑定書をダウンロード（HTML）",
                data=html_rev.encode("utf-8"),
                file_name=f"tenmei_{_info['name']}_{ts_rev}_rev.html",
                mime="text/html",
                key=f"dl_rev_{ts_rev}",
            )
            st.caption("ダウンロードしたHTMLをChromeで開き、印刷→PDFに保存してください。")
