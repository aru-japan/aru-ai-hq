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
    research_db_id = env.get("RESEARCH_DB_ID", "")

    if not token or not page_id:
        print("ERROR: NOTION_TOKEN or ARU_STUDIO_PAGE_ID missing in .env")
        sys.exit(1)
    if not research_db_id:
        print("ERROR: RESEARCH_DB_ID missing in .env (Research must exist first)")
        sys.exit(1)

    print("Creating 'Source Library' database under ARu Studio page...")

    properties = {
        "Source Name": {"title": {}},
        "URL": {"url": {}},
        "Source Type": select_options(
            "政府", "自治体", "観光協会", "ニュース", "学術", "SNS", "コミュニティ", "商店街", "地域メディア"
        ),
        "Tier": select_options("高", "中", "低"),
        "Trust Score": {"number": {"format": "number"}},
        "Check Frequency": select_options("Daily", "Weekly", "Monthly", "Quarterly"),
        "Last Checked": {"date": {}},
        "Status": select_options("Active", "Inactive", "Under Review"),
        "Record ID": {"unique_id": {"prefix": "SRC"}},
        "Tags": {"multi_select": {"options": []}},
        "Confidentiality": select_options("Public", "Internal", "Confidential"),
        "AI Generated": {"checkbox": {}},
        "Verification Status": select_options("Unverified", "Verified", "Needs Recheck"),
        "Related Research": {
            "relation": {
                "database_id": research_db_id,
                "type": "dual_property",
                "dual_property": {},
            }
        },
    }

    body = {
        "parent": {"type": "page_id", "page_id": page_id},
        "icon": {"type": "emoji", "emoji": "📚"},
        "title": [{"type": "text", "text": {"content": "Source Library"}}],
        "properties": properties,
    }

    db = notion_request(token, "POST", "/databases", body)
    db_id = db["id"]
    print(f"Created database. SOURCE_LIBRARY_DB_ID = {db_id}")

    print("Creating 1 test record...")
    page = notion_request(token, "POST", "/pages", {
        "parent": {"database_id": db_id},
        "properties": {
            "Source Name": {"title": [{"text": {"content": "【テスト】出入国在留管理庁 公式サイト"}}]},
            "URL": {"url": "https://www.moj.go.jp/isa/"},
            "Source Type": {"select": {"name": "政府"}},
            "Tier": {"select": {"name": "高"}},
            "Check Frequency": {"select": {"name": "Weekly"}},
            "Status": {"select": {"name": "Active"}},
            "Confidentiality": {"select": {"name": "Public"}},
            "AI Generated": {"checkbox": False},
            "Verification Status": {"select": {"name": "Verified"}},
        },
    })
    print(f"Test page created: {page['id']}")

    set_env_value(ENV_PATH, "SOURCE_LIBRARY_DB_ID", db_id)
    print("Wrote SOURCE_LIBRARY_DB_ID to .env")
    print("DONE.")


if __name__ == "__main__":
    main()
