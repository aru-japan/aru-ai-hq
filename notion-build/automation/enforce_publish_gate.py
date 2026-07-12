"""Editor-in-Chief Agent behavior: enforce ARu Constitution Sec.9/10/13 as code.

Any Article that is Status=Published but has NOT actually passed the required gate
(QA Status=Passed, and for Update Level 2/3 also Human Reviewed=true) is reverted to
Human Review and flagged, rather than silently trusted.

Roadmap Version 3 item: encode the Quality Gate / publish gate programmatically.
"""
from _common import get_env, notion_request, query_database, get_prop


def main():
    env = get_env()
    token = env["NOTION_TOKEN"]
    articles_db_id = env["ARTICLES_DB_ID"]

    print("Scanning Published Articles for gate violations...")
    published = query_database(token, articles_db_id, filter_obj={
        "property": "Status", "select": {"equals": "Published"}
    })
    print(f"Found {len(published)} Published article(s).")

    reverted = 0
    for article in published:
        title = get_prop(article, "Title", "title")
        qa_status = get_prop(article, "QA Status", "select")
        human_reviewed = get_prop(article, "Human Reviewed", "checkbox")
        update_level = get_prop(article, "Update Level", "number")

        violations = []
        if qa_status != "Passed":
            violations.append(f"QA Status={qa_status} (expected Passed)")
        if update_level in (2, 3) and not human_reviewed:
            violations.append(f"Update Level {update_level} requires Human Reviewed=true, was false")

        if violations:
            notion_request(token, "PATCH", f"/pages/{article['id']}", {
                "properties": {"Status": {"select": {"name": "Human Review"}}}
            })
            print(f"  REVERTED to Human Review: {title}")
            for v in violations:
                print(f"    - {v}")
            reverted += 1
        else:
            print(f"  OK: {title}")

    print(f"DONE. {reverted} article(s) reverted for gate violations.")


if __name__ == "__main__":
    main()
