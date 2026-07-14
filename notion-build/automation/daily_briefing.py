"""CLI equivalent of the Dashboard page (editor-in-chief home screen), for use until
linked views are manually embedded in Notion (or as a terminal-based alternative for
Rei / Claude Code).

Section order matches the Dashboard page exactly: (0) articles flagged by the Article
Freshness Monitor, (1)-(4) things awaiting a human decision, (5)-(6) today's plan,
(7)-(9) external signals/monitoring.
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
    monitor_db = env["SOURCE_MONITOR_DB_ID"]
    event_db = env["EVENT_CALENDAR_DB_ID"]
    law_db = env["LAW_UPDATE_DB_ID"]
    sns_db = env["SNS_QUEUE_DB_ID"]

    # 0. Update Needed (Article Freshness Monitor)
    section("🔴 Update Needed")
    stale = query_database(token, articles_db, filter_obj={
        "property": "Freshness Status", "select": {"equals": "Needs Update"}
    }, sorts=[{"property": "Freshness Urgency Score", "direction": "descending"}])
    if not stale:
        print("  (none)")
    for a in stale:
        days = get_prop(a, "Days Since Verification", "number")
        urgency = get_prop(a, "Freshness Urgency Score", "number")
        note = get_prop(a, "Freshness Note", "rich_text")
        print(f"  - [Urgency {urgency}] {get_prop(a, 'Title', 'title')} ({days}日経過)")
        if note:
            print(f"      note: {note}")

    # 1. Publish Approval Pending
    section("① Publish Approval Pending")
    pending = query_database(token, translation_db, filter_obj={
        "property": "Publish Approval", "select": {"equals": "Pending"}
    })
    if not pending:
        print("  (none)")
    for t in pending:
        print(f"  - {get_prop(t, 'Translation Name', 'title')}  [Quality Overall={get_prop(t, 'Quality Overall Score', 'formula')}]")

    # 2. Article Review Waiting
    section("② Article Review Waiting")
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

    # 3. Translation Review Waiting
    section("③ Translation Review Waiting")
    translations = query_database(token, translation_db, filter_obj={
        "property": "Quality Result", "select": {"equals": "Not Reviewed"}
    })
    if not translations:
        print("  (none)")
    for t in translations:
        print(f"  - {get_prop(t, 'Translation Name', 'title')}")

    # 4. SNS Draft Waiting
    section("④ SNS Draft Waiting")
    sns_waiting = query_database(token, sns_db, filter_obj={
        "and": [
            {"property": "Status", "select": {"equals": "Draft"}},
            {"property": "Review Result", "select": {"does_not_equal": "Pass"}},
        ]
    })
    if not sns_waiting:
        print("  (none)")
    for s in sns_waiting:
        print(f"  - [{get_prop(s, 'Platform', 'select')}] {get_prop(s, 'Title', 'title')}")

    # 5. Today's Editorial Calendar
    section("⑤ Today's Editorial Calendar")
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

    # 6. Today's Research
    section("⑥ Today's Research")
    new_research = query_database(token, research_db, filter_obj={
        "property": "Status", "select": {"equals": "New"}
    })
    if not new_research:
        print("  (none)")
    for r in new_research:
        print(f"  - {get_prop(r, 'Topic', 'title')}")

    # 7. Source Monitor Alerts
    section("⑦ Source Monitor Alerts")
    changes = query_database(token, monitor_db, filter_obj={
        "property": "Change Detected", "checkbox": {"equals": True}
    })
    if not changes:
        print("  (none)")
    for c in changes:
        print(f"  - [{get_prop(c, 'Change Type', 'select')}/{get_prop(c, 'Impact Level', 'select')}] {get_prop(c, 'Monitor Entry', 'title')}")

    # 8. Recent Law Updates
    section("⑧ Recent Law Updates")
    laws = query_database(token, law_db)
    if not laws:
        print("  (none)")
    for law in laws:
        print(f"  - [{get_prop(law, 'Significance', 'select')}] {get_prop(law, 'Law Name', 'title')}")

    # 9. Recent Event Calendar
    section("⑨ Recent Event Calendar")
    events = query_database(token, event_db, filter_obj={
        "property": "Status", "select": {"does_not_equal": "Cancelled"}
    })
    if not events:
        print("  (none)")
    for e in events:
        print(f"  - {get_prop(e, 'Event Name', 'title')}")

    print()


if __name__ == "__main__":
    main()
