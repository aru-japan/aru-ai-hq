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
    research_db_id = env.get("RESEARCH_DB_ID", "")

    if not token or not page_id:
        print("ERROR: NOTION_TOKEN or ARU_STUDIO_PAGE_ID missing in .env")
        sys.exit(1)
    if not articles_db_id or not research_db_id:
        print("ERROR: ARTICLES_DB_ID or RESEARCH_DB_ID missing in .env")
        sys.exit(1)

    print("Creating 'Editorial Calendar' database under ARu Studio page...")

    properties = {
        "Planned Topic": {"title": {}},
        "Category": select_options(
            "法律・制度", "イベント", "日本文化", "旅行情報", "生活情報", "ニュース", "トレンド"
        ),
        "Planned Date": {"date": {}},
        "Status": select_options(
            "Idea", "Planned", "In Progress", "Drafted", "Published", "Skipped", "Cancelled"
        ),
        "Content Goal": select_options(
            "Education", "Culture", "Emergency", "SEO", "Seasonal", "Engagement", "Partner", "News"
        ),
        "Campaign": {"rich_text": {}},
        "Success KPI": {"number": {"format": "number"}},
        "Linked Article": {
            "relation": {
                "database_id": articles_db_id,
                "type": "dual_property",
                "dual_property": {},
            }
        },
        "Linked Research": {
            "relation": {
                "database_id": research_db_id,
                "type": "dual_property",
                "dual_property": {},
            }
        },
        "Audience": multi_select_options(
            "観光客", "在住外国人", "留学生", "技能実習生", "特定技能", "永住者",
            "高度人材", "外国籍社員", "家族", "子ども", "企業担当者", "自治体", "日本人"
        ),
        "Season": multi_select_options("春", "夏", "秋", "冬", "通年"),
        "Urgency": select_options("Critical", "High", "Medium", "Low"),
        "Recommendation Score": {"number": {"format": "number"}},
        "Record ID": {"unique_id": {"prefix": "CAL"}},
        "Tags": {"multi_select": {"options": []}},
        "Confidentiality": select_options("Public", "Internal", "Confidential"),
        "AI Generated": {"checkbox": {}},
    }

    body = {
        "parent": {"type": "page_id", "page_id": page_id},
        "icon": {"type": "emoji", "emoji": "📅"},
        "title": [{"type": "text", "text": {"content": "Editorial Calendar"}}],
        "properties": properties,
    }

    db = notion_request(token, "POST", "/databases", body)
    db_id = db["id"]
    print(f"Created database. EDITORIAL_CALENDAR_DB_ID = {db_id}")

    # Link test record to existing Article + Research test pages (relation smoke test)
    print("Looking up Articles / Research test records to link...")
    art_q = notion_request(token, "POST", f"/databases/{articles_db_id}/query", {})
    art_results = art_q.get("results", [])
    article_test_page_id = art_results[0]["id"] if art_results else None

    res_q = notion_request(token, "POST", f"/databases/{research_db_id}/query", {})
    res_results = res_q.get("results", [])
    research_test_page_id = res_results[0]["id"] if res_results else None

    print("Creating 1 test record...")
    props = {
        "Planned Topic": {"title": [{"text": {"content": "【テスト】在留カード更新手続きガイド 公開計画"}}]},
        "Category": {"select": {"name": "法律・制度"}},
        "Status": {"select": {"name": "Drafted"}},
        "Content Goal": {"select": {"name": "Education"}},
        "Campaign": {"rich_text": [{"text": {"content": "テスト運用：5DB疎通確認キャンペーン"}}]},
        "Success KPI": {"number": 100},
        "Audience": {"multi_select": [{"name": "在住外国人"}]},
        "Season": {"multi_select": [{"name": "通年"}]},
        "Urgency": {"select": {"name": "Medium"}},
        "Confidentiality": {"select": {"name": "Public"}},
        "AI Generated": {"checkbox": False},
    }
    if article_test_page_id:
        props["Linked Article"] = {"relation": [{"id": article_test_page_id}]}
    if research_test_page_id:
        props["Linked Research"] = {"relation": [{"id": research_test_page_id}]}

    page = notion_request(token, "POST", "/pages", {"parent": {"database_id": db_id}, "properties": props})
    print(f"Test page created: {page['id']}")
    print(f"Linked Article: {'yes' if article_test_page_id else 'NOT FOUND'}")
    print(f"Linked Research: {'yes' if research_test_page_id else 'NOT FOUND'}")

    set_env_value(ENV_PATH, "EDITORIAL_CALENDAR_DB_ID", db_id)
    print("Wrote EDITORIAL_CALENDAR_DB_ID to .env")
    print("DONE.")


if __name__ == "__main__":
    main()
