"""
ビジネス鑑定書 生成ロジック（天命鑑定書と同じ確定占術データ＋アンケート回答を統合）

7章構成：
  1. 天命の核心（つらい経験から見える魂のテーマ）
  2. 天職のヒント＆才能
  3. 現在地分析（仕事・収益・悩み）
  4. ビジネスロードマップ（3年間・月収目標）
  5. 理想の暮らし・パートナーシップ
  6. 性格・価値観・人間関係パターン
  7. 天命宣言＆鑑定士からのメッセージ
"""

BUSINESS_CHAPTER_META = {
    1: ("天命の核心",             "つらい経験の奥にある、魂のテーマ"),
    2: ("天職のヒント＆才能",      "嬉しかった経験・才能・没頭できること"),
    3: ("現在地分析",             "今の仕事・収益・悩みの棚卸し"),
    4: ("ビジネスロードマップ",     "3年間の月収目標と行動指針"),
    5: ("理想の暮らし・パートナーシップ", "叶えたい生き方と関係性"),
    6: ("性格・価値観・人間関係パターン", "才能の活かし方と注意点"),
    7: ("天命宣言",               "あなただけの宣言文"),
}

SYSTEM = """あなたは東洋・西洋の占術と、経験の棚卸しからの天職発見を統合する世界最高峰のビジネス鑑定士です。
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

【形式のルール】
・テキストのみで記述し、HTMLタグは一切使わない
・段落は空行で区切る
・箇条書きは「・」で始める
・各章の冒頭に【要点】として3行サマリーを必ず入れる
・章内の各テーマには「「見出し」── 解説のサブタイトル」形式でヘッダーを付ける"""


def base_info(record, astro):
    directions = astro["directions"]
    directions_text = (
        f"今年（{astro['target_year']}年）の吉方位：{'・'.join(directions['吉方位']) or 'なし'}／"
        f"避けるべき方位：五黄殺{directions['五黄殺'] or 'なし'}・"
        f"暗剣殺{directions['暗剣殺'] or 'なし'}・歳破{directions['歳破']}・"
        f"本命殺{directions['本命殺'] or 'なし'}・本命的殺{directions['本命的殺'] or 'なし'}"
    )
    kaku_text = (f"総格{astro['soukaku']}"
                 if astro.get('sei') is None else
                 f"天格{astro['tenkaku']}／人格{astro['jinkaku']}／地格{astro['chikaku']}／外格{astro['gaikaku']}／総格{astro['soukaku']}")

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


def call_part1(client, record, astro):
    prompt = base_info(record, astro) + """

以下のXMLタグで出力してください：

<catchphrase>その人の経験から見える天職・使命を表す印象的なキャッチコピー（20〜40文字・1〜2文）</catchphrase>
<edition_name>その人のビジネスの方向性を表す英語2〜3語のエディション名（大文字のみ）</edition_name>

<chapter1>
第1章：天命の核心（約600文字）
「人生で最も辛かった経験」①②③に共通するテーマを読み解き、そこで「奪われたもの」の逆側にある
本当に大切にしたい価値観・魂のテーマを言語化する。占術データ（四柱・九星気学・星座・五格）の
根拠を添えて、辛い経験こそが天職の種であることを伝える。
</chapter1>

<chapter2>
第2章：天職のヒント＆才能（約700文字）
「人生で最も嬉しかった経験」①②③・没頭できること・褒められること・子どもの頃夢中だったこと・
感謝された体験から、3つの具体的な才能を抽出し、それぞれ「「才能名」── 占術的根拠」形式で展開する。
</chapter2>

<chapter3>
第3章：現在地分析（約600文字）
現在の仕事内容・悩み・「好きなこと/嫌いなこと」を占術データと才能の観点から分析し、
今のズレ（消耗ポイント）と伸ばすべき方向を明確にする。
</chapter3>

<chapter4>
第4章：ビジネスロードマップ（約800文字）
ロードマップ開始年から3年間（開始年／開始年+1／開始年+2）で、現在の月収から理想の月収へ
どう近づけるか、才能を活かした具体的な行動指針を年ごとに示す。
</chapter4>"""
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8192,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def call_part2(client, record, astro):
    first_name = record.get('call_name') or record['name']
    prompt = base_info(record, astro) + f"""

呼びかける名前：{first_name}さん（必ずこの名前で統一すること）

<chapter5>
第5章：理想の暮らし・パートナーシップ（約500文字）
理想の暮らし・生活スタイル、理想のパートナー像をもとに、天職が軌道に乗った先にある
理想の日常を具体的に描写する。
</chapter5>

<chapter6>
第6章：性格・価値観・人間関係パターン（約500文字）
性格・友人家族からの評価・大切にしている価値観・人間関係で繰り返しやすいパターン・
苦手な人や環境を占術データと結びつけて分析し、才能を活かすために意識すべき人間関係の築き方を伝える。
</chapter6>

<chapter7>
第7章：天命宣言（約400文字）
「絶対に叶えたい夢・使命」「一番の問い」への答えを込めた、{first_name}さんだけの
天命宣言文（アファメーション形式）を作る。
</chapter7>

<from_message>鑑定士から{first_name}さんへの個人的なメッセージ（300〜400文字）。
・「{first_name}さん、」で書き始める
・「YURIへのメッセージ」で書かれた内容に触れながら、天命から見たポジティブな真実を伝える
・「一番の問い」「鑑定書に込めてほしいこと」に直接答える
・具体的な最初の一歩を1つだけ提案する
・重要な気づきや励ましの言葉は **このように** ダブルアスタリスクで囲む（2〜3箇所）</from_message>"""
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8192,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def build_business_html(record, astro, data, sender="YURI（結梨嘉望）"):
    import re
    from report_html import HTML_TEMPLATE, text_to_html, parse_tag, build_astro_cards

    chapters_html = ""
    for i in range(1, 8):
        title, subtitle = BUSINESS_CHAPTER_META[i]
        body = text_to_html(data.get(f"chapter{i}", ""))

        prefix = ""
        if i == 1:
            catch_fmt = data.get('catchphrase', '').replace('\n', '<br>')
            prefix = f"""
<div class="thesis-box">
  <div class="thesis-label">✦ YOUR BUSINESS THESIS ✦</div>
  <div class="thesis-catch">{catch_fmt}</div>
</div>
{build_astro_cards(astro, {"month_pillar": astro["month_pillar"], "day_pillar": astro["day_pillar"]})}"""

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
            .replace("{{SIGNER_TITLE}}", "ビジネス鑑定士")
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
