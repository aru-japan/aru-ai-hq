import os
from notion_api import load_env, notion_request

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")


def main():
    env = load_env(ENV_PATH)
    token = env.get("NOTION_TOKEN", "")
    db_id = env.get("ARTICLES_DB_ID", "")

    if not token or not db_id:
        print("ERROR: NOTION_TOKEN or ARTICLES_DB_ID missing in .env")
        return

    print("Adding 'Article Owner' (Person) property to Articles database...")
    notion_request(token, "PATCH", f"/databases/{db_id}", {
        "properties": {
            "Article Owner": {"people": {}}
        }
    })
    print("Property added.")

    print("Looking up workspace users to find 'Rei'...")
    try:
        users_resp = notion_request(token, "GET", "/users", None)
    except RuntimeError as e:
        print(f"Could not list users: {e}")
        print("This usually means the Integration's capability 'Read user information' is disabled.")
        print("Skipping auto-assignment of the test record's Article Owner. You can set it manually in Notion.")
        return

    rei_user = None
    for user in users_resp.get("results", []):
        name = (user.get("name") or "")
        if "rei" in name.lower():
            rei_user = user
            break

    if not rei_user:
        print("No workspace user matching 'Rei' was found via the API.")
        print("Available users:", [u.get("name") for u in users_resp.get("results", [])])
        print("Please set the test record's Article Owner manually in Notion.")
        return

    print(f"Found user: {rei_user.get('name')} ({rei_user['id']})")

    # find the test page we created earlier and set Article Owner on it
    query_resp = notion_request(token, "POST", f"/databases/{db_id}/query", {})
    results = query_resp.get("results", [])
    if not results:
        print("No pages found in Articles database to update.")
        return
    test_page_id = results[0]["id"]

    notion_request(token, "PATCH", f"/pages/{test_page_id}", {
        "properties": {
            "Article Owner": {"people": [{"id": rei_user["id"]}]}
        }
    })
    print(f"Set Article Owner = {rei_user.get('name')} on test page {test_page_id}")
    print("DONE.")


if __name__ == "__main__":
    main()
