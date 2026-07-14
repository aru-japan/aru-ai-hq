"""Phase B3.7 (Article/Translation/SNS generation), refactored in Phase B3.11 (Day 2)
into three independently callable stages, each its own CLI subcommand:

    python3 generate_article_pipeline.py article     --keyword "..." --category "..."
    python3 generate_article_pipeline.py translation  --article-id "..."
    python3 generate_article_pipeline.py sns          --article-id "..."
    python3 generate_article_pipeline.py all          --keyword "..." --category "..."  (runs all three, as before)

All content is generated via the real Claude/OpenAI Gateway. No new databases.
Everything is saved at AI Draft / Pending / Not Published so a human still reviews
before anything is published (ARu Constitution Sec.9/13).
"""
import argparse
import os
import re
import sys

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
REPO_ROOT = os.path.dirname(NOTION_BUILD_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from notion_api import load_env, notion_request, query_database, get_prop  # noqa: E402
import ai_gateway  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")

LEVEL_1_CATEGORIES = {"イベント", "日本文化", "旅行情報", "生活情報", "ニュース", "トレンド"}
LEVEL_2_CATEGORIES = {"法律・制度"}


def compute_update_level(category):
    if category in LEVEL_2_CATEGORIES:
        return 2
    return 1


def rich_text_chunks(content, chunk_size=1990):
    """Notion limits each rich_text item to 2000 chars; split longer content into
    multiple text objects so the API call doesn't fail on long AI-generated bodies."""
    chunks = [content[i:i + chunk_size] for i in range(0, len(content), chunk_size)] or [""]
    return [{"text": {"content": c}} for c in chunks]


def find_research(token, research_db_id, keyword):
    results = query_database(token, research_db_id, filter_obj={
        "and": [
            {"property": "Topic", "title": {"contains": keyword}},
            {"property": "Status", "select": {"equals": "Converted"}},
        ]
    })
    return results[0] if results else None


ARU_ARTICLE_TEMPLATE_INSTRUCTIONS = """記事は必ず以下のARu公式テンプレート（9セクション）の構成で書いてください。各セクションの見出しはそのまま太字（**見出し**）で示し、9つすべてを含めてください。

1. **Question** — ユーザーが最初に知りたい質問（1文、疑問形）
2. **Basic Answer** — 短く明確な基本回答。これだけ読んでも要点が分かる、無料部分として単独で読める内容にする
3. **More Details** — 基本回答だけでは分からない背景・例外・具体例
4. **Why Does Japan Do This?** — 日本独自の文化・制度・暗黙のルール・背景理由
5. **Practical Steps and Cautions** — 実際の手順、必要なもの、よくある失敗、注意点
6. **Latest Information** — 法改正・制度変更等の最新情報があれば明記する。無ければ「最終確認日：{verified_date}」と明記する
7. **ARu Tip** — 外国籍ユーザーの不安を減らす、短く実践的なアドバイス（1〜2文）
8. **Related Questions** — 関連するテーマを2〜3件、箇条書きで提案する
9. **Mentor Support** — それでも分からない場合や日本語をもっと学びたい場合に、メンター相談へ自然につなげる案内"""


def generate_article_text(topic, research_summary, update_level, verified_date):
    template = ARU_ARTICLE_TEMPLATE_INSTRUCTIONS.format(verified_date=verified_date)
    prompt = f"""あなたはARu（外国籍の方向け日本生活サポートメディア）のWriter Agentです。
ARu Constitutionの原則に従ってください：「何をすべきか」だけでなく「なぜそうするのか」という文化的・制度的背景を書く。Update Level={update_level}のコンテンツです（2以上は法律・制度系として一般的情報にとどめ断定的な個別助言をせず免責事項を1文入れる。1は文化・イベント・生活情報として温かく書く）。

{template}

以下のリサーチ内容をもとに、テーマ「{topic}」について記事を書いてください。

リサーチ内容：
{research_summary}

出力形式（このまま2つのセクションで出力し、他の説明は付けないこと）：
TITLE: <記事タイトル>
BODY: <本文。9セクションすべてを含む、1200〜1800文字程度>
"""
    provider, text = ai_gateway.complete(prompt, max_tokens=2400)
    title, body = "", text
    for line in text.splitlines():
        if line.startswith("TITLE:"):
            title = line[len("TITLE:"):].strip()
    body_start = text.find("BODY:")
    if body_start != -1:
        body = text[body_start + len("BODY:"):].strip()
    return provider, title or f"{topic}について", body


def generate_translation_text(title, body, language_name="English"):
    prompt = f"""以下の日本語記事を、自然な{language_name}に翻訳してください。直訳ではなく意味を伝える翻訳にしてください。

日本独自の文化・制度・暗黙のルールを表す語句（固有名詞、慣習、行政手続き名など）があれば、{language_name}話者にも分かるよう本文中に簡潔な補足を加えてください。

出力形式（このまま出力し、他の説明は付けないこと）：
TITLE: <翻訳タイトル>
BODY: <翻訳本文>
CULTURAL_ADAPTATION: <Done または Needs Review — 文化的補足を十分に行えたらDone、自信が持てない・判断が難しい場合はNeeds Review>
CULTURAL_NOTE: <文化的補足をどう行ったか、またはNeeds Reviewの場合はその理由を1文で>

タイトル: {title}
本文:
{body}
"""
    provider, text = ai_gateway.complete(prompt, max_tokens=1500)
    en_title, en_body, cultural_adaptation, cultural_note = "", text, "Needs Review", ""

    for line in text.splitlines():
        if line.startswith("TITLE:"):
            en_title = line[len("TITLE:"):].strip()
        if line.startswith("CULTURAL_ADAPTATION:"):
            cultural_adaptation = line[len("CULTURAL_ADAPTATION:"):].strip()
        if line.startswith("CULTURAL_NOTE:"):
            cultural_note = line[len("CULTURAL_NOTE:"):].strip()

    body_match = re.search(r"BODY:\s*(.+?)(?:\nCULTURAL_ADAPTATION:|\Z)", text, re.DOTALL)
    if body_match:
        en_body = body_match.group(1).strip()

    return provider, en_title, en_body, cultural_adaptation, cultural_note


def generate_sns_caption_text(platform, title, body):
    tone = {
        "Instagram": "文化・体験を視覚的に伝える、温かいトーン。絵文字を少し使ってよい",
        "Threads": "会話的で、コミュニティとの対話を誘うトーン。問いかけを1つ入れる",
        "X": "速報性・簡潔さを重視。140文字以内",
    }[platform]
    prompt = f"""ARuのSocial Manager Agentとして、{platform}向けの投稿文を作成してください。
トーン：{tone}
記事タイトル：{title}
記事本文の要旨：{body[:300]}

出力は投稿文のみ（説明や前置きは不要）。ハッシュタグを2〜3個含めてよい。
"""
    provider, text = ai_gateway.complete(prompt, max_tokens=300)
    return provider, text.strip()


# --- independently runnable stages ---

def run_article(env, keyword, category):
    token = env["NOTION_TOKEN"]
    articles_db = env["ARTICLES_DB_ID"]
    update_level = compute_update_level(category)

    print(f"[Article] Finding source Research (keyword={keyword}, Status=Converted)...")
    research = find_research(token, env["RESEARCH_DB_ID"], keyword)
    if not research:
        print("ERROR: no Converted Research record found matching the keyword.")
        sys.exit(1)
    topic = get_prop(research, "Topic", "title")
    summary = get_prop(research, "Summary", "rich_text")
    print(f"  Using Research: {topic}")

    verified_date = __import__("datetime").date.today().isoformat()
    print(f"[Article] Generating via AI Gateway (Category={category}, Update Level={update_level})...")
    provider, title, body = generate_article_text(topic, summary, update_level, verified_date)
    print(f"  provider={provider}")
    print(f"  Title: {title}")
    print(f"  Body ({len(body)} chars): {body[:120]}...")

    article_props = {
        "Title": {"title": [{"text": {"content": title}}]},
        "Body": {"rich_text": rich_text_chunks(body)},
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
        "Source Research": {"relation": [{"id": research["id"]}]},
        "Verification Status": {"select": {"name": "Verified"}},
        "Last Verified Date": {"date": {"start": verified_date}},
    }
    article_page = notion_request(token, "POST", "/pages", {
        "parent": {"database_id": articles_db}, "properties": article_props
    })
    print(f"  SAVED Article: {article_page['id']}")
    return article_page["id"]


def run_translation(env, article_id, language="en", language_name="English"):
    token = env["NOTION_TOKEN"]
    translation_db = env["TRANSLATION_DB_ID"]

    article_page = notion_request(token, "GET", f"/pages/{article_id}")
    title = get_prop(article_page, "Title", "title")
    body = get_prop(article_page, "Body", "rich_text")

    print(f"[Translation] Generating {language_name} translation via AI Gateway...")
    provider, en_title, en_body, cultural_adaptation, cultural_note = generate_translation_text(title, body, language_name)
    print(f"  provider={provider}")
    print(f"  Title: {en_title}")
    print(f"  Cultural adaptation self-assessment: {cultural_adaptation} ({cultural_note[:100]})")

    localization_status = "Culturally Adapted" if cultural_adaptation.strip().lower().startswith("done") else "Needs Cultural Review"

    translation_props = {
        "Translation Name": {"title": [{"text": {"content": f"{title} ({language.upper()})"}}]},
        "Parent Article": {"relation": [{"id": article_id}]},
        "Language": {"select": {"name": language}},
        "Translated Title": {"rich_text": rich_text_chunks(en_title)},
        "Translated Body": {"rich_text": rich_text_chunks(en_body)},
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
        "parent": {"database_id": translation_db}, "properties": translation_props
    })
    print(f"  SAVED Translation: {translation_page['id']} (Localization Status={localization_status})")
    return translation_page["id"]


def run_sns(env, article_id, platforms=("Instagram", "Threads", "X")):
    token = env["NOTION_TOKEN"]
    sns_db = env["SNS_QUEUE_DB_ID"]

    article_page = notion_request(token, "GET", f"/pages/{article_id}")
    title = get_prop(article_page, "Title", "title")
    body = get_prop(article_page, "Body", "rich_text")

    created = []
    for platform in platforms:
        print(f"[SNS] Generating {platform} draft via AI Gateway...")
        provider, caption = generate_sns_caption_text(platform, title, body)
        sns_props = {
            "Title": {"title": [{"text": {"content": f"{title} - {platform}"}}]},
            "Platform": {"select": {"name": platform}},
            "Status": {"select": {"name": "Draft"}},
            "Caption": {"rich_text": rich_text_chunks(caption)},
            "Language": {"select": {"name": "ja"}},
            "Target Audience": {"multi_select": [{"name": "在住外国人"}]},
            "AI Generated": {"checkbox": True},
            "Human Reviewed": {"checkbox": False},
            "Related Article": {"relation": [{"id": article_id}]},
        }
        sns_page = notion_request(token, "POST", "/pages", {
            "parent": {"database_id": sns_db}, "properties": sns_props
        })
        print(f"  [{platform}] provider={provider} -> SAVED {sns_page['id']}")
        created.append(sns_page["id"])
    return created


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="stage", required=True)

    p_article = sub.add_parser("article", help="Generate + save an Article from a Converted Research record")
    p_article.add_argument("--keyword", required=True)
    p_article.add_argument("--category", default="法律・制度")

    p_translation = sub.add_parser("translation", help="Generate + save a Translation for an existing Article")
    p_translation.add_argument("--article-id", required=True)
    p_translation.add_argument("--language", default="en")
    p_translation.add_argument("--language-name", default="English")

    p_sns = sub.add_parser("sns", help="Generate + save SNS Queue drafts for an existing Article")
    p_sns.add_argument("--article-id", required=True)
    p_sns.add_argument("--platforms", nargs="+", default=["Instagram", "Threads", "X"])

    p_all = sub.add_parser("all", help="Run article -> translation -> sns in sequence (legacy combined behavior)")
    p_all.add_argument("--keyword", required=True)
    p_all.add_argument("--category", default="法律・制度")

    args = parser.parse_args()
    env = load_env(ENV_PATH)

    if args.stage == "article":
        run_article(env, args.keyword, args.category)
    elif args.stage == "translation":
        run_translation(env, args.article_id, args.language, args.language_name)
    elif args.stage == "sns":
        run_sns(env, args.article_id, tuple(args.platforms))
    elif args.stage == "all":
        article_id = run_article(env, args.keyword, args.category)
        run_translation(env, article_id)
        run_sns(env, article_id)
        print(f"\nDONE. Article {article_id} + Translation + 3x SNS Queue created.")


if __name__ == "__main__":
    main()
