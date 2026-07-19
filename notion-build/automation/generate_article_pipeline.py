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
from life_topics import classify_life_topics  # noqa: E402
from duplicate_guard import check_before_generate, log_generated  # noqa: E402
from article_template import (  # noqa: E402
    get_template, template_for_category, template_for_content, parse_body_sections, validate_sections,
)
import render_article_layout  # noqa: E402
import article_brief  # noqa: E402

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


# Templates whose section count/depth needs materially more room than the
# standard 8-section article -- both the requested body length and the token
# budget scale up for these (2026-07-19 fix: the shared 2400-token / 1200-1800
# char defaults, sized for "standard", silently truncated Premium output mid
# sentence with its mandatory Sources section missing entirely).
_LONG_FORM_TEMPLATES = {"premium", "deep_guide"}


def generate_article_text(topic, research_summary, update_level, verified_date, template_instructions,
                           article_brief_text="", template_name="standard", max_tokens=None):
    brief_section = ""
    if article_brief_text:
        brief_section = (
            f"\nArticle Brief（Reader Need・採用するClaims・裏付けとなるEvidence。Rejected/Supersededは除外済み）：\n"
            f"{article_brief_text}\n{article_brief.STRICT_GENERATION_RULES}\n"
        )

    if template_name in _LONG_FORM_TEMPLATES:
        length_guidance = "テンプレートの全セクションを含み、Sourcesセクションを省略しないこと。2500〜3800文字程度"
        effective_max_tokens = max_tokens or 4400
    else:
        length_guidance = "8セクションすべてを含む、1200〜1800文字程度"
        effective_max_tokens = max_tokens or 2400

    prompt = f"""あなたはARu（外国籍の方向け日本生活サポートメディア）のWriter Agentです。
ARu Constitutionの原則に従ってください：「何をすべきか」だけでなく「なぜそうするのか」という文化的・制度的背景を書く。Update Level={update_level}のコンテンツです（2以上は法律・制度系として一般的情報にとどめ断定的な個別助言をせず免責事項を1文入れる。1は文化・イベント・生活情報として温かく書く）。

{template_instructions}

以下のリサーチ内容をもとに、テーマ「{topic}」について記事を書いてください（最終確認日：{verified_date}）。

リサーチ内容：
{research_summary}
{brief_section}
出力形式（このまま2つのセクションで出力し、他の説明は付けないこと）：
TITLE: <記事タイトル>
BODY: <本文。{length_guidance}>
"""
    provider, text = ai_gateway.complete(prompt, max_tokens=effective_max_tokens)
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

def run_article(env, keyword, category, content_type=None):
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

    existing = check_before_generate(token, env, topic, expect_research=True)
    if existing:
        print(f"  Status: Already Exists (stage={existing['stage']}, article_id={existing['article_id']}). Skipping generation.")
        return existing["article_id"]

    # Article Brief (docs/Article-Brief-Specification-v1.0.md): Editor's Notes is
    # read on a best-effort basis. Research records that predate the format (no
    # "## Reader Need" / "## Claims") fall through unchanged to the pre-v4.2
    # Summary-only prompt -- this must never block existing article generation.
    # Mechanical Check vs Final Brief Status are reported separately (2026-07-19
    # correction); this script never writes "Brief Status" back to Notion.
    editor_notes = get_prop(research, "Editor's Notes", "rich_text")
    parsed_brief = article_brief.parse_editor_notes(editor_notes)
    brief_prompt_text = article_brief.format_for_prompt(parsed_brief)
    if parsed_brief["reader_need"] or parsed_brief["claims"]:
        source_cache = {}

        def _source_exists(title, _cache=source_cache):
            if title not in _cache:
                _cache[title] = bool(query_database(token, env["SOURCE_LIBRARY_DB_ID"], filter_obj={
                    "property": "Source Name", "title": {"equals": title}
                }))
            return _cache[title]

        freshness = None
        law_rel = research["properties"].get("Related Law Updates", {}).get("relation", [])
        if not law_rel:
            freshness = True
        else:
            freshness = all(
                get_prop(notion_request(token, "GET", f"/pages/{ref['id']}"), "Update Status", "select") == "Confirmed"
                for ref in law_rel
            )

        result = article_brief.check_completion(parsed_brief, source_exists_fn=_source_exists, freshness_confirmed=freshness)
        print("[Article Brief] Mechanical Check（docs/Article-Brief-Specification-v1.0.md §6）:")
        for key, r in result["mechanical_check"].items():
            print(f"  [{r['status']}] {key}: {r['note']}")
        print(f"[Article Brief] Final Brief Status: {result['final_brief_status']} -- {result['final_brief_status_note']}")
    else:
        print("[Article Brief] Editor's NotesにArticle Brief形式が見つかりません。従来通りSummaryのみで生成します。")

    template_name = template_for_content(category, content_type)
    template_def = get_template(template_name)
    print(f"  Template: {template_name}" + (f" (Content Type={content_type})" if content_type else ""))

    verified_date = __import__("datetime").date.today().isoformat()
    print(f"[Article] Generating via AI Gateway (Category={category}, Update Level={update_level})...")
    provider, title, body = generate_article_text(
        topic, summary, update_level, verified_date, template_def["instructions"],
        article_brief_text=brief_prompt_text, template_name=template_name,
    )
    print(f"  provider={provider}")
    print(f"  Title: {title}")
    print(f"  Body ({len(body)} chars): {body[:120]}...")

    # 2026-07-19 fix: detect truncation (cut off mid-sentence by the token limit)
    # and retry once at double the token budget before saving anything. A body
    # that is still truncated after the retry is saved but forced to a failing
    # review state below rather than silently passed as complete.
    if article_brief.is_body_truncated(body):
        retry_tokens = (4400 if template_name in _LONG_FORM_TEMPLATES else 2400) * 2
        print(f"  WARNING: generated Body looks truncated (does not end on terminal punctuation/URL). "
              f"Retrying once with max_tokens={retry_tokens}...")
        provider, title, body = generate_article_text(
            topic, summary, update_level, verified_date, template_def["instructions"],
            article_brief_text=brief_prompt_text, template_name=template_name, max_tokens=retry_tokens,
        )
        print(f"  Retry Body ({len(body)} chars): {'still truncated' if article_brief.is_body_truncated(body) else 'looks complete'}")

    sections = parse_body_sections(body, template=template_name)
    missing, mandatory_missing = validate_sections(sections, template=template_name)
    if mandatory_missing:
        print(f"  WARNING: mandatory section(s) missing from generated Body: {mandatory_missing} "
              f"-- required by the {template_name} template. Article is still saved; "
              f"flag this for editorial review.")
    elif missing:
        print(f"  Note: optional section(s) not found: {missing}")

    life_topics = classify_life_topics(title, body)
    print(f"  Life Topics: {life_topics}")

    # Priority/Urgency are set by whoever created the Research (a human, or
    # Editorial Planner's star-derived values) -- the Article inherits them
    # rather than getting a hardcoded default, so Ready to Publish / Article
    # Review Waiting sort meaningfully instead of tying on "Medium" for everyone.
    research_priority = get_prop(research, "Priority", "select")
    research_urgency = get_prop(research, "Urgency", "select")
    print(f"  Inherited from Research: Priority={research_priority}, Urgency={research_urgency}")

    article_props = {
        "Title": {"title": [{"text": {"content": title}}]},
        "Body": {"rich_text": rich_text_chunks(body)},
        "Category": {"select": {"name": category}},
        "Status": {"select": {"name": "AI Draft"}},
        "Update Level": {"number": update_level},
        "Audience": {"multi_select": [{"name": "観光客"}, {"name": "在住外国人"}]},
        "Season": {"multi_select": [{"name": "通年"}]},
        "Master Language": {"select": {"name": "ja"}},
        "Confidentiality": {"select": {"name": "Public"}},
        "Usage Scope": {"multi_select": [{"name": "Consumer App"}]},
        "AI Generated": {"checkbox": True},
        "Human Reviewed": {"checkbox": False},
        "Source Research": {"relation": [{"id": research["id"]}]},
        "Verification Status": {"select": {"name": "Verified"}},
        "Last Verified Date": {"date": {"start": verified_date}},
    }
    article_props["Priority"] = {"select": {"name": research_priority}} if research_priority else {"select": {"name": "Medium"}}
    article_props["Urgency"] = {"select": {"name": research_urgency}} if research_urgency else {"select": {"name": "Medium"}}
    if life_topics:
        article_props["Life Topics"] = {"multi_select": [{"name": t} for t in life_topics]}
    if content_type:
        article_props["Content Type"] = {"select": {"name": content_type}}
    article_page = notion_request(token, "POST", "/pages", {
        "parent": {"database_id": articles_db}, "properties": article_props
    })
    print(f"  SAVED Article: {article_page['id']}")
    log_generated(topic, article_page["id"])

    try:
        result = render_article_layout.render_article(env, article_page["id"], title=title, body=body)
        print(f"  Rendered {result['block_count']} article page block(s) ({len(result['found'])}/{result['total_sections']} sections found)")
    except Exception as e:
        print(f"  WARNING: article page rendering failed (non-fatal, Article record itself is saved): {e}")

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
    p_article.add_argument("--content-type", default=None,
                            help="Articles.Content Type (e.g. Premium) -- selects the matching template "
                                 "via article_template.template_for_content() and is written to the Article record")

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
    p_all.add_argument("--content-type", default=None)

    args = parser.parse_args()
    env = load_env(ENV_PATH)

    if args.stage == "article":
        run_article(env, args.keyword, args.category, content_type=args.content_type)
    elif args.stage == "translation":
        run_translation(env, args.article_id, args.language, args.language_name)
    elif args.stage == "sns":
        run_sns(env, args.article_id, tuple(args.platforms))
    elif args.stage == "all":
        article_id = run_article(env, args.keyword, args.category, content_type=args.content_type)
        run_translation(env, article_id)
        run_sns(env, article_id)
        print(f"\nDONE. Article {article_id} + Translation + 3x SNS Queue created.")


if __name__ == "__main__":
    main()
