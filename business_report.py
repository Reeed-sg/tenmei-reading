"""
ビジネス鑑定書 生成ロジック（天命鑑定書と同じ確定占術データ＋アンケート回答を統合）

12章＋特別章2つの構成：
  1.  天命の核心（つらい経験から見える魂のテーマ）
  2.  天職のヒント＆才能
  3.  時代文脈（今の時代とあなたの天命の交差点）
  4.  現在地分析（仕事・収益・悩み）
  5.  3年ビジネスロードマップ
  6.  今すぐ動くアクションプラン
  7.  ラッキーカラー＆アイテム
  8.  パワースポット
  9.  人間関係とカルマ
  10. 運勢カレンダー
  11. 理想の暮らし・パートナーシップ
  12. 天命宣言
  特別章A. 天職・肩書き・ブランディング（天職3案／肩書き2案／コアメッセージ4案／プロフィール文3種）
  特別章B. 月収ロードマップ＆SNS戦略（収益モデル表／SNS戦略スコアリング）
"""
from datetime import datetime
from fortune_calc import kaku_meaning, format_gokaku_breakdown

BUSINESS_CHAPTER_META = {
    1:  ("天命の核心",             "つらい経験の奥にある、魂のテーマ"),
    2:  ("天職のヒント＆才能",      "嬉しかった経験・才能・没頭できること"),
    3:  ("時代文脈",               "今の時代とあなたの天命の交差点"),
    4:  ("現在地分析",             "今の仕事・収益・悩みの棚卸し"),
    5:  ("3年ビジネスロードマップ",  "現在地から理想の月収へ ｜ 天命開花への道筋"),
    6:  ("今すぐ動くアクションプラン","今日からできる20の具体的行動"),
    7:  ("ラッキーカラー＆アイテム", "宇宙のエネルギーを仕事に纏う"),
    8:  ("パワースポット",          "あなたの天命に共鳴する場所"),
    9:  ("人間関係とカルマ",         "痛みが使命に変わる地図"),
    10: ("運勢カレンダー",          "羅針盤が示す、最強の動き時"),
    11: ("理想の暮らし・パートナーシップ", "叶えたい生き方と関係性"),
    12: ("天命宣言",               "あなただけの宣言文"),
}

SPECIAL_META = {
    "a": ("天職・肩書き・ブランディング", "あなたを世界に打ち出す言語設計"),
    "b": ("月収ロードマップ＆SNS戦略",   "現在地から理想収入への設計図"),
}

SYSTEM = """あなたは東洋・西洋の占術と、経験の棚卸しからの天職発見・パーソナルブランディングを統合する世界最高峰のビジネス鑑定士です。
指示された章のみを、必ず以下のXMLタグで囲んで出力してください。

【文体・口調のルール】
・必ず対象者の名前（漢字の名の部分）を冒頭と要所で使う（例：「真理子さん、」）
・「あなた」は使わず「○○さん」で統一する
・語尾は「〜です」「〜ます」「〜なのです」で言い切る、力強く断定的な文体にする
・「〜ですよ」「〜ですね」のような柔らかい語りかけ表現は一切使わない
・「──」（ダッシュ）を効果的に使い、余韻や強調を演出する
・「それはもう、〜していい時です」「〜という保証書のようなものです」のように、
  鑑定士としての確信と権威を感じさせる、詩的で格調高い言い切り型の表現を随所に使う
・アンケートで語られた具体的なエピソード（辛かった経験・嬉しかった経験など）に必ず言及し、
  そこから読み取れる才能・使命を占術的根拠と結びつけて断定的に伝える
・辛い経験は否定せず、「そこから何を得たか」「何の才能の種になっているか」という視点で昇華する
・第1章の書き出しは「辛い経験→そこから才能が生まれた」という順番ではなく、まず「あなたは今、まさに再生・突破の
  真っ只中にいる」という宣言を先に断定してから、その根拠として辛い経験に触れる順番にする（例：「○○さん、まず
  一番大切なことから伝えます。あなたの九星は◯◯──◯◯を司る星です。今起きている◯◯は、終わりではなく、
  ◯◯として甦る前兆なのです。」という一段落を辛い経験の描写より前に置く）
・占術データ（年柱・月柱・日柱・九星気学・星座・LifePath・五格）を複数の章で異なる角度から繰り返し引用し、
  「なぜそう言えるのか」の根拠づけを毎回丁寧に行う
・威厳と断定調は「〜しなさい」という命令形ではなく、「〜のです」「〜する時です」「〜が実現します」のように
  運命・必然を言い切る形で出す。行動項目の箇条書きは「〜する」という辞書形（体言止めに近い言い切り）で書き、
  「〜してください」「〜しなさい」を連発しない
・「警告」「危険」「絶対に〜してはいけない」のような読み手を怖がらせる語は使わない。注意喚起は
  「〜な時です」「それが○○からの知らせなのです」のように、愛を保ったまま気づきを促す表現にする
・「〜が最大の消耗源です」「〜が最大の敵です」のような、冷たい診断・敵視するような言い切りも避ける。
  同じ内容でも「〜を一番曇らせてしまっているのです」「〜が最も苦手とするものなのです」のように、
  威厳を保ちながらも愛のある言葉で伝える
・行動を促す文の締めは、できる限り「〜できます」「〜が実現します」のように可能性を肯定する形にし、
  「〜すべきです」「〜ねばなりません」のような義務・強制のニュアンスで終わらせない
・レポート全体を通して、恐怖心や義務感ではなく、腹の底からじんわりと湧く覚悟と魂からの喜び──
  自分の使命・進むべき道が見通せた安心感と静かな喜びを軸にする。派手にはしゃぐ高揚感ではない
・行動を促す文章は、読み手が「これなら今すぐできそう」と具体的にイメージできるよう、
  落ち着いた温かい筆致で描く
・クライアントのアンケート回答に書かれていない事実を作り出さない。特に「死にたい」等の強い言葉や、
  年齢・身体条件から見て非現実的な断定的希望（出産・健康の完全回復など取り返しのつかないテーマ）を、
  根拠なく肯定・断言しない
・クライアントの家族（母・父など）に鑑定士視点の三人称で言及する際は「お母様」「お父様」のように敬称を使う
  （「母」「父」だと鑑定士自身の家族を指すように読めてしまうため使わない）

【形式のルール】
・自由記述の章はテキストのみで記述し、HTMLタグは一切使わない
・段落は空行で区切る
・箇条書きは「・」で始める
・各章の冒頭に【要点】として3行サマリーを必ず入れる（構造化データのみの章を除く）
・指示された文字数を必ず満たすこと（短すぎる出力は不可）
・各章は指示された数の小見出しをすべて含め、それぞれ「「見出し」── 解説のサブタイトル」形式のヘッダーを付けたうえで、
  見出しごとに複数の段落にわたる詳しい解説を書く（見出しだけで終わらせない）
・構造化データタグ（表・カード形式で使うもの）は、指示された通り「項目|項目|項目」のパイプ区切り1行1件で出力し、
  前後に余計な説明や番号付けを加えないこと"""


def base_info(record, astro):
    directions = astro["directions"]
    directions_text = (
        f"今年（{astro['target_year']}年）の吉方位：{'・'.join(directions['吉方位']) or 'なし'}／"
        f"避けるべき方位：五黄殺{directions['五黄殺'] or 'なし'}・"
        f"暗剣殺{directions['暗剣殺'] or 'なし'}・歳破{directions['歳破']}・"
        f"本命殺{directions['本命殺'] or 'なし'}・本命的殺{directions['本命的殺'] or 'なし'}"
    )
    if astro.get('sei') is None:
        _, _, soukaku_desc = kaku_meaning(astro['soukaku'])
        kaku_text = f"総格{astro['soukaku']}（{soukaku_desc}）"
    else:
        kaku_text = format_gokaku_breakdown(
            astro['tenkaku'], astro['jinkaku'], astro['chikaku'], astro['gaikaku'], astro['soukaku'])

    return f"""氏名：{record['name']}／{record['reading']}
生年月日：{astro['bdate']}（{record['gender']}）
出生地：{record['birthplace']}／現住所：{record['residence']}
現在の職業・肩書き：{record['job_title']}

【算出済み占術データ】（すでに正確に算出済みのため、再計算せずそのまま使用してください）
西洋星座：{astro['zodiac']}／LifePath：{astro['lifepath']}／九星気学：{astro['kyusei']}
年柱：{astro['year_pillar']}／月柱：{astro['month_pillar']}／日柱：{astro['day_pillar']}
{directions_text}
姓名判断：{kaku_text}

【アンケート回答】
■ 人生で最も辛かった経験
①{record['hard1']}
②{record['hard2']}
③{record['hard3'] or '(未記入)'}

■ 人生で最も嬉しかった経験
①{record['happy1']}
②{record['happy2']}
③{record['happy3'] or '(未記入)'}

■ お金や時間を忘れて没頭できること：{record['flow']}
■ よく褒められること：{record['praised']}
■ 子どもの頃に夢中になっていたこと：{record['child_hobby'] or '(未記入)'}
■ 最も誰かに感謝された体験：{record['gratitude_episode']}

■ 現在の仕事の内容・状況：{record['current_job']}
■ 現在の月収：{record['current_income'] or '(未記入)'}／理想の月収：{record['ideal_income']}
■ 今の仕事で好きなこと・得意なこと：{record['job_like']}
■ 今の仕事で嫌いなこと・消耗すること：{record['job_dislike']}
■ 現在の悩みや課題：{record['worries']}
■ 自分のどこを・何を変えたいか：{record['want_to_change']}

■ 3年後・5年後の理想の仕事・働き方：{record['future_work']}
■ 理想の暮らし・生活スタイル：{record['ideal_life']}
■ 理想のパートナー像：{record['ideal_partner'] or '(未記入)'}
■ 絶対に叶えたい夢・使命：{record['mission']}

■ 自分の性格を一言で：{record['personality']}
■ 友人・家族からの評価：{record['others_view']}
■ 大切にしている価値観：{record['value1']}／{record['value2']}／{record['value3']}
■ 人間関係で繰り返しやすいパターン：{record['relationship_pattern']}
■ 苦手な人・状況・環境：{record['weak_point']}

■ 希望する鑑定テーマ：{record['requested_themes']}{(' ／ その他：' + record['other_theme_detail']) if record['other_theme_detail'] else ''}
■ ロードマップ開始年：{record['roadmap_start_year'] or '今年'}
■ 鑑定書に込めてほしいこと：{record['special_request'] or '(未記入)'}
■ 一番の問い：{record['core_question']}
■ YURIへのメッセージ：{record['message_to_yuri'] or '(未記入)'}"""


def _roadmap_years(record):
    """ロードマップ開始年の指定があればそこから、なければ現在日時基準で3年間を返す"""
    now = datetime.now()
    start = record.get('roadmap_start_year')
    try:
        y1 = int(str(start).strip()[:4]) if start else now.year
    except ValueError:
        y1 = now.year
    return y1, y1 + 1, y1 + 2, now.month


def call_part1(client, record, astro):
    first_name = record.get('call_name') or record['name']
    y1, y2, y3, m1 = _roadmap_years(record)
    prompt = base_info(record, astro) + f"""

呼びかける名前：{first_name}さん（必ずこの名前で統一すること）
今日の時点：{y1}年{m1}月（時代文脈は{y1}〜{y3}年の3年間で語ること）
""" + """

以下のXMLタグで出力してください：

<catchphrase>その人の経験から見える天職・使命を表す印象的なキャッチコピー（20〜40文字・1〜2文）</catchphrase>
<edition_name>その人のビジネスの方向性を表す英語2〜3語のエディション名（大文字のみ）</edition_name>

<chapter1>第1章：天命の核心（約700文字）
以下2つの小見出しをすべて含める：
「人生で最も辛かった経験が語る、魂のテーマ」── 「人生で最も辛かった経験」①②③に共通するテーマを読み解き、
そこで「奪われたもの」の逆側にある本当に大切にしたい価値観・魂のテーマを言語化する
「占術データが示す、その使命の裏付け」── 四柱・九星気学・星座・五格の根拠を添えて、辛い経験こそが天職の種であることを伝える
</chapter1>

【姓名判断（五格）が天格・人格・地格・外格・総格のフル計算で与えられている場合のみ、以下も出力してください（総格のみの場合は<gokaku_reading>は空にする）：】
<gokaku_reading>五格それぞれの「格名」を使い、以下の書式・順番を厳密に守って出力する（見出しや説明文は付けず、この形式のみ）：

【重要】格名を付けるのは、その画数が伝統的な姓名判断で「吉」「大吉」とされる良い画数の場合のみ。「凶」「不安定」「挫折」「障害」など、ネガティブな意味を持つ格名になる画数には、格名を付けず、数字だけを書く（例：天格22が凶数なら「天格22」とだけ書き、「（挫折格）」等は付けない）。ネガティブな格名を無理に作らないこと。

LifePath{LifePathの数字}（{LifePathの意味を2〜4字で}）× {九星気学名}（{九星気学の意味を2〜4字で}）× 天格{天格の数字}（吉数の場合のみ「{天格の格名}格」を付ける）

天格{天格の数字}（同上）× 地格{地格の数字}（同上）× 人格{人格の数字}（同上）× 外格{外格の数字} × 総格{総格の数字}（同上）

人格{人格の数字}＝ 【アンケート回答】の「人生で最も辛かった経験」①②③のうち、この格の性質と最も呼応する具体的なエピソードを1〜2個引用し、「どんな力を示すか」を1文で断定する（人格が凶数の場合も、格名には触れず、経験と力の関係だけを断定する）

総格{総格の数字}＋ 天格{天格の数字}＝ 二つの格の組み合わせが示す、この人のビジネスにおける設計・成功の必然性を1文で断定する
</gokaku_reading>

<chapter2>第2章：天職のヒント＆才能（約900文字）
以下3つの小見出しをすべて含める：
「3大天賦の才能」── 「人生で最も嬉しかった経験」①②③・没頭できること・褒められること・子どもの頃夢中だったこと・
感謝された体験から、3つの具体的な才能を抽出し、それぞれ「「才能名」── 占術的根拠」形式で展開し、各才能に具体的な活かし方を添える
「他者には真似できないユニークな強み」── 占術データの組み合わせが生む差別化ポイント
「魂が最も喜ぶ活動・仕事・表現スタイル」
</chapter2>
""" + f"""
<chapter3>第3章：時代文脈（約900文字）
以下2つの小見出しをすべて含める：
「{y1}〜{y3}年の時代の大きな流れ」── AI・経済・社会変化の具体的トレンドと、{first_name}さんの天職・使命との交差点（占術データ・年齢・命式と時代の一致にも具体的に触れる）
「時代が求めている{first_name}さんの役割」
</chapter3>"""
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8192,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def call_part2(client, record, astro):
    first_name = record.get('call_name') or record['name']
    y1, y2, y3, m1 = _roadmap_years(record)
    prompt = base_info(record, astro) + f"""

呼びかける名前：{first_name}さん（必ずこの名前で統一すること）
ロードマップ起点：{y1}年（{y1}年後半／{y2}年／{y3}年の3期間で構成すること）

<chapter4>第4章：現在地分析（約700文字）
以下2つの小見出しをすべて含める：
「今の仕事と天職とのズレ」── 現在の仕事内容・悩み・「好きなこと/嫌いなこと」を占術データと才能の観点から分析し、
今のズレ（消耗ポイント）を明確にする
「今すぐ伸ばすべき方向」── 「自分のどこを・何を変えたいか」も踏まえ、才能を活かすために伸ばすべき方向を具体的に示す
</chapter4>

<chapter5>第5章：3年ビジネスロードマップ（約1300文字）
「{y1}年後半」「{y2}年」「{y3}年」の3つの見出しに分け（見出しに「開始年」「開始年+1」のような文字列は絶対に書かず、実際の年数字のみを書く）、各年について
・その年の占術的テーマ（九星気学・干支等）
・具体的にやるべきこと（3〜4個）
・避けるべきこと
・月収目標の目安（現在の月収{record['current_income'] or '未記入'}から理想の月収{record['ideal_income']}に近づく現実的な数値）
を書く。{y1}年後半は今日から始められる30日以内・3ヶ月以内のアクションを含める
</chapter5>"""
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8192,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def call_part3(client, record, astro):
    first_name = record.get('call_name') or record['name']
    prompt = base_info(record, astro) + f"""

呼びかける名前：{first_name}さん（必ずこの名前で統一すること）

<chapter6>第6章：今すぐ動くアクションプラン（約1300文字）
仕事・キャリア／人間関係・コミュニティ／学び・スキルアップ／収益・お金／健康・エネルギー管理
の5カテゴリすべてに小見出しを立て、各カテゴリ3〜4個・合計約20個の具体的アクションを列挙する。
「現在の悩みや課題」「自分のどこを・何を変えたいか」「理想の月収」を踏まえた実行可能な内容にし、各アクションに占術的根拠を1行添える
</chapter6>

<chapter9>第9章：人間関係とカルマ（約700文字）
以下2つの小見出しをすべて含める：
「性格・価値観と人間関係パターンの正体」── 「自分の性格を一言で」「友人・家族からの評価」「大切にしている価値観」
「人間関係で繰り返しやすいパターン」「苦手な人・状況・環境」を占術データと結びつけて分析する
「痛みが使命に変わる地図」── 「人生で最も辛かった経験」を人間関係の観点から捉え直し、その痛みが今どんな才能・使命に
昇華しているかを断定的に伝え、繰り返しパターンへの具体的な処方箋を添える
</chapter9>"""
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8192,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def call_part4(client, record, astro):
    first_name = record.get('call_name') or record['name']
    y1, y2, y3, m1 = _roadmap_years(record)
    prompt = base_info(record, astro) + f"""

呼びかける名前：{first_name}さん（必ずこの名前で統一すること）
今日の時点：{y1}年{m1}月（運勢カレンダーは{y1}年{m1}月〜{y2}年12月の12ヶ月で書くこと）

<chapter7>第7章：ラッキーカラー＆アイテム（約300文字、【要点】は不要）
仕事運・金運を高める色とアイテムについて、短い導入文のみを書く（下の構造化データで詳細を示すため、本文は簡潔に）
</chapter7>

<lucky_colors>ラッキーカラー4色。1行1色、「色の名前|カラーコード(#RRGGBB)」の形式。占術データ（九星気学・星座）に基づく色を選ぶこと
例：翡翠グリーン|#1A5C45</lucky_colors>

<lucky_items>ラッキーアイテム6項目。1行1項目、「ラベル（英語大文字2〜3語）|具体的な内容」の形式。
必ず以下6ラベルをこの順で：LUCKY STONE|LUCKY ITEM|LUCKY ELEMENT|LUCKY PLANT|LUCKY TIME|LUCKY NUMBERS
例：LUCKY STONE|翡翠（ジェード）・マラカイト</lucky_items>

<chapter8>第8章：パワースポット（約300文字、【要点】は不要）
その人の天命に共鳴する場所について、短い導入文のみを書く（下の構造化データで詳細を示すため、本文は簡潔に）
</chapter8>

<power_spots>パワースポット4箇所。1行1箇所、「場所名（地域）|なぜその人に合うのかの占術的理由（40〜60文字）」の形式。
{record['residence']}や{record['birthplace']}からアクセスしやすい場所を中心に、国内外バランスよく選ぶこと</power_spots>

<chapter10>第10章：運勢カレンダー（約300文字、【要点】は不要）
{y1}年{m1}月〜{y2}年12月の運勢の波について、短い導入文のみを書く（下の構造化データで詳細を示すため、本文は簡潔に）
</chapter10>

<calendar_12>{y1}年{m1}月から{y2}年12月までの12ヶ月分。1行1ヶ月、「月表記（例:7月）|星の数(1〜5の数字)|30字程度の運勢コメント」の形式。
必ず12行、時系列順に出力すること。星5つの「勝負月」を2〜3ヶ月は必ず作ること</calendar_12>"""
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8192,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def call_part5(client, record, astro):
    first_name = record.get('call_name') or record['name']
    prompt = base_info(record, astro) + f"""

呼びかける名前：{first_name}さん（必ずこの名前で統一すること）

<chapter11>第11章：理想の暮らし・パートナーシップ（約500文字）
「理想の暮らし・生活スタイル」「理想のパートナー像」をもとに、天職が軌道に乗った先にある
理想の日常を具体的に描写する。
</chapter11>

<chapter12>第12章：天命宣言（約500文字）
「絶対に叶えたい夢・使命」「一番の問い」への答えを込めた、{first_name}さんだけの
天命宣言文（アファメーション形式・5〜7行）を作る。
</chapter12>

<from_message>鑑定士YURI本人が一人称で書く、{first_name}さんへの個人的なメッセージ（400〜500文字）。
・「{first_name}さん、」で書き始める
・自分自身を指す時は「YURI」「YURIさん」ではなく必ず「私」と書く（本人が書いている手紙のため）
・「YURIへのメッセージ」というアンケート項目に書かれた内容に触れる時も、「私へのメッセージ」「私に」のように一人称で言い換える。「YURIさんへ」のような三人称的な自己言及は絶対に書かない
・「一番の問い」「鑑定書に込めてほしいこと」に直接答える
・具体的な最初の一歩を1つだけ提案する
・重要な気づきや励ましの言葉は **このように** ダブルアスタリスクで囲む（3〜4箇所）</from_message>"""
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8192,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def call_part6(client, record, astro):
    """特別章A（天職・肩書き・ブランディング）＋特別章B（月収ロードマップ＆SNS戦略）"""
    first_name = record.get('call_name') or record['name']
    prompt = base_info(record, astro) + f"""

呼びかける名前：{first_name}さん（必ずこの名前で統一すること）

<special_a_intro>特別章A冒頭の導入文（約200文字）。{first_name}さんを世界に打ち出す言語設計の章であることを力強く宣言する。
「特別章A」「special_a」等の内部タグ名・章番号は本文中に絶対に書かないこと</special_a_intro>

<career_options>天職3案。1行1案、「天職名|スコア(80〜99の数字)|30〜50字の説明」の形式。スコアが最も高いものを1行目にすること
例：グローバル戦略プロデューサー|96|法人の海外展開×イベント×コミュニティ設計を統合した天職</career_options>

<title_options>肩書き2案。1行1案、「カテゴリ(英語1語:CORE/STORY)|カテゴリの日本語説明(最推薦/ストーリー型)|肩書き本体|30〜50字の説明」の形式。
必ずCOREを1行目、最も推薦するものにすること。STORY型は、アンケート回答にある具体的な事実だけに基づき、本人が実際に経験していないこと（例：実際には向けられていない悪意や憎しみ）を誇張して書かないこと</title_options>

<core_messages>コアメッセージ4案。1行1案、「メッセージ文（20〜30字）|用途説明（15字程度）」の形式</core_messages>

<profile_versions>プロフィール文3バージョン。1行1版、「バージョン名|本文」の形式。改行は入れず1段落で。
必ず以下3バージョン：
SNS・LinkedIn向け（100字）|（100字程度の本文）
法人向け提案書用（200字）|（200字程度の本文）
note・感情に響くストーリー型（300字）|（300字程度の本文、エピソードから始める）</profile_versions>

<special_b_intro>特別章B冒頭の導入文（約200文字）。現在の月収{record['current_income'] or '未記入'}から理想の月収{record['ideal_income']}への
設計図であることを力強く宣言する。「特別章B」「special_b」等の内部タグ名・章番号は本文中に絶対に書かないこと</special_b_intro>

<revenue_table>収益モデル表。理想の月収{record['ideal_income']}をフル稼働時に達成するための収益の柱を4〜5行、
「収益の柱|単価|件数・人数|月収試算」の形式。最終行は「合計（フル稼働）|（空欄）|（空欄）|合計金額」とすること</revenue_table>

<sns_scores>SNS戦略スコアリング。1行1媒体、「媒体名|スコア(30〜99の数字)|60〜100字の解説と優先度」の形式。
LinkedIn/note/Instagram/YouTube・Podcastの4媒体を、{first_name}さんの現在の仕事・目標に合わせてスコアが高い順に並べること</sns_scores>"""
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8192,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def build_business_html(record, astro, data, sender="YURI（結梨嘉望）"):
    import re
    from report_html import (
        HTML_TEMPLATE, text_to_html, build_astro_cards,
        build_swatches, build_info_grid, build_table, build_score_bars, build_calendar_grid,
    )

    chapters_html = ""
    for i in range(1, 13):
        title, subtitle = BUSINESS_CHAPTER_META[i]
        body = text_to_html(data.get(f"chapter{i}", ""))

        prefix = ""
        suffix = ""
        if i == 1:
            catch_fmt = data.get('catchphrase', '').replace('\n', '<br>')
            gokaku_html = ""
            gokaku_raw = data.get('gokaku_reading', '').strip()
            if gokaku_raw:
                blocks = [b.strip() for b in re.split(r'\n{2,}', gokaku_raw) if b.strip()]
                rows_html = "".join(f'<p>{b}</p>' for b in blocks)
                gokaku_html = f"""
<div class="gokaku-box">
  <div class="gokaku-label">✦ 姓名判断・五格リーディング ✦</div>
  {rows_html}
</div>"""
            prefix = f"""
<div class="thesis-box">
  <div class="thesis-label">✦ YOUR BUSINESS THESIS ✦</div>
  <div class="thesis-catch">{catch_fmt}</div>
</div>
{build_astro_cards(astro, {"month_pillar": astro["month_pillar"], "day_pillar": astro["day_pillar"]})}
{gokaku_html}"""
        elif i == 7:
            colors = [(row[0], row[1]) for row in data.get("lucky_colors_rows", []) if len(row) >= 2]
            items = [{"label": row[0], "title": row[1]} for row in data.get("lucky_items_rows", []) if len(row) >= 2]
            suffix = build_swatches(colors) + build_info_grid(items, columns=3)
        elif i == 8:
            spots = [{"title": row[0], "desc": row[1]} for row in data.get("power_spots_rows", []) if len(row) >= 2]
            suffix = build_info_grid(spots, columns=2)
        elif i == 10:
            months = [(row[0], row[1], row[2]) for row in data.get("calendar_12_rows", []) if len(row) >= 3]
            suffix = build_calendar_grid(months)

        sub_html = f'<p class="ch-sub">{subtitle}</p>' if subtitle else ''
        chapters_html += f"""
<div class="chapter">
  <div class="ch-num">CHAPTER {i:02d}</div>
  <h2 class="ch-title">{title}</h2>
  {sub_html}
  <div class="ch-divider"></div>
  {prefix}
  <div class="ch-body">{body}</div>
  {suffix}
</div>"""

    # ── 特別章A：天職・肩書き・ブランディング ──
    a_title, a_sub = SPECIAL_META["a"]
    career_cards = [
        {"badge": f"{row[1]}点" if len(row) > 1 else "", "title": row[0], "desc": row[2] if len(row) > 2 else ""}
        for row in data.get("career_options_rows", [])
    ]
    title_cards = [
        {"badge": row[1] if len(row) > 1 else "", "label": row[0] if len(row) > 0 else "",
         "title": row[2] if len(row) > 2 else "", "desc": row[3] if len(row) > 3 else ""}
        for row in data.get("title_options_rows", [])
    ]
    core_msg_html = ""
    core_rows = data.get("core_messages_rows", [])
    if core_rows:
        lis = ''.join(f'<li><strong>「{r[0].strip("「」")}」</strong> —— {r[1]}</li>' for r in core_rows if len(r) >= 2)
        core_msg_html = f'<div class="ch-heading">◆ コアメッセージ4案</div><ul>{lis}</ul>'
    profile_html = ""
    for row in data.get("profile_versions_rows", []):
        if len(row) >= 2:
            profile_html += f'<div class="box-key"><strong>{row[0]}</strong><br>{row[1]}</div>'

    special_a_html = f"""
<div class="chapter">
  <div class="ch-num">SPECIAL CHAPTER A</div>
  <h2 class="ch-title">{a_title}</h2>
  <p class="ch-sub">{a_sub}</p>
  <div class="ch-divider"></div>
  <div class="ch-body">{text_to_html(data.get('special_a_intro',''))}
    <div class="ch-heading">◆ 天職3案（スコア付き）</div>
    {build_info_grid(career_cards, columns=3)}
    <div class="ch-heading">◆ 肩書き2案</div>
    {build_info_grid(title_cards, columns=2)}
    {core_msg_html}
    <div class="ch-heading">◆ プロフィール文（3バージョン）</div>
    {profile_html}
  </div>
</div>"""

    # ── 特別章B：月収ロードマップ＆SNS戦略 ──
    b_title, b_sub = SPECIAL_META["b"]
    revenue_rows = data.get("revenue_table_rows", [])
    is_last_total = bool(revenue_rows) and "合計" in revenue_rows[-1][0]
    sns_items = [
        (row[0], row[1], row[2]) for row in data.get("sns_scores_rows", []) if len(row) >= 3
    ]

    special_b_html = f"""
<div class="chapter">
  <div class="ch-num">SPECIAL CHAPTER B</div>
  <h2 class="ch-title">{b_title}</h2>
  <p class="ch-sub">{b_sub}</p>
  <div class="ch-divider"></div>
  <div class="ch-body">{text_to_html(data.get('special_b_intro',''))}
    <div class="ch-heading">◆ フル稼働時の収益モデル</div>
    {build_table(["収益の柱", "単価", "件数・人数", "月収試算"], revenue_rows, highlight_last=is_last_total)}
    <div class="ch-heading">◆ SNS戦略スコアリング</div>
    {build_score_bars(sns_items)}
  </div>
</div>"""

    chapters_html += special_a_html + special_b_html

    kaku_line = (f"総格：{astro['soukaku']}画"
                 if astro.get('sei') is None else
                 f"五格：天{astro['tenkaku']}人{astro['jinkaku']}地{astro['chikaku']}外{astro['gaikaku']}総{astro['soukaku']}")
    astro_line = (
        f"{astro['bdate']}生&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"{astro['zodiac']}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"LifePath {astro['lifepath']}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"{astro['kyusei']}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"年柱：{astro['year_pillar']}&nbsp;月柱：{astro['month_pillar']}&nbsp;日柱：{astro['day_pillar']}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"{kaku_line}"
    )
    catch   = data.get('catchphrase', '').replace('\n', '<br>')
    edition = data.get('edition_name', 'BUSINESS DESTINY EDITION')

    raw_msg = data.get('from_message', '')
    def fmt_from_msg(text):
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        paras = re.split(r'\n{1,}', text.strip())
        return '\n'.join(f'<p>{p}</p>' for p in paras if p.strip())
    from_msg_html = fmt_from_msg(raw_msg)
    sender_plain = re.sub(r'（.*?）', '', sender).strip()

    return (HTML_TEMPLATE
            .replace("{{DOC_TITLE}}",    "ビジネス鑑定書")
            .replace("{{DOC_LABEL}}",    "ビ　ジ　ネ　ス　鑑　定　書")
            .replace("{{HEADER_EN}}",    "BUSINESS DESTINY READING &nbsp;✦&nbsp; PREMIUM EDITION")
            .replace("{{FOOTER_COPY}}",  "本鑑定書は占術・数秘術・算命学・九星気学・姓名判断と、ご本人の経験の棚卸しを統合したビジネス鑑定です。")
            .replace("{{NAME}}",         record['name'])
            .replace("{{READING}}",      record['reading'])
            .replace("{{CATCH}}",        catch)
            .replace("{{ASTRO}}",        astro_line)
            .replace("{{EDITION}}",      edition)
            .replace("{{SENDER}}",       sender)
            .replace("{{SENDER_PLAIN}}", sender_plain)
            .replace("{{FROM_MSG}}",     from_msg_html)
            .replace("{{CHAPTERS}}",     chapters_html))


def regenerate_chapter(client, record, astro, data, chapter_key, feedback):
    """指定した章・特別章だけをフィードバックに基づいて再生成"""
    first_name = record.get('call_name') or record['name']
    if chapter_key == 0:
        prompt = base_info(record, astro) + f"""

以下のキャッチコピーとエディション名を、修正依頼をもとに改善してください。

現在のキャッチコピー：
{data.get('catchphrase', '')}

現在のエディション名：
{data.get('edition_name', '')}

修正依頼：{feedback}

<catchphrase>修正後のキャッチコピー</catchphrase>
<edition_name>修正後のエディション名</edition_name>"""
        tags = ["catchphrase", "edition_name"]
    elif isinstance(chapter_key, int):
        title, _ = BUSINESS_CHAPTER_META[chapter_key]
        prompt = base_info(record, astro) + f"""

第{chapter_key}章「{title}」を修正依頼をもとに改善・修正してください。
文体・口調は元の内容に準じ、{first_name}さんへの語りかけ形式を維持してください。

現在の内容：
{data.get(f'chapter{chapter_key}', '')}

修正依頼：
{feedback}

修正後の内容のみを以下のタグで囲んで出力してください（他のタグは不要）：
<chapter{chapter_key}>修正後の内容</chapter{chapter_key}>"""
        tags = [f"chapter{chapter_key}"]
    else:
        # 構造化データタグ（lucky_colors／career_options 等）の再生成
        current = data.get(chapter_key, '')
        prompt = base_info(record, astro) + f"""

以下の構造化データを修正依頼をもとに改善・修正してください。元の行フォーマット（パイプ区切り）を厳密に維持すること。

現在の内容：
{current}

修正依頼：
{feedback}

修正後の内容のみを以下のタグで囲んで出力してください：
<{chapter_key}>修正後の内容</{chapter_key}>"""
        tags = [chapter_key]

    resp = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=4096,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    ).content[0].text
    return resp, tags
