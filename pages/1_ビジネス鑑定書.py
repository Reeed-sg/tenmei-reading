import os, re
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

try:
    from anthropic import Anthropic
except ImportError:
    st.error("pip install anthropic を実行してください")
    st.stop()

from fortune_calc import (
    lifepath, zodiac_sign, kyusei, year_pillar, month_pillar, day_pillar,
    lucky_directions, five_kaku, soukaku,
)
from business_fields import parse_business_tsv, BUSINESS_FIELDS, record_label
from business_report import call_part1, call_part2, build_business_html, BUSINESS_CHAPTER_META
from report_html import parse_tag
from report_utils import (
    BASE_CSS, DAILY_LIMIT, require_password, sanitize,
    load_counter, increment_counter, save_reading_json, list_readings_json,
)

st.set_page_config(page_title="ビジネス鑑定書 生成システム", page_icon="💼", layout="centered")

require_password("ビジネス鑑定書", "BUSINESS DESTINY READING SYSTEM")

st.markdown(BASE_CSS, unsafe_allow_html=True)
st.markdown('<div class="main-title">💼 ビジネス鑑定書</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">BUSINESS DESTINY READING SYSTEM</div>', unsafe_allow_html=True)
st.markdown('<div class="gold-line"></div>', unsafe_allow_html=True)


def split_name(name: str):
    """氏名を姓・名に分割する（全角/半角スペースがある場合のみ）"""
    parts = re.split(r'[ 　]+', name.strip())
    parts = [p for p in parts if p]
    if len(parts) == 2:
        return parts[0], parts[1]
    return None, None


def build_astro(record: dict) -> dict:
    m = re.search(r'(\d{4})[年/\-](\d{1,2})[月/\-](\d{1,2})', record['bdate'])
    if not m:
        raise ValueError(f"生年月日の形式を認識できません: {record['bdate']}")
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    kyusei_star = kyusei(y, mo, d)
    target_year = datetime.now().year
    directions  = lucky_directions(kyusei_star, target_year)

    sei, mei = split_name(record['name'])
    if sei and mei:
        kaku = five_kaku(sei, mei)
        kaku_extra = {"sei": sei, "mei": mei, "tenkaku": kaku["天格"], "jinkaku": kaku["人格"],
                      "chikaku": kaku["地格"], "gaikaku": kaku["外格"], "soukaku": kaku["総格"],
                      "soukaku_missing": kaku["missing"]}
    else:
        total, missing = soukaku(record['name'])
        kaku_extra = {"sei": None, "mei": None, "tenkaku": None, "jinkaku": None,
                      "chikaku": None, "gaikaku": None, "soukaku": total, "soukaku_missing": missing}

    return {
        "bdate": f"{y}年{mo}月{d}日",
        "lifepath": lifepath(y, mo, d),
        "zodiac": zodiac_sign(mo, d),
        "kyusei": kyusei_star,
        "year_pillar": year_pillar(y, mo, d),
        "month_pillar": month_pillar(y, mo, d),
        "day_pillar": day_pillar(y, mo, d),
        "target_year": target_year,
        "directions": directions,
        **kaku_extra,
    }


# ── 過去のビジネス鑑定書を読み込む ──────────────────────────────

past = list_readings_json("business_readings")
if past and not st.session_state.get("biz_data"):
    with st.expander("📂 過去のビジネス鑑定書を読み込んで修正する"):
        labels = [f"{p['record']['name']}様　{p['created_at'][:16].replace('T',' ')}" for p in past]
        sel_idx = st.selectbox("鑑定を選択", options=range(len(past)), format_func=lambda i: labels[i], key="biz_past_sel")
        if st.button("読み込む", key="biz_load_past"):
            chosen = past[sel_idx]
            st.session_state.biz_record = chosen["record"]
            st.session_state.biz_astro  = chosen["astro"]
            st.session_state.biz_data   = chosen["data"]
            st.session_state.biz_sender = chosen.get("sender", "")
            st.rerun()

# ── TSV貼り付け ──────────────────────────────────────────────

st.markdown('<p class="section-label">▸ アンケート回答の貼り付け</p>', unsafe_allow_html=True)
st.caption(f"Googleフォーム/スプレッドシートの回答行（タブ区切り・{len(BUSINESS_FIELDS)}列）をそのまま貼り付けてください。複数人分をまとめて貼り付けても、1人ずつ選んで生成できます。")

tsv_text = st.text_area("回答データ（タブ区切り）", height=150, key="tsv_input",
                         placeholder="タイムスタンプ\tメールアドレス\tお名前（漢字）\t...")

if st.button("📋 貼り付けデータを解析する"):
    records = parse_business_tsv(tsv_text)
    if not records:
        st.error("データを解析できませんでした。タイムスタンプ列（例: 2026/06/30 10:20:48）から始まる行になっているか確認してください。")
    else:
        st.session_state.biz_records = records
        st.success(f"{len(records)}件のレコードを読み込みました。")

records = st.session_state.get("biz_records", [])

if records:
    st.markdown('<div class="gold-line"></div>', unsafe_allow_html=True)
    st.markdown('<p class="section-label">▸ 対象者を選択</p>', unsafe_allow_html=True)
    idx = st.selectbox(
        "対象者",
        options=range(len(records)),
        format_func=lambda i: record_label(records[i]),
        key="biz_record_idx",
    )
    record = dict(records[idx])  # コピーして編集可能に

    with st.expander("回答内容を確認・修正する", expanded=False):
        for key, label in BUSINESS_FIELDS:
            record[key] = st.text_area(label, value=record.get(key, ""), height=68, key=f"biz_field_{key}")

    call_name = st.text_input("呼びかける名前*（漢字の「名」部分）", value=split_name(record.get("name",""))[1] or "",
                               placeholder="真理子")
    sender = st.text_input("差出人名", value="YURI（結梨嘉望）", key="biz_sender_input")

    if st.button("✦ ビジネス鑑定書を生成する", key="biz_generate"):
        current_count = load_counter()
        if current_count >= DAILY_LIMIT:
            st.error(f"本日の生成上限（{DAILY_LIMIT}件）に達しました。明日またお試しください。")
            st.stop()
        if not record.get("name") or not record.get("bdate"):
            st.error("お名前・生年月日は必須です。")
            st.stop()
        if not call_name:
            st.error("呼びかける名前を入力してください。")
            st.stop()

        for key, _ in BUSINESS_FIELDS:
            record[key] = sanitize(record.get(key, ""), 3000)
        record["call_name"] = sanitize(call_name, 20)

        try:
            astro = build_astro(record)
        except ValueError as e:
            st.error(str(e))
            st.stop()

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            st.error("ANTHROPIC_API_KEY が設定されていません。管理者にお問い合わせください。")
            st.stop()

        client = Anthropic(api_key=api_key)
        progress = st.progress(0, text="✦ 経験の声を聴いています…")
        try:
            progress.progress(10, text="📖 第1〜4章を生成中（1〜2分）…")
            resp1 = call_part1(client, record, astro)
            progress.progress(55, text="📖 第5〜7章を生成中（1〜2分）…")
            resp2 = call_part2(client, record, astro)
            progress.progress(90, text="📄 鑑定書を組み立て中…")

            data = {}
            all_tags = ["catchphrase", "edition_name", "from_message"] + [f"chapter{i}" for i in range(1, 8)]
            for tag in all_tags:
                data[tag] = parse_tag(resp1, tag) or parse_tag(resp2, tag)

            html = build_business_html(record, astro, data, sender=sender or "YURI（結梨嘉望）")
            progress.progress(100, text="✅ 完成！")

            increment_counter()
            save_reading_json("business_readings", record["name"],
                               {"record": record, "astro": astro, "data": data, "sender": sender})
            st.session_state.biz_record = record
            st.session_state.biz_astro  = astro
            st.session_state.biz_data   = data
            st.session_state.biz_sender = sender

            st.success(f"✦ {record['name']} 様のビジネス鑑定書が完成しました！")
            st.markdown(f"""
<div class="result-box">
    <p style="font-size:1.1rem; color:#C5A84B; letter-spacing:0.1em;">{data.get('catchphrase','').replace(chr(10),'<br>')}</p>
</div>
""", unsafe_allow_html=True)

            ts = datetime.now().strftime("%Y%m%d_%H%M")
            st.download_button(
                "📥 HTMLをダウンロード（Chrome等で開いて印刷→PDF保存）",
                data=html,
                file_name=f"business_{record['name']}_{ts}.html",
                mime="text/html",
            )
        except Exception as e:
            st.error(f"生成中にエラーが発生しました：{e}")

if st.session_state.get("biz_data") and not records:
    # 過去データ読み込み直後（貼り付けをまだしていない場合）のダウンロード導線
    record = st.session_state.biz_record
    data   = st.session_state.biz_data
    astro  = st.session_state.biz_astro
    sender = st.session_state.get("biz_sender", "YURI（結梨嘉望）")
    html = build_business_html(record, astro, data, sender=sender or "YURI（結梨嘉望）")
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    st.download_button(
        "📥 HTMLをダウンロード",
        data=html,
        file_name=f"business_{record['name']}_{ts}.html",
        mime="text/html",
    )
