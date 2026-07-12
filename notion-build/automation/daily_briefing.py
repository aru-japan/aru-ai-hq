"""CLI equivalent of the Dashboard page's 8 sections, for use until linked views are
manually embedded in Notion (or as a terminal-based alternative for Rei / Claude Code).

Roadmap Version 3 item: a working "Today's Briefing" without needing new DBs.
"""
from _common import get_env, query_database, get_prop


def section(title):
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def main():
    env = get_env()
    token = env["NOTION_TOKEN"]

    articles_db = env["ARTICLES_DB_ID"]
    research_db = env["RESEARCH_DB_ID"]
    translation_db = env["TRANSLATION_DB_ID"]
    calendar_db = env["EDITORIAL_CALENDAR_DB_ID"]
    ei_db = env["EXPERIENCE_INTELLIGENCE_DB_ID"]
    monitor_db = env["SOURCE_MONITOR_DB_ID"]
    event_db = env["EVENT_CALENDAR_DB_ID"]

    # 1. Today's Opportunities
    section("Today's Opportunities")
    opps = query_database(token, ei_db, filter_obj={
        "and": [
            {"property": "Intelligence Type", "select": {"equals": "Opportunity"}},
            {"property": "Status", "select": {"does_not_equal": "Resolved"}},
        ]
    })
    if not opps:
        print("  (none)")
    for o in opps:
        print(f"  - {get_prop(o, 'Title', 'title')}  [Score={get_prop(o, 'Opportunity Score', 'number')}]")

    # 2. Knowledge Gaps
    section("Knowledge Gaps")
    gaps = query_database(token, ei_db, filter_obj={
        "and": [
            {"property": "Intelligence Type", "select": {"equals": "Gap"}},
            {"property": "Status", "select": {"equals": "New"}},
        ]
    })
    if not gaps:
        print("  (none)")
    for g in gaps:
        gap_type = get_prop(g, "Gap Type", "select")
        marker = " *** LEGAL ***" if gap_type == "Legal Gap" else ""
        print(f"  - [{gap_type}] {get_prop(g, 'Title', 'title')}{marker}")

    # 3. Critical Updates
    section("Critical Updates")
    critical = query_database(token, ei_db, filter_obj={
        "property": "Urgency", "select": {"equals": "Critical"}
    })
    if not critical:
        print("  (none)")
    for c in critical:
        print(f"  - [{get_prop(c, 'Intelligence Type', 'select')}] {get_prop(c, 'Title', 'title')}")

    # 4. Translation Queue
    section("Translation Queue")
    translations = query_database(token, translation_db, filter_obj={
        "or": [
            {"property": "Needs Re-Translation", "checkbox": {"equals": True}},
            {"property": "AI Translation Status", "select": {"equals": "Queued"}},
        ]
    })
    if not translations:
        print("  (none)")
    for t in translations:
        print(f"  - {get_prop(t, 'Translation Name', 'title')}")

    # 5. Today's Editorial Tasks
    section("Today's Editorial Tasks")
    tasks = query_database(token, calendar_db, filter_obj={
        "or": [
            {"property": "Status", "select": {"equals": "Idea"}},
            {"property": "Status", "select": {"equals": "Planned"}},
            {"property": "Status", "select": {"equals": "In Progress"}},
        ]
    })
    if not tasks:
        print("  (none)")
    for t in tasks:
        print(f"  - [{get_prop(t, 'Status', 'select')}] {get_prop(t, 'Planned Topic', 'title')}")

    # 6. Articles Awaiting Review
    section("Articles Awaiting Review")
    awaiting = query_database(token, articles_db, filter_obj={
        "or": [
            {"property": "Status", "select": {"equals": "AI Draft"}},
            {"property": "Status", "select": {"equals": "Human Review"}},
        ]
    })
    if not awaiting:
        print("  (none)")
    for a in awaiting:
        print(f"  - [{get_prop(a, 'Status', 'select')}] {get_prop(a, 'Title', 'title')}")

    # 7. Upcoming Events
    section("Upcoming Events")
    events = query_database(token, event_db, filter_obj={
        "property": "Status", "select": {"does_not_equal": "Cancelled"}
    })
    if not events:
        print("  (none)")
    for e in events:
        print(f"  - {get_prop(e, 'Event Name', 'title')}")

    # 8. Recent Source Changes
    section("Recent Source Changes")
    changes = query_database(token, monitor_db, filter_obj={
        "property": "Change Detected", "checkbox": {"equals": True}
    })
    if not changes:
        print("  (none)")
    for c in changes:
        print(f"  - [{get_prop(c, 'Change Type', 'select')}/{get_prop(c, 'Impact Level', 'select')}] {get_prop(c, 'Monitor Entry', 'title')}")

    print()


if __name__ == "__main__":
    main()
