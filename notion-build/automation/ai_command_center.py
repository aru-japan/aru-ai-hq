"""ARu Studio v4.2 home screen -- writes directly into the Dashboard page
(formerly wrote to a separate "AI Command Center" page; unified into
Dashboard on 2026-07-19 per Rei's decision to have a single home screen).

**v4.2 "editor-first" redesign (2026-07-19, per the approved Design
Proposal)**: the page is organized into 3 zones of descending priority
instead of a flat list of sections, so opening Dashboard answers "what do I
do today" in about 30 seconds:

  Zone 1 -- ✍️ 今すぐ書く (always expanded, top of page): the single
  highest-priority thing to write next, chosen by gather_write_now()'s
  cascade (resume an in-progress article > start the top Research
  candidate > fall back to a Story Bank idea). The title itself is a real
  Notion hyperlink straight to that record. This satisfies Rei's "3クリック
  以内で記事を書き始められる" requirement: open Dashboard (1) -> the card is
  already visible, nothing to expand (0) -> click the title (1) = 2 clicks
  to the actual Research/Articles/Story Bank page.

  Zone 2 -- 📋 今日の判断 (always expanded): exactly 3 numbers in a 3-column
  layout (🔴 Critical / 🚀 公開判断待ち / 🔧 更新が必要), no lists -- just
  enough to see if anything needs a decision today.

  Zone 3 -- 🔍 詳細・AI監視 (collapsed by default): everything else --
  every count and list Zone 1/2 summarize, plus the AI-facing signal layer
  (Source Monitor, Law Update Pipeline, Production Stage breakdown, Source
  Intelligence, Coverage Analysis/Editorial Planner pointers, Today's
  Opportunities, Critical Updates detail, full Research ranking) -- as one
  small toggle per topic rather than one giant toggle, so Rei can open just
  the one she needs instead of one wall of text. Nothing here is deleted,
  only folded away; the AI-facing databases underneath keep running exactly
  as before.

**Known API limitation (confirmed 2026-07-19 via Notion's own developer
docs, not assumed)**: Rei asked that this redesign lean on Notion's Button
blocks. The Notion public API (version 2022-06-28, same as this whole
codebase) does not support creating Button blocks -- reading an existing
one returns type "unsupported", and there is no way to create one via
POST/PATCH. Real Notion buttons would have to be added by hand in the
Notion UI (same category of manual step as the 13 Linked Views), so this
script instead uses rich_text hyperlinks on ordinary blocks (callout/
paragraph text with a `link`), which the API has always supported reliably
-- functionally the same "click it, it opens the record" outcome. Column
layouts (`column_list`/`column`) ARE supported and are used for Zone 2's
3-number row.

Dashboard's existing 13 manually-configured Linked Database Views (see
docs/Dashboard-Setup-Guide.md) are intentionally left alone -- Rei chose not
to delete them (safety-first during the first weeks of real operation).
Since Notion's public API can only insert blocks via "after: <existing
block id>" (never "before" or "at position 0"), this script's own section is
bounded by two marker callouts (see write_to_dashboard()) so every run can
find and refresh only its own content, wherever Rei has placed it, without
ever touching the Linked Views. The old standalone AI Command Center page is
kept as a backup/reference but is no longer written to.

This page never recomputes Coverage Analysis or Editorial Planner's AI
content itself (that would mean extra AI Gateway calls and a second copy
that can drift from the real page) -- it only points at those existing
pages with light metadata (last-edited time + URL). Everything else here
is a cheap, deterministic, live query against DBs that already exist --
no new database, no schema change, anywhere in this redesign.
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

from notion_api import load_env, notion_request, query_database, get_prop  # noqa: E402
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
# Source Monitor Alerts / Recent Law Updates moved out of this generic list
# in the v4.1 reorder -- they're now their own promoted top-level sections
# (gather_source_monitor_alerts / gather_law_update_queue) with richer
# detail than a bare count, so keeping them here too would just duplicate
# them. Event Calendar has no promoted section of its own, so it stays here.
MONITOR_STAT_DEFS = [
    ("⑨", "Recent Event Calendar", "EVENT_CALENDAR_DB_ID",
     {"property": "Status", "select": {"does_not_equal": "Cancelled"}}),
]

WRITING_STAGES = ["Headline Ready", "Basic Writing", "Deep Writing"]

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


def gather_todays_writing_by_stage(env):
    """ARu Studio v4.1 core section 2/7: "執筆中の記事（Production Stage別）" --
    Articles currently sitting in one of the three writing-in-progress
    stages (Headline Ready/Basic Writing/Deep Writing), grouped by stage.
    Distinct from gather_production_stage_breakdown() (section 5/7), which
    is the full 8-stage pipeline count for both DBs -- this is narrower and
    answers "what should I actually sit down and write today", not "what's
    the overall pipeline state"."""
    token = env["NOTION_TOKEN"]
    articles = query_database(token, env["ARTICLES_DB_ID"])
    by_stage = {s: [] for s in WRITING_STAGES}
    for a in articles:
        stage = get_prop(a, "Production Stage", "select")
        if stage in by_stage:
            by_stage[stage].append(get_prop(a, "Title", "title"))
    return by_stage


def gather_write_now(env):
    """ARu Studio v4.2 Zone 1: the single "next thing to write" for the
    editor-first redesign. Selection cascade, in priority order:
      1. Resume the most-advanced in-progress Article (Deep Writing before
         Basic Writing before Headline Ready -- finishing something close to
         done beats starting something new)
      2. Otherwise start the #1 Research candidate by research_prioritizer.py's
         existing 5-axis score (no new scoring logic)
      3. Otherwise fall back to a Story Bank idea flagged Article Needed with
         no Generated Article yet (manual-authorship path, matches Story
         Bank's operator-guide description -- see add_operator_guide.py)
    Each branch is a minimal, self-contained query; whichever branch fires
    also carries the record's own Notion page URL so the caller can render a
    real hyperlink straight to it (Rei's 2026-07-19 "3クリック以内で書き始め
    られる" requirement)."""
    token = env["NOTION_TOKEN"]
    browse_url = notion_request(token, "GET", f"/databases/{env['RESEARCH_DB_ID']}").get("url")

    for stage in ["Deep Writing", "Basic Writing", "Headline Ready"]:
        pages = query_database(token, env["ARTICLES_DB_ID"], filter_obj={
            "property": "Production Stage", "select": {"equals": stage}
        })
        if pages:
            p = pages[0]
            return {
                "title": get_prop(p, "Title", "title"), "url": p.get("url"),
                "source": "Articles", "meta": f"執筆中・{stage}", "browse_url": browse_url,
            }

    scored, _ = rank_research_candidates(env, limit=1)
    if scored:
        s = scored[0]
        page = notion_request(token, "GET", f"/pages/{s['id']}")
        return {
            "title": s["topic"], "url": page.get("url"),
            "source": "Research", "meta": f"Research候補 1位・スコア{s['total']}点",
            "browse_url": browse_url,
        }

    story_bank = query_database(token, env["STORY_BANK_DB_ID"], filter_obj={
        "and": [
            {"property": "Article Needed", "checkbox": {"equals": True}},
            {"property": "Generated Article", "relation": {"is_empty": True}},
        ]
    })
    if story_bank:
        p = story_bank[0]
        return {
            "title": get_prop(p, "Title", "title"), "url": p.get("url"),
            "source": "Story Bank", "meta": "Story Bank・記事化待ち", "browse_url": browse_url,
        }

    return {"title": None, "url": None, "source": None, "meta": None, "browse_url": browse_url}


def gather_source_monitor_alerts(env, limit=5):
    """ARu Studio v4.1 core section 6/7: "Source Monitor Alerts", promoted
    from the generic MONITOR_STAT_DEFS count into its own section with the
    actual flagged entries (Monitor Entry + Impact Level), matching
    Dashboard-Setup-Guide.md's ⑦ Source Monitor Alerts columns."""
    token = env["NOTION_TOKEN"]
    pages = query_database(token, env["SOURCE_MONITOR_DB_ID"], filter_obj={
        "property": "Change Detected", "checkbox": {"equals": True}
    }, sorts=[{"property": "Checked At", "direction": "descending"}])
    return {
        "total": len(pages),
        "top": [(get_prop(p, "Monitor Entry", "title"), get_prop(p, "Impact Level", "select")) for p in pages[:limit]],
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


def rt(text, link=None):
    obj = {"content": str(text)[:2000]}
    if link:
        obj["link"] = {"url": link}
    return [{"text": obj}]


def _toggle(label, children):
    return {"toggle": {"rich_text": rt(label), "children": children}}


def build_page_blocks(opportunities, critical, top_research, publishing_queue, recently_updated,
                       freshness, monitor_stats, pointers, dup_today, source_intel,
                       content_pipeline, law_update_queue, translation_queue, sns_pending,
                       updates_needed, publish_pending, production_stage,
                       todays_writing, monitor_alerts, write_now):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    blocks = []

    # ================= Zone 1 -- 今すぐ書く (always expanded, top) =================
    blocks.append({"heading_2": {"rich_text": rt("✍️ 今すぐ書く")}})
    if write_now["title"]:
        blocks.append({"callout": {
            "rich_text": rt(write_now["title"], link=write_now["url"]),
            "icon": {"type": "emoji", "emoji": "✍️"},
        }})
        blocks.append({"bulleted_list_item": {"rich_text": rt(f"{write_now['source']}・{write_now['meta']}")}})
    else:
        blocks.append({"callout": {
            "rich_text": rt("今すぐ書ける候補がありません。Researchで新しい候補を検討してください。"),
            "icon": {"type": "emoji", "emoji": "✅"},
        }})
    if write_now["browse_url"]:
        blocks.append({"paragraph": {"rich_text": rt("他の候補を見る（Research）→", link=write_now["browse_url"])}})
    blocks.append({"divider": {}})

    # ================= Zone 2 -- 今日の判断 (always expanded, 3 numbers only) =================
    blocks.append({"heading_2": {"rich_text": rt("📋 今日の判断")}})
    total_critical = len(critical["articles"]) + len(critical["source_changes"]) + len(critical["law_updates"])
    blocks.append({"column_list": {"children": [
        {"column": {"children": [{"callout": {
            "rich_text": rt(f"{total_critical}件\n🔴 Critical"),
            "icon": {"type": "emoji", "emoji": "🔴" if total_critical else "✅"},
        }}]}},
        {"column": {"children": [{"callout": {
            "rich_text": rt(f"{publish_pending['articles_ready']}件\n🚀 公開判断待ち"),
            "icon": {"type": "emoji", "emoji": "🚀" if publish_pending["articles_ready"] else "✅"},
        }}]}},
        {"column": {"children": [{"callout": {
            "rich_text": rt(f"{updates_needed['total']}件\n🔧 更新が必要"),
            "icon": {"type": "emoji", "emoji": "🔧" if updates_needed["total"] else "✅"},
        }}]}},
    ]}})
    blocks.append({"divider": {}})

    # ================= Zone 3 -- 詳細・AI監視 (collapsed, one small toggle per topic) =================
    blocks.append({"heading_2": {"rich_text": rt("🔍 詳細・AI監視")}})
    blocks.append({"paragraph": {"rich_text": rt(
        "普段は開かなくて大丈夫です。Zone 1・2の数字の根拠と、AIが裏側で見ている信号はここに畳んであります。"
    )}})

    qa_children = [{"callout": {
        "rich_text": rt(f"本日追加されたStory Bank QA: {len(content_pipeline['new_qa_today'])}件"),
        "icon": {"type": "emoji", "emoji": "🆕" if content_pipeline["new_qa_today"] else "✅"},
    }}]
    for t in content_pipeline["new_qa_today"][:5]:
        qa_children.append({"bulleted_list_item": {"rich_text": rt(t)}})
    qa_children.append({"bulleted_list_item": {"rich_text": rt(f"本日作成された記事: {len(content_pipeline['new_articles_today'])}件")}})
    for t in content_pipeline["new_articles_today"][:5]:
        qa_children.append({"bulleted_list_item": {"rich_text": rt(f"　- {t}")}})
    qa_children.append({"bulleted_list_item": {"rich_text": rt(f"Deep Guide候補（Deep Article Needed、未着手）: {len(content_pipeline['deep_guide_candidates'])}件")}})
    for t in content_pipeline["deep_guide_candidates"][:5]:
        qa_children.append({"bulleted_list_item": {"rich_text": rt(f"　- {t}")}})
    blocks.append(_toggle("今日追加されたStory Bank QA", qa_children))

    writing_children = []
    total_writing = sum(len(v) for v in todays_writing.values())
    writing_children.append({"callout": {
        "rich_text": rt(f"執筆中・執筆待ち合計: {total_writing}件"),
        "icon": {"type": "emoji", "emoji": "✍" if total_writing else "✅"},
    }})
    for stage in WRITING_STAGES:
        titles = todays_writing[stage]
        writing_children.append({"bulleted_list_item": {"rich_text": rt(f"{stage}: {len(titles)}件")}})
        for t in titles[:5]:
            writing_children.append({"bulleted_list_item": {"rich_text": rt(f"　- {t}")}})
    blocks.append(_toggle("執筆中の記事（Production Stage別）", writing_children))

    updates_children = [{"callout": {
        "rich_text": rt(f"合計（重複除く）: {updates_needed['total']}件"),
        "icon": {"type": "emoji", "emoji": "🔴" if updates_needed["total"] else "✅"},
    }}]
    updates_children.append({"bulleted_list_item": {"rich_text": rt(
        f"内訳 -- Freshness（時間経過）: {updates_needed['freshness_count']}件 / "
        f"Current Validity（法改正等）: {updates_needed['validity_count']}件 / "
        f"定期レビュー期限超過（Next Review）: {updates_needed['review_due_count']}件"
    )}})
    for t in updates_needed["top"]:
        updates_children.append({"bulleted_list_item": {"rich_text": rt(t)}})
    if updates_needed["story_bank_review_due"]:
        updates_children.append({"bulleted_list_item": {"rich_text": rt(
            f"Story Bank側の定期レビュー期限超過: {len(updates_needed['story_bank_review_due'])}件"
            f"（{'、'.join(updates_needed['story_bank_review_due'][:5])}）"
        )}})
    if translation_queue["total"]:
        updates_children.append({"bulleted_list_item": {"rich_text": rt(f"翻訳の再翻訳待ち（Needs Re-Translation）: {translation_queue['total']}件")}})
    blocks.append(_toggle("更新が必要な記事（詳細）", updates_children))

    publish_children = [{"callout": {
        "rich_text": rt(f"合計: {publish_pending['total']}件"),
        "icon": {"type": "emoji", "emoji": "🚀" if publish_pending["total"] else "✅"},
    }}]
    publish_children.append({"bulleted_list_item": {"rich_text": rt(f"記事 Ready to Publish: {publish_pending['articles_ready']}件")}})
    for title in publish_pending["articles_top"]:
        publish_children.append({"bulleted_list_item": {"rich_text": rt(f"　- {title}")}})
    publish_children.append({"bulleted_list_item": {"rich_text": rt(f"SNS投稿 Draft: {publish_pending['sns_draft']}件")}})
    publish_children.append({"bulleted_list_item": {"rich_text": rt(f"翻訳レビュー待ち（Human Review Status=Pending）: {publish_pending['translation_pending']}件")}})
    blocks.append(_toggle("公開待ちコンテンツ（詳細）", publish_children))

    stage_children = [{"paragraph": {"rich_text": rt(
        "カンバン表示（Board View）はNotion公開APIで作成できないため手動設定——"
        "Studio-v4.1-View-Setup-Guide.mdの「Production Stage Kanban」参照。以下は件数表示。"
    )}}, {"heading_3": {"rich_text": rt("Articles")}}]
    for stage in PRODUCTION_STAGE_OPTIONS:
        count = production_stage["articles_counts"][stage]
        if count:
            stage_children.append({"bulleted_list_item": {"rich_text": rt(f"{stage}: {count}件")}})
    if production_stage["articles_unset"]:
        stage_children.append({"bulleted_list_item": {"rich_text": rt(f"（未設定）: {production_stage['articles_unset']}件")}})
    stage_children.append({"heading_3": {"rich_text": rt("Story Bank")}})
    for stage in PRODUCTION_STAGE_OPTIONS:
        count = production_stage["story_bank_counts"][stage]
        if count:
            stage_children.append({"bulleted_list_item": {"rich_text": rt(f"{stage}: {count}件")}})
    if production_stage["story_bank_unset"]:
        stage_children.append({"bulleted_list_item": {"rich_text": rt(f"（未設定）: {production_stage['story_bank_unset']}件")}})
    blocks.append(_toggle("Production Stage内訳", stage_children))

    monitor_children = [{"callout": {
        "rich_text": rt(f"Change Detected: {monitor_alerts['total']}件"),
        "icon": {"type": "emoji", "emoji": "📡" if monitor_alerts["total"] else "✅"},
    }}]
    for name, impact in monitor_alerts["top"]:
        monitor_children.append({"bulleted_list_item": {"rich_text": rt(f"[{impact or '未分類'}] {name}")}})
    blocks.append(_toggle("Source Monitor Alerts", monitor_children))

    law_children = []
    if law_update_queue["counts"]:
        breakdown = "、".join(f"{k}: {v}件" for k, v in law_update_queue["counts"].items())
        law_children.append({"bulleted_list_item": {"rich_text": rt(f"内訳: {breakdown}")}})
    else:
        law_children.append({"paragraph": {"rich_text": rt("Law Updateレコードはまだありません。")}})
    if law_update_queue["monitoring"]:
        law_children.append({"bulleted_list_item": {"rich_text": rt(
            f"⚠️ 人間の確認待ち（Monitoring）: {'、'.join(law_update_queue['monitoring'][:5])}"
        )}})
    if law_update_queue["approval_required"]:
        law_children.append({"bulleted_list_item": {"rich_text": rt(
            f"⚠️ 承認待ち（Approval Required）: {'、'.join(law_update_queue['approval_required'][:5])}"
        )}})
    blocks.append(_toggle("Law Update Pipeline", law_children))

    opp_children = []
    if opportunities["events"]:
        opp_children.append({"heading_3": {"rich_text": rt("直近2週間のイベント")}})
        for e in opportunities["events"]:
            opp_children.append({"bulleted_list_item": {"rich_text": rt(f"[{e['type']}] {e['name']}（{e['date']}、{e['location'] or '場所未定'}）")}})
    if opportunities["source_signals"]:
        opp_children.append({"heading_3": {"rich_text": rt("本日検知した重要な情報源の変化")}})
        for s in opportunities["source_signals"]:
            opp_children.append({"bulleted_list_item": {"rich_text": rt(f"[{s['impact']}/{s['classification'] or '未分類'}] {s['name']}")}})
    if opportunities["law_updates"]:
        opp_children.append({"heading_3": {"rich_text": rt("最近Confirmedされた法改正")}})
        for l in opportunities["law_updates"]:
            opp_children.append({"bulleted_list_item": {"rich_text": rt(f"[{l['significance']}] {l['name']}（施行日: {l['effective_date'] or '未定'}）")}})
    if opportunities["seasonal_research"]:
        opp_children.append({"heading_3": {"rich_text": rt("季節性の高いResearch候補")}})
        for r in opportunities["seasonal_research"]:
            opp_children.append({"bulleted_list_item": {"rich_text": rt(f"[{r['total']}点] {r['topic']}")}})
    if not any(opportunities.values()):
        opp_children.append({"paragraph": {"rich_text": rt("本日、新たな機会は検知されていません。")}})
    blocks.append(_toggle("🎯 Today's Opportunities", opp_children))

    critical_children = [{"callout": {
        "rich_text": rt(f"合計: {total_critical}件"),
        "icon": {"type": "emoji", "emoji": "🔴" if total_critical else "✅"},
    }}]
    for label, items in (("外部シグナルで要更新フラグの記事", critical["articles"]),
                         ("本日のCritical情報源変化", critical["source_changes"]),
                         ("重要度Majorの未反映法改正", critical["law_updates"])):
        if items:
            critical_children.append({"bulleted_list_item": {"rich_text": rt(f"{label}: {len(items)}件（{'、'.join(items[:5])}）")}})
    blocks.append(_toggle("🔴 Critical Updates（詳細）", critical_children))

    research_children = []
    if top_research:
        for s in top_research:
            research_children.append({"numbered_list_item": {"rich_text": rt(f"[{s['total']}点] {s['topic']}")}})
    else:
        research_children.append({"paragraph": {"rich_text": rt("Status=NewのResearchはありません。")}})
    blocks.append(_toggle("Top Research Candidates（全件）", research_children))

    recent_children = [{"bulleted_list_item": {"rich_text": rt(f"{a['title']}（{a['updated'] or '不明'}）")}} for a in recently_updated]
    blocks.append(_toggle("🕐 Recently Updated Articles", recent_children))

    freshness_children = [{"callout": {
        "rich_text": rt(f"合計: {freshness['total']}件"),
        "icon": {"type": "emoji", "emoji": "🔴" if freshness["total"] else "✅"},
    }}]
    freshness_children.append({"bulleted_list_item": {"rich_text": rt(
        f"外部シグナル起因（法改正・情報源変化・イベント中止）: {freshness['signal_flagged']}件"
    )}})
    freshness_children.append({"bulleted_list_item": {"rich_text": rt(
        f"時間経過による定期レビュー期限超過: {freshness['time_based_flagged']}件"
    )}})
    if freshness["validity_total"]:
        validity_breakdown = "、".join(f"{k}: {v}件" for k, v in freshness["validity_counts"].items())
        freshness_children.append({"bulleted_list_item": {"rich_text": rt(
            f"法改正等により事実確認が必要（Current Validity）: {freshness['validity_total']}件（{validity_breakdown}）"
        )}})
    blocks.append(_toggle("Freshness 内訳（更新が必要な記事の根拠データ）", freshness_children))

    dup_children = [
        {"bulleted_list_item": {"rich_text": rt(f"本日の生成件数: {dup_today['generated']}件")}},
        {"bulleted_list_item": {"rich_text": rt(f"本日の重複スキップ件数: {dup_today['skipped']}件")}},
    ]
    blocks.append(_toggle("🛡 Duplicate Prevention（本日）", dup_children))

    monitor_stats_children = [
        {"bulleted_list_item": {"rich_text": rt(f"{'✅' if s['count'] == 0 else '🔔'} {s['emoji']} {s['label']}: {s['count']}件")}}
        for s in monitor_stats
    ]
    blocks.append(_toggle("📅 その他の外部監視（Event Calendar）", monitor_stats_children))

    intel_children = [{"bulleted_list_item": {"rich_text": rt(
        f"監視対象ソース数: {source_intel['total_sources']}件（うちActive: {source_intel['active_sources']}件）"
    )}}, {"bulleted_list_item": {"rich_text": rt(f"本日の変化検知: {source_intel['todays_changes']}件")}}]
    error_icon = "✅" if not source_intel["errored_sources"] else "⚠️"
    error_text = "なし" if not source_intel["errored_sources"] else "、".join(source_intel["errored_sources"])
    intel_children.append({"bulleted_list_item": {"rich_text": rt(f"{error_icon} エラー中のソース: {error_text}")}})
    if source_intel["classification_breakdown"]:
        breakdown_text = "、".join(f"{k}: {v}件" for k, v in source_intel["classification_breakdown"].items())
        intel_children.append({"bulleted_list_item": {"rich_text": rt(f"本日の内訳（Update Classification）: {breakdown_text}")}})
    blocks.append(_toggle("🌐 Source Intelligence", intel_children))

    pointer_children = []
    for p in pointers:
        if p["url"]:
            pointer_children.append({"paragraph": {"rich_text": rt(f"{p['label']}（最終更新: {p['last_edited']}） →", link=p["url"])}})
        else:
            pointer_children.append({"paragraph": {"rich_text": rt(f"{p['label']}: 未作成（対応スクリプトを一度実行してください）")}})
    blocks.append(_toggle("🧭 AI分析ページへのリンク", pointer_children))

    blocks.append({"divider": {}})

    # 運営ガイド（初回セットアップ向け説明。折りたたみ、毎日は開かなくてよい）
    blocks.append({"toggle": {
        "rich_text": rt("📖 運営ガイド（初回セットアップ内容 -- 毎日確認する必要はありません）"),
        "children": [
            {"heading_1": {"rich_text": rt("🤖 AI Command Center — 編集長の毎日のホーム画面")}},
            {"paragraph": {"rich_text": rt(f"最終更新: {now}（ai_command_center.py）")}},
            {"paragraph": {"rich_text": rt(
                "役割：ARu Studio運営の毎日のホーム画面。編集長が3クリック以内で執筆を始められることを最優先に設計"
            )}},
            {"paragraph": {"rich_text": rt("使うタイミング：毎日、作業を始める一番最初")}},
            {"paragraph": {"rich_text": rt(
                "担当：AI（自動集計・毎朝の実行で最新化、Zone 1の候補選定も含む）＋人（内容を見て判断・実際の作業へ進む）"
            )}},
            {"paragraph": {"rich_text": rt(
                "確認する順番：① ✍️ 今すぐ書く（そのままクリックして着手）② 📋 今日の判断（3つの数字に問題がないか）"
                "③ 必要なときだけ 🔍 詳細・AI監視 を開く"
            )}},
            {"paragraph": {"rich_text": rt(
                "次の作業：\n① の記事タイトルをクリックすると、Research／Articles／Story Bankの該当ページが直接開きます。"
            )}},
        ],
    }})

    return blocks


# ARu Studio v4.1 (2026-07-19, home screen unification): Rei decided Dashboard
# (the manually-configured 13-Linked-View page) becomes the single home
# screen, absorbing AI Command Center's role -- but the 13 Linked Views stay
# (Rei chose not to delete them; safety-first during the first weeks of real
# operation, cleanup deferred to later). Notion's public API can insert
# blocks only via "after: <existing block id>", never "before" or "at
# position 0" -- so this section can't be forced to the very top
# automatically. Instead it's bounded by two stable marker callouts
# (MARKER_START/MARKER_END) that persist across runs regardless of where
# Rei has dragged them: every run finds the markers, deletes only what's
# between them, and reinserts fresh content right after MARKER_START,
# leaving everything else on the page (the 13 Linked Views, their headers)
# completely untouched. On the very first run (no markers yet) the whole
# section is appended at the bottom, and Rei does one manual drag to move it
# to the top -- a single action, not 13.
#
# The old standalone AI Command Center page (AI_COMMAND_CENTER_PAGE_ID) is
# intentionally left alone from this point on -- not deleted, not archived,
# simply no longer written to (Rei's choice: keep it as a backup/reference
# during the transition).
MARKER_START = "🤖 AI Command Center（自動生成セクション開始 -- 以下は毎回自動更新されます。手動編集しないでください）"
MARKER_END = "🤖 AI Command Center（自動生成セクション終了）"


def _block_plain_text(b):
    rt_list = b.get(b["type"], {}).get("rich_text")
    if not rt_list:
        return None
    return "".join(x.get("plain_text", "") for x in rt_list)


def _append_children(token, page_id, children_batch, after=None):
    body = {"children": children_batch}
    if after:
        body["after"] = after
    result = notion_request(token, "PATCH", f"/blocks/{page_id}/children", body)
    results = result.get("results") or []
    return results[-1]["id"] if results else after


def _fetch_all_children(token, page_id):
    """Paginated children fetch -- the Dashboard page exceeds 100 top-level
    blocks once this section is appended (13 Linked Views + this section),
    so a single page_size=100 call would silently miss the END marker on
    later runs and cause a duplicate section to be appended each time."""
    all_blocks = []
    cursor = None
    while True:
        url = f"/blocks/{page_id}/children?page_size=100"
        if cursor:
            url += f"&start_cursor={cursor}"
        resp = notion_request(token, "GET", url)
        all_blocks.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return all_blocks


def write_to_dashboard(env, blocks):
    token = env["NOTION_TOKEN"]
    page_id = env["DASHBOARD_PAGE_ID"]

    results = _fetch_all_children(token, page_id)

    start_idx = end_idx = None
    for i, b in enumerate(results):
        text = _block_plain_text(b)
        if text == MARKER_START:
            start_idx = i
        elif text == MARKER_END:
            end_idx = i

    if start_idx is not None and end_idx is not None and end_idx > start_idx:
        log(f"  Found existing markers (start={start_idx}, end={end_idx}); refreshing in place.")
        for b in results[start_idx + 1:end_idx]:
            notion_request(token, "DELETE", f"/blocks/{b['id']}")
        anchor = results[start_idx]["id"]
        for i in range(0, len(blocks), 90):
            anchor = _append_children(token, page_id, blocks[i:i + 90], after=anchor)
    else:
        log("  No existing markers found; appending new section to the BOTTOM of Dashboard "
            "(existing Linked Views untouched). Move this section (between the two 🤖 marker "
            "callouts) to the top once, manually -- future runs refresh it in place.")
        start_marker = {"callout": {"rich_text": rt(MARKER_START), "icon": {"type": "emoji", "emoji": "🤖"}}}
        end_marker = {"callout": {"rich_text": rt(MARKER_END), "icon": {"type": "emoji", "emoji": "🤖"}}}
        all_new = [start_marker] + blocks + [end_marker]
        for i in range(0, len(all_new), 90):
            _append_children(token, page_id, all_new[i:i + 90])

    return page_id


def print_report(opportunities, critical, top_research, publishing_queue, recently_updated,
                  freshness, monitor_stats, pointers, dup_today, source_intel,
                  content_pipeline, law_update_queue, translation_queue, sns_pending,
                  updates_needed, publish_pending, production_stage,
                  todays_writing, monitor_alerts, write_now):
    print("\n" + "=" * 70)
    print("🤖 AI Command Center — 編集長の毎日のホーム画面")
    print("=" * 70)
    print(f"✍️ 今すぐ書く: {write_now['source']}・{write_now['title']} ({write_now['meta']})"
          if write_now["title"] else "✍️ 今すぐ書く: 候補なし")
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
    print(f"✍ 今日作る記事（Production Stage別）: "
          + ", ".join(f"{stage}={len(titles)}" for stage, titles in todays_writing.items()))
    print(f"📡 Source Monitor Alerts: {monitor_alerts['total']}件")
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

    log("Gathering today's writing by Production Stage...")
    todays_writing = gather_todays_writing_by_stage(env)

    log("Gathering Source Monitor Alerts...")
    monitor_alerts = gather_source_monitor_alerts(env)

    log("Selecting Zone 1 'write now' candidate (resume in-progress > top Research > Story Bank)...")
    write_now = gather_write_now(env)

    print_report(opportunities, critical, top_research, publishing_queue, recently_updated,
                 freshness, monitor_stats, pointers, dup_today, source_intel,
                 content_pipeline, law_update_queue, translation_queue, sns_pending,
                 updates_needed, publish_pending, production_stage,
                 todays_writing, monitor_alerts, write_now)

    blocks = build_page_blocks(opportunities, critical, top_research, publishing_queue, recently_updated,
                                freshness, monitor_stats, pointers, dup_today, source_intel,
                                content_pipeline, law_update_queue, translation_queue, sns_pending,
                                updates_needed, publish_pending, production_stage,
                                todays_writing, monitor_alerts, write_now)
    log("Writing v4.2 editor-first section to Dashboard (3-zone redesign -- old standalone AI Command "
        "Center page is intentionally left untouched, per Rei's decision)...")
    page_id = write_to_dashboard(env, blocks)
    log(f"DONE. Dashboard page: {page_id}")


if __name__ == "__main__":
    main()
