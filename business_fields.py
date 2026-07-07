"""
ビジネス鑑定書アンケートの列定義とTSV貼り付けパーサー

Googleフォーム/スプレッドシートからコピーした回答（タブ区切り・複数人分）を
そのまま貼り付けて解析できるようにする。各セルは改行を含みうるが、タブは
含まない前提で、タイムスタンプ（各レコード先頭列）を目印にレコード境界を検出する。
"""
import re

BUSINESS_FIELDS = [
    ("timestamp", "タイムスタンプ"),
    ("email", "メールアドレス"),
    ("name", "お名前（漢字）"),
    ("reading", "ふりがな"),
    ("bdate", "生年月日"),
    ("gender", "性別"),
    ("birthplace", "出生地（都道府県・市区町村）"),
    ("residence", "現在のお住まい（都道府県まで）"),
    ("job_title", "現在の職業・肩書き"),
    ("hard1", "人生で最も辛かった経験①【天命の核心】"),
    ("hard2", "人生で最も辛かった経験②"),
    ("hard3", "人生で最も辛かった経験③（任意）"),
    ("happy1", "人生で最も嬉しかった経験①【天職のヒント】"),
    ("happy2", "人生で最も嬉しかった経験②"),
    ("happy3", "人生で最も嬉しかった経験③（任意）"),
    ("flow", "没頭できること【魂の燃料】"),
    ("praised", "褒められること【天職の才】"),
    ("child_hobby", "子どもの頃に夢中になっていたこと（任意）"),
    ("gratitude_episode", "感謝された体験【天命の証拠】"),
    ("current_job", "現在の仕事の内容・状況"),
    ("current_income", "現在の月収（任意）"),
    ("ideal_income", "理想の月収"),
    ("job_like", "今の仕事で好きなこと・得意なこと"),
    ("job_dislike", "今の仕事で嫌いなこと・消耗すること"),
    ("worries", "現在の悩みや課題"),
    ("want_to_change", "自分のどこを・何を変えたいか"),
    ("future_work", "3年後・5年後の理想の仕事・働き方"),
    ("ideal_life", "理想の暮らし・生活スタイル"),
    ("ideal_partner", "理想のパートナー像（任意）"),
    ("mission", "絶対に叶えたい夢・使命【天命の核心】"),
    ("personality", "自分の性格を一言で"),
    ("others_view", "友人・家族からの評価"),
    ("value1", "大切にしている価値観①"),
    ("value2", "大切にしている価値観②"),
    ("value3", "大切にしている価値観③"),
    ("relationship_pattern", "人間関係で繰り返しやすいパターン"),
    ("weak_point", "苦手な人・状況・環境"),
    ("requested_themes", "希望する内容（複数選択可）"),
    ("other_theme_detail", "その他の自由記載テーマ"),
    ("roadmap_start_year", "ロードマップ開始年"),
    ("special_request", "鑑定書に込めて欲しいこと"),
    ("core_question", "一番の問い"),
    ("message_to_yuri", "YURIへのメッセージ（任意）"),
]

_N = len(BUSINESS_FIELDS)
_RECORD_START = re.compile(r'\d{4}/\d{1,2}/\d{1,2}\s+\d{1,2}:\d{2}:\d{2}\t')


def parse_business_tsv(text):
    """貼り付けられたTSVテキストを解析し、レコード（dict）のリストを返す。
    各セルは改行を含みうる前提。タイムスタンプ列（YYYY/M/D H:MM:SS）を
    レコード境界の目印として使うため、通常のstr.split('\\n')では分割しない。"""
    text = text.strip()
    if not text:
        return []
    starts = [m.start() for m in _RECORD_START.finditer(text)]
    if not starts:
        return []
    blocks = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(text)
        blocks.append(text[start:end].strip('\n'))

    records = []
    for block in blocks:
        cells = block.split('\t')
        cells = (cells + [''] * _N)[:_N]
        record = {key: cells[i].strip() for i, (key, _label) in enumerate(BUSINESS_FIELDS)}
        records.append(record)
    return records


def record_label(record):
    return f"{record.get('name','(名前未入力)')}様　{record.get('bdate','')}　{record.get('timestamp','')}"
