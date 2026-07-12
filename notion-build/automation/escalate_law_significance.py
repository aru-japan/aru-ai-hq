"""Editor-in-Chief Agent behavior: when a Law Update is Significance=Major, escalate the
Urgency of every Affected Article to Critical.

Roadmap Version 2/3 item: Law Update -> Article urgency propagation
(ARu Constitution Update Level 3 escalation logic).
"""
from _common import get_env, notion_request, query_database, get_prop


def main():
    env = get_env()
    token = env["NOTION_TOKEN"]
    law_update_db_id = env["LAW_UPDATE_DB_ID"]

    print("Scanning Law Update for Significance=Major...")
    majors = query_database(token, law_update_db_id, filter_obj={
        "property": "Significance", "select": {"equals": "Major"}
    })
    print(f"Found {len(majors)} Major law update(s).")

    escalated = 0
    for law in majors:
        law_name = get_prop(law, "Law Name", "title")
        affected_articles = get_prop(law, "Affected Articles", "relation")
        if not affected_articles:
            print(f"  no Affected Articles linked: {law_name}")
            continue

        for article_id in affected_articles:
            article = notion_request(token, "GET", f"/pages/{article_id}")
            current_urgency = get_prop(article, "Urgency", "select")
            title = get_prop(article, "Title", "title")
            if current_urgency == "Critical":
                print(f"  already Critical: {title}")
                continue
            notion_request(token, "PATCH", f"/pages/{article_id}", {
                "properties": {"Urgency": {"select": {"name": "Critical"}}}
            })
            print(f"  ESCALATED to Critical: {title} (was {current_urgency}, due to '{law_name}')")
            escalated += 1

    print(f"DONE. {escalated} article(s) escalated to Urgency=Critical.")


if __name__ == "__main__":
    main()
