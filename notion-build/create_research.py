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
    articles_db_id = env.get("ARTICLES_DB_ID", "")

    if not token or not page_id:
        print("ERROR: NOTION_TOKEN or ARU_STUDIO_PAGE_ID missing in .env")
        sys.exit(1)
    if not articles_db_id:
        print("ERROR: ARTICLES_DB_ID missing in .env (Articles must exist first)")
        sys.exit(1)

    print("Creating 'Research' database under ARu Studio page...")

    properties = {
        "Topic": {"title": {}},
        "Category": select_options(
            "法律・制度", "イベント", "日本文化", "旅行情報", "生活情報", "ニュース", "トレンド"
        ),
        "Summary": {"rich_text": {}},
        "Raw Notes": {"rich_text": {}},
        "Evidence Level": select_options(
            "Official", "Verified", "Reported", "Rumor", "AI Suggested"
        ),
        "Status": select_options("New", "Reviewing", "Converted", "Rejected"),
        "Record ID": {"unique_id": {"prefix": "RES"}},
        "Tags": {"multi_select": {"options": []}},
        "Priority": select_options("High", "Medium", "Low"),
        "Trust Score": {"number": {"format": "number"}},
        "Review Level": {"number": {"format": "number"}},
        "QA Status": select_options("Not Started", "Passed", "Failed", "Needs Rework"),
        "Verification Status": select_options("Unverified", "Verified", "Needs Recheck"),
        "AI Generated": {"checkbox": {}},
        "Human Reviewed": {"checkbox": {}},
        "Last AI Update": {"date": {}},
        "Recommendation Score": {"number": {"format": "number"}},
        "Audience": multi_select_options(
            "観光客", "在住外国人", "留学生", "技能実習生", "特定技能", "永住者",
            "高度人材", "外国籍社員", "家族", "子ども", "企業担当者", "自治体", "日本人"
        ),
        "Season": multi_select_options("春", "夏", "秋", "冬", "通年"),
        "Urgency": select_options("Critical", "High", "Medium", "Low"),
        "Version": {"number": {"format": "number"}},
        "Revision": {"number": {"format": "number"}},
        "Confidentiality": select_options("Public", "Internal", "Confidential"),
        "Usage Scope": multi_select_options(
            "Consumer App", "Enterprise", "Municipal Partnership", "Internal Only"
        ),
        "Related Constitution Version": {"rich_text": {}},
        "Converted Article": {
            "relation": {
                "database_id": articles_db_id,
                "type": "dual_property",
                "dual_property": {},
            }
        },
    }

    body = {
        "parent": {"type": "page_id", "page_id": page_id},
        "icon": {"type": "emoji", "emoji": "🔍"},
        "title": [{"type": "text", "text": {"content": "Research"}}],
        "properties": properties,
    }

    db = notion_request(token, "POST", "/databases", body)
    db_id = db["id"]
    print(f"Created database. RESEARCH_DB_ID = {db_id}")

    # find the existing Articles test page to link as a relation test
    print("Looking up the Articles test record to link Converted Article -> Article...")
    query_resp = notion_request(token, "POST", f"/databases/{articles_db_id}/query", {})
    article_results = query_resp.get("results", [])
    article_test_page_id = article_results[0]["id"] if article_results else None

    print("Creating 1 test record...")
    props = {
        "Topic": {"title": [{"text": {"content": "【テスト】在留カード更新手続きの最新情報"}}]},
        "Category": {"select": {"name": "法律・制度"}},
        "Summary": {"rich_text": [{"text": {"content": "Research-Article間のRelation疎通確認用テストレコード。"}}]},
        "Evidence Level": {"select": {"name": "AI Suggested"}},
        "Status": {"select": {"name": "Converted"}},
        "Priority": {"select": {"name": "Medium"}},
        "Audience": {"multi_select": [{"name": "在住外国人"}]},
        "Season": {"multi_select": [{"name": "通年"}]},
        "Urgency": {"select": {"name": "Medium"}},
        "Confidentiality": {"select": {"name": "Public"}},
        "Usage Scope": {"multi_select": [{"name": "Consumer App"}]},
        "AI Generated": {"checkbox": True},
        "Human Reviewed": {"checkbox": False},
        "Related Constitution Version": {"rich_text": [{"text": {"content": "v2.0.0"}}]},
    }
    if article_test_page_id:
        props["Converted Article"] = {"relation": [{"id": article_test_page_id}]}

    test_page_body = {"parent": {"database_id": db_id}, "properties": props}
    page = notion_request(token, "POST", "/pages", test_page_body)
    print(f"Test page created: {page['id']}")
    if article_test_page_id:
        print("Linked to Articles test record via Converted Article relation.")
    else:
        print("WARNING: No Articles test record found to link.")

    set_env_value(ENV_PATH, "RESEARCH_DB_ID", db_id)
    print("Wrote RESEARCH_DB_ID to .env")
    print("DONE.")


if __name__ == "__main__":
    main()
