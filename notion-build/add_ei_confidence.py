import os
from notion_api import load_env, notion_request

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")


def main():
    env = load_env(ENV_PATH)
    token = env.get("NOTION_TOKEN", "")
    db_id = env.get("EXPERIENCE_INTELLIGENCE_DB_ID", "")

    if not token or not db_id:
        print("ERROR: NOTION_TOKEN or EXPERIENCE_INTELLIGENCE_DB_ID missing in .env")
        return

    print("Adding 'Confidence Score' and 'Source Confidence' to Experience Intelligence...")
    notion_request(token, "PATCH", f"/databases/{db_id}", {
        "properties": {
            "Confidence Score": {"number": {"format": "number"}},
            "Source Confidence": {"number": {"format": "number"}},
        }
    })
    print("Properties added.")


if __name__ == "__main__":
    main()
