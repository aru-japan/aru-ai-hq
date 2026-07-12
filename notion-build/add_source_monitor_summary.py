import os
from notion_api import load_env, notion_request

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")


def main():
    env = load_env(ENV_PATH)
    token = env.get("NOTION_TOKEN", "")
    db_id = env.get("SOURCE_MONITOR_DB_ID", "")

    if not token or not db_id:
        print("ERROR: NOTION_TOKEN or SOURCE_MONITOR_DB_ID missing in .env")
        return

    print("Adding 'Change Summary' (rich_text) to Source Monitor...")
    notion_request(token, "PATCH", f"/databases/{db_id}", {
        "properties": {"Change Summary": {"rich_text": {}}}
    })
    print("Property added.")


if __name__ == "__main__":
    main()
