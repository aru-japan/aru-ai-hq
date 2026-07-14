"""Life Topic taxonomy for the Coverage Analyzer.

This is deliberately a *separate* classification dimension from Articles.Category.
Category (the existing 7-value select: イベント/日本文化/旅行情報/生活情報/ニュース/
トレンド/法律・制度) drives Update Level gating throughout the pipeline and must not
change. Life Topics is a finer-grained, multi-select view of "which life domain does
this article actually help with," used only for coverage/gap analysis -- an article
can (and often should) carry more than one.

The taxonomy is meant to approximate the real information needs of a foreign
resident/visitor in Japan (ARu's actual audience), not just mirror however articles
happen to be filed today.
"""
import ai_gateway

LIFE_TOPICS = [
    "住居・引っ越し",
    "医療・健康",
    "税金",
    "年金・社会保険",
    "教育",
    "子育て",
    "介護",
    "妊娠・出産",
    "高齢者支援",
    "障がい者支援",
    "防災・緊急対応",
    "就労・キャリア",
    "在留資格・ビザ",
    "交通",
    "通信・インフラ",
    "金融・銀行",
    "買い物・消費",
    "文化・マナー",
    "イベント・季節行事",
    "旅行・観光",
    "ニュース・トレンド",
    "行政手続き・相談窓口",
]

# Real-life impact tier per topic, independent of how many articles currently exist.
# Used by the Editorial Planner to weight priority: a Critical topic with only a few
# articles should outrank a Low topic with zero, because the cost of the reader not
# finding an answer is much higher (health, disaster, legal status, money to live on).
LIFE_TOPIC_IMPACT = {
    "医療・健康": "Critical",
    "妊娠・出産": "Critical",
    "防災・緊急対応": "Critical",
    "在留資格・ビザ": "Critical",
    "介護": "High",
    "高齢者支援": "High",
    "障がい者支援": "High",
    "税金": "High",
    "年金・社会保険": "High",
    "住居・引っ越し": "High",
    "子育て": "High",
    "就労・キャリア": "High",
    "行政手続き・相談窓口": "Medium",
    "金融・銀行": "Medium",
    "交通": "Medium",
    "通信・インフラ": "Medium",
    "教育": "Medium",
    "買い物・消費": "Low",
    "文化・マナー": "Low",
    "イベント・季節行事": "Low",
    "旅行・観光": "Low",
    "ニュース・トレンド": "Low",
}

# Sensible default among the existing 7-value Articles.Category (which drives Update
# Level gating) for each Life Topic. Used by the Editorial Planner as a fallback when
# the AI's suggested category is missing or not one of the 7 valid values.
DEFAULT_CATEGORY_FOR_TOPIC = {
    "住居・引っ越し": "生活情報",
    "医療・健康": "生活情報",
    "税金": "法律・制度",
    "年金・社会保険": "法律・制度",
    "教育": "生活情報",
    "子育て": "生活情報",
    "介護": "法律・制度",
    "妊娠・出産": "生活情報",
    "高齢者支援": "法律・制度",
    "障がい者支援": "法律・制度",
    "防災・緊急対応": "生活情報",
    "就労・キャリア": "法律・制度",
    "在留資格・ビザ": "法律・制度",
    "交通": "生活情報",
    "通信・インフラ": "生活情報",
    "金融・銀行": "生活情報",
    "買い物・消費": "生活情報",
    "文化・マナー": "日本文化",
    "イベント・季節行事": "イベント",
    "旅行・観光": "旅行情報",
    "ニュース・トレンド": "トレンド",
    "行政手続き・相談窓口": "法律・制度",
}


def classify_life_topics(title, body, max_topics=3):
    """Ask AI to pick 1-max_topics topics from LIFE_TOPICS that best describe what
    life need(s) this article actually serves. Returns a validated list (unknown/
    hallucinated topic names are dropped rather than saved to Notion)."""
    topic_list = "\n".join(f"- {t}" for t in LIFE_TOPICS)
    prompt = f"""以下は、外国籍の方向け日本生活サポートメディアARuの記事です。
この記事が実際にどの生活トピックの助けになるかを、以下のリストから最大{max_topics}件選んでください。

選択肢（このリストの表記そのままで、1行に1つ、他の説明なしで出力すること）：
{topic_list}

タイトル：{title}
本文：{body[:800]}

出力形式（このまま、他の説明は付けないこと）：
TOPIC: <選択肢のいずれか>
TOPIC: <選択肢のいずれか>
"""
    _, text = ai_gateway.complete(prompt, max_tokens=150)
    valid = set(LIFE_TOPICS)
    picked = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("TOPIC:"):
            name = line[len("TOPIC:"):].strip()
            if name in valid and name not in picked:
                picked.append(name)
    return picked[:max_topics]
