import os
import sys
from notion_api import load_env, set_env_value, notion_request

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")


def select_options(*names):
    return {"select": {"options": [{"name": n} for n in names]}}


def main():
    env = load_env(ENV_PATH)
    token = env.get("NOTION_TOKEN", "")
    page_id = env.get("ARU_STUDIO_PAGE_ID", "")
    articles_db_id = env.get("ARTICLES_DB_ID", "")

    if not token or not page_id:
        print("ERROR: NOTION_TOKEN or ARU_STUDIO_PAGE_ID missing in .env")
        sys.exit(1)
    if not articles_db_id:
        print("ERROR: ARTICLES_DB_ID missing in .env (Articles must exist first)")
        sys.exit(1)

    print("Creating 'Translation' database under ARu Studio page...")

    properties = {
        "Translation Name": {"title": {}},
        "Parent Article": {
            "relation": {
                "database_id": articles_db_id,
                "type": "dual_property",
                "dual_property": {},
            }
        },
        "Language": select_options(
            "en", "zh-CN", "zh-TW", "ko", "vi", "id", "es", "tl", "ne", "pt", "th"
        ),
        "Translated Title": {"rich_text": {}},
        "Translated Body": {"rich_text": {}},
        "AI Translation Status": select_options("Not Started", "Queued", "In Progress", "Done"),
        "Localization Status": select_options(
            "Not Started", "Translated", "Culturally Adapted", "Needs Cultural Review"
        ),
        "Human Review Status": select_options("Not Required", "Pending", "In Review", "Reviewed"),
        "Publish Approval": select_options("Not Required", "Pending", "Approved", "Rejected"),
        "Approved Date": {"date": {}},
        "Published Date": {"date": {}},
        "Last Source Check": {"date": {}},
        "Change Summary": {"rich_text": {}},
        "Publish Status": select_options("Not Published", "Published"),
        "Record ID": {"unique_id": {"prefix": "TRN"}},
        "Tags": {"multi_select": {"options": []}},
        "Archived Date": {"date": {}},
        "AI Generated": {"checkbox": {}},
        "Human Reviewed": {"checkbox": {}},
        "Last AI Update": {"date": {}},
        "Popularity Score": {"number": {"format": "number"}},
        "Confidentiality": select_options("Public", "Internal", "Confidential"),
        "Usage Scope": {"multi_select": {"options": [
            {"name": "Consumer App"}, {"name": "Enterprise"},
            {"name": "Municipal Partnership"}, {"name": "Internal Only"}
        ]}},
    }

    body = {
        "parent": {"type": "page_id", "page_id": page_id},
        "icon": {"type": "emoji", "emoji": "🌍"},
        "title": [{"type": "text", "text": {"content": "Translation"}}],
        "properties": properties,
    }

    db = notion_request(token, "POST", "/databases", body)
    db_id = db["id"]
    print(f"Created database. TRANSLATION_DB_ID = {db_id}")

    # Add rollups now that Parent Article relation + Article DB properties both exist
    print("Adding rollups (Review Level <- Update Level, Source Updated At <- Updated Date)...")
    notion_request(token, "PATCH", f"/databases/{db_id}", {
        "properties": {
            "Review Level": {
                "rollup": {
                    "relation_property_name": "Parent Article",
                    "rollup_property_name": "Update Level",
                    "function": "max",
                }
            },
            "Source Updated At": {
                "rollup": {
                    "relation_property_name": "Parent Article",
                    "rollup_property_name": "Updated Date",
                    "function": "max",
                }
            },
        }
    })
    print("Rollups added.")

    # Try the Needs Re-Translation formula; fall back to a plain checkbox if the API rejects the expression
    print("Attempting to add 'Needs Re-Translation' as a Formula...")
    try:
        notion_request(token, "PATCH", f"/databases/{db_id}", {
            "properties": {
                "Needs Re-Translation": {
                    "formula": {
                        "expression": 'if(prop("Source Updated At") > prop("Last Source Check"), true, false)'
                    }
                }
            }
        })
        print("Formula accepted.")
    except RuntimeError as e:
        print(f"Formula rejected by API ({e}); falling back to a plain Checkbox for manual/automation use.")
        notion_request(token, "PATCH", f"/databases/{db_id}", {
            "properties": {"Needs Re-Translation": {"checkbox": {}}}
        })

    # Test record, linked to the Articles test page (tests the Article <-> Translation relation)
    print("Looking up the Articles test record to link Parent Article -> Article...")
    query_resp = notion_request(token, "POST", f"/databases/{articles_db_id}/query", {})
    article_results = query_resp.get("results", [])
    article_test_page_id = article_results[0]["id"] if article_results else None

    print("Creating 1 test record...")
    props = {
        "Translation Name": {"title": [{"text": {"content": "【テスト】在留カード更新手続きガイド (EN)"}}]},
        "Language": {"select": {"name": "en"}},
        "Translated Title": {"rich_text": [{"text": {"content": "[TEST] Residence Card Renewal Guide"}}]},
        "AI Translation Status": {"select": {"name": "Not Started"}},
        "Localization Status": {"select": {"name": "Not Started"}},
        "Human Review Status": {"select": {"name": "Not Required"}},
        "Publish Approval": {"select": {"name": "Not Required"}},
        "Publish Status": {"select": {"name": "Not Published"}},
        "AI Generated": {"checkbox": False},
        "Human Reviewed": {"checkbox": False},
        "Confidentiality": {"select": {"name": "Public"}},
        "Usage Scope": {"multi_select": [{"name": "Consumer App"}]},
    }
    if article_test_page_id:
        props["Parent Article"] = {"relation": [{"id": article_test_page_id}]}

    page = notion_request(token, "POST", "/pages", {"parent": {"database_id": db_id}, "properties": props})
    print(f"Test page created: {page['id']}")
    if article_test_page_id:
        print("Linked to Articles test record via Parent Article relation.")
    else:
        print("WARNING: No Articles test record found to link.")

    set_env_value(ENV_PATH, "TRANSLATION_DB_ID", db_id)
    print("Wrote TRANSLATION_DB_ID to .env")
    print("DONE.")


if __name__ == "__main__":
    main()
