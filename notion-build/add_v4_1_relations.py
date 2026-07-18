"""ARu Studio v4.1 Editorial Intelligence -- Stage 2: Relations.

Adds only the links that genuinely don't exist anywhere in the graph today
(checked against the live schema dump taken before Stage 1 -- see
docs/Automation-Scripts.md "ARu Studio v4.1" section for the full
existing-relation reuse table). All new relations use dual_property so the
mirror property appears automatically on the target DB, matching the
existing convention (e.g. Story Bank's Generated Article / Related SNS Posts).

New links, closing real gaps in the Source Monitor -> Law Update -> impacted
content pipeline that didn't exist before this session:
  Story Bank    -> Source Library : Related Sources
  Articles      -> Source Library : Related Source
  Source Monitor-> Story Bank     : Related Stories
  Source Monitor-> Articles       : Related Articles   (direct; today only reachable via Research)
  Source Monitor-> Law Update     : Related Law Updates (today Source Monitor has no forward link to Law Update at all)
  Law Update    -> Story Bank     : Affected Stories
  Law Update    -> SNS Queue      : Affected SNS

Idempotent: safe to re-run, skips any relation name already present.
"""
import os
from notion_api import load_env, notion_request

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")


def get_db(token, db_id):
    return notion_request(token, "GET", f"/databases/{db_id}")


def add_relation(token, db_id, db, prop_name, target_db_id):
    if prop_name in db["properties"]:
        return False
    notion_request(token, "PATCH", f"/databases/{db_id}", {
        "properties": {
            prop_name: {
                "relation": {
                    "database_id": target_db_id,
                    "type": "dual_property",
                    "dual_property": {},
                }
            }
        }
    })
    return True


def main():
    env = load_env(ENV_PATH)
    token = env["NOTION_TOKEN"]

    story_bank_id = env["STORY_BANK_DB_ID"]
    articles_id = env["ARTICLES_DB_ID"]
    source_monitor_id = env["SOURCE_MONITOR_DB_ID"]
    law_update_id = env["LAW_UPDATE_DB_ID"]
    source_library_id = env["SOURCE_LIBRARY_DB_ID"]
    sns_queue_id = env["SNS_QUEUE_DB_ID"]

    plan = [
        (story_bank_id, "Story Bank", "Related Sources", source_library_id),
        (articles_id, "Articles", "Related Source", source_library_id),
        (source_monitor_id, "Source Monitor", "Related Stories", story_bank_id),
        (source_monitor_id, "Source Monitor", "Related Articles", articles_id),
        (source_monitor_id, "Source Monitor", "Related Law Updates", law_update_id),
        (law_update_id, "Law Update", "Affected Stories", story_bank_id),
        (law_update_id, "Law Update", "Affected SNS", sns_queue_id),
    ]

    report = []
    for db_id, label, prop_name, target_id in plan:
        db = get_db(token, db_id)
        created = add_relation(token, db_id, db, prop_name, target_id)
        report.append((label, prop_name, created))

    print("=" * 70)
    print("Relations Migration Report -- ARu Studio v4.1 Editorial Intelligence (Stage 2)")
    print("=" * 70)
    for label, prop_name, created in report:
        status = "created" if created else "already existed, skipped"
        print(f"{label}.{prop_name}: {status}")


if __name__ == "__main__":
    main()
