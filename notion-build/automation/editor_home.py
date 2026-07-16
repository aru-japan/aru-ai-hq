"""Editor Home -- Version 4 Phase 5 (Editor Experience).

A navigation hub for the editor-in-chief: one page that answers "what needs my
decision today?" with real counts, then links back to the already-configured
Dashboard Linked Views to actually work the list. This does NOT recreate those
13 Linked Views (Notion's public API cannot create them at all -- see
Dashboard-Setup-Guide.md) -- it just surfaces the same numbers a human sees
there, computed straight from the same databases with the same filters, so the
two can never silently drift apart.

Covers only human-decision items (things a person must act on). AI/ops
monitoring (freshness breakdown, coverage gaps, duplicate-prevention activity,
external signal feeds) lives on the separate AI Command Center page instead --
see ai_command_center.py.
"""
import os
import sys
import time
import datetime

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
REPO_ROOT = os.path.dirname(NOTION_BUILD_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, AUTOMATION_DIR)

from notion_api import load_env, notion_request, query_database, get_prop, set_env_value  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")

# (emoji, label, db env key, filter). Filters copied verbatim from
# docs/Dashboard-Setup-Guide.md's 13-section table so these counts can never
# drift from what the real Dashboard Linked Views show.
STAT_DEFS = [
    ("🚀", "Ready to Publish", "ARTICLES_DB_ID",
     {"property": "Publishing Status", "select": {"equals": "Ready to Publish"}}),
    ("📚", "Published Articles", "ARTICLES_DB_ID",
     {"property": "Publishing Status", "select": {"equals": "Published"}}),
    ("🛠", "Needs Update（公開済み）", "ARTICLES_DB_ID",
     {"property": "Publishing Status", "select": {"equals": "Needs Update"}}),
    ("①", "Publish Approval Pending", "TRANSLATION_DB_ID",
     {"property": "Publish Approval", "select": {"equals": "Pending"}}),
    ("②", "Article Review Waiting", "ARTICLES_DB_ID",
     {"or": [
         {"property": "Status", "select": {"equals": "AI Draft"}},
         {"property": "Status", "select": {"equals": "Human Review"}},
     ]}),
    ("③", "Translation Review Waiting", "TRANSLATION_DB_ID",
     {"or": [
         {"property": "Quality Result", "select": {"is_empty": True}},
         {"property": "Quality Result", "select": {"equals": "Not Reviewed"}},
     ]}),
    ("④", "SNS Draft Waiting", "SNS_QUEUE_DB_ID",
     {"and": [
         {"property": "Status", "select": {"equals": "Draft"}},
         {"property": "Review Result", "select": {"does_not_equal": "Pass"}},
     ]}),
    ("⑤", "Today's Editorial Calendar", "EDITORIAL_CALENDAR_DB_ID",
     {"or": [
         {"property": "Status", "select": {"equals": "Idea"}},
         {"property": "Status", "select": {"equals": "Planned"}},
         {"property": "Status", "select": {"equals": "In Progress"}},
     ]}),
    ("⑥", "Today's Research", "RESEARCH_DB_ID",
     {"property": "Status", "select": {"equals": "New"}}),
]


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def gather_stats(env):
    token = env["NOTION_TOKEN"]
    stats = []
    for emoji, label, db_key, filter_obj in STAT_DEFS:
        pages = query_database(token, env[db_key], filter_obj=filter_obj)
        stats.append({"emoji": emoji, "label": label, "count": len(pages)})
        log(f"  {emoji} {label}: {len(pages)}")
    return stats


def get_dashboard_url(env):
    token = env["NOTION_TOKEN"]
    page = notion_request(token, "GET", f"/pages/{env['DASHBOARD_PAGE_ID']}")
    return page.get("url", "")


def rt(text, link=None):
    obj = {"content": str(text)[:2000]}
    if link:
        obj["link"] = {"url": link}
    return [{"text": obj}]


def build_page_blocks(stats, dashboard_url):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    total_pending = sum(s["count"] for s in stats)

    blocks = [
        {"heading_1": {"rich_text": rt("🏠 Editor Home")}},
        {"paragraph": {"rich_text": rt(f"最終更新: {now}（editor_home.py。数値は実データから毎回再計算）")}},
        {"callout": {
            "rich_text": rt(f"本日、対応が必要な件数の合計: {total_pending}件"),
            "icon": {"type": "emoji", "emoji": "📋"},
        }},
        {"paragraph": {"rich_text": rt(
            "このページはナビゲーションハブです。実際の記事一覧・翻訳一覧などの操作は、"
            "下のリンクからDashboardの該当セクション（Linked View）を開いて行ってください。"
        )}},
        {"divider": {}},
    ]

    for s in stats:
        blocks.append({"heading_3": {"rich_text": rt(f"{s['emoji']} {s['label']}")}})
        icon = "✅" if s["count"] == 0 else "🔔"
        blocks.append({"callout": {
            "rich_text": rt(f"{s['count']}件"),
            "icon": {"type": "emoji", "emoji": icon},
        }})
        if dashboard_url:
            blocks.append({"paragraph": {"rich_text": rt("→ Dashboardで見る", link=dashboard_url)}})
        blocks.append({"divider": {}})

    return blocks


def get_or_create_page(env):
    token = env["NOTION_TOKEN"]
    page_id = env.get("EDITOR_HOME_PAGE_ID")
    if page_id:
        try:
            page = notion_request(token, "GET", f"/pages/{page_id}")
            if not page.get("archived"):
                return page_id
        except RuntimeError:
            pass

    page = notion_request(token, "POST", "/pages", {
        "parent": {"page_id": env["ARU_STUDIO_PAGE_ID"]},
        "properties": {"title": {"title": rt("Editor Home")}},
    })
    set_env_value(ENV_PATH, "EDITOR_HOME_PAGE_ID", page["id"])
    log(f"Created new Editor Home page: {page['id']}")
    return page["id"]


def clear_page(token, page_id):
    children = notion_request(token, "GET", f"/blocks/{page_id}/children?page_size=100")
    for b in children.get("results", []):
        notion_request(token, "DELETE", f"/blocks/{b['id']}")


def write_page(env, blocks):
    token = env["NOTION_TOKEN"]
    page_id = get_or_create_page(env)
    log("Clearing previous Editor Home page content...")
    clear_page(token, page_id)
    for i in range(0, len(blocks), 90):
        notion_request(token, "PATCH", f"/blocks/{page_id}/children", {"children": blocks[i:i + 90]})
    return page_id


def print_report(stats):
    print("\n" + "=" * 70)
    print("🏠 Editor Home -- 本日の対応件数")
    print("=" * 70)
    for s in stats:
        print(f"  {s['emoji']} {s['label']}: {s['count']}件")
    print(f"\n  合計: {sum(s['count'] for s in stats)}件")
    print()


def main():
    env = load_env(ENV_PATH)
    log("Gathering editor decision stats (same filters as Dashboard Linked Views)...")
    stats = gather_stats(env)
    print_report(stats)

    log("Resolving Dashboard page URL...")
    dashboard_url = get_dashboard_url(env)

    blocks = build_page_blocks(stats, dashboard_url)
    log("Writing Editor Home Notion page...")
    page_id = write_page(env, blocks)
    log(f"DONE. Editor Home page: {page_id}")


if __name__ == "__main__":
    main()
