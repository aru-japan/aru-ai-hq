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
    source_library_db_id = env.get("SOURCE_LIBRARY_DB_ID", "")
    ei_db_id = env.get("EXPERIENCE_INTELLIGENCE_DB_ID", "")

    missing = [
        name for name, val in [
            ("NOTION_TOKEN", token), ("ARU_STUDIO_PAGE_ID", page_id),
            ("ARTICLES_DB_ID", articles_db_id),
            ("SOURCE_LIBRARY_DB_ID", source_library_db_id),
            ("EXPERIENCE_INTELLIGENCE_DB_ID", ei_db_id),
        ] if not val
    ]
    if missing:
        print(f"ERROR: missing in .env: {missing}")
        sys.exit(1)

    print("Creating 'Event Calendar' database under ARu Studio page...")

    properties = {
        "Event Name": {"title": {}},
        "Type": select_options(
            "祭り", "花火大会", "フードフェス", "蚤の市", "マルシェ",
            "文化イベント", "自治体イベント", "季節イベント", "期間限定イベント"
        ),
        "Location": {"rich_text": {}},
        "Event Date": {"date": {}},
        "Status": select_options("Planning", "Confirmed", "Promoting", "Completed", "Cancelled"),
        "Experience Score": {"number": {"format": "number"}},
        "Reservation Required": {"checkbox": {}},
        "Family Friendly": {"checkbox": {}},
        "Rain Policy": select_options(
            "Proceeds Rain or Shine", "Cancelled if Rain", "Indoor Alternative", "Postponed"
        ),
        "Accessibility": multi_select_options(
            "車椅子対応", "ベビーカー可", "多言語対応あり", "高齢者配慮", "特になし"
        ),
        "Best Season": multi_select_options("春", "夏", "秋", "冬", "通年"),
        "Official SNS": {"rich_text": {}},
        "Repeat Schedule": select_options("One-time", "Annual", "Monthly", "Weekly", "Irregular"),
        "AI Highlight": {"rich_text": {}},
        "Recommended Audience": multi_select_options(
            "観光客", "在住外国人", "留学生", "技能実習生", "特定技能", "永住者",
            "高度人材", "外国籍社員", "家族", "子ども", "企業担当者", "自治体", "日本人"
        ),
        "Audience": multi_select_options(
            "観光客", "在住外国人", "留学生", "技能実習生", "特定技能", "永住者",
            "高度人材", "外国籍社員", "家族", "子ども", "企業担当者", "自治体", "日本人"
        ),
        "Season": multi_select_options("春", "夏", "秋", "冬", "通年"),
        "Record ID": {"unique_id": {"prefix": "EVT"}},
        "Tags": {"multi_select": {"options": []}},
        "Priority": select_options("High", "Medium", "Low"),
        "Urgency": select_options("Critical", "High", "Medium", "Low"),
        "Trust Score": {"number": {"format": "number"}},
        "Recommendation Score": {"number": {"format": "number"}},
        "AI Generated": {"checkbox": {}},
        "Human Reviewed": {"checkbox": {}},
        "Last AI Update": {"date": {}},
        "Archived Date": {"date": {}},
        "Confidentiality": select_options("Public", "Internal", "Confidential"),
        "Usage Scope": multi_select_options(
            "Consumer App", "Enterprise", "Municipal Partnership", "Internal Only"
        ),
        "Related Constitution Version": {"rich_text": {}},
        "Related Article": {
            "relation": {"database_id": articles_db_id, "type": "dual_property", "dual_property": {}}
        },
        "Related Source Library": {
            "relation": {"database_id": source_library_db_id, "type": "dual_property", "dual_property": {}}
        },
        "Related Experience Intelligence": {
            "relation": {"database_id": ei_db_id, "type": "dual_property", "dual_property": {}}
        },
    }

    body = {
        "parent": {"type": "page_id", "page_id": page_id},
        "icon": {"type": "emoji", "emoji": "🎉"},
        "title": [{"type": "text", "text": {"content": "Event Calendar"}}],
        "properties": properties,
    }

    db = notion_request(token, "POST", "/databases", body)
    db_id = db["id"]
    print(f"Created database. EVENT_CALENDAR_DB_ID = {db_id}")

    print("Looking up Experience Intelligence Opportunity test record to link...")
    ei_q = notion_request(token, "POST", f"/databases/{ei_db_id}/query", {})
    ei_results = ei_q.get("results", [])
    opportunity_signal_id = None
    for r in ei_results:
        it = r["properties"].get("Intelligence Type", {}).get("select")
        if it and it.get("name") == "Opportunity":
            opportunity_signal_id = r["id"]
            break

    print("Creating 1 test record...")
    props = {
        "Event Name": {"title": [{"text": {"content": "【テスト】京都 東福寺 紅葉ライトアップ"}}]},
        "Type": {"select": {"name": "季節イベント"}},
        "Location": {"rich_text": [{"text": {"content": "京都府京都市東山区（テスト値）"}}]},
        "Event Date": {"date": {"start": "2026-11-15", "end": "2026-11-30"}},
        "Status": {"select": {"name": "Confirmed"}},
        "Experience Score": {"number": 88},
        "Reservation Required": {"checkbox": False},
        "Family Friendly": {"checkbox": True},
        "Rain Policy": {"select": {"name": "Proceeds Rain or Shine"}},
        "Accessibility": {"multi_select": [{"name": "多言語対応あり"}]},
        "Best Season": {"multi_select": [{"name": "秋"}]},
        "Season": {"multi_select": [{"name": "秋"}]},
        "Official SNS": {"rich_text": [{"text": {"content": "https://www.instagram.com/example (テスト)"}}]},
        "Repeat Schedule": {"select": {"name": "Annual"}},
        "AI Highlight": {"rich_text": [{"text": {"content": "夜の紅葉ライトアップは外国人観光客にとって非日常感が高く、SNS映えする体験（テストAI生成文）。"}}]},
        "Recommended Audience": {"multi_select": [{"name": "観光客"}, {"name": "家族"}]},
        "Audience": {"multi_select": [{"name": "観光客"}]},
        "Priority": {"select": {"name": "High"}},
        "Urgency": {"select": {"name": "Medium"}},
        "AI Generated": {"checkbox": True},
        "Human Reviewed": {"checkbox": False},
        "Confidentiality": {"select": {"name": "Public"}},
        "Usage Scope": {"multi_select": [{"name": "Consumer App"}]},
    }
    if opportunity_signal_id:
        props["Related Experience Intelligence"] = {"relation": [{"id": opportunity_signal_id}]}

    page = notion_request(token, "POST", "/pages", {"parent": {"database_id": db_id}, "properties": props})
    print(f"Test page created: {page['id']}")
    print(f"Linked to Experience Intelligence Opportunity record: {'yes' if opportunity_signal_id else 'NOT FOUND'}")

    set_env_value(ENV_PATH, "EVENT_CALENDAR_DB_ID", db_id)
    print("Wrote EVENT_CALENDAR_DB_ID to .env")
    print("DONE.")


if __name__ == "__main__":
    main()
