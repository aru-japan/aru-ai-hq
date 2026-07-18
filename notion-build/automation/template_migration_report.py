"""Template Migration Report -- ARu Official Article Template.

Legacy articles (generated before this template redesign, or under the
still-earlier 9-section template) do not follow the new 8-section structure
and should not be silently rewritten -- that would be a destructive,
unreviewed overwrite of real published content. Instead this script:

  1. Scans every non-Archived Article, parses its Body with the same
     article_template.parse_body_sections() reviewer_agent.py and
     render_article_layout.py already use (one parser, one source of truth)
  2. Sets Articles.Template Status = "Up to Date" / "Update Needed" -- the
     one new property this phase adds, so Dashboard/AI Command Center can
     query compliance directly going forward, not just from a report snapshot
  3. Prioritizes the "Update Needed" list: already-Published articles first
     (real readers are seeing these today), then by existing Priority/Urgency
     -- same deterministic-scoring spirit as research_prioritizer.py, no new
     AI calls
  4. Produces a CLI report + a dedicated "Template Migration Report" Notion
     page (same get_or_create_page/clear_page/write_page pattern as Coverage
     Analysis / Duplicate Prevention)
"""
import os
import sys
import time

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
REPO_ROOT = os.path.dirname(NOTION_BUILD_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, AUTOMATION_DIR)

from notion_api import load_env, notion_request, query_database, get_prop, set_env_value  # noqa: E402
from article_template import get_template, template_for_category, parse_body_sections, validate_sections  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")

PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}
URGENCY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def ensure_schema(token, articles_db_id):
    notion_request(token, "PATCH", f"/databases/{articles_db_id}", {
        "properties": {
            "Template Status": {"select": {"options": [
                {"name": "Up to Date", "color": "green"},
                {"name": "Update Needed", "color": "yellow"},
            ]}},
        }
    })


def scan_articles(token, articles_db_id):
    pages = query_database(token, articles_db_id, filter_obj={
        "property": "Status", "select": {"does_not_equal": "Archived"}
    })
    results = []
    for page in pages:
        title = get_prop(page, "Title", "title")
        body = get_prop(page, "Body", "rich_text")
        category = get_prop(page, "Category", "select")
        template = template_for_category(category)
        section_order = get_template(template)["section_order"]
        sections = parse_body_sections(body, template=template)
        missing, mandatory_missing = validate_sections(sections, template=template)
        results.append({
            "id": page["id"],
            "title": title,
            "template": template,
            "total_sections": len(section_order),
            "found": len(section_order) - len(missing),
            "missing": missing,
            "mandatory_missing": mandatory_missing,
            "up_to_date": not missing,
            "publishing_status": get_prop(page, "Publishing Status", "select"),
            "priority": get_prop(page, "Priority", "select"),
            "urgency": get_prop(page, "Urgency", "select"),
        })
    return results


def sort_key(article):
    published_first = 0 if article["publishing_status"] == "Published" else 1
    priority = PRIORITY_ORDER.get(article["priority"], 3)
    urgency = URGENCY_ORDER.get(article["urgency"], 4)
    return (published_first, urgency, priority)


def apply_template_status(token, results):
    for r in results:
        notion_request(token, "PATCH", f"/pages/{r['id']}", {
            "properties": {
                "Template Status": {"select": {"name": "Up to Date" if r["up_to_date"] else "Update Needed"}},
            }
        })


def rt(text):
    return [{"text": {"content": str(text)[:2000]}}]


def table_row(cells):
    return {"table_row": {"cells": [rt(c) for c in cells]}}


def build_page_blocks(results, up_to_date, needs_update):
    now = time.strftime("%Y-%m-%d %H:%M")
    header = ["記事", "検出セクション数", "Publishing Status", "Priority/Urgency", "欠落セクション"]
    rows = [table_row(header)]
    for r in needs_update[:20]:
        rows.append(table_row([
            r["title"][:60],
            f"{r['found']}/{r['total_sections']} [{r['template']}]",
            r["publishing_status"] or "-",
            f"{r['priority'] or '-'}/{r['urgency'] or '-'}",
            "、".join(r["missing"]),
        ]))

    blocks = [
        {"heading_1": {"rich_text": rt("📐 Template Migration Report")}},
        {"paragraph": {"rich_text": rt(f"最終更新: {now}（template_migration_report.py。ARu公式テンプレート（8セクション）準拠状況）")}},
        {"divider": {}},
        {"callout": {
            "rich_text": rt(f"対象記事: {len(results)}件／Up to Date: {len(up_to_date)}件／Update Needed: {len(needs_update)}件"),
            "icon": {"type": "emoji", "emoji": "📐"},
        }},
        {"divider": {}},
        {"heading_2": {"rich_text": rt("優先更新リスト（上位20件、Published優先→Urgency→Priority順）")}},
        {
            "table": {
                "table_width": len(header),
                "has_column_header": True,
                "has_row_header": False,
                "children": rows,
            }
        },
    ]
    return blocks


def get_or_create_page(env):
    token = env["NOTION_TOKEN"]
    page_id = env.get("TEMPLATE_MIGRATION_REPORT_PAGE_ID")
    if page_id:
        try:
            page = notion_request(token, "GET", f"/pages/{page_id}")
            if not page.get("archived"):
                return page_id
        except RuntimeError:
            pass

    page = notion_request(token, "POST", "/pages", {
        "parent": {"page_id": env["ARU_STUDIO_PAGE_ID"]},
        "properties": {"title": {"title": rt("Template Migration Report")}},
    })
    set_env_value(ENV_PATH, "TEMPLATE_MIGRATION_REPORT_PAGE_ID", page["id"])
    log(f"Created new Template Migration Report page: {page['id']}")
    return page["id"]


def clear_page(token, page_id):
    children = notion_request(token, "GET", f"/blocks/{page_id}/children?page_size=100")
    for b in children.get("results", []):
        notion_request(token, "DELETE", f"/blocks/{b['id']}")


def write_page(env, blocks):
    token = env["NOTION_TOKEN"]
    page_id = get_or_create_page(env)
    log("Clearing previous Template Migration Report page content...")
    clear_page(token, page_id)
    for i in range(0, len(blocks), 90):
        notion_request(token, "PATCH", f"/blocks/{page_id}/children", {"children": blocks[i:i + 90]})
    return page_id


def print_report(results, up_to_date, needs_update):
    print("\n" + "=" * 70)
    print("📐 Template Migration Report")
    print("=" * 70)
    print(f"対象記事: {len(results)}件")
    print(f"  Up to Date: {len(up_to_date)}件")
    print(f"  Update Needed: {len(needs_update)}件")
    print("\n優先更新リスト（上位10件）:")
    for r in needs_update[:10]:
        print(f"  [{r['found']}/{r['total_sections']} {r['template']}] {r['title'][:50]} "
              f"(Publishing={r['publishing_status']}, Priority={r['priority']}, Urgency={r['urgency']})")
        print(f"      欠落: {', '.join(r['missing'])}")
    print()


def main():
    env = load_env(ENV_PATH)
    token = env["NOTION_TOKEN"]
    articles_db = env["ARTICLES_DB_ID"]

    log("Ensuring Articles DB schema has Template Status...")
    ensure_schema(token, articles_db)

    log("Scanning all non-Archived Articles...")
    results = scan_articles(token, articles_db)
    log(f"  {len(results)} article(s) scanned")

    up_to_date = [r for r in results if r["up_to_date"]]
    needs_update = sorted([r for r in results if not r["up_to_date"]], key=sort_key)

    log("Applying Template Status to each Article...")
    apply_template_status(token, results)

    print_report(results, up_to_date, needs_update)

    blocks = build_page_blocks(results, up_to_date, needs_update)
    log("Writing Template Migration Report Notion page...")
    page_id = write_page(env, blocks)
    log(f"DONE. Template Migration Report page: {page_id}")


if __name__ == "__main__":
    main()
