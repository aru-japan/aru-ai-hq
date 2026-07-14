"""Bulk-generate Articles (with Translation + 3x SNS drafts, all reviewed) and
register them directly into Notion via the API -- the fastest reliable path, since
Notion's native CSV import cannot set Select/Relation/Formula properties correctly
for a schema this rich.

Reusable across batches: swap the TOPICS list for each day's run (renamed from
bulk_generate_20_articles.py -- Phase B3.12 -- to reflect that it's not tied to a
fixed count).

For each topic:
  Research (Converted) -> Article (AI Draft, ARu 9-section template) -> Article Review
                        -> Translation (EN)                          -> Translation Review
                        -> SNS x3 (IG/Threads/X)                     -> SNS Review x3

All content is generated via the real Claude API (same prompts/quality bar as the
rest of ARu Studio -- reviewer_agent.py / translation_quality_reviewer.py /
sns_quality_reviewer.py's own scoring logic is reused, not reimplemented). Article
bodies follow the ARu 9-section template (Question / Basic Answer / More Details /
Why Does Japan Do This? / Practical Steps and Cautions / Latest Information / ARu
Tip / Related Questions / Mentor Support) via generate_article_pipeline.py's shared
ARU_ARTICLE_TEMPLATE_INSTRUCTIONS, and every Article gets Verification Status=Verified
+ Last Verified Date=today regardless of Update Level.

Everything is saved at AI Draft / Pending / Not Published; nothing is auto-published.
This is a long-running script; run it in the background for batches larger than a
handful of topics.
"""
import os
import sys
import time
import traceback
import datetime

AUTOMATION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "automation")
NOTION_BUILD_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(NOTION_BUILD_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)
sys.path.insert(0, AUTOMATION_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from notion_api import load_env, notion_request, get_prop  # noqa: E402
import ai_gateway  # noqa: E402
import generate_article_pipeline as gap  # noqa: E402
import reviewer_agent as ra  # noqa: E402
import translation_quality_reviewer as tqr  # noqa: E402
import sns_quality_reviewer as sqr  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")

# --- Batch: 2026-07-14 (15 topics, ARu app content, distinct from the 2026-07-13 batch of 20) ---
TOPICS = [
    {"topic": "日本での自転車の乗り方とルールは？", "category": "生活情報",
     "summary": "日本では自転車は原則車道の左側通行（例外的に歩道通行可の場合もある）。二人乗り・並走・傘さし運転・スマホ操作をしながらの運転は禁止。夜間はライト点灯必須。防犯登録が義務付けられている。"},
    {"topic": "花火大会を楽しむには何を準備すればいい？", "category": "イベント",
     "summary": "夏の花火大会は場所取り・浴衣・屋台グルメが定番。混雑や打ち上げ場所への交通規制があるため、早めの到着や公共交通機関の利用が推奨される。有料観覧席がある大会も増えている。"},
    {"topic": "日本のお辞儀にはどんな意味とマナーがある？", "category": "日本文化",
     "summary": "お辞儀には会釈（15度）・敬礼（30度）・最敬礼（45度）等、角度によって敬意の度合いが異なる。握手文化とは違い、身体的接触を避けつつ敬意を示す方法として定着している。"},
    {"topic": "日本でスキー・スノーボードを楽しむには？", "category": "旅行情報",
     "summary": "北海道・長野・新潟等が有名なスキーエリア。リフト券・レンタル用品・スキーウェアの準備が必要。初心者向けゲレンデやスクールも充実しており、外国人観光客にも人気が高い。"},
    {"topic": "日本のラジオ体操はなぜ習慣になっているのか？", "category": "日本文化",
     "summary": "ラジオ体操は1928年に始まった国民的な体操。夏休みの朝に子供が公園で参加する光景や、企業の始業前体操として今も続く。健康増進と地域コミュニティの結びつきという側面がある。"},
    {"topic": "コインランドリーの使い方を知りたい", "category": "生活情報",
     "summary": "日本のコインランドリーは大型洗濯機・乾燥機を備え、布団や大量の衣類を洗うのに便利。洗剤は備え付けまたは自販機で購入できる場合が多い。硬貨またはICカード決済に対応。"},
    {"topic": "お中元・お歳暮とは何か？", "category": "日本文化",
     "summary": "お中元（7月頃）・お歳暮（12月頃）は、日頃お世話になっている人へ贈り物をする習慣。ビジネス関係や親戚間で行われることが多く、百貨店等で専用のギフトセットが販売される。"},
    {"topic": "忘年会・新年会に誘われたらどうすればいい？", "category": "日本文化",
     "summary": "忘年会（年末）・新年会（年始）は職場や友人グループで行われる会食。参加は基本的に任意だが、日本の職場文化では人間関係構築の場として重視される傾向がある。乾杯の作法等の基本マナーがある。"},
    {"topic": "図書館の使い方と会員登録方法は？", "category": "生活情報",
     "summary": "日本の公共図書館は住民登録があれば誰でも無料で利用でき、外国籍住民も利用可能。本人確認書類（在留カード等）と住所確認書類で利用者カードを作成できる。多言語書籍を置く図書館もある。"},
    {"topic": "クリスマス・ハロウィンは日本でどう祝われている？", "category": "トレンド",
     "summary": "日本のクリスマスは宗教行事というより恋人・家族と過ごすイベント化した文化。ハロウィンは近年、渋谷等での仮装イベントとして若者文化に定着した、比較的新しい輸入行事。"},
    {"topic": "日本で運転免許を取得・切り替えするには？", "category": "法律・制度",
     "summary": "外国の免許を持つ場合、国により「切り替え（外国免許切替）」または学科・実技試験からの新規取得が必要。国際運転免許証は発給国によって有効期間や条件が異なる。運転免許センターでの手続きが基本。"},
    {"topic": "ふるさと納税とは何か、外国籍でも利用できる？", "category": "法律・制度",
     "summary": "ふるさと納税は、任意の自治体に寄付し返礼品を受け取りつつ、翌年の税金が控除される制度。日本に住民登録し納税義務がある人であれば、国籍を問わず利用可能。確定申告またはワンストップ特例で手続きする。"},
    {"topic": "年末調整と確定申告、自分はどちらが必要？", "category": "法律・制度",
     "summary": "会社員で1つの勤務先のみの場合は通常、年末調整で完結する。副業収入がある、年の途中で退職した、医療費控除を受けたい等の場合は確定申告が必要になる。"},
    {"topic": "携帯電話（スマートフォン）を契約するには？", "category": "生活情報",
     "summary": "携帯電話契約には在留カード・銀行口座（または クレジットカード）・住所確認書類が必要な場合が多い。大手キャリアと格安SIM（MVNO）で審査基準や必要書類が異なることがある。"},
    {"topic": "転職・退職時に必要な行政手続きは？", "category": "法律・制度",
     "summary": "退職時は健康保険・年金の切り替え手続きが必要。就労系の在留資格の場合、転職後は「所属機関に関する届出」を14日以内に出入国在留管理庁へ提出する必要がある。"},
]


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def process_topic(env, index, total, item):
    token = env["NOTION_TOKEN"]
    research_db = env["RESEARCH_DB_ID"]

    category = item["category"]
    topic = item["topic"]
    update_level = gap.compute_update_level(category)
    verified_date = datetime.date.today().isoformat()

    log(f"=== [{index}/{total}] {topic} (Category={category}, Update Level={update_level}) ===")

    # 1. Research
    research_props = {
        "Topic": {"title": [{"text": {"content": topic}}]},
        "Category": {"select": {"name": category}},
        "Summary": {"rich_text": [{"text": {"content": item["summary"]}}]},
        "Evidence Level": {"select": {"name": "Verified"}},
        "Status": {"select": {"name": "Converted"}},
        "Priority": {"select": {"name": "Medium"}},
        "Discovery Method": {"select": {"name": "Manual"}},
        "Urgency": {"select": {"name": "Medium"}},
        "AI Generated": {"checkbox": False},
        "Human Reviewed": {"checkbox": True},
    }
    research_page = notion_request(token, "POST", "/pages", {
        "parent": {"database_id": research_db}, "properties": research_props
    })
    log(f"  Research created: {research_page['id']}")

    # 2. Article (ARu 9-section template)
    provider, title, body = gap.generate_article_text(topic, item["summary"], update_level, verified_date)
    article_props = {
        "Title": {"title": [{"text": {"content": title}}]},
        "Body": {"rich_text": gap.rich_text_chunks(body)},
        "Category": {"select": {"name": category}},
        "Status": {"select": {"name": "AI Draft"}},
        "Update Level": {"number": update_level},
        "Audience": {"multi_select": [{"name": "観光客"}, {"name": "在住外国人"}]},
        "Season": {"multi_select": [{"name": "通年"}]},
        "Urgency": {"select": {"name": "Medium"}},
        "Master Language": {"select": {"name": "ja"}},
        "Confidentiality": {"select": {"name": "Public"}},
        "Usage Scope": {"multi_select": [{"name": "Consumer App"}]},
        "AI Generated": {"checkbox": True},
        "Human Reviewed": {"checkbox": False},
        "Source Research": {"relation": [{"id": research_page["id"]}]},
        "Verification Status": {"select": {"name": "Verified"}},
        "Last Verified Date": {"date": {"start": verified_date}},
    }
    article_page = notion_request(token, "POST", "/pages", {
        "parent": {"database_id": env["ARTICLES_DB_ID"]}, "properties": article_props
    })
    log(f"  Article created: {article_page['id']} ({title[:40]}...)")

    # 3. Article Review
    a_provider, a_scores, a_overall, a_result, a_suggestions = ra.review_article(article_page)
    notion_request(token, "PATCH", f"/pages/{article_page['id']}", {
        "properties": {
            "Review Accuracy Score": {"number": a_scores["ACCURACY"]},
            "Review Evidence Score": {"number": a_scores["EVIDENCE"]},
            "Review Readability Score": {"number": a_scores["READABILITY"]},
            "Review Risk Score": {"number": a_scores["RISK"]},
            "Review Localization Score": {"number": a_scores["LOCALIZATION"]},
            "Review Result": {"select": {"name": a_result}},
            "Review Suggestions": {"rich_text": gap.rich_text_chunks(a_suggestions)},
            "Review Date": {"date": {"start": verified_date}},
        }
    })
    log(f"  Article Review: Overall={a_overall} Result={a_result}")

    # 4. Translation
    t_provider, en_title, en_body, cultural_adaptation, cultural_note = gap.generate_translation_text(title, body, "English")
    localization_status = "Culturally Adapted" if cultural_adaptation.strip().lower().startswith("done") else "Needs Cultural Review"
    translation_props = {
        "Translation Name": {"title": [{"text": {"content": f"{title} (EN)"}}]},
        "Parent Article": {"relation": [{"id": article_page["id"]}]},
        "Language": {"select": {"name": "en"}},
        "Translated Title": {"rich_text": gap.rich_text_chunks(en_title)},
        "Translated Body": {"rich_text": gap.rich_text_chunks(en_body)},
        "AI Translation Status": {"select": {"name": "Done"}},
        "Localization Status": {"select": {"name": localization_status}},
        "Human Review Status": {"select": {"name": "Pending"}},
        "Publish Approval": {"select": {"name": "Pending"}},
        "Publish Status": {"select": {"name": "Not Published"}},
        "AI Generated": {"checkbox": True},
        "Human Reviewed": {"checkbox": False},
        "Confidentiality": {"select": {"name": "Public"}},
    }
    translation_page = notion_request(token, "POST", "/pages", {
        "parent": {"database_id": env["TRANSLATION_DB_ID"]}, "properties": translation_props
    })
    log(f"  Translation created: {translation_page['id']} (Localization={localization_status})")

    # 5. Translation Review
    translation_page = notion_request(token, "GET", f"/pages/{translation_page['id']}")
    tr_prompt = tqr.build_prompt(title, body, en_title, en_body, "English")
    tr_provider, tr_text = ai_gateway.complete(tr_prompt, max_tokens=800)
    tr_scores, tr_suggestions = tqr.parse_review(tr_text)
    tr_overall, tr_result = tqr.decide_result(tr_scores)

    update_props = {
        "Quality Meaning Accuracy Score": {"number": tr_scores["MEANING_ACCURACY"]},
        "Quality Naturalness Score": {"number": tr_scores["NATURALNESS"]},
        "Quality Cultural Adaptation Score": {"number": tr_scores["CULTURAL_ADAPTATION"]},
        "Quality Terminology Score": {"number": tr_scores["TERMINOLOGY"]},
        "Quality Hallucination Risk Score": {"number": tr_scores["HALLUCINATION_RISK"]},
        "Quality Result": {"select": {"name": tr_result}},
        "Quality Suggestions": {"rich_text": gap.rich_text_chunks(tr_suggestions)},
        "Quality Review Date": {"date": {"start": verified_date}},
    }
    # Gate: Update Level 2/3 ALWAYS stays Pending regardless of score (ARu Constitution Sec.9/13)
    if tr_result != "Pass":
        update_props["Publish Approval"] = {"select": {"name": "Pending"}}
    elif update_level in (2, 3):
        update_props["Publish Approval"] = {"select": {"name": "Pending"}}
    elif localization_status != "Culturally Adapted":
        update_props["Publish Approval"] = {"select": {"name": "Pending"}}
    else:
        update_props["Publish Approval"] = {"select": {"name": "Not Required"}}
    notion_request(token, "PATCH", f"/pages/{translation_page['id']}", {"properties": update_props})
    log(f"  Translation Review: Overall={tr_overall} Result={tr_result} PublishApproval={update_props['Publish Approval']['select']['name']}")

    # 6. SNS x3 + review
    for platform in ["Instagram", "Threads", "X"]:
        s_provider, caption = gap.generate_sns_caption_text(platform, title, body)
        sns_props = {
            "Title": {"title": [{"text": {"content": f"{title} - {platform}"}}]},
            "Platform": {"select": {"name": platform}},
            "Status": {"select": {"name": "Draft"}},
            "Caption": {"rich_text": gap.rich_text_chunks(caption)},
            "Language": {"select": {"name": "ja"}},
            "Target Audience": {"multi_select": [{"name": "在住外国人"}]},
            "AI Generated": {"checkbox": True},
            "Human Reviewed": {"checkbox": False},
            "Related Article": {"relation": [{"id": article_page["id"]}]},
        }
        sns_page = notion_request(token, "POST", "/pages", {
            "parent": {"database_id": env["SNS_QUEUE_DB_ID"]}, "properties": sns_props
        })
        sns_page = notion_request(token, "GET", f"/pages/{sns_page['id']}")
        result = sqr.review_one(token, sns_page)
        log(f"  SNS [{platform}]: created {sns_page['id']}, Review Overall={result['overall'] if result else 'N/A'} Result={result['result'] if result else 'N/A'}")

    return {
        "topic": topic, "update_level": update_level,
        "article_id": article_page["id"], "article_result": a_result,
        "translation_id": translation_page["id"], "translation_result": tr_result,
        "publish_approval": update_props["Publish Approval"]["select"]["name"],
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N topics (for testing)")
    args = parser.parse_args()

    topics = TOPICS[:args.limit] if args.limit else TOPICS
    total = len(topics)

    env = load_env(ENV_PATH)
    results = []
    failures = []

    for i, item in enumerate(topics, start=1):
        try:
            r = process_topic(env, i, total, item)
            results.append(r)
        except Exception as e:
            log(f"  !!! FAILED: {item['topic']}: {e}")
            traceback.print_exc()
            failures.append({"topic": item["topic"], "error": str(e)})

    log("\n" + "=" * 70)
    log(f"DONE. {len(results)}/{total} articles fully generated, reviewed, and saved.")
    if failures:
        log(f"FAILURES ({len(failures)}):")
        for f in failures:
            log(f"  - {f['topic']}: {f['error']}")

    log("\nSummary:")
    for r in results:
        log(f"  - {r['topic']}: Article={r['article_result']}, Translation={r['translation_result']}, PublishApproval={r['publish_approval']}")


if __name__ == "__main__":
    main()
