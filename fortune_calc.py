"""
占術データの確定計算ロジック（app.py / generate_reading.py 共通）

年柱・月柱・日柱・九星気学の本命星は、太陽黄経（節気）に基づいて算出する。
固定日付（毎年2/4など）で近似すると、立春が2/3や2/5にずれる年に誤差が出るため、
Meeusの低精度太陽位置式で太陽黄経を計算し、二分探索で節気の正確な瞬間を求めている。
生年月日のみで時刻が不明な場合は正午（JST）を仮定する。
"""
import json
import math
from datetime import datetime, timedelta
from pathlib import Path

# 姓名判断の画数辞書（KANJIDIC2の現代画数＋伝統的な部首補正を反映済み。
# 補正対象：氵→水/忄→心/扌→手/艹→艸/辶→辵/阝→阜・邑/王→玉/月→肉）
_KANJI_STROKES_PATH = Path(__file__).parent / "kanji_strokes.json"
with open(_KANJI_STROKES_PATH, encoding="utf-8") as _f:
    KANJI_STROKES = json.load(_f)

STEMS    = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
MONTH_BRANCHES = ["寅","卯","辰","巳","午","未","申","酉","戌","亥","子","丑"]
# 五虎遁：年干から寅月（正月）の月干を決める対応表
WUHU_DUN = {"甲":"丙","己":"丙","乙":"戊","庚":"戊","丙":"庚","辛":"庚","丁":"壬","壬":"壬","戊":"甲","癸":"甲"}
STARS    = ["一白水星","二黒土星","三碧木星","四緑木星","五黄土星",
            "六白金星","七赤金星","八白土星","九紫火星"]
ZODIAC = [
    (1,19,"山羊座 ♑"), (2,18,"水瓶座 ♒"), (3,20,"魚座 ♓"),
    (4,19,"牡羊座 ♈"), (5,20,"牡牛座 ♉"), (6,21,"双子座 ♊"),
    (7,22,"蟹座 ♋"),   (8,22,"獅子座 ♌"), (9,22,"乙女座 ♍"),
    (10,23,"天秤座 ♎"),(11,22,"蠍座 ♏"),  (12,21,"射手座 ♐"),
    (12,31,"山羊座 ♑"),
]

# 九星の五行（相生：木生火・火生土・土生金・金生水・水生木）
STAR_ELEMENT = {1:"水", 2:"土", 3:"木", 4:"木", 5:"土", 6:"金", 7:"金", 8:"土", 9:"火"}
PRODUCES     = {"木":"火", "火":"土", "土":"金", "金":"水", "水":"木"}
# 年盤の遁行順（後天定位盤：中宮→乾→兌→艮→離→坎→坤→震→巽の順に九星が巡る）
DIRECTION_FLOW = ["中央","北西","西","北東","南","北","南西","東","南東"]
BRANCH_DIRECTION = {
    "子":"北","丑":"北東","寅":"北東","卯":"東","辰":"南東","巳":"南東",
    "午":"南","未":"南西","申":"南西","酉":"西","戌":"北西","亥":"北西",
}
OPPOSITE_DIRECTION = {
    "北":"南","南":"北","東":"西","西":"東",
    "北東":"南西","南西":"北東","北西":"南東","南東":"北西",
}

JST = timedelta(hours=9)


def _jd_utc(dt):
    y, m, d = dt.year, dt.month, dt.day
    frac = (dt.hour + dt.minute / 60 + dt.second / 3600) / 24
    a  = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    jdn = d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045
    return jdn - 0.5 + frac


def _solar_longitude(jd):
    T  = (jd - 2451545.0) / 36525.0
    L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T ** 2
    M  = 357.52911 + 35999.05029 * T - 0.0001537 * T ** 2
    Mr = math.radians(M)
    C  = ((1.914602 - 0.004817 * T - 0.000014 * T ** 2) * math.sin(Mr)
          + (0.019993 - 0.000101 * T) * math.sin(2 * Mr)
          + 0.000289 * math.sin(3 * Mr))
    true_long = L0 + C
    omega = 125.04 - 1934.136 * T
    lam = true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega))
    return lam % 360


def _find_solar_term(target_lon, approx_utc):
    lo, hi = approx_utc - timedelta(days=6), approx_utc + timedelta(days=6)
    def diff(dt):
        return (_solar_longitude(_jd_utc(dt)) - target_lon + 540) % 360 - 180
    for _ in range(60):
        mid = lo + (hi - lo) / 2
        if diff(lo) * diff(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return lo + (hi - lo) / 2


def _risshun_utc(year):
    approx_utc = datetime(year, 2, 4, 12) - JST
    return _find_solar_term(315, approx_utc)


def digit_reduce(n):
    while n > 9:
        n = sum(int(c) for c in str(n))
    return n


def _reduce_keep_master(n):
    """1桁になるまで桁を合算するが、11・22・33（マスターナンバー）に到達したらそこで止める"""
    while n > 9 and n not in (11, 22, 33):
        n = sum(int(c) for c in str(n))
    return n


def lifepath(y, m, d):
    n = _reduce_keep_master(y) + _reduce_keep_master(m) + _reduce_keep_master(d)
    while n not in (11, 22, 33) and n > 9:
        n = sum(int(x) for x in str(n))
    return n


def zodiac_sign(m, d):
    for cm, cd, sign in ZODIAC:
        if m < cm or (m == cm and d <= cd):
            return sign
    return "山羊座 ♑"


def ganshi_year(y, m, d, hour=12, minute=0):
    """立春基準の干支年（節入り前の生まれは前年の干支を使う）"""
    birth_utc = datetime(y, m, d, hour, minute) - JST
    return y - 1 if birth_utc < _risshun_utc(y) else y


def kyusei(y, m, d, hour=12, minute=0):
    adj = ganshi_year(y, m, d, hour, minute)
    n   = digit_reduce(sum(int(c) for c in str(adj)))
    idx = (11 - n) % 9
    return STARS[idx - 1 if idx > 0 else 8]


def year_pillar(y, m, d, hour=12, minute=0):
    adj = ganshi_year(y, m, d, hour, minute)
    return STEMS[(adj - 4) % 10] + BRANCHES[(adj - 4) % 12]


def month_pillar(y, m, d, hour=12, minute=0):
    adj_year  = ganshi_year(y, m, d, hour, minute)
    year_stem = STEMS[(adj_year - 4) % 10]
    birth_utc = datetime(y, m, d, hour, minute) - JST
    lam       = _solar_longitude(_jd_utc(birth_utc))
    sector    = int(((lam - 315) % 360) // 30)  # 0=寅 ... 11=丑
    branch    = MONTH_BRANCHES[sector]
    start_idx = STEMS.index(WUHU_DUN[year_stem])
    stem      = STEMS[(start_idx + sector) % 10]
    return stem + branch


def day_pillar(y, m, d):
    a  = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    jdn = d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045
    return STEMS[(jdn + 9) % 10] + BRANCHES[(jdn + 1) % 12]


# ── 九星気学：吉方位・凶方位 ────────────────────────────────

def star_number(star_name):
    """「八白土星」のような星名から番号（1〜9）を返す"""
    return STARS.index(star_name) + 1


def year_star_number(year):
    """その年の中宮に入る九星の番号（1〜9）"""
    n = digit_reduce(sum(int(c) for c in str(year)))
    idx = (11 - n) % 9
    return idx if idx > 0 else 9


def year_direction_board(year):
    """その年の年盤：{方位: 星番号}（中央を含む9マス）"""
    center = year_star_number(year)
    return {pos: ((center - 1 + i) % 9) + 1 for i, pos in enumerate(DIRECTION_FLOW)}


def lucky_directions(honmei_star_name, year):
    """本命星と対象年から、今年の吉方位・凶方位を算出する"""
    board = year_direction_board(year)

    def find_dir(num):
        for pos, n in board.items():
            if pos != "中央" and n == num:
                return pos
        return None  # 該当の星が中央に回座している年は方位なし

    my_num  = star_number(honmei_star_name)
    my_elem = STAR_ELEMENT[my_num]

    gohou_satsu   = find_dir(5)  # 五黄殺
    ken_satsu     = OPPOSITE_DIRECTION[gohou_satsu] if gohou_satsu else None  # 暗剣殺
    branch        = BRANCHES[(year - 4) % 12]
    sai_ha        = OPPOSITE_DIRECTION[BRANCH_DIRECTION[branch]]  # 歳破
    honmei_satsu  = find_dir(my_num)  # 本命殺
    honmei_teki   = OPPOSITE_DIRECTION[honmei_satsu] if honmei_satsu else None  # 本命的殺

    bad_directions = {d for d in (gohou_satsu, ken_satsu, sai_ha, honmei_satsu, honmei_teki) if d}

    good_directions = []
    for pos, num in board.items():
        if pos == "中央" or pos in bad_directions:
            continue
        elem = STAR_ELEMENT[num]
        if elem == my_elem or PRODUCES[my_elem] == elem:  # 比和・生気
            good_directions.append(pos)

    return {
        "吉方位":  good_directions,
        "五黄殺":  gohou_satsu,
        "暗剣殺":  ken_satsu,
        "歳破":    sai_ha,
        "本命殺":  honmei_satsu,
        "本命的殺": honmei_teki,
    }


# ── 姓名判断：総格・五格 ──────────────────────────────────────

def soukaku(full_name):
    """氏名（フルネーム文字列）の総格（全画数合計）を返す。
    戻り値: (総格, 画数不明の文字のリスト)"""
    total = 0
    missing = []
    for ch in full_name:
        if ch.isspace():
            continue
        sc = KANJI_STROKES.get(ch)
        if sc is None:
            missing.append(ch)
        else:
            total += sc
    return total, missing


def _stroke_list(chars, missing_out):
    strokes = []
    for ch in chars:
        if ch.isspace():
            continue
        sc = KANJI_STROKES.get(ch)
        if sc is None:
            missing_out.append(ch)
            strokes.append(0)
        else:
            strokes.append(sc)
    return strokes


def five_kaku(sei, mei):
    """姓・名から五格（天格・人格・地格・外格・総格）を算出する。
    姓・名が1文字の場合は、人格・外格の計算で仮成分「1」を補う（姓名判断の標準的な扱い）。
    戻り値: {"天格","人格","地格","外格","総格","missing"}"""
    missing = []
    sei_strokes = _stroke_list(sei, missing)
    mei_strokes = _stroke_list(mei, missing)

    tenkaku = sum(sei_strokes)
    chikaku = sum(mei_strokes)
    jinkaku = sei_strokes[-1] + mei_strokes[0]
    soukaku_total = tenkaku + chikaku
    # 外格＝総格－人格（姓の末字・名の初字を除いた残り全文字の合計）。
    # 3文字以上の姓・名では中間の文字も含めて合計する。1文字の場合は仮成分「1」（霊数）で補う。
    sei_rest = sum(sei_strokes[:-1]) if len(sei_strokes) >= 2 else 1
    mei_rest = sum(mei_strokes[1:]) if len(mei_strokes) >= 2 else 1
    gaikaku = sei_rest + mei_rest

    return {
        "天格": tenkaku, "人格": jinkaku, "地格": chikaku,
        "外格": gaikaku, "総格": soukaku_total, "missing": missing,
    }


# ── 姓名判断：画数の意味（格名・吉凶・特徴）── 熊崎式系の一般的な数意早見表 ──
# 出典：jinseiwohiraku.work「名前の画数◯画〜◯画の意味」シリーズ（1〜60画）を基に整理。
# 61画以上は該当データがまれなため、下12桁のパターンから簡易的にフォールバックする。
KAKU_MEANINGS = {
    1: ("生数", "大吉", "無から有を生み出す吉数"),
    2: ("動揺", "凶", "周囲との調和が難しく、破壊やトラブルが多い"),
    3: ("希望", "吉", "人柄が良く信用を得られ、順調に成功する"),
    4: ("困苦", "凶", "健康や家庭に乱れが生じ、成就が難しい"),
    5: ("福寿", "吉", "万物の最初の調和数で心身のバランスが良好"),
    6: ("天徳", "吉", "誠実で信念を持ち、周囲から信頼される"),
    7: ("独立", "半吉", "意思が強く行動力があるが、周囲との対立に注意"),
    8: ("根気", "吉", "努力する勤勉さで金運も良く着実に上昇する"),
    9: ("逆境", "凶", "能力は高いが神経質さから家庭や健康に影響が出やすい"),
    10: ("不安定", "凶", "不安定な状況になりやすく、転機が起きやすい"),
    11: ("迎春", "大吉", "コツコツと着実に事を成し遂げ、年長者に引き立てられる"),
    12: ("挫折", "凶", "美的センスや芸術面に才能があるが途中で挫折しやすい"),
    13: ("人気", "吉", "信用と実力を併せ持ち、明るく人に好かれ金銭にも恵まれる"),
    14: ("不如意", "凶", "考えが偏りがちで孤独感を味わいやすい"),
    15: ("徳望", "吉", "穏やかで円満、名誉運に恵まれ理想的なリーダーになれる"),
    16: ("衆望", "大吉", "三大吉数の一つ。指導者となり大きな発展が期待できる"),
    17: ("権威", "吉", "信念を持ち義理堅く、職人や専門職で活躍できる"),
    18: ("剛気", "吉", "金運や物質運に恵まれ、温和で信頼と尊敬を得られる"),
    19: ("障害", "凶", "美的センスがあるが神経質になり健康に影響しやすい"),
    20: ("災厄", "凶", "物事が極端になりやすく、心身や家庭運に障害が多い"),
    21: ("頭領", "大吉", "努力家で信念を貫き、事を成し遂げるリーダーシップの数"),
    22: ("挫折", "凶", "美的感覚に優れるが孤独感を抱えやすい"),
    23: ("頭領", "大吉", "一代で名誉・地位を得られる、早期の出世が特徴の数"),
    24: ("興産", "大吉", "心身穏やかで、家庭運や金運に恵まれる"),
    25: ("鋭敏", "吉", "活動的で独立心があり、商売向きの吉数"),
    26: ("波乱", "凶", "真面目だが欲が強く、家族や周囲と波乱が起きやすい"),
    27: ("孤立", "半吉", "直観力と行動力があるが、強情さが強いと孤立しやすい"),
    28: ("遭難", "凶", "変化が起こりやすく、肝心な時に波乱が生じやすい"),
    29: ("知謀", "大吉", "頭脳明晰で誠実、才知と財力を兼ね備えた数"),
    30: ("波乱", "半吉", "人柄は良いが環境の変化に流されやすい"),
    31: ("頭領", "大吉", "地位・名誉・金運に恵まれ、信念を持ってコツコツ築く数"),
    32: ("暁光", "大吉", "思いがけぬ好機（僥倖）を掴むと大きく飛躍できる数"),
    33: ("昇龍", "吉", "日の出のごとく、名誉・出世を目指す力強い経営者向きの数"),
    34: ("変転", "半吉", "誤解を招きやすいが、強い信念と決断力で独立成功に至る数"),
    35: ("温和", "吉", "感性豊かで堅実。粘り強さに勇気が加わると飛躍する数"),
    36: ("英雄", "半吉", "頭脳明晰で独立心旺盛。協調性を重ねることで大成する数"),
    37: ("独立", "大吉", "順応力と忍耐力があり、独立・海外でも活躍できる強い数"),
    38: ("技芸", "半吉", "誠実で信用され、技術・専門分野で前向きに成功する数"),
    39: ("頭領", "大吉", "誠実で冷静なリーダー素質。自信と謙虚さが鍵になる数"),
    40: ("波乱", "半吉", "頭の回転は速いが極端になりやすく、謙虚さが大切な数"),
    41: ("実力", "大吉", "コツコツと努力し、堅実に物事を成し遂げる数"),
    42: ("多芸", "半吉", "優しく穏やかで、勇気を持つことで幸運に恵まれる数"),
    43: ("独立", "半吉", "若いうちから認められ、名声や地位を得やすい数"),
    44: ("遅咲", "吉", "おとなしく優しい性質で、地道な努力が実を結ぶ数"),
    45: ("順風", "吉", "前向きに、苦難も一つ一つ乗り越えていける数"),
    46: ("泥船", "凶", "神経が細やかで、周囲の目が気になりやすい数"),
    47: ("開花", "吉", "花のように静かに、しかし着実に開花できる数"),
    48: ("軍師", "吉", "体力と決断力があり、才知と徳を兼ね備えた数"),
    49: ("変転", "半吉", "周囲の援助を受けやすく、努力により好転する数"),
    50: ("衰退", "凶", "不安定な要素があるが、信念と努力でチャンスを掴める数"),
    51: ("確実な進展", "吉", "真面目で慎重派。着実に前へ進む数"),
    52: ("安泰", "吉", "積極的で勇気があり、大きな力を発揮する数"),
    53: ("勤勉", "半吉", "温厚で周囲から慕われる数"),
    54: ("破兆", "凶", "神経が細やかで、協調性が重要になる数"),
    55: ("横柄", "凶", "機転と行動力があるが、寛容さが必要な数"),
    56: ("裏目", "凶", "消極的になりやすく、前向きさが必要な数"),
    57: ("再起", "半吉", "災難から起き上がれる、再起の力を持つ数"),
    58: ("再起", "半吉", "謙虚さと感謝の心が運気を上げる数"),
    59: ("怠慢", "凶", "忍耐力・向上心を意識して補いたい数"),
    60: ("迷走", "凶", "迷いやすいため、判断は慎重に行いたい数"),
}


def kaku_meaning(n):
    """画数nの(格名, 吉凶, 特徴)を返す。60画超は下一桁のパターンで簡易フォールバックする。"""
    if n in KAKU_MEANINGS:
        return KAKU_MEANINGS[n]
    base = KAKU_MEANINGS.get(((n - 1) % 60) + 1)
    if base:
        return (base[0], base[1], base[2] + "（60超の大数のため参考値）")
    return ("大数", "吉", "大きな数のため個性が強く出る数")


def format_gokaku_breakdown(tenkaku, jinkaku, chikaku, gaikaku, soukaku_total):
    """五格それぞれに格名を添えた文字列を返す（プロンプトに埋め込む用）。
    吉数（吉・大吉）の場合のみ格名を添え、凶数・半吉は数字のみ表示する。"""
    def fmt(label, n):
        name, kikkyo, _ = kaku_meaning(n)
        if kikkyo in ("吉", "大吉"):
            return f"{label}{n}（{name}格・{kikkyo}）"
        return f"{label}{n}"
    return "／".join([
        fmt("天格", tenkaku), fmt("人格", jinkaku),
        fmt("地格", chikaku), fmt("外格", gaikaku),
        fmt("総格", soukaku_total),
    ])
