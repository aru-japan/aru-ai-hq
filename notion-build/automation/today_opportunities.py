"""Today's Opportunities -- ARu Intelligence Phase 3 (Editorial Intelligence).

Answers "what should an editor act on today?" by merging four existing
systems into one near-term view -- no new database, no new relation, just
four targeted queries against DBs that already exist:

    Event Calendar  -- festivals/fireworks/food festivals/local events/
                       tourism campaigns happening soon (Event Date within
                       a near-term window, not Cancelled/Completed)
    Source Monitor  -- government announcements / visa updates detected
                       *today* with Critical/High Impact Level
    Law Update      -- visa/regulation changes just Confirmed (not yet
                       reflected into an Article)
    Research        -- seasonal/tourism-relevant candidates from
                       research_prioritizer.py that aren't on the Event
                       Calendar yet (Category=イベント/旅行情報, season match)

Each group is kept separate rather than merged into one artificial
cross-type score -- a festival and a visa policy change aren't comparable on
a single number, and pretending otherwise would hide more than it reveals.
"""
import os
import sys
import datetime

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
REPO_ROOT = os.path.dirname(NOTION_BUILD_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, AUTOMATION_DIR)

from notion_api import load_env, query_database, get_prop  # noqa: E402
from research_prioritizer import rank_research_candidates  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")

EVENT_WINDOW_DAYS = 14
SEASONAL_RESEARCH_CATEGORIES = {"イベント", "旅行情報"}


def gather_upcoming_events(env, today):
    token = env["NOTION_TOKEN"]
    window_end = (today + datetime.timedelta(days=EVENT_WINDOW_DAYS)).isoformat()
    pages = query_database(token, env["EVENT_CALENDAR_DB_ID"], filter_obj={
        "and": [
            {"property": "Status", "select": {"does_not_equal": "Cancelled"}},
            {"property": "Status", "select": {"does_not_equal": "Completed"}},
            {"property": "Event Date", "date": {"on_or_after": today.isoformat()}},
            {"property": "Event Date", "date": {"on_or_before": window_end}},
        ]
    }, sorts=[{"property": "Event Date", "direction": "ascending"}])
    return [{
        "name": get_prop(p, "Event Name", "title"),
        "type": get_prop(p, "Type", "select"),
        "date": get_prop(p, "Event Date", "date"),
        "location": get_prop(p, "Location", "rich_text"),
    } for p in pages]


def gather_todays_source_signals(env, today):
    token = env["NOTION_TOKEN"]
    pages = query_database(token, env["SOURCE_MONITOR_DB_ID"], filter_obj={
        "and": [
            {"property": "Change Detected", "checkbox": {"equals": True}},
            {"property": "Checked At", "date": {"equals": today.isoformat()}},
            {"or": [
                {"property": "Impact Level", "select": {"equals": "Critical"}},
                {"property": "Impact Level", "select": {"equals": "High"}},
            ]},
        ]
    })
    return [{
        "name": get_prop(p, "Monitor Entry", "title"),
        "impact": get_prop(p, "Impact Level", "select"),
        "classification": get_prop(p, "Update Classification", "select"),
        "summary": get_prop(p, "Diff Summary", "rich_text"),
    } for p in pages]


def gather_recent_law_updates(env):
    token = env["NOTION_TOKEN"]
    pages = query_database(token, env["LAW_UPDATE_DB_ID"], filter_obj={
        "property": "Update Status", "select": {"equals": "Confirmed"}
    })
    return [{
        "name": get_prop(p, "Law Name", "title"),
        "significance": get_prop(p, "Significance", "select"),
        "effective_date": get_prop(p, "Effective Date", "date"),
        "summary": get_prop(p, "Impact Summary", "rich_text"),
    } for p in pages]


def gather_seasonal_research_candidates(env, today, limit=5):
    scored, _ = rank_research_candidates(env, limit=50, today=today)
    seasonal_hits = []
    token = env["NOTION_TOKEN"]
    for s in scored:
        page = None
        try:
            from notion_api import notion_request
            page = notion_request(token, "GET", f"/pages/{s['id']}")
        except RuntimeError:
            continue
        category = get_prop(page, "Category", "select")
        seasonal_pts = s["breakdown"]["Seasonal Relevance"][0]
        if category in SEASONAL_RESEARCH_CATEGORIES and seasonal_pts >= 12:
            seasonal_hits.append(s)
        if len(seasonal_hits) >= limit:
            break
    return seasonal_hits


def gather_opportunities(env, today=None):
    today = today or datetime.date.today()
    return {
        "events": gather_upcoming_events(env, today),
        "source_signals": gather_todays_source_signals(env, today),
        "law_updates": gather_recent_law_updates(env),
        "seasonal_research": gather_seasonal_research_candidates(env, today),
    }


def print_report(opportunities):
    print("\n" + "=" * 70)
    print("🎯 Today's Opportunities")
    print("=" * 70)
    print(f"直近{EVENT_WINDOW_DAYS}日以内のイベント: {len(opportunities['events'])}件")
    for e in opportunities["events"]:
        print(f"  - [{e['type']}] {e['name']} ({e['date']}, {e['location']})")
    print(f"本日検知した重要な情報源変化: {len(opportunities['source_signals'])}件")
    for s in opportunities["source_signals"]:
        print(f"  - [{s['impact']}/{s['classification']}] {s['name']}")
    print(f"最近Confirmedされた法改正: {len(opportunities['law_updates'])}件")
    for l in opportunities["law_updates"]:
        print(f"  - [{l['significance']}] {l['name']} (施行日: {l['effective_date']})")
    print(f"季節性の高いResearch候補: {len(opportunities['seasonal_research'])}件")
    for r in opportunities["seasonal_research"]:
        print(f"  - [{r['total']}点] {r['topic']}")
    print()


def main():
    env = load_env(ENV_PATH)
    opportunities = gather_opportunities(env)
    print_report(opportunities)


if __name__ == "__main__":
    main()
