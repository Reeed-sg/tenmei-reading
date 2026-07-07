"""
天命鑑定書・ビジネス鑑定書で共用するユーティリティ
（Secrets取得・レート制限カウンタ・保存/一覧・入力サニタイズ・共通CSS）
"""
import json
import os
import re
from datetime import date, datetime
from pathlib import Path

import streamlit as st

BASE_DIR     = Path(__file__).parent
COUNTER_FILE = BASE_DIR / ".usage_counter.json"


def get_secret(key, default=None):
    """Streamlit Secrets → .env の順で取得"""
    try:
        return st.secrets[key]
    except Exception:
        return os.environ.get(key, default)


APP_PASSWORD = get_secret("APP_PASSWORD", "")
DAILY_LIMIT  = int(get_secret("DAILY_LIMIT", "50"))


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


def require_password(title: str, subtitle: str):
    """APP_PASSWORD が設定されている場合、簡易パスワードゲートを表示してブロックする"""
    if not APP_PASSWORD:
        return
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.markdown(f'<div class="main-title">✦ {title}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sub-title">{subtitle}</div>', unsafe_allow_html=True)
        st.markdown("---")
        pw = st.text_input("アクセスコードを入力してください", type="password")
        if st.button("認証"):
            if pw == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("アクセスコードが正しくありません")
        st.stop()


def save_reading_json(subdir: str, name: str, payload: dict) -> Path:
    """payload（info/data等を含む辞書）をJSONとして保存し、最新30件のみ保持する"""
    out_dir = BASE_DIR / "output" / subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r'[^\w぀-鿿]', '_', name)
    path = out_dir / f"{ts}_{safe_name}.json"
    payload = {**payload, "created_at": datetime.now().isoformat()}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    files = sorted(out_dir.glob("*.json"), reverse=True)
    for old in files[30:]:
        old.unlink(missing_ok=True)
    return path


def list_readings_json(subdir: str) -> list:
    out_dir = BASE_DIR / "output" / subdir
    if not out_dir.exists():
        return []
    files = sorted(out_dir.glob("*.json"), reverse=True)
    result = []
    for f in files:
        try:
            result.append({"path": f, **json.loads(f.read_text(encoding="utf-8"))})
        except Exception:
            pass
    return result


BASE_CSS = """
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
"""
