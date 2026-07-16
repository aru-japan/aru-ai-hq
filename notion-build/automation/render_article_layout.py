"""Article Page Layout Renderer -- Version 4 Phase 5 (Editor Experience).

Renders the ARu 9-section article template out of the Articles.Body property
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
    ## Question
    <paragraph>
    ## Basic Answer
    <paragraph>
    ## More Details
    <paragraph>
    ## Why Does Japan Do This?
    <paragraph>
    ## ARu Tip
    <paragraph>
    ---
    > toggle: その他の詳細
        ### Practical Steps and Cautions
        <paragraph>
        ### Latest Information
        <paragraph>
        ### Related Questions
        <paragraph>
        ### Mentor Support
        <paragraph>

Body's format is an AI *prompt instruction* (see ARU_ARTICLE_TEMPLATE_INSTRUCTIONS
in generate_article_pipeline.py), not code-enforced -- so parsing here is
best-effort: normalized exact match first, fuzzy match as a fallback, and any
section not found is simply omitted rather than raising.
"""
import os
import re
import sys
import time
import difflib
import argparse
import datetime

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
REPO_ROOT = os.path.dirname(NOTION_BUILD_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, AUTOMATION_DIR)

from notion_api import load_env, notion_request, query_database, get_prop  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")


def rich_text_chunks(content, chunk_size=1990):
    """Same helper as generate_article_pipeline.py's -- duplicated locally rather
    than imported, since generate_article_pipeline.py imports this module too
    (to trigger rendering right after Article creation) and a cross-import would
    be circular."""
    chunks = [content[i:i + chunk_size] for i in range(0, len(content), chunk_size)] or [""]
    return [{"text": {"content": c}} for c in chunks]

SECTION_ORDER = [
    "Question", "Basic Answer", "More Details", "Why Does Japan Do This?",
    "Practical Steps and Cautions", "Latest Information", "ARu Tip",
    "Related Questions", "Mentor Support",
]
PRIMARY_SECTIONS = ["Question", "Basic Answer", "More Details", "Why Does Japan Do This?", "ARu Tip"]
SECONDARY_SECTIONS = ["Practical Steps and Cautions", "Latest Information", "Related Questions", "Mentor Support"]

_HEADING_RE = re.compile(r"\*\*\s*([^\*]{2,80}?)\s*\*\*")


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _normalize(text):
    text = text.strip().lower()
    text = re.sub(r"[?？:：]+$", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


_CANONICAL_BY_NORMALIZED = {_normalize(s): s for s in SECTION_ORDER}


def _match_canonical(raw_heading):
    norm = _normalize(raw_heading)
    if norm in _CANONICAL_BY_NORMALIZED:
        return _CANONICAL_BY_NORMALIZED[norm]
    close = difflib.get_close_matches(norm, _CANONICAL_BY_NORMALIZED.keys(), n=1, cutoff=0.6)
    if close:
        return _CANONICAL_BY_NORMALIZED[close[0]]
    return None


def parse_body_sections(body_text):
    """Best-effort split of the 9-section Body text into {canonical_name: content}.
    Unrecognized bold spans are ignored. Missing sections are simply absent from
    the returned dict -- callers must .get() rather than assume all 9 exist."""
    if not body_text:
        return {}

    matches = list(_HEADING_RE.finditer(body_text))
    sections = {}
    for i, m in enumerate(matches):
        canonical = _match_canonical(m.group(1))
        if not canonical or canonical in sections:
            continue  # unrecognized heading, or a duplicate -- keep the first occurrence
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body_text)
        content = body_text[start:end].strip()
        if content:
            sections[canonical] = content
    return sections


def _heading_block(text, level=2):
    key = f"heading_{level}"
    return {key: {"rich_text": [{"text": {"content": text[:2000]}}]}}


def _paragraph_block(text):
    return {"paragraph": {"rich_text": rich_text_chunks(text)}}


def build_article_blocks(sections, body_text=None):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    found = [s for s in SECTION_ORDER if s in sections]
    missing = [s for s in SECTION_ORDER if s not in sections]

    blocks = [
        {"callout": {
            "rich_text": [{"text": {"content": f"最終レンダリング: {now}（render_article_layout.py。本文はBodyプロパティが唯一の原本、これは表示用）"}}],
            "icon": {"type": "emoji", "emoji": "\U0001f4c4"},
        }},
        {"divider": {}},
    ]

    if not found:
        # Pre-dates the 9-section template (older article) -- nothing to split,
        # so show the raw Body text as-is rather than leaving the page empty.
        blocks.append({"callout": {
            "rich_text": [{"text": {"content": "この記事はARu公式9セクションテンプレート導入以前に生成されたため、セクション分割ができません。本文をそのまま表示しています。"}}],
            "icon": {"type": "emoji", "emoji": "ℹ️"},
        }})
        blocks.append({"divider": {}})
        if body_text:
            blocks.append(_paragraph_block(body_text))
        return blocks, found, missing

    for name in PRIMARY_SECTIONS:
        if name in sections:
            blocks.append(_heading_block(name, level=2))
            blocks.append(_paragraph_block(sections[name]))

    secondary_present = [name for name in SECONDARY_SECTIONS if name in sections]
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

    if missing:
        blocks.append({"divider": {}})
        blocks.append({"callout": {
            "rich_text": [{"text": {"content": f"未検出のセクション（Body側の見出し表記を確認してください）: {', '.join(missing)}"}}],
            "icon": {"type": "emoji", "emoji": "⚠️"},
        }})

    return blocks, found, missing


def clear_article_blocks(token, article_id):
    children = notion_request(token, "GET", f"/blocks/{article_id}/children?page_size=100")
    for b in children.get("results", []):
        notion_request(token, "DELETE", f"/blocks/{b['id']}")


def render_article(env, article_id, title=None, body=None):
    token = env["NOTION_TOKEN"]
    if body is None:
        page = notion_request(token, "GET", f"/pages/{article_id}")
        title = get_prop(page, "Title", "title")
        body = get_prop(page, "Body", "rich_text")

    sections = parse_body_sections(body)
    blocks, found, missing = build_article_blocks(sections, body_text=body)

    clear_article_blocks(token, article_id)
    for i in range(0, len(blocks), 90):
        notion_request(token, "PATCH", f"/blocks/{article_id}/children", {"children": blocks[i:i + 90]})

    return {"block_count": len(blocks), "found": found, "missing": missing, "title": title}


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
        try:
            sections = parse_body_sections(body)
            found = [s for s in SECTION_ORDER if s in sections]
            missing = [s for s in SECTION_ORDER if s not in sections]
            log(f"  {title[:50]}: {len(found)}/9 sections found" + (f" (missing: {missing})" if missing else ""))
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
        log(f"Rendered {result['block_count']} block(s) for '{result['title']}' ({len(result['found'])}/9 sections found)")
        if result["missing"]:
            log(f"  Missing: {result['missing']}")
    elif args.cmd == "backfill":
        run_backfill(env, limit=args.limit, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
