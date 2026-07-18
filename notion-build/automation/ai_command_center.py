"""AI Command Center -- Version 4 Phase 5 (Editor Experience) + ARu Intelligence
Phase 1/2 (Source Monitoring).

The AI/ops counterpart to editor_home.py: a navigation hub summarizing what
the AI layer is currently flagging or monitoring, rather than what a human
must directly decide on. Split rationale:

    Editor Home        -- "what do I need to act on?" (human decisions)
    AI Command Center   -- "what is the AI watching / has the AI already found?"

This page never recomputes Coverage Analysis or Editorial Planner's AI content
itself (that would mean extra AI Gateway calls and a second copy that can
drift from the real page) -- it only points at those existing pages with
light metadata (last-edited time + URL). Freshness breakdown, Duplicate
Prevention "today" stats, external-signal-feed counts, and (Phase 2) Source
Library monitoring stats are cheap local reads/queries computed fresh each
run, reusing the existing modules' constants and functions directly rather
than re-deriving them.
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
from article_freshness_monitor import FORCE_FLAG_URGENCY_SCORE  # noqa: E402
from source_categories import UPDATE_CLASSIFICATIONS  # noqa: E402
import duplicate_prevention_report as dpr  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")

# (emoji, label, db env key, filter). Filters copied verbatim from
# docs/Dashboard-Setup-Guide.md's 13-section table so these counts can never
# drift from what the real Dashboard Linked Views show.
MONITOR_STAT_DEFS = [
    ("⑦", "Source Monitor Alerts", "SOURCE_MONITOR_DB_ID",
     {"property": "Change Detected", "checkbox": {"equals": True}}),
    ("⑧", "Recent Law Updates", "LAW_UPDATE_DB_ID", None),
    ("⑨", "Recent Event Calendar", "EVENT_CALENDAR_DB_ID",
     {"property": "Status", "select": {"does_not_equal": "Cancelled"}}),
]

# label -> env key holding that page's id, for the light metadata pointers.
POINTER_PAGES = [
    ("📊 Coverage Analysis", "COVERAGE_ANALYSIS_PAGE_ID"),
    ("📝 Editorial Planner", "EDITORIAL_PLANNER_PAGE_ID"),
]


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def gather_freshness_breakdown(env):
    token = env["NOTION_TOKEN"]
    pages = query_database(token, env["ARTICLES_DB_ID"], filter_obj={
        "property": "Freshness Status", "select": {"equals": "Needs Update"}
    })
    signal_flagged = 0
    time_based_flagged = 0
    for page in pages:
        score = get_prop(page, "Freshness Urgency Score", "number") or 0
        if score >= FORCE_FLAG_URGENCY_SCORE:
            signal_flagged += 1
        else:
            time_based_flagged += 1
    return {"total": len(pages), "signal_flagged": signal_flagged, "time_based_flagged": time_based_flagged}


def gather_monitor_stats(env):
    token = env["NOTION_TOKEN"]
    stats = []
    for emoji, label, db_key, filter_obj in MONITOR_STAT_DEFS:
        pages = query_database(token, env[db_key], filter_obj=filter_obj)
        stats.append({"emoji": emoji, "label": label, "count": len(pages)})
        log(f"  {emoji} {label}: {len(pages)}")
    return stats


def gather_page_pointers(env):
    token = env["NOTION_TOKEN"]
    pointers = []
    for label, page_key in POINTER_PAGES:
        page_id = env.get(page_key)
        if not page_id:
            pointers.append({"label": label, "url": None, "last_edited": None})
            continue
        try:
            page = notion_request(token, "GET", f"/pages/{page_id}")
            pointers.append({
                "label": label,
                "url": page.get("url"),
                "last_edited": page.get("last_edited_time", "")[:16].replace("T", " "),
            })
        except RuntimeError:
            pointers.append({"label": label, "url": None, "last_edited": None})
    return pointers


def gather_duplicate_prevention_today(env):
    events = dpr.read_today_events()
    generated, skipped = dpr.summarize(events)
    return {"generated": len(generated), "skipped": len(skipped)}


def gather_source_intelligence(env):
    """ARu Intelligence Phase 2: Source Library/Monitor stats. Sources monitored
    and errored-sources counts come straight from Source Library; today's
    changes and their Update Classification breakdown come from Source
    Monitor -- all direct live queries, nothing recomputed or cached."""
    token = env["NOTION_TOKEN"]
    today = datetime.date.today().isoformat()

    all_sources = query_database(token, env["SOURCE_LIBRARY_DB_ID"])
    active_sources = [p for p in all_sources if get_prop(p, "Status", "select") == "Active"]
    errored_sources = [p for p in all_sources if (get_prop(p, "Last Check Error", "rich_text") or "").strip()]

    todays_changes = query_database(token, env["SOURCE_MONITOR_DB_ID"], filter_obj={
        "and": [
            {"property": "Change Detected", "checkbox": {"equals": True}},
            {"property": "Checked At", "date": {"equals": today}},
        ]
    })
    critical_today = [p for p in todays_changes if get_prop(p, "Impact Level", "select") == "Critical"]

    classification_breakdown = {c: 0 for c in UPDATE_CLASSIFICATIONS}
    for p in todays_changes:
        classification = get_prop(p, "Update Classification", "select")
        if classification in classification_breakdown:
            classification_breakdown[classification] += 1

    research_candidates = query_database(token, env["RESEARCH_DB_ID"], filter_obj={
        "and": [
            {"property": "Status", "select": {"equals": "New"}},
            {"property": "Discovery Method", "select": {"equals": "Source Monitor"}},
        ]
    })

    return {
        "total_sources": len(all_sources),
        "active_sources": len(active_sources),
        "errored_sources": [get_prop(p, "Source Name", "title") for p in errored_sources],
        "todays_changes": len(todays_changes),
        "critical_today": len(critical_today),
        "classification_breakdown": {k: v for k, v in classification_breakdown.items() if v > 0},
        "research_candidates": len(research_candidates),
    }


def get_dashboard_url(env):
    token = env["NOTION_TOKEN"]
    page = notion_request(token, "GET", f"/pages/{env['DASHBOARD_PAGE_ID']}")
    return page.get("url", "")


def rt(text, link=None):
    obj = {"content": str(text)[:2000]}
    if link:
        obj["link"] = {"url": link}
    return [{"text": obj}]


def build_page_blocks(freshness, monitor_stats, pointers, dup_today, source_intel, dashboard_url):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    blocks = [
        {"heading_1": {"rich_text": rt("🤖 AI Command Center")}},
        {"paragraph": {"rich_text": rt(f"最終更新: {now}（ai_command_center.py。AIが検知・監視している内容の一覧）")}},
        {"paragraph": {"rich_text": rt(
            "このページはナビゲーションハブです。実際の記事一覧などの操作は、"
            "下のリンクからDashboardの該当セクション（Linked View）を開いて行ってください。"
        )}},
        {"divider": {}},
        {"heading_2": {"rich_text": rt("🔴 Freshness 内訳（更新が必要な記事）")}},
        {"callout": {
            "rich_text": rt(f"合計: {freshness['total']}件"),
            "icon": {"type": "emoji", "emoji": "🔴" if freshness["total"] else "✅"},
        }},
        {"bulleted_list_item": {"rich_text": rt(
            f"外部シグナル起因（法改正・情報源変化・イベント中止）: {freshness['signal_flagged']}件"
        )}},
        {"bulleted_list_item": {"rich_text": rt(
            f"時間経過による定期レビュー期限超過: {freshness['time_based_flagged']}件"
        )}},
    ]
    if dashboard_url:
        blocks.append({"paragraph": {"rich_text": rt("→ Dashboardの「🔴 Update Needed」で見る", link=dashboard_url)}})
    blocks.append({"divider": {}})

    blocks.append({"heading_2": {"rich_text": rt("🛡 Duplicate Prevention（本日）")}})
    blocks.append({"bulleted_list_item": {"rich_text": rt(f"本日の生成件数: {dup_today['generated']}件")}})
    blocks.append({"bulleted_list_item": {"rich_text": rt(f"本日の重複スキップ件数: {dup_today['skipped']}件")}})
    blocks.append({"divider": {}})

    blocks.append({"heading_2": {"rich_text": rt("📡 外部監視フィード")}})
    for s in monitor_stats:
        icon = "✅" if s["count"] == 0 else "🔔"
        blocks.append({"bulleted_list_item": {"rich_text": rt(f"{icon} {s['emoji']} {s['label']}: {s['count']}件")}})
    blocks.append({"divider": {}})

    blocks.append({"heading_2": {"rich_text": rt("🌐 Source Intelligence（ARu Intelligence Phase 2）")}})
    blocks.append({"bulleted_list_item": {"rich_text": rt(
        f"監視対象ソース数: {source_intel['total_sources']}件（うちActive: {source_intel['active_sources']}件）"
    )}})
    blocks.append({"bulleted_list_item": {"rich_text": rt(f"本日の変化検知: {source_intel['todays_changes']}件")}})
    blocks.append({"bulleted_list_item": {"rich_text": rt(
        f"うちCritical（🔴 Critical Source Updatesで確認）: {source_intel['critical_today']}件"
    )}})
    error_icon = "✅" if not source_intel["errored_sources"] else "⚠️"
    error_text = "なし" if not source_intel["errored_sources"] else "、".join(source_intel["errored_sources"])
    blocks.append({"bulleted_list_item": {"rich_text": rt(f"{error_icon} エラー中のソース: {error_text}")}})
    if source_intel["classification_breakdown"]:
        breakdown_text = "、".join(f"{k}: {v}件" for k, v in source_intel["classification_breakdown"].items())
        blocks.append({"bulleted_list_item": {"rich_text": rt(f"本日の内訳（Update Classification）: {breakdown_text}")}})
    blocks.append({"bulleted_list_item": {"rich_text": rt(
        f"Research候補（Source Monitor起点、未レビュー）: {source_intel['research_candidates']}件"
    )}})
    blocks.append({"divider": {}})

    blocks.append({"heading_2": {"rich_text": rt("🧭 AI分析ページへのリンク")}})
    for p in pointers:
        if p["url"]:
            blocks.append({"paragraph": {"rich_text": rt(f"{p['label']}（最終更新: {p['last_edited']}） →", link=p["url"])}})
        else:
            blocks.append({"paragraph": {"rich_text": rt(f"{p['label']}: 未作成（対応スクリプトを一度実行してください）")}})

    return blocks


def get_or_create_page(env):
    token = env["NOTION_TOKEN"]
    page_id = env.get("AI_COMMAND_CENTER_PAGE_ID")
    if page_id:
        try:
            page = notion_request(token, "GET", f"/pages/{page_id}")
            if not page.get("archived"):
                return page_id
        except RuntimeError:
            pass

    page = notion_request(token, "POST", "/pages", {
        "parent": {"page_id": env["ARU_STUDIO_PAGE_ID"]},
        "properties": {"title": {"title": rt("AI Command Center")}},
    })
    set_env_value(ENV_PATH, "AI_COMMAND_CENTER_PAGE_ID", page["id"])
    log(f"Created new AI Command Center page: {page['id']}")
    return page["id"]


def clear_page(token, page_id):
    children = notion_request(token, "GET", f"/blocks/{page_id}/children?page_size=100")
    for b in children.get("results", []):
        notion_request(token, "DELETE", f"/blocks/{b['id']}")


def write_page(env, blocks):
    token = env["NOTION_TOKEN"]
    page_id = get_or_create_page(env)
    log("Clearing previous AI Command Center page content...")
    clear_page(token, page_id)
    for i in range(0, len(blocks), 90):
        notion_request(token, "PATCH", f"/blocks/{page_id}/children", {"children": blocks[i:i + 90]})
    return page_id


def print_report(freshness, monitor_stats, pointers, dup_today, source_intel):
    print("\n" + "=" * 70)
    print("🤖 AI Command Center")
    print("=" * 70)
    print(f"Freshness 内訳: 合計={freshness['total']} 外部シグナル={freshness['signal_flagged']} "
          f"時間経過={freshness['time_based_flagged']}")
    print(f"Duplicate Prevention（本日）: 生成={dup_today['generated']} スキップ={dup_today['skipped']}")
    for s in monitor_stats:
        print(f"  {s['emoji']} {s['label']}: {s['count']}件")
    for p in pointers:
        print(f"  {p['label']}: {'last_edited=' + p['last_edited'] if p['url'] else '未作成'}")
    print(f"Source Intelligence: 監視対象={source_intel['total_sources']}（Active={source_intel['active_sources']}） "
          f"本日の変化={source_intel['todays_changes']}（Critical={source_intel['critical_today']}） "
          f"エラー中={len(source_intel['errored_sources'])} Research候補={source_intel['research_candidates']}")
    if source_intel["classification_breakdown"]:
        print(f"  内訳: {source_intel['classification_breakdown']}")
    print()


def main():
    env = load_env(ENV_PATH)

    log("Gathering freshness breakdown...")
    freshness = gather_freshness_breakdown(env)

    log("Gathering external monitor stats...")
    monitor_stats = gather_monitor_stats(env)

    log("Gathering AI analysis page pointers...")
    pointers = gather_page_pointers(env)

    log("Gathering today's Duplicate Prevention activity...")
    dup_today = gather_duplicate_prevention_today(env)

    log("Gathering Source Intelligence stats (ARu Intelligence Phase 2)...")
    source_intel = gather_source_intelligence(env)

    print_report(freshness, monitor_stats, pointers, dup_today, source_intel)

    log("Resolving Dashboard page URL...")
    dashboard_url = get_dashboard_url(env)

    blocks = build_page_blocks(freshness, monitor_stats, pointers, dup_today, source_intel, dashboard_url)
    log("Writing AI Command Center Notion page...")
    page_id = write_page(env, blocks)
    log(f"DONE. AI Command Center page: {page_id}")


if __name__ == "__main__":
    main()
