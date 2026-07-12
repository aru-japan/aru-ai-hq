import os
from notion_api import load_env, notion_request

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")


def main():
    env = load_env(ENV_PATH)
    token = env.get("NOTION_TOKEN", "")
    db_id = env.get("TRANSLATION_DB_ID", "")

    if not token or not db_id:
        print("ERROR: NOTION_TOKEN or TRANSLATION_DB_ID missing in .env")
        return

    print("Adding 'Translation Memory' (rich_text) to Translation database...")
    notion_request(token, "PATCH", f"/databases/{db_id}", {
        "properties": {
            "Translation Memory": {"rich_text": {}}
        }
    })
    print("Property added.")


if __name__ == "__main__":
    main()
