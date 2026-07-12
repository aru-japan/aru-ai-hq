import os
from notion_api import load_env, notion_request

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")


def main():
    env = load_env(ENV_PATH)
    token = env.get("NOTION_TOKEN", "")
    db_id = env.get("RESEARCH_DB_ID", "")

    if not token or not db_id:
        print("ERROR: NOTION_TOKEN or RESEARCH_DB_ID missing in .env")
        return

    print("Adding 'Source Count' and 'Discovery Method' to Research database...")
    notion_request(token, "PATCH", f"/databases/{db_id}", {
        "properties": {
            "Source Count": {"number": {"format": "number"}},
            "Discovery Method": {
                "select": {
                    "options": [
                        {"name": "AI Search"},
                        {"name": "Source Monitor"},
                        {"name": "Manual"},
                        {"name": "Experience Intelligence"},
                        {"name": "Gap Engine"},
                        {"name": "Mentor"},
                        {"name": "User Request"},
                        {"name": "Trend Detection"},
                    ]
                }
            },
        }
    })
    print("Properties added.")


if __name__ == "__main__":
    main()
