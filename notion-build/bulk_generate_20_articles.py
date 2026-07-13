"""Bulk-generate 20 Articles (with Translation + 3x SNS drafts, all reviewed) and
register them directly into Notion via the API -- the fastest reliable path, since
Notion's native CSV import cannot set Select/Relation/Formula properties correctly
for a schema this rich.

For each of the 20 topics:
  Research (Converted) -> Article (AI Draft) -> Article Review
                        -> Translation (EN)   -> Translation Review
                        -> SNS x3 (IG/Threads/X) -> SNS Review x3

All content is generated via the real Claude API (same prompts/quality bar as the
rest of ARu Studio -- reviewer_agent.py / translation_quality_reviewer.py /
sns_quality_reviewer.py's own scoring logic is reused, not reimplemented).

Everything is saved at AI Draft / Pending / Not Published; nothing is auto-published.
This is a long-running script (~20-30 min for 20 topics); run it in the background.
"""
import os
import sys
import time
import traceback

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

TOPICS = [
    {"topic": "日本のゴミ分別ルールを理解する", "category": "生活情報",
     "summary": "日本の多くの自治体では、可燃ごみ・不燃ごみ・資源ごみ・粗大ごみ等に分別する必要があり、収集日や出し方が地域ごとに細かく決まっている。違反すると回収されないことがある。分別は環境保護とリサイクル効率のための制度。"},
    {"topic": "温泉の入り方とマナー", "category": "日本文化",
     "summary": "日本の温泉では、湯船に入る前に体を洗い流す「かけ湯」が基本マナー。タオルを湯船に入れない、大声で騒がない等の暗黙のルールがある。刺青がある場合は施設によって入浴を断られることがある。"},
    {"topic": "お花見（桜の季節）の楽しみ方", "category": "日本文化",
     "summary": "3月末〜4月上旬、桜の開花に合わせて公園等で花見をする習慣がある。場所取りのマナー、ゴミの持ち帰り、夜桜のライトアップ等が特徴。桜前線という開花予想も毎年話題になる。"},
    {"topic": "コンビニエンスストアの活用術", "category": "生活情報",
     "summary": "日本のコンビニは24時間営業が多く、公共料金の支払い、宅配便の発送・受取、ATM、コピー・チケット発券端末（マルチコピー機）など、生活インフラとして機能している。"},
    {"topic": "電車・バスの乗り方とマナー", "category": "生活情報",
     "summary": "日本の公共交通機関は時間に正確で、優先席・車内での通話禁止・電源オフ推奨エリア等のマナーがある。ICカード（Suica等）を使うと乗り換えがスムーズ。ラッシュ時間帯の混雑にも注意が必要。"},
    {"topic": "夏祭りの楽しみ方（浴衣・屋台・盆踊り）", "category": "イベント",
     "summary": "日本各地で7〜8月に夏祭りが開催され、浴衣を着て屋台グルメを楽しんだり、盆踊りに参加したりする。花火大会と組み合わせて行われることも多い、夏の代表的な文化行事。"},
    {"topic": "和食レストランでの基本マナー", "category": "日本文化",
     "summary": "「いただきます」「ごちそうさま」という食事の挨拶、箸の使い方のタブー（刺し箸・渡し箸等）、そばを音を立てて食べることが許容される文化など、和食独自のマナーがある。"},
    {"topic": "日本の四季と衣替えの習慣", "category": "日本文化",
     "summary": "日本には四季があり、6月と10月頃に「衣替え」として制服や衣服を季節に合わせて切り替える習慣が学校や企業にある。季節の変化を楽しむ文化的背景がある。"},
    {"topic": "100円ショップの活用法", "category": "生活情報",
     "summary": "日本の100円ショップ（ダイソー、セリア等）は、生活雑貨から文房具、食品まで幅広く安価に手に入る。新生活を始める外国籍の方にとって初期費用を抑える助けになる。"},
    {"topic": "神社と寺院、参拝の作法の違い", "category": "日本文化",
     "summary": "神社は神道、寺院は仏教の施設で、参拝の作法が異なる（神社は二礼二拍手一礼、寺院は合掌のみで拍手はしない等）。鳥居のくぐり方等の細かい違いもある。"},
    {"topic": "宅配便・郵便サービスの使い方", "category": "生活情報",
     "summary": "日本郵便やヤマト運輸・佐川急便等の宅配便は、コンビニでの発送・受取、再配達依頼（アプリや電話）、時間指定など便利な機能が充実している。"},
    {"topic": "紅葉狩りのおすすめスポットと楽しみ方", "category": "旅行情報",
     "summary": "11月頃、日本各地で紅葉が見頃を迎える。京都・日光等が有名だが、都市部の公園でも楽しめる。紅葉前線という見頃予想が春の桜前線同様に話題になる。"},
    {"topic": "スーパーマーケットでの買い物のコツ", "category": "生活情報",
     "summary": "日本のスーパーは夕方以降に惣菜が値引きされることが多く、マイバッグ持参が推奨される（レジ袋有料化）。地域や店舗によって品揃え・価格帯が異なる。"},
    {"topic": "お盆と正月、日本の伝統行事", "category": "日本文化",
     "summary": "お盆（8月中旬）は先祖の霊を迎える行事で帰省ラッシュが起きる。正月は初詣・おせち料理・年賀状等の習慣がある、日本で最も重要な伝統行事の1つ。"},
    {"topic": "日本で話題の最新カフェ・グルメトレンド", "category": "トレンド",
     "summary": "SNS映えするスイーツや、地域限定コラボカフェ等、日本では季節ごとに新しいグルメトレンドが話題になる。行列必至の人気店も多い。"},
    {"topic": "マイナンバーカードの申請方法", "category": "法律・制度",
     "summary": "マイナンバーカードは、行政手続きの本人確認等に使える身分証明書。市区町村窓口またはオンラインで申請でき、交付まで数週間かかる。在留カードとは別の制度。"},
    {"topic": "国民健康保険の加入手続き", "category": "法律・制度",
     "summary": "会社の健康保険に加入しない場合、市区町村で国民健康保険への加入が必要。医療費の自己負担割合が軽減される制度で、転入時の手続きが必要。"},
    {"topic": "銀行口座の開設方法", "category": "法律・制度",
     "summary": "日本で銀行口座を開設するには、在留カード・住所を証明する書類等が必要。給与受け取りや公共料金の引き落としに必須で、銀行により外国籍対応の充実度が異なる。"},
    {"topic": "住民票の取得方法", "category": "法律・制度",
     "summary": "住民票は居住地を証明する公的書類で、市区町村窓口で取得できる。中長期在留者は住民登録の対象であり、各種行政手続きで提出を求められることが多い。"},
    {"topic": "賃貸アパート契約の基本知識", "category": "法律・制度",
     "summary": "日本の賃貸契約には敷金・礼金・仲介手数料等の初期費用や、連帯保証人または保証会社の利用が一般的。外国籍向けの物件紹介サービスも増えている。"},
]


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def process_topic(env, index, item):
    token = env["NOTION_TOKEN"]
    research_db = env["RESEARCH_DB_ID"]

    category = item["category"]
    topic = item["topic"]
    update_level = gap.compute_update_level(category)

    log(f"=== [{index}/20] {topic} (Category={category}, Update Level={update_level}) ===")

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

    # 2. Article
    provider, title, body = gap.generate_article_text(topic, item["summary"], update_level)
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
            "Review Date": {"date": {"start": time.strftime("%Y-%m-%d")}},
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

    # 5. Translation Review (re-fetch to get a clean page object with all props)
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
        "Quality Review Date": {"date": {"start": time.strftime("%Y-%m-%d")}},
    }
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

    return {"topic": topic, "article_id": article_page["id"], "article_result": a_result,
            "translation_id": translation_page["id"], "translation_result": tr_result}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N topics (for testing)")
    args = parser.parse_args()

    topics = TOPICS[:args.limit] if args.limit else TOPICS

    env = load_env(ENV_PATH)
    results = []
    failures = []

    for i, item in enumerate(topics, start=1):
        try:
            r = process_topic(env, i, item)
            results.append(r)
        except Exception as e:
            log(f"  !!! FAILED: {item['topic']}: {e}")
            traceback.print_exc()
            failures.append({"topic": item["topic"], "error": str(e)})

    log("\n" + "=" * 70)
    log(f"DONE. {len(results)}/{len(topics)} articles fully generated, reviewed, and saved.")
    if failures:
        log(f"FAILURES ({len(failures)}):")
        for f in failures:
            log(f"  - {f['topic']}: {f['error']}")

    log("\nSummary:")
    for r in results:
        log(f"  - {r['topic']}: Article={r['article_result']}, Translation={r['translation_result']}")


if __name__ == "__main__":
    main()
