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
