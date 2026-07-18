import os
from notion_api import load_env, notion_request

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")


def main():
    env = load_env(ENV_PATH)
    token = env.get("NOTION_TOKEN", "")
    db_id = env.get("STORY_BANK_DB_ID", "")

    if not token or not db_id:
        print("ERROR: NOTION_TOKEN or STORY_BANK_DB_ID missing in .env")
        return

    db = notion_request(token, "GET", f"/databases/{db_id}")

    print("Renaming 'Region' -> 'Primary Region' (Rei's formal rule: when a Story spans "
          "multiple prefectures, set one Primary Region and put the rest in Notes)...")
    notion_request(token, "PATCH", f"/databases/{db_id}", {
        "properties": {
            "Region": {"name": "Primary Region"},
        }
    })

    print("Adding 'Notes' (rich_text) for Primary Region overflow and other supplementary detail...")
    notion_request(token, "PATCH", f"/databases/{db_id}", {
        "properties": {
            "Notes": {"rich_text": {}},
        }
    })

    print("Adding 'Multiple' as an Event Month option (for events held several times a year -- "
          "never left blank per Rei's rule)...")
    existing_months = db["properties"]["Event Month"]["multi_select"]["options"]
    month_names = [o["name"] for o in existing_months]
    if "Multiple" not in month_names:
        notion_request(token, "PATCH", f"/databases/{db_id}", {
            "properties": {
                "Event Month": {
                    "multi_select": {
                        "options": existing_months + [{"name": "Multiple"}]
                    }
                }
            }
        })
    else:
        print("  'Multiple' already present, skipping.")

    print("DONE.")


if __name__ == "__main__":
    main()
