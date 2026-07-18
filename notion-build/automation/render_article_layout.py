"""Article Page Layout Renderer -- Version 4 Phase 5 (Editor Experience),
updated for the ARu Official Article Template (Rei's 11-item structure).

Renders the ARu official article template out of the Articles.Body property
(one long rich_text blob with `**Heading**` markers) into actual Notion page
BLOCKS, so an editor opening an Article sees the article laid out with real
headings instead of one wall of text in the property panel.

This is purely additive: it never touches the Body property itself (still the
single source of truth every other script reads/writes), never touches any
other Article property, and never touches the database schema. No existing
script reads or depends on an Article page's block children -- confirmed by a
full-repo audit before writing this -- so this is safe to run at any time,
repeatedly, without risk to Freshness Monitor, Publishing Center, Reviewer
Agent, Coverage Analyzer, Editorial Planner, Duplicate Prevention, or the
Publish Gate.

Layout produced on the Article page:
    [meta callout: last rendered timestamp]
    ---
    ## Basic Answer / More Details / Cultural Background / ARu Tip / Things to Know
    <paragraph each>
    ---
    > toggle: その他の詳細
        ### FAQ
    ---
    > toggle: 💎 Premium Section
        <paragraph>
    ---
    ### Sources
    <paragraph>
    ---
    Related Articles (from Knowledge Links relation) / Last Updated (from
    Last Verified Date / Updated Date) -- these two are property-driven, never
    parsed out of Body.

SECTION_ORDER/parsing now live in article_template.py (single source of
truth shared with generate_article_pipeline.py and reviewer_agent.py) --
Body's format is still an AI *prompt instruction*, not code-enforced, so
parsing here remains best-effort: normalized exact match first, fuzzy match
as a fallback, and any section not found is simply omitted rather than
raising.
"""
import os
import sys
import time
import argparse
import datetime

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
REPO_ROOT = os.path.dirname(NOTION_BUILD_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, AUTOMATION_DIR)

from notion_api import load_env, notion_request, query_database, get_prop  # noqa: E402
from article_template import (  # noqa: E402
    get_template, template_for_content, parse_body_sections,
)

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")


def rich_text_chunks(content, chunk_size=1990):
    """Same helper as generate_article_pipeline.py's -- duplicated locally rather
    than imported, since generate_article_pipeline.py imports this module too
    (to trigger rendering right after Article creation) and a cross-import would
    be circular. article_template.py has no dependency on either module, so
    importing SECTION_ORDER etc. from there doesn't introduce a new cycle."""
    chunks = [content[i:i + chunk_size] for i in range(0, len(content), chunk_size)] or [""]
    return [{"text": {"content": c}} for c in chunks]


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _heading_block(text, level=2):
    key = f"heading_{level}"
    return {key: {"rich_text": [{"text": {"content": text[:2000]}}]}}


def _paragraph_block(text):
    return {"paragraph": {"rich_text": rich_text_chunks(text)}}


def _fetch_related_articles(token, knowledge_links_ids):
    related = []
    for rid in knowledge_links_ids:
        try:
            page = notion_request(token, "GET", f"/pages/{rid}")
        except RuntimeError:
            continue
        related.append({"title": get_prop(page, "Title", "title") or "(無題)", "url": page.get("url")})
    return related


def build_article_blocks(sections, template="standard", body_text=None, related_articles=None, last_updated=None):
    td = get_template(template)
    section_order = td["section_order"]
    primary_sections = td["primary_sections"]
    secondary_sections = td["secondary_sections"]
    premium_section = td["premium_section"]
    sources_section = td["sources_section"]

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    found = [s for s in section_order if s in sections]
    missing = [s for s in section_order if s not in sections]
    related_articles = related_articles or []

    blocks = [
        {"callout": {
            "rich_text": [{"text": {"content": f"最終レンダリング: {now}（render_article_layout.py。本文はBodyプロパティが唯一の原本、これは表示用）"}}],
            "icon": {"type": "emoji", "emoji": "\U0001f4c4"},
        }},
        {"divider": {}},
    ]

    if not found:
        # Pre-dates the official template (older article) -- nothing to split,
        # so show the raw Body text as-is rather than leaving the page empty.
        blocks.append({"callout": {
            "rich_text": [{"text": {"content": "この記事はARu公式テンプレート導入以前に生成されたため、セクション分割ができません。本文をそのまま表示しています。"}}],
            "icon": {"type": "emoji", "emoji": "ℹ️"},
        }})
        blocks.append({"divider": {}})
        if body_text:
            blocks.append(_paragraph_block(body_text))
        _append_trailing_blocks(blocks, related_articles, last_updated)
        return blocks, found, missing

    for name in primary_sections:
        if name in sections:
            blocks.append(_heading_block(name, level=2))
            blocks.append(_paragraph_block(sections[name]))

    secondary_present = [name for name in secondary_sections if name in sections]
    if secondary_present:
        blocks.append({"divider": {}})
        toggle_children = []
        for name in secondary_present:
            toggle_children.append(_heading_block(name, level=3))
            toggle_children.append(_paragraph_block(sections[name]))
        blocks.append({"toggle": {
            "rich_text": [{"text": {"content": "その他の詳細"}}],
            "children": toggle_children,
        }})

    if premium_section in sections:
        blocks.append({"divider": {}})
        blocks.append({"toggle": {
            "rich_text": [{"text": {"content": "💎 Premium Section"}}],
            "children": [_paragraph_block(sections[premium_section])],
        }})

    if sources_section in sections:
        blocks.append({"divider": {}})
        blocks.append(_heading_block(sources_section, level=3))
        blocks.append(_paragraph_block(sections[sources_section]))

    if missing:
        blocks.append({"divider": {}})
        blocks.append({"callout": {
            "rich_text": [{"text": {"content": f"未検出のセクション（Body側の見出し表記を確認してください）: {', '.join(missing)}"}}],
            "icon": {"type": "emoji", "emoji": "⚠️"},
        }})

    _append_trailing_blocks(blocks, related_articles, last_updated)
    return blocks, found, missing


def _append_trailing_blocks(blocks, related_articles, last_updated):
    """Related Articles and Last Updated are property-driven (Knowledge Links,
    Last Verified Date/Updated Date) -- never parsed out of Body, always
    appended regardless of whether Body-section parsing succeeded."""
    blocks.append({"divider": {}})
    blocks.append(_heading_block("Related Articles", level=3))
    if related_articles:
        for r in related_articles:
            text = r["title"]
            blocks.append({"bulleted_list_item": {
                "rich_text": [{"text": {"content": text, "link": {"url": r["url"]} if r["url"] else None}}],
            }})
    else:
        blocks.append({"paragraph": {"rich_text": rich_text_chunks("（関連記事は未設定です。Knowledge Linksで設定できます）")}})

    blocks.append({"paragraph": {
        "rich_text": rich_text_chunks(f"Last Updated: {last_updated or '未設定'}"),
    }})


def clear_article_blocks(token, article_id):
    children = notion_request(token, "GET", f"/blocks/{article_id}/children?page_size=100")
    for b in children.get("results", []):
        notion_request(token, "DELETE", f"/blocks/{b['id']}")


def render_article(env, article_id, title=None, body=None):
    token = env["NOTION_TOKEN"]
    page = notion_request(token, "GET", f"/pages/{article_id}")
    if body is None:
        title = get_prop(page, "Title", "title")
        body = get_prop(page, "Body", "rich_text")

    category = get_prop(page, "Category", "select")
    content_type = get_prop(page, "Content Type", "select")
    template = template_for_content(category, content_type)

    knowledge_links = get_prop(page, "Knowledge Links", "relation") or []
    last_updated = get_prop(page, "Last Verified Date", "date") or get_prop(page, "Updated Date", "date")
    related_articles = _fetch_related_articles(token, knowledge_links)

    sections = parse_body_sections(body, template=template)
    blocks, found, missing = build_article_blocks(
        sections, template=template, body_text=body, related_articles=related_articles, last_updated=last_updated
    )

    clear_article_blocks(token, article_id)
    for i in range(0, len(blocks), 90):
        notion_request(token, "PATCH", f"/blocks/{article_id}/children", {"children": blocks[i:i + 90]})

    return {
        "block_count": len(blocks), "found": found, "missing": missing, "title": title,
        "template": template, "total_sections": len(get_template(template)["section_order"]),
    }


def run_backfill(env, limit=None, dry_run=False):
    token = env["NOTION_TOKEN"]
    articles_db = env["ARTICLES_DB_ID"]

    pages = query_database(token, articles_db, filter_obj={
        "property": "Status", "select": {"does_not_equal": "Archived"}
    })
    if limit:
        pages = pages[:limit]
    log(f"{len(pages)} article(s) to process (dry_run={dry_run})")

    rendered = 0
    failed = 0
    for page in pages:
        title = get_prop(page, "Title", "title")
        body = get_prop(page, "Body", "rich_text")
        category = get_prop(page, "Category", "select")
        content_type = get_prop(page, "Content Type", "select")
        template = template_for_content(category, content_type)
        section_order = get_template(template)["section_order"]
        try:
            sections = parse_body_sections(body, template=template)
            found = [s for s in section_order if s in sections]
            missing = [s for s in section_order if s not in sections]
            log(f"  {title[:50]} [{template}]: {len(found)}/{len(section_order)} sections found" + (f" (missing: {missing})" if missing else ""))
            if not dry_run:
                result = render_article(env, page["id"], title=title, body=body)
                log(f"    -> rendered {result['block_count']} block(s)")
            rendered += 1
        except Exception as e:
            log(f"  FAILED: {title[:50]}: {e}")
            failed += 1

    log(f"DONE. {rendered} processed, {failed} failed" + (" (dry run, nothing written)" if dry_run else "."))
    return rendered, failed


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_article = sub.add_parser("article", help="Render a single Article's page blocks")
    p_article.add_argument("--article-id", required=True)

    p_backfill = sub.add_parser("backfill", help="Render all existing Articles")
    p_backfill.add_argument("--limit", type=int, default=None)
    p_backfill.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    env = load_env(ENV_PATH)

    if args.cmd == "article":
        result = render_article(env, args.article_id)
        log(f"Rendered {result['block_count']} block(s) for '{result['title']}' [{result['template']}] "
            f"({len(result['found'])}/{result['total_sections']} sections found)")
        if result["missing"]:
            log(f"  Missing: {result['missing']}")
    elif args.cmd == "backfill":
        run_backfill(env, limit=args.limit, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
