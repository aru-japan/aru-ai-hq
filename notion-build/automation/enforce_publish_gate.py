"""Editor-in-Chief Agent behavior: enforce ARu Constitution Sec.9/10/13 as code.

Any Article that is Status=Published but has NOT actually passed the required gate
(QA Status=Passed, Review Result=Pass for Update Level >= 2, and Human Reviewed=true
for Update Level 2/3) is reverted to Human Review and flagged, rather than silently
trusted.

Publishing Center (Version 4 Phase 3) addition: Publishing Status=Published is now
the actually-used "this is live in the ARu app" signal (Status=Published was never
reached by any real article -- see docs/Automation-Scripts.md for the responsibility
split). The same gate is enforced there too, reverting to Publishing Status=Needs
Update on violation, which is the existing "needs attention" state the Freshness
Monitor / Publishing Center already use -- not a new state invented here.

Roadmap Version 3 item: encode the Quality Gate / publish gate programmatically.
Phase B3.8 addition: also enforce the Reviewer Agent's 5-dimension Review Result.
"""
import datetime
from _common import get_env, notion_request, query_database, get_prop


def check_gate_violations(article):
    qa_status = get_prop(article, "QA Status", "select")
    human_reviewed = get_prop(article, "Human Reviewed", "checkbox")
    update_level = get_prop(article, "Update Level", "number")
    review_result = get_prop(article, "Review Result", "select")

    violations = []
    if qa_status != "Passed":
        violations.append(f"QA Status={qa_status} (expected Passed)")
    if update_level in (2, 3) and not human_reviewed:
        violations.append(f"Update Level {update_level} requires Human Reviewed=true, was false")
    if update_level in (2, 3) and review_result != "Pass":
        violations.append(f"Update Level {update_level} requires Review Result=Pass, was {review_result} (Reviewer Agent gate, Phase B3.8)")
    return violations


def main():
    env = get_env()
    token = env["NOTION_TOKEN"]
    articles_db_id = env["ARTICLES_DB_ID"]
    today = datetime.date.today().isoformat()

    print("Scanning Status=Published Articles for gate violations...")
    published = query_database(token, articles_db_id, filter_obj={
        "property": "Status", "select": {"equals": "Published"}
    })
    print(f"Found {len(published)} Article(s) with Status=Published.")

    reverted = 0
    for article in published:
        title = get_prop(article, "Title", "title")
        violations = check_gate_violations(article)
        if violations:
            notion_request(token, "PATCH", f"/pages/{article['id']}", {
                "properties": {"Status": {"select": {"name": "Human Review"}}}
            })
            print(f"  REVERTED Status to Human Review: {title}")
            for v in violations:
                print(f"    - {v}")
            reverted += 1
        else:
            print(f"  OK: {title}")

    print("\nScanning Publishing Status=Published Articles for gate violations...")
    pub_published = query_database(token, articles_db_id, filter_obj={
        "property": "Publishing Status", "select": {"equals": "Published"}
    })
    print(f"Found {len(pub_published)} Article(s) with Publishing Status=Published.")

    pub_reverted = 0
    for article in pub_published:
        title = get_prop(article, "Title", "title")
        violations = check_gate_violations(article)
        if violations:
            notion_request(token, "PATCH", f"/pages/{article['id']}", {
                "properties": {
                    "Publishing Status": {"select": {"name": "Needs Update"}},
                    "Previous Publishing Status": {"select": {"name": "Published"}},
                    "Publishing Status Updated Date": {"date": {"start": today}},
                }
            })
            print(f"  REVERTED Publishing Status to Needs Update: {title}")
            for v in violations:
                print(f"    - {v}")
            pub_reverted += 1
        else:
            print(f"  OK: {title}")

    print(f"\nDONE. {reverted} article(s) reverted via Status, {pub_reverted} article(s) reverted via Publishing Status.")


if __name__ == "__main__":
    main()
