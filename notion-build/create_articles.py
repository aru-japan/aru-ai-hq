import os
import sys
from notion_api import load_env, set_env_value, notion_request

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")


def select_options(*names):
    return {"select": {"options": [{"name": n} for n in names]}}


def multi_select_options(*names):
    return {"multi_select": {"options": [{"name": n} for n in names]}}


def main():
    env = load_env(ENV_PATH)
    token = env.get("NOTION_TOKEN", "")
    page_id = env.get("ARU_STUDIO_PAGE_ID", "")

    if not token:
        print("ERROR: NOTION_TOKEN is empty in .env")
        sys.exit(1)
    if not page_id:
        print("ERROR: ARU_STUDIO_PAGE_ID is empty in .env")
        sys.exit(1)

    print(f"NOTION_TOKEN: set (length {len(token)})")
    print(f"ARU_STUDIO_PAGE_ID: {page_id}")
    print("Creating 'Articles' database under ARu Studio page...")

    properties = {
        "Title": {"title": {}},
        "Body": {"rich_text": {}},
        "Slug": {"rich_text": {}},
        "Record ID": {"unique_id": {"prefix": "ART"}},
        "Category": select_options(
            "法律・制度", "イベント", "日本文化", "旅行情報", "生活情報", "ニュース", "トレンド"
        ),
        "Status": select_options(
            "Draft", "AI Draft", "Human Review", "Approved", "Published", "Archived"
        ),
        "Tags": {"multi_select": {"options": []}},
        "Priority": select_options("High", "Medium", "Low"),
        "Audience": multi_select_options(
            "観光客", "在住外国人", "留学生", "技能実習生", "特定技能", "永住者",
            "高度人材", "外国籍社員", "家族", "子ども", "企業担当者", "自治体", "日本人"
        ),
        "Season": multi_select_options("春", "夏", "秋", "冬", "通年"),
        "Urgency": select_options("Critical", "High", "Medium", "Low"),
        "Master Language": select_options("ja"),
        "Confidentiality": select_options("Public", "Internal", "Confidential"),
        "Usage Scope": multi_select_options(
            "Consumer App", "Enterprise", "Municipal Partnership", "Internal Only"
        ),
        "Update Level": {"number": {"format": "number"}},
        "Trust Score": {"number": {"format": "number"}},
        "Cultural Value Score": {"number": {"format": "number"}},
        "Visitor Suitability Score": {"number": {"format": "number"}},
        "Popularity Score": {"number": {"format": "number"}},
        "Recommendation Score": {"number": {"format": "number"}},
        "Version": {"number": {"format": "number"}},
        "Revision": {"number": {"format": "number"}},
        "Published Date": {"date": {}},
        "Updated Date": {"date": {}},
        "Archived Date": {"date": {}},
        "Last Verified Date": {"date": {}},
        "Last AI Update": {"date": {}},
        "QA Status": select_options("Not Started", "Passed", "Failed", "Needs Rework"),
        "Verification Status": select_options("Unverified", "Verified", "Needs Recheck"),
        "AI Generated": {"checkbox": {}},
        "Human Reviewed": {"checkbox": {}},
        "Related Constitution Version": {"rich_text": {}},
    }

    body = {
        "parent": {"type": "page_id", "page_id": page_id},
        "icon": {"type": "emoji", "emoji": "📄"},
        "title": [{"type": "text", "text": {"content": "Articles"}}],
        "properties": properties,
    }

    db = notion_request(token, "POST", "/databases", body)
    db_id = db["id"]
    print(f"Created database. ARTICLES_DB_ID = {db_id}")

    # Step 2: add the self-relation (Knowledge Links) now that we know the DB's own id
    print("Adding self-relation property 'Knowledge Links'...")
    patch_body = {
        "properties": {
            "Knowledge Links": {
                "relation": {
                    "database_id": db_id,
                    "type": "dual_property",
                    "dual_property": {},
                }
            }
        }
    }
    notion_request(token, "PATCH", f"/databases/{db_id}", patch_body)
    print("Self-relation added.")

    # Step 3: create one test page
    print("Creating 1 test record...")
    test_page_body = {
        "parent": {"database_id": db_id},
        "properties": {
            "Title": {"title": [{"text": {"content": "【テスト】在留カードの更新手続きガイド"}}]},
            "Body": {"rich_text": [{"text": {"content": "これはArticlesデータベースの接続確認用テストレコードです。"}}]},
            "Category": {"select": {"name": "法律・制度"}},
            "Status": {"select": {"name": "Draft"}},
            "Priority": {"select": {"name": "Medium"}},
            "Audience": {"multi_select": [{"name": "在住外国人"}, {"name": "留学生"}]},
            "Season": {"multi_select": [{"name": "通年"}]},
            "Urgency": {"select": {"name": "Medium"}},
            "Master Language": {"select": {"name": "ja"}},
            "Confidentiality": {"select": {"name": "Public"}},
            "Usage Scope": {"multi_select": [{"name": "Consumer App"}]},
            "Update Level": {"number": 2},
            "AI Generated": {"checkbox": True},
            "Human Reviewed": {"checkbox": False},
            "Related Constitution Version": {"rich_text": [{"text": {"content": "v2.0.0"}}]},
        },
    }
    page = notion_request(token, "POST", "/pages", test_page_body)
    print(f"Test page created: {page['id']}")

    # Step 4: write DB id back to .env
    set_env_value(ENV_PATH, "ARTICLES_DB_ID", db_id)
    print("Wrote ARTICLES_DB_ID to .env")
    print("DONE.")


if __name__ == "__main__":
    main()
