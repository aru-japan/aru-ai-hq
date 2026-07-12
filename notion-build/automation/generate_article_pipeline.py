"""Phase B3.7: end-to-end AI generation pipeline using the real Claude/OpenAI Gateway.

Research (Notion) -> Article Draft (Claude API) -> saved to Articles
                                                  -> English Translation (Claude API) -> saved to Translation
                                                  -> 3 SNS drafts (Claude API) -> saved to SNS Queue

No new databases. Everything is saved with Status/AI Draft-level fields so a human
still reviews before anything is published (ARu Constitution Sec.9/13).
"""
import argparse
import os
import sys

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
REPO_ROOT = os.path.dirname(NOTION_BUILD_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from notion_api import load_env, notion_request, query_database, get_prop  # noqa: E402
import ai_gateway  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")


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


def generate_article(topic, research_summary):
    prompt = f"""あなたはARu（外国籍の方向け日本生活サポートメディア）のWriter Agentです。
ARu Constitutionの原則に従ってください：「何をすべきか」だけでなく「なぜそうするのか」という文化的・制度的背景を書く。法律系の内容は一般的情報として書き、断定的な個別助言をしない。最後に免責事項を1文入れる。

以下のリサーチ内容をもとに、テーマ「{topic}」について記事を書いてください。

リサーチ内容：
{research_summary}

出力形式（このまま2つのセクションで出力し、他の説明は付けないこと）：
TITLE: <記事タイトル>
BODY: <本文。600〜900文字程度。導入・背景・手順・注意点・相談先の流れで>
"""
    provider, text = ai_gateway.complete(prompt, max_tokens=1500)
    title, body = "", text
    for line in text.splitlines():
        if line.startswith("TITLE:"):
            title = line[len("TITLE:"):].strip()
    body_start = text.find("BODY:")
    if body_start != -1:
        body = text[body_start + len("BODY:"):].strip()
    return provider, title or f"{topic}について", body


def generate_translation(title, body):
    prompt = f"""以下の日本語記事を、自然な英語に翻訳してください。直訳ではなく意味を伝える翻訳にし、日本文化特有の概念（例：在留カード等）は英語話者にも分かるよう簡潔に補足してください。

出力形式：
TITLE: <英語タイトル>
BODY: <英語本文>

タイトル: {title}
本文:
{body}
"""
    provider, text = ai_gateway.complete(prompt, max_tokens=1500)
    en_title, en_body = "", text
    for line in text.splitlines():
        if line.startswith("TITLE:"):
            en_title = line[len("TITLE:"):].strip()
    body_start = text.find("BODY:")
    if body_start != -1:
        en_body = text[body_start + len("BODY:"):].strip()
    return provider, en_title, en_body


def generate_sns_caption(platform, title, body):
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keyword", default="在留")
    parser.add_argument("--resume-article-id", default=None,
                         help="Skip Research lookup + Article creation; continue from an already-saved Article (used to recover from a mid-pipeline failure without creating a duplicate Article)")
    args = parser.parse_args()

    env = load_env(ENV_PATH)
    token = env["NOTION_TOKEN"]
    articles_db = env["ARTICLES_DB_ID"]
    translation_db = env["TRANSLATION_DB_ID"]
    sns_db = env["SNS_QUEUE_DB_ID"]

    print(f"### Phase B3.7 Pipeline (keyword={args.keyword}) ###\n")

    if args.resume_article_id:
        print(f"[1-2/4] Resuming from existing Article {args.resume_article_id} (skipping Research lookup + Article creation)...")
        article_page = notion_request(token, "GET", f"/pages/{args.resume_article_id}")
        title = get_prop(article_page, "Title", "title")
        body = get_prop(article_page, "Body", "rich_text")
        print(f"  Title: {title}")
        print(f"  Body ({len(body)} chars): {body[:120]}...")
    else:
        print("[1/4] Finding source Research (Status=Converted)...")
        research = find_research(token, env["RESEARCH_DB_ID"], args.keyword)
        if not research:
            print("ERROR: no Converted Research record found matching the keyword.")
            sys.exit(1)
        topic = get_prop(research, "Topic", "title")
        summary = get_prop(research, "Summary", "rich_text")
        print(f"  Using Research: {topic}")

        print("[2/4] Generating Article via AI Gateway...")
        provider, title, body = generate_article(topic, summary)
        print(f"  provider={provider}")
        print(f"  Title: {title}")
        print(f"  Body ({len(body)} chars): {body[:120]}...")

        article_props = {
            "Title": {"title": [{"text": {"content": title}}]},
            "Body": {"rich_text": rich_text_chunks(body)},
            "Category": {"select": {"name": "法律・制度"}},
            "Status": {"select": {"name": "AI Draft"}},
            "Update Level": {"number": 2},
            "Audience": {"multi_select": [{"name": "在住外国人"}, {"name": "留学生"}, {"name": "技能実習生"}, {"name": "特定技能"}]},
            "Season": {"multi_select": [{"name": "通年"}]},
            "Urgency": {"select": {"name": "Medium"}},
            "Master Language": {"select": {"name": "ja"}},
            "Confidentiality": {"select": {"name": "Public"}},
            "Usage Scope": {"multi_select": [{"name": "Consumer App"}]},
            "AI Generated": {"checkbox": True},
            "Human Reviewed": {"checkbox": False},
            "Source Research": {"relation": [{"id": research["id"]}]},
        }
        article_page = notion_request(token, "POST", "/pages", {
            "parent": {"database_id": articles_db}, "properties": article_props
        })
        print(f"  SAVED Article: {article_page['id']}")

    print("\n[3/4] Generating English Translation via AI Gateway...")
    provider_t, en_title, en_body = generate_translation(title, body)
    print(f"  provider={provider_t}")
    print(f"  EN Title: {en_title}")

    translation_props = {
        "Translation Name": {"title": [{"text": {"content": f"{title} (EN)"}}]},
        "Parent Article": {"relation": [{"id": article_page["id"]}]},
        "Language": {"select": {"name": "en"}},
        "Translated Title": {"rich_text": rich_text_chunks(en_title)},
        "Translated Body": {"rich_text": rich_text_chunks(en_body)},
        "AI Translation Status": {"select": {"name": "Done"}},
        "Localization Status": {"select": {"name": "Translated"}},
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
    print(f"  SAVED Translation: {translation_page['id']}")

    print("\n[4/4] Generating 3 SNS Queue drafts via AI Gateway...")
    for platform in ["Instagram", "Threads", "X"]:
        provider_s, caption = generate_sns_caption(platform, title, body)
        sns_props = {
            "Title": {"title": [{"text": {"content": f"{title} - {platform}"}}]},
            "Platform": {"select": {"name": platform}},
            "Status": {"select": {"name": "Draft"}},
            "Caption": {"rich_text": [{"text": {"content": caption}}]},
            "Language": {"select": {"name": "ja"}},
            "Target Audience": {"multi_select": [{"name": "在住外国人"}]},
            "AI Generated": {"checkbox": True},
            "Human Reviewed": {"checkbox": False},
            "Related Article": {"relation": [{"id": article_page["id"]}]},
        }
        sns_page = notion_request(token, "POST", "/pages", {
            "parent": {"database_id": sns_db}, "properties": sns_props
        })
        print(f"  [{platform}] provider={provider_s} -> SAVED {sns_page['id']}")
        print(f"    {caption[:100]}...")

    print("\nDONE. Article/Translation/3x SNS Queue records created (all AI Draft / Not Published / Pending).")


if __name__ == "__main__":
    main()
