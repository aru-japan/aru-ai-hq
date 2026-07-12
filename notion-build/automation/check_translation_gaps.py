"""Translator Agent behavior: detect Translation records whose parent Article has been
updated more recently than the last source check, and flag Needs Re-Translation.

Roadmap Version 3 item: "Needs Re-Translationの自動検知".
"""
import datetime
from _common import get_env, notion_request, query_database, get_prop

TODAY = datetime.date.today().isoformat()


def main():
    env = get_env()
    token = env["NOTION_TOKEN"]
    translation_db_id = env["TRANSLATION_DB_ID"]

    print("Scanning Translation records...")
    translations = query_database(token, translation_db_id)
    print(f"Found {len(translations)} Translation record(s).")

    flagged = 0
    for t in translations:
        title = get_prop(t, "Translation Name", "title")
        source_updated_at = get_prop(t, "Source Updated At", "rollup")
        last_source_check = get_prop(t, "Last Source Check", "date")
        already_flagged = get_prop(t, "Needs Re-Translation", "checkbox")

        needs_check = False
        if source_updated_at:
            if not last_source_check or source_updated_at > last_source_check:
                needs_check = True

        if needs_check and not already_flagged:
            notion_request(token, "PATCH", f"/pages/{t['id']}", {
                "properties": {
                    "Needs Re-Translation": {"checkbox": True},
                }
            })
            print(f"  FLAGGED: {title} (Source Updated At={source_updated_at}, Last Source Check={last_source_check})")
            flagged += 1
        elif needs_check and already_flagged:
            print(f"  already flagged: {title}")
        else:
            print(f"  up to date: {title}")

    print(f"DONE. {flagged} record(s) newly flagged for re-translation.")


if __name__ == "__main__":
    main()
