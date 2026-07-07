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


def lifepath(y, m, d):
    n = digit_reduce(y) + digit_reduce(m) + digit_reduce(d)
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
    sei_first_for_gai = sei_strokes[0] if len(sei_strokes) >= 2 else 1
    mei_last_for_gai  = mei_strokes[-1] if len(mei_strokes) >= 2 else 1
    gaikaku = sei_first_for_gai + mei_last_for_gai
    soukaku_total = tenkaku + chikaku

    return {
        "天格": tenkaku, "人格": jinkaku, "地格": chikaku,
        "外格": gaikaku, "総格": soukaku_total, "missing": missing,
    }
