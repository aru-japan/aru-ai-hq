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
    translation_db_id = env.get("TRANSLATION_DB_ID", "")
    source_library_db_id = env.get("SOURCE_LIBRARY_DB_ID", "")

    missing = [
        name for name, val in [
            ("NOTION_TOKEN", token), ("ARU_STUDIO_PAGE_ID", page_id),
            ("ARTICLES_DB_ID", articles_db_id), ("TRANSLATION_DB_ID", translation_db_id),
            ("SOURCE_LIBRARY_DB_ID", source_library_db_id),
        ] if not val
    ]
    if missing:
        print(f"ERROR: missing in .env: {missing}")
        sys.exit(1)

    print("Creating 'Law Update' database under ARu Studio page...")

    properties = {
        "Law Name": {"title": {}},
        "Jurisdiction": select_options("国", "都道府県", "市区町村"),
        "Governing Body": {"rich_text": {}},
        "Significance": select_options("Minor", "Major"),
        "Impact Summary": {"rich_text": {}},
        "Action Required": {"rich_text": {}},
        "Effective Date": {"date": {}},
        "Grace Period": {"rich_text": {}},
        "Official Notice URL": {"url": {}},
        "Update Status": select_options(
            "Monitoring", "Confirmed", "Reflecting to Article", "Article Published", "Archived"
        ),
        "Impact Scope": multi_select_options(
            "観光客", "在住外国人", "留学生", "技能実習生", "特定技能", "永住者",
            "高度人材", "外国籍社員", "家族", "子ども", "企業担当者", "自治体", "日本人"
        ),
        "Record ID": {"unique_id": {"prefix": "LAW"}},
        "Tags": {"multi_select": {"options": []}},
        "Priority": select_options("High", "Medium", "Low"),
        "Urgency": select_options("Critical", "High", "Medium", "Low"),
        "Trust Score": {"number": {"format": "number"}},
        "Recommendation Score": {"number": {"format": "number"}},
        "Review Level": {"number": {"format": "number"}},
        "QA Status": select_options("Not Started", "Passed", "Failed", "Needs Rework"),
        "Verification Status": select_options("Unverified", "Verified", "Needs Recheck"),
        "AI Generated": {"checkbox": {}},
        "Human Reviewed": {"checkbox": {}},
        "Last AI Update": {"date": {}},
        "Archived Date": {"date": {}},
        "Confidentiality": select_options("Public", "Internal", "Confidential"),
        "Usage Scope": multi_select_options(
            "Consumer App", "Enterprise", "Municipal Partnership", "Internal Only"
        ),
        "Related Constitution Version": {"rich_text": {}},
        "Affected Articles": {
            "relation": {"database_id": articles_db_id, "type": "dual_property", "dual_property": {}}
        },
        "Affected Translation": {
            "relation": {"database_id": translation_db_id, "type": "dual_property", "dual_property": {}}
        },
        "Related Source Library": {
            "relation": {"database_id": source_library_db_id, "type": "dual_property", "dual_property": {}}
        },
    }

    body = {
        "parent": {"type": "page_id", "page_id": page_id},
        "icon": {"type": "emoji", "emoji": "⚖️"},
        "title": [{"type": "text", "text": {"content": "Law Update"}}],
        "properties": properties,
    }

    db = notion_request(token, "POST", "/databases", body)
    db_id = db["id"]
    print(f"Created database. LAW_UPDATE_DB_ID = {db_id}")

    # Test record, linked to Articles test page (Affected Articles) and Source Library test page
    print("Looking up Articles / Source Library test records...")
    art_q = notion_request(token, "POST", f"/databases/{articles_db_id}/query", {})
    art_results = art_q.get("results", [])
    article_test_page_id = art_results[0]["id"] if art_results else None

    src_q = notion_request(token, "POST", f"/databases/{source_library_db_id}/query", {})
    src_results = src_q.get("results", [])
    source_test_page_id = src_results[0]["id"] if src_results else None

    print("Creating 1 test record...")
    props = {
        "Law Name": {"title": [{"text": {"content": "【テスト】入管法改正（資格外活動許可の上限時間見直し）"}}]},
        "Jurisdiction": {"select": {"name": "国"}},
        "Governing Body": {"rich_text": [{"text": {"content": "出入国在留管理庁"}}]},
        "Significance": {"select": {"name": "Major"}},
        "Impact Summary": {"rich_text": [{"text": {"content": "【テスト】留学生の資格外活動における週あたりの就労可能時間が変更される想定。"}}]},
        "Action Required": {"rich_text": [{"text": {"content": "【テスト】既存の許可証を持つ留学生は、次回更新時までに新基準を確認する必要がある。"}}]},
        "Effective Date": {"date": {"start": "2026-08-01"}},
        "Grace Period": {"rich_text": [{"text": {"content": "施行から3ヶ月間は旧基準の許可も有効（テスト値）。"}}]},
        "Official Notice URL": {"url": "https://www.moj.go.jp/isa/"},
        "Update Status": {"select": {"name": "Confirmed"}},
        "Impact Scope": {"multi_select": [{"name": "留学生"}]},
        "Priority": {"select": {"name": "High"}},
        "Urgency": {"select": {"name": "Critical"}},
        "Verification Status": {"select": {"name": "Verified"}},
        "AI Generated": {"checkbox": True},
        "Human Reviewed": {"checkbox": False},
        "Confidentiality": {"select": {"name": "Internal"}},
        "Usage Scope": {"multi_select": [{"name": "Consumer App"}]},
    }
    if article_test_page_id:
        props["Affected Articles"] = {"relation": [{"id": article_test_page_id}]}
    if source_test_page_id:
        props["Related Source Library"] = {"relation": [{"id": source_test_page_id}]}

    page = notion_request(token, "POST", "/pages", {"parent": {"database_id": db_id}, "properties": props})
    print(f"Test page created: {page['id']}")

    set_env_value(ENV_PATH, "LAW_UPDATE_DB_ID", db_id)
    print("Wrote LAW_UPDATE_DB_ID to .env")

    # Now wire the previously-deferred Article <-> Law Update connection
    print("Adding 'Source Law Update' relation + 'Law Significance' rollup to Articles (previously deferred)...")
    notion_request(token, "PATCH", f"/databases/{articles_db_id}", {
        "properties": {
            "Source Law Update": {
                "relation": {"database_id": db_id, "type": "dual_property", "dual_property": {}}
            }
        }
    })
    notion_request(token, "PATCH", f"/databases/{articles_db_id}", {
        "properties": {
            "Law Significance": {
                "rollup": {
                    "relation_property_name": "Source Law Update",
                    "rollup_property_name": "Significance",
                    "function": "show_original",
                }
            }
        }
    })
    print("Articles updated with Source Law Update + Law Significance.")
    print("DONE.")


if __name__ == "__main__":
    main()
