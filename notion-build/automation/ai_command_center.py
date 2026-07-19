"""AI Command Center -- Version 4 Phase 5 (Editor Experience) + ARu Intelligence
Phase 1/2/3 (Source Monitoring + Editorial Intelligence) + ARu Studio v4.1
Editorial Intelligence.

ARu Studio v4.1 (2026-07-19) restructured this page's daily-homepage top
around Rei's three named priorities -- 今日追加するQA / 更新が必要な記事 /
公開待ちコンテンツ -- as the first three sections. These are aggregates over
existing per-DB gather functions (gather_updates_needed() folds together
Freshness Status, Current Validity, and the new review_scheduler.py due-date
signal; gather_publish_pending() folds together Articles Ready to Publish,
SNS Queue Drafts, and Translation pending review) rather than duplicating
those queries under new headings. Everything that isn't one of the three
(Today's Opportunities, Critical Updates, Top Research Candidates, Recently
Updated Articles, the Law Update Pipeline queue, and the original Phase 1/2
monitoring detail) is kept, just demoted below as supporting detail -- not
deleted, since each still answers a real question on its own.

This page never recomputes Coverage Analysis or Editorial Planner's AI
content itself (that would mean extra AI Gateway calls and a second copy
that can drift from the real page) -- it only points at those existing
pages with light metadata (last-edited time + URL). Everything else here
is a cheap, deterministic, live query against DBs that already exist --
no new database anywhere in Phase 3 or v4.1.
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
from research_prioritizer import rank_research_candidates  # noqa: E402
from today_opportunities import gather_opportunities  # noqa: E402
from review_scheduler import find_review_due  # noqa: E402
from add_production_stage import PRODUCTION_STAGE_OPTIONS  # noqa: E402
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

RECENTLY_UPDATED_LIMIT = 5
TOP_RESEARCH_LIMIT = 5


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# --- Phase 3: Editorial Intelligence (daily homepage) ---

def gather_critical_updates(env, today):
    """Union of everything demanding urgent human attention right now:
    Articles force-flagged by an external signal (not just time decay),
    today's Critical-impact Source Monitor changes, and Law Updates
    significant enough (Major) to matter but not yet reflected into an
    Article. Reuses existing properties/queries throughout -- no new
    schema, no recomputation of anything already computed elsewhere."""
    token = env["NOTION_TOKEN"]

    signal_flagged_articles = query_database(token, env["ARTICLES_DB_ID"], filter_obj={
        "and": [
            {"property": "Status", "select": {"does_not_equal": "Archived"}},
            {"property": "Freshness Status", "select": {"equals": "Needs Update"}},
            {"property": "Freshness Urgency Score", "number": {"greater_than_or_equal_to": FORCE_FLAG_URGENCY_SCORE}},
        ]
    })
    critical_source_changes = query_database(token, env["SOURCE_MONITOR_DB_ID"], filter_obj={
        "and": [
            {"property": "Change Detected", "checkbox": {"equals": True}},
            {"property": "Checked At", "date": {"equals": today.isoformat()}},
            {"property": "Impact Level", "select": {"equals": "Critical"}},
        ]
    })
    major_law_updates = query_database(token, env["LAW_UPDATE_DB_ID"], filter_obj={
        "and": [
            {"property": "Significance", "select": {"equals": "Major"}},
            {"property": "Update Status", "select": {"does_not_equal": "Article Published"}},
            {"property": "Update Status", "select": {"does_not_equal": "Archived"}},
        ]
    })

    return {
        "articles": [get_prop(p, "Title", "title") for p in signal_flagged_articles],
        "source_changes": [get_prop(p, "Monitor Entry", "title") for p in critical_source_changes],
        "law_updates": [get_prop(p, "Law Name", "title") for p in major_law_updates],
    }


def gather_publishing_queue(env, limit=5):
    """Same Ready to Publish query as editor_home.py's stat -- reused
    verbatim, not redefined, so the two pages never disagree on what
    counts as ready."""
    token = env["NOTION_TOKEN"]
    pages = query_database(token, env["ARTICLES_DB_ID"], filter_obj={
        "property": "Publishing Status", "select": {"equals": "Ready to Publish"}
    }, sorts=[
        {"property": "Priority", "direction": "descending"},
        {"property": "Update Level", "direction": "descending"},
    ])
    return {
        "total": len(pages),
        "top": [get_prop(p, "Title", "title") for p in pages[:limit]],
    }


def gather_recently_updated_articles(env, limit=RECENTLY_UPDATED_LIMIT):
    token = env["NOTION_TOKEN"]
    pages = query_database(token, env["ARTICLES_DB_ID"], filter_obj={
        "property": "Status", "select": {"does_not_equal": "Archived"}
    }, sorts=[{"property": "Updated Date", "direction": "descending"}])
    return [{
        "title": get_prop(p, "Title", "title"),
        "updated": get_prop(p, "Updated Date", "date"),
    } for p in pages[:limit]]


# --- Phase 1/2: monitoring detail (unchanged) ---

def gather_freshness_breakdown(env):
    """ARu Studio v4.1: also reports Current Validity (Review Due/Outdated/
    Under Review), the narrower "is the underlying fact still correct" signal
    the Law Update Pipeline drives -- extends this existing section rather
    than adding a second parallel "articles needing update" heading. Current
    Validity and Freshness Status are independent axes (one time-based, one
    law-change-based) and are reported side by side, not merged."""
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

    validity_pages = query_database(token, env["ARTICLES_DB_ID"], filter_obj={
        "and": [
            {"property": "Current Validity", "select": {"is_not_empty": True}},
            {"property": "Current Validity", "select": {"does_not_equal": "Current"}},
        ]
    })
    validity_counts = {}
    for page in validity_pages:
        v = get_prop(page, "Current Validity", "select")
        validity_counts[v] = validity_counts.get(v, 0) + 1

    return {
        "total": len(pages), "signal_flagged": signal_flagged, "time_based_flagged": time_based_flagged,
        "validity_total": len(validity_pages), "validity_counts": validity_counts,
    }


def gather_content_pipeline_today(env, today):
    """ARu Studio v4.1: today's QA/article creation activity (Story Bank ->
    QA card -> Article) plus the Deep Guide backlog. created_time comes
    straight from the Notion page object, not a property -- no new schema."""
    token = env["NOTION_TOKEN"]
    today_str = today.isoformat()

    story_bank = query_database(token, env["STORY_BANK_DB_ID"])
    new_qa_today = [p for p in story_bank
                    if p.get("created_time", "").startswith(today_str) and get_prop(p, "QA Question", "rich_text")]

    articles = query_database(token, env["ARTICLES_DB_ID"])
    new_articles_today = [p for p in articles if p.get("created_time", "").startswith(today_str)]

    deep_guide_candidates = [p for p in story_bank
                             if get_prop(p, "Deep Article Needed", "checkbox")
                             and not p["properties"].get("Generated Article", {}).get("relation")]

    return {
        "new_qa_today": [get_prop(p, "Title", "title") for p in new_qa_today],
        "new_articles_today": [get_prop(p, "Title", "title") for p in new_articles_today],
        "deep_guide_candidates": [get_prop(p, "Title", "title") for p in deep_guide_candidates],
    }


def gather_production_stage_breakdown(env):
    """ARu Studio v4.1: count-based Kanban view of Articles' (and Story
    Bank's) Production Stage -- Notion Board views can't be created via API
    (same limitation as every other View in this project, see
    Studio-v4.1-View-Setup-Guide.md), so this is the count-display half of
    Rei's request; the real drag-and-drop Kanban still needs the manual
    Board view. Counts are reported in pipeline order, not alphabetically."""
    token = env["NOTION_TOKEN"]

    articles = query_database(token, env["ARTICLES_DB_ID"])
    story_bank = query_database(token, env["STORY_BANK_DB_ID"])

    articles_counts = {s: 0 for s in PRODUCTION_STAGE_OPTIONS}
    articles_unset = 0
    for p in articles:
        stage = get_prop(p, "Production Stage", "select")
        if stage in articles_counts:
            articles_counts[stage] += 1
        else:
            articles_unset += 1

    story_bank_counts = {s: 0 for s in PRODUCTION_STAGE_OPTIONS}
    story_bank_unset = 0
    for p in story_bank:
        stage = get_prop(p, "Production Stage", "select")
        if stage in story_bank_counts:
            story_bank_counts[stage] += 1
        else:
            story_bank_unset += 1

    return {
        "articles_counts": articles_counts, "articles_unset": articles_unset,
        "story_bank_counts": story_bank_counts, "story_bank_unset": story_bank_unset,
    }


def gather_law_update_queue(env):
    """ARu Studio v4.1: status breakdown of the Law Update Pipeline queue
    (law_update_pipeline.py) -- Monitoring (unconfirmed candidates awaiting a
    human decision) and Approval Required (edits awaiting human sign-off) are
    surfaced by name since those are exactly the two points a human needs to
    act at."""
    token = env["NOTION_TOKEN"]
    law_updates = query_database(token, env["LAW_UPDATE_DB_ID"])
    counts = {}
    for p in law_updates:
        status = get_prop(p, "Update Status", "select") or "(未設定)"
        counts[status] = counts.get(status, 0) + 1
    monitoring = [get_prop(p, "Law Name", "title") for p in law_updates
                  if get_prop(p, "Update Status", "select") == "Monitoring"]
    approval_required = [get_prop(p, "Law Name", "title") for p in law_updates
                         if get_prop(p, "Update Status", "select") == "Approval Required"]
    return {"counts": counts, "monitoring": monitoring, "approval_required": approval_required}


def gather_translation_queue(env):
    token = env["NOTION_TOKEN"]
    pages = query_database(token, env["TRANSLATION_DB_ID"], filter_obj={
        "property": "Needs Re-Translation", "checkbox": {"equals": True}
    })
    return {"total": len(pages), "top": [get_prop(p, "Translation Name", "title") for p in pages[:5]]}


def gather_sns_queue_pending(env):
    token = env["NOTION_TOKEN"]
    pages = query_database(token, env["SNS_QUEUE_DB_ID"], filter_obj={
        "property": "Status", "select": {"equals": "Draft"}
    })
    return {"total": len(pages)}


def gather_updates_needed(env):
    """ARu Studio v4.1 core section 2/3: "更新が必要な記事" -- the union of
    every reason an Article (or Story Bank record) might need editorial
    attention: Freshness Status (time-based, article_freshness_monitor.py),
    Current Validity (law-change-based, law_update_pipeline.py), and Next
    Review due (calendar-based, review_scheduler.py). Reports the union by
    Title (de-duplicated) so an article flagged by two signals at once isn't
    double-counted, plus each signal's own count for diagnosis."""
    token = env["NOTION_TOKEN"]

    freshness_pages = query_database(token, env["ARTICLES_DB_ID"], filter_obj={
        "property": "Freshness Status", "select": {"equals": "Needs Update"}
    })
    validity_pages = query_database(token, env["ARTICLES_DB_ID"], filter_obj={
        "and": [
            {"property": "Current Validity", "select": {"is_not_empty": True}},
            {"property": "Current Validity", "select": {"does_not_equal": "Current"}},
        ]
    })
    due = find_review_due(env)

    freshness_titles = {get_prop(p, "Title", "title") for p in freshness_pages}
    validity_titles = {get_prop(p, "Title", "title") for p in validity_pages}
    review_due_titles = set(due["articles"])
    all_titles = freshness_titles | validity_titles | review_due_titles

    return {
        "total": len(all_titles),
        "freshness_count": len(freshness_titles),
        "validity_count": len(validity_titles),
        "review_due_count": len(review_due_titles),
        "story_bank_review_due": due["story_bank"],
        "top": sorted(all_titles)[:8],
    }


def gather_translation_pending_review(env):
    token = env["NOTION_TOKEN"]
    pages = query_database(token, env["TRANSLATION_DB_ID"], filter_obj={
        "property": "Human Review Status", "select": {"equals": "Pending"}
    })
    return {"total": len(pages)}


def gather_publish_pending(env, publishing_queue, sns_pending, translation_pending_review):
    """ARu Studio v4.1 core section 3/3: "公開待ちコンテンツ" -- everything
    sitting in a "ready, waiting on a human" state across the pipeline.
    Takes the already-gathered Articles Ready to Publish (gather_publishing_queue)
    and SNS Queue Drafts (gather_sns_queue_pending) rather than re-querying,
    plus the new Translation "Human Review Status=Pending" count -- pure
    aggregation, no duplicated query logic."""
    return {
        "total": publishing_queue["total"] + sns_pending["total"] + translation_pending_review["total"],
        "articles_ready": publishing_queue["total"],
        "articles_top": publishing_queue["top"],
        "sns_draft": sns_pending["total"],
        "translation_pending": translation_pending_review["total"],
    }


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


def build_page_blocks(opportunities, critical, top_research, publishing_queue, recently_updated,
                       freshness, monitor_stats, pointers, dup_today, source_intel, dashboard_url,
                       content_pipeline, law_update_queue, translation_queue, sns_pending,
                       updates_needed, publish_pending, production_stage):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    blocks = [
        {"heading_1": {"rich_text": rt("🤖 AI Command Center — 編集長の毎日のホーム画面")}},
        {"paragraph": {"rich_text": rt(f"最終更新: {now}（ai_command_center.py）")}},
        {"paragraph": {"rich_text": rt("ARu Studio v4.1: 以下3セクションを中心に構成——今日追加するQA／更新が必要な記事／公開待ちコンテンツ")}},
        {"divider": {}},
    ]

    # CORE 1/3: 今日追加するQA（今日の記事・Deep Guide候補も含む -- 新規コンテンツ制作の活動全体）
    blocks.append({"heading_2": {"rich_text": rt("🆕 今日追加するQA")}})
    blocks.append({"callout": {
        "rich_text": rt(f"本日追加されたStory Bank QA: {len(content_pipeline['new_qa_today'])}件"),
        "icon": {"type": "emoji", "emoji": "🆕" if content_pipeline["new_qa_today"] else "✅"},
    }})
    for t in content_pipeline["new_qa_today"][:5]:
        blocks.append({"bulleted_list_item": {"rich_text": rt(t)}})
    blocks.append({"bulleted_list_item": {"rich_text": rt(f"本日作成された記事: {len(content_pipeline['new_articles_today'])}件")}})
    for t in content_pipeline["new_articles_today"][:5]:
        blocks.append({"bulleted_list_item": {"rich_text": rt(f"　- {t}")}})
    blocks.append({"bulleted_list_item": {"rich_text": rt(f"Deep Guide候補（Deep Article Needed、未着手）: {len(content_pipeline['deep_guide_candidates'])}件")}})
    for t in content_pipeline["deep_guide_candidates"][:5]:
        blocks.append({"bulleted_list_item": {"rich_text": rt(f"　- {t}")}})
    blocks.append({"divider": {}})

    # Production Stage件数表示（Rei指示：件数表示＋カンバン表示）。カンバン（Board View）自体は
    # Notion公開APIで作成不可のため、Studio-v4.1-View-Setup-Guide.mdへ手動設定を委譲し、
    # ここでは件数表示のみ自動化する。
    blocks.append({"heading_2": {"rich_text": rt("📋 Production Stage内訳")}})
    blocks.append({"paragraph": {"rich_text": rt(
        "カンバン表示（Board View）はNotion公開APIで作成できないため手動設定——"
        "Studio-v4.1-View-Setup-Guide.mdの「Articles: Production Stage Kanban」参照。以下は件数表示。"
    )}})
    blocks.append({"heading_3": {"rich_text": rt("Articles")}})
    for stage in PRODUCTION_STAGE_OPTIONS:
        count = production_stage["articles_counts"][stage]
        if count:
            blocks.append({"bulleted_list_item": {"rich_text": rt(f"{stage}: {count}件")}})
    if production_stage["articles_unset"]:
        blocks.append({"bulleted_list_item": {"rich_text": rt(f"（未設定）: {production_stage['articles_unset']}件")}})
    blocks.append({"heading_3": {"rich_text": rt("Story Bank")}})
    for stage in PRODUCTION_STAGE_OPTIONS:
        count = production_stage["story_bank_counts"][stage]
        if count:
            blocks.append({"bulleted_list_item": {"rich_text": rt(f"{stage}: {count}件")}})
    if production_stage["story_bank_unset"]:
        blocks.append({"bulleted_list_item": {"rich_text": rt(f"（未設定）: {production_stage['story_bank_unset']}件")}})
    blocks.append({"divider": {}})

    # CORE 2/3: 更新が必要な記事 -- Freshness Status／Current Validity／Next Review期限の統合ビュー
    blocks.append({"heading_2": {"rich_text": rt("🔴 更新が必要な記事")}})
    blocks.append({"callout": {
        "rich_text": rt(f"合計（重複除く）: {updates_needed['total']}件"),
        "icon": {"type": "emoji", "emoji": "🔴" if updates_needed["total"] else "✅"},
    }})
    blocks.append({"bulleted_list_item": {"rich_text": rt(
        f"内訳 -- Freshness（時間経過）: {updates_needed['freshness_count']}件 / "
        f"Current Validity（法改正等）: {updates_needed['validity_count']}件 / "
        f"定期レビュー期限超過（Next Review）: {updates_needed['review_due_count']}件"
    )}})
    for t in updates_needed["top"]:
        blocks.append({"bulleted_list_item": {"rich_text": rt(t)}})
    if updates_needed["story_bank_review_due"]:
        blocks.append({"bulleted_list_item": {"rich_text": rt(
            f"Story Bank側の定期レビュー期限超過: {len(updates_needed['story_bank_review_due'])}件"
            f"（{'、'.join(updates_needed['story_bank_review_due'][:5])}）"
        )}})
    if translation_queue["total"]:
        blocks.append({"bulleted_list_item": {"rich_text": rt(f"翻訳の再翻訳待ち（Needs Re-Translation）: {translation_queue['total']}件")}})
    blocks.append({"divider": {}})

    # CORE 3/3: 公開待ちコンテンツ -- Articles Ready to Publish／SNS Draft／Translation Pending の統合ビュー
    blocks.append({"heading_2": {"rich_text": rt("🚀 公開待ちコンテンツ")}})
    blocks.append({"callout": {
        "rich_text": rt(f"合計: {publish_pending['total']}件"),
        "icon": {"type": "emoji", "emoji": "🚀" if publish_pending["total"] else "✅"},
    }})
    blocks.append({"bulleted_list_item": {"rich_text": rt(f"記事 Ready to Publish: {publish_pending['articles_ready']}件")}})
    for title in publish_pending["articles_top"]:
        blocks.append({"bulleted_list_item": {"rich_text": rt(f"　- {title}")}})
    blocks.append({"bulleted_list_item": {"rich_text": rt(f"SNS投稿 Draft: {publish_pending['sns_draft']}件")}})
    blocks.append({"bulleted_list_item": {"rich_text": rt(f"翻訳レビュー待ち（Human Review Status=Pending）: {publish_pending['translation_pending']}件")}})
    blocks.append({"divider": {}})

    blocks.append({"paragraph": {"rich_text": rt(
        "ここから下は、上記3セクションの根拠となる詳細（Today's Opportunities・Critical Updates・"
        "Law Update Pipeline・Freshness内訳・重複防止・外部監視・Source Intelligence）です。"
    )}})
    blocks.append({"divider": {}})

    # --- Detail: Today's Opportunities ---
    blocks.append({"heading_2": {"rich_text": rt("🎯 Today's Opportunities")}})
    if opportunities["events"]:
        blocks.append({"heading_3": {"rich_text": rt("直近2週間のイベント")}})
        for e in opportunities["events"]:
            blocks.append({"bulleted_list_item": {"rich_text": rt(f"[{e['type']}] {e['name']}（{e['date']}、{e['location'] or '場所未定'}）")}})
    if opportunities["source_signals"]:
        blocks.append({"heading_3": {"rich_text": rt("本日検知した重要な情報源の変化")}})
        for s in opportunities["source_signals"]:
            blocks.append({"bulleted_list_item": {"rich_text": rt(f"[{s['impact']}/{s['classification'] or '未分類'}] {s['name']}")}})
    if opportunities["law_updates"]:
        blocks.append({"heading_3": {"rich_text": rt("最近Confirmedされた法改正")}})
        for l in opportunities["law_updates"]:
            blocks.append({"bulleted_list_item": {"rich_text": rt(f"[{l['significance']}] {l['name']}（施行日: {l['effective_date'] or '未定'}）")}})
    if opportunities["seasonal_research"]:
        blocks.append({"heading_3": {"rich_text": rt("季節性の高いResearch候補")}})
        for r in opportunities["seasonal_research"]:
            blocks.append({"bulleted_list_item": {"rich_text": rt(f"[{r['total']}点] {r['topic']}")}})
    if not any(opportunities.values()):
        blocks.append({"paragraph": {"rich_text": rt("本日、新たな機会は検知されていません。")}})
    blocks.append({"divider": {}})

    # --- Detail: Critical Updates ---
    blocks.append({"heading_2": {"rich_text": rt("🔴 Critical Updates")}})
    total_critical = len(critical["articles"]) + len(critical["source_changes"]) + len(critical["law_updates"])
    blocks.append({"callout": {
        "rich_text": rt(f"合計: {total_critical}件"),
        "icon": {"type": "emoji", "emoji": "🔴" if total_critical else "✅"},
    }})
    for label, items in (("外部シグナルで要更新フラグの記事", critical["articles"]),
                         ("本日のCritical情報源変化", critical["source_changes"]),
                         ("重要度Majorの未反映法改正", critical["law_updates"])):
        if items:
            blocks.append({"bulleted_list_item": {"rich_text": rt(f"{label}: {len(items)}件（{'、'.join(items[:5])}）")}})
    blocks.append({"divider": {}})

    # --- Detail: Top Research Candidates ---
    blocks.append({"heading_2": {"rich_text": rt("📊 Top Research Candidates")}})
    if top_research:
        for i, s in enumerate(top_research, 1):
            blocks.append({"numbered_list_item": {"rich_text": rt(f"[{s['total']}点] {s['topic']}")}})
    else:
        blocks.append({"paragraph": {"rich_text": rt("Status=NewのResearchはありません。")}})
    blocks.append({"divider": {}})

    # --- Detail: Recently Updated Articles ---
    blocks.append({"heading_2": {"rich_text": rt("🕐 Recently Updated Articles")}})
    for a in recently_updated:
        blocks.append({"bulleted_list_item": {"rich_text": rt(f"{a['title']}（{a['updated'] or '不明'}）")}})
    blocks.append({"divider": {}})

    # --- Detail: Law Update Pipeline queue (covers "情報更新アラート" and "法改正・制度変更") ---
    blocks.append({"heading_2": {"rich_text": rt("⚖️ 法改正・制度変更キュー（Law Update Pipeline）")}})
    if law_update_queue["counts"]:
        breakdown = "、".join(f"{k}: {v}件" for k, v in law_update_queue["counts"].items())
        blocks.append({"bulleted_list_item": {"rich_text": rt(f"内訳: {breakdown}")}})
    else:
        blocks.append({"paragraph": {"rich_text": rt("Law Updateレコードはまだありません。")}})
    if law_update_queue["monitoring"]:
        blocks.append({"bulleted_list_item": {"rich_text": rt(
            f"⚠️ 人間の確認待ち（Monitoring）: {'、'.join(law_update_queue['monitoring'][:5])}"
        )}})
    if law_update_queue["approval_required"]:
        blocks.append({"bulleted_list_item": {"rich_text": rt(
            f"⚠️ 承認待ち（Approval Required）: {'、'.join(law_update_queue['approval_required'][:5])}"
        )}})
    blocks.append({"divider": {}})

    # --- Phase 1/2 detail (unchanged) ---
    blocks.append({"heading_2": {"rich_text": rt("🔴 Freshness 内訳（更新が必要な記事の根拠データ）")}})
    blocks.append({"callout": {
        "rich_text": rt(f"合計: {freshness['total']}件"),
        "icon": {"type": "emoji", "emoji": "🔴" if freshness["total"] else "✅"},
    }})
    blocks.append({"bulleted_list_item": {"rich_text": rt(
        f"外部シグナル起因（法改正・情報源変化・イベント中止）: {freshness['signal_flagged']}件"
    )}})
    blocks.append({"bulleted_list_item": {"rich_text": rt(
        f"時間経過による定期レビュー期限超過: {freshness['time_based_flagged']}件"
    )}})
    if freshness["validity_total"]:
        validity_breakdown = "、".join(f"{k}: {v}件" for k, v in freshness["validity_counts"].items())
        blocks.append({"bulleted_list_item": {"rich_text": rt(
            f"法改正等により事実確認が必要（Current Validity）: {freshness['validity_total']}件（{validity_breakdown}）"
        )}})
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

    blocks.append({"heading_2": {"rich_text": rt("🌐 Source Intelligence")}})
    blocks.append({"bulleted_list_item": {"rich_text": rt(
        f"監視対象ソース数: {source_intel['total_sources']}件（うちActive: {source_intel['active_sources']}件）"
    )}})
    blocks.append({"bulleted_list_item": {"rich_text": rt(f"本日の変化検知: {source_intel['todays_changes']}件")}})
    error_icon = "✅" if not source_intel["errored_sources"] else "⚠️"
    error_text = "なし" if not source_intel["errored_sources"] else "、".join(source_intel["errored_sources"])
    blocks.append({"bulleted_list_item": {"rich_text": rt(f"{error_icon} エラー中のソース: {error_text}")}})
    if source_intel["classification_breakdown"]:
        breakdown_text = "、".join(f"{k}: {v}件" for k, v in source_intel["classification_breakdown"].items())
        blocks.append({"bulleted_list_item": {"rich_text": rt(f"本日の内訳（Update Classification）: {breakdown_text}")}})
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


def print_report(opportunities, critical, top_research, publishing_queue, recently_updated,
                  freshness, monitor_stats, pointers, dup_today, source_intel,
                  content_pipeline, law_update_queue, translation_queue, sns_pending,
                  updates_needed, publish_pending, production_stage):
    print("\n" + "=" * 70)
    print("🤖 AI Command Center — 編集長の毎日のホーム画面")
    print("=" * 70)
    print(f"🎯 Today's Opportunities: events={len(opportunities['events'])} "
          f"source_signals={len(opportunities['source_signals'])} "
          f"law_updates={len(opportunities['law_updates'])} "
          f"seasonal_research={len(opportunities['seasonal_research'])}")
    total_critical = len(critical["articles"]) + len(critical["source_changes"]) + len(critical["law_updates"])
    print(f"🔴 Critical Updates: 合計={total_critical} "
          f"(articles={len(critical['articles'])} source={len(critical['source_changes'])} law={len(critical['law_updates'])})")
    print(f"📊 Top Research Candidates: {len(top_research)}件")
    for s in top_research:
        print(f"    [{s['total']}点] {s['topic']}")
    print(f"🚀 Publishing Queue: {publishing_queue['total']}件")
    print(f"🕐 Recently Updated Articles: {len(recently_updated)}件")
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
    print(f"🆕 今日のQA/記事: QA={len(content_pipeline['new_qa_today'])} 記事={len(content_pipeline['new_articles_today'])} "
          f"Deep Guide候補={len(content_pipeline['deep_guide_candidates'])}")
    print(f"⚖️ Law Update Queue: {law_update_queue['counts']}")
    print(f"🈂️ 翻訳更新待ち: {translation_queue['total']}件")
    print(f"📱 SNS公開待ち: {sns_pending['total']}件")
    print(f"🔴 更新が必要な記事（統合）: {updates_needed['total']}件 "
          f"(freshness={updates_needed['freshness_count']} validity={updates_needed['validity_count']} "
          f"review_due={updates_needed['review_due_count']})")
    print(f"🚀 公開待ちコンテンツ（統合）: {publish_pending['total']}件 "
          f"(articles={publish_pending['articles_ready']} sns={publish_pending['sns_draft']} "
          f"translation={publish_pending['translation_pending']})")
    print(f"📋 Production Stage (Articles): {production_stage['articles_counts']} "
          f"(未設定={production_stage['articles_unset']})")
    print(f"📋 Production Stage (Story Bank): {production_stage['story_bank_counts']} "
          f"(未設定={production_stage['story_bank_unset']})")
    print()


def main():
    env = load_env(ENV_PATH)
    today = datetime.date.today()

    log("Gathering Today's Opportunities...")
    opportunities = gather_opportunities(env, today)

    log("Gathering Critical Updates...")
    critical = gather_critical_updates(env, today)

    log("Gathering Top Research Candidates...")
    top_research, _ = rank_research_candidates(env, limit=TOP_RESEARCH_LIMIT, today=today)

    log("Gathering Publishing Queue...")
    publishing_queue = gather_publishing_queue(env)

    log("Gathering Recently Updated Articles...")
    recently_updated = gather_recently_updated_articles(env)

    log("Gathering freshness breakdown...")
    freshness = gather_freshness_breakdown(env)

    log("Gathering external monitor stats...")
    monitor_stats = gather_monitor_stats(env)

    log("Gathering AI analysis page pointers...")
    pointers = gather_page_pointers(env)

    log("Gathering today's Duplicate Prevention activity...")
    dup_today = gather_duplicate_prevention_today(env)

    log("Gathering Source Intelligence stats...")
    source_intel = gather_source_intelligence(env)

    log("Gathering today's QA/Article production and Deep Guide backlog...")
    content_pipeline = gather_content_pipeline_today(env, today)

    log("Gathering Law Update Pipeline queue...")
    law_update_queue = gather_law_update_queue(env)

    log("Gathering Translation queue...")
    translation_queue = gather_translation_queue(env)

    log("Gathering SNS Queue pending...")
    sns_pending = gather_sns_queue_pending(env)

    log("Gathering Translation pending human review...")
    translation_pending_review = gather_translation_pending_review(env)

    log("Gathering consolidated 更新が必要な記事 (Freshness + Current Validity + Next Review due)...")
    updates_needed = gather_updates_needed(env)

    log("Gathering consolidated 公開待ちコンテンツ (Articles + SNS + Translation)...")
    publish_pending = gather_publish_pending(env, publishing_queue, sns_pending, translation_pending_review)

    log("Gathering Production Stage breakdown...")
    production_stage = gather_production_stage_breakdown(env)

    print_report(opportunities, critical, top_research, publishing_queue, recently_updated,
                 freshness, monitor_stats, pointers, dup_today, source_intel,
                 content_pipeline, law_update_queue, translation_queue, sns_pending,
                 updates_needed, publish_pending, production_stage)

    log("Resolving Dashboard page URL...")
    dashboard_url = get_dashboard_url(env)

    blocks = build_page_blocks(opportunities, critical, top_research, publishing_queue, recently_updated,
                                freshness, monitor_stats, pointers, dup_today, source_intel, dashboard_url,
                                content_pipeline, law_update_queue, translation_queue, sns_pending,
                                updates_needed, publish_pending, production_stage)
    log("Writing AI Command Center Notion page...")
    page_id = write_page(env, blocks)
    log(f"DONE. AI Command Center page: {page_id}")


if __name__ == "__main__":
    main()
