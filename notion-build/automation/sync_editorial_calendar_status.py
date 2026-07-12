"""Editor-in-Chief Agent behavior: when a Linked Article is Published, mark the
corresponding Editorial Calendar entry as Published too.

Roadmap Version 3 item: Editorial Calendar <-> Article status sync.
"""
from _common import get_env, notion_request, query_database, get_prop


def main():
    env = get_env()
    token = env["NOTION_TOKEN"]
    calendar_db_id = env["EDITORIAL_CALENDAR_DB_ID"]

    print("Scanning Editorial Calendar entries not yet marked Published...")
    entries = query_database(token, calendar_db_id, filter_obj={
        "property": "Status", "select": {"does_not_equal": "Published"}
    })
    print(f"Found {len(entries)} non-Published entries.")

    updated = 0
    for entry in entries:
        title = get_prop(entry, "Planned Topic", "title")
        linked_articles = get_prop(entry, "Linked Article", "relation")
        if not linked_articles:
            continue

        for article_id in linked_articles:
            article = notion_request(token, "GET", f"/pages/{article_id}")
            article_status = get_prop(article, "Status", "select")
            if article_status == "Published":
                notion_request(token, "PATCH", f"/pages/{entry['id']}", {
                    "properties": {"Status": {"select": {"name": "Published"}}}
                })
                print(f"  SYNCED to Published: {title}")
                updated += 1
                break

    print(f"DONE. {updated} Editorial Calendar entr(y/ies) synced to Published.")


if __name__ == "__main__":
    main()
