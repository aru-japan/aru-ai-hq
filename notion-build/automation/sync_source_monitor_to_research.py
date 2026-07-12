"""Researcher Agent behavior: for Source Monitor entries that detected a change and have
no linked Research yet, create a draft Research record.

Roadmap Version 3 item: "Source変化検知→Research起票".
"""
from _common import get_env, notion_request, query_database, get_prop

IMPACT_TO_EVIDENCE = {
    "Critical": "Reported",
    "High": "Reported",
    "Medium": "AI Suggested",
    "Low": "AI Suggested",
}

CHANGE_TYPE_TO_URGENCY = {
    "Emergency": "Critical",
    "Policy Change": "High",
    "Updated": "Medium",
    "New": "Medium",
    "Deleted": "Low",
}


def main():
    env = get_env()
    token = env["NOTION_TOKEN"]
    monitor_db_id = env["SOURCE_MONITOR_DB_ID"]
    research_db_id = env["RESEARCH_DB_ID"]

    print("Scanning Source Monitor for undetected-but-unresearched changes...")
    entries = query_database(token, monitor_db_id, filter_obj={
        "property": "Change Detected", "checkbox": {"equals": True}
    })
    print(f"Found {len(entries)} entries with Change Detected=true.")

    created = 0
    for entry in entries:
        title = get_prop(entry, "Monitor Entry", "title")
        triggered_research = get_prop(entry, "Triggered Research", "relation")
        if triggered_research:
            print(f"  already has Research: {title}")
            continue

        impact_level = get_prop(entry, "Impact Level", "select") or "Medium"
        change_type = get_prop(entry, "Change Type", "select") or "Updated"
        diff_summary = get_prop(entry, "Diff Summary", "rich_text") or ""
        change_summary = get_prop(entry, "Change Summary", "rich_text") or ""

        research_props = {
            "Topic": {"title": [{"text": {"content": f"[Source Monitor起点] {title}"}}]},
            "Summary": {"rich_text": [{"text": {"content": (change_summary or diff_summary)[:2000]}}]},
            "Evidence Level": {"select": {"name": IMPACT_TO_EVIDENCE.get(impact_level, "AI Suggested")}},
            "Status": {"select": {"name": "New"}},
            "Discovery Method": {"select": {"name": "Source Monitor"}},
            "Urgency": {"select": {"name": CHANGE_TYPE_TO_URGENCY.get(change_type, "Medium")}},
            "AI Generated": {"checkbox": True},
            "Human Reviewed": {"checkbox": False},
        }
        page = notion_request(token, "POST", "/pages", {
            "parent": {"database_id": research_db_id},
            "properties": research_props,
        })
        notion_request(token, "PATCH", f"/pages/{entry['id']}", {
            "properties": {"Triggered Research": {"relation": [{"id": page["id"]}]}}
        })
        print(f"  CREATED Research from: {title} -> {page['id']}")
        created += 1

    print(f"DONE. {created} new Research record(s) created.")


if __name__ == "__main__":
    main()
