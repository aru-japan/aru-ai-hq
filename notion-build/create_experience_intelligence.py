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
    source_library_db_id = env.get("SOURCE_LIBRARY_DB_ID", "")
    editorial_calendar_db_id = env.get("EDITORIAL_CALENDAR_DB_ID", "")

    missing = [
        name for name, val in [
            ("NOTION_TOKEN", token), ("ARU_STUDIO_PAGE_ID", page_id),
            ("ARTICLES_DB_ID", articles_db_id), ("RESEARCH_DB_ID", research_db_id),
            ("SOURCE_LIBRARY_DB_ID", source_library_db_id),
            ("EDITORIAL_CALENDAR_DB_ID", editorial_calendar_db_id),
        ] if not val
    ]
    if missing:
        print(f"ERROR: missing in .env: {missing}")
        sys.exit(1)

    print("Creating 'Experience Intelligence' database under ARu Studio page...")

    properties = {
        "Title": {"title": {}},
        "Intelligence Type": select_options(
            "Event", "Culture", "Trend", "Local", "Gap", "Opportunity", "User"
        ),
        "Description": {"rich_text": {}},
        "Status": select_options(
            "New", "Reviewing", "Acknowledged", "Actioned",
            "Converted", "Resolved", "Rejected", "Expired"
        ),
        "Record ID": {"unique_id": {"prefix": "EXI"}},
        "Tags": {"multi_select": {"options": []}},
        "Priority": select_options("High", "Medium", "Low"),
        "Trust Score": {"number": {"format": "number"}},
        "Recommendation Score": {"number": {"format": "number"}},
        "Audience": multi_select_options(
            "観光客", "在住外国人", "留学生", "技能実習生", "特定技能", "永住者",
            "高度人材", "外国籍社員", "家族", "子ども", "企業担当者", "自治体", "日本人"
        ),
        "Season": multi_select_options("春", "夏", "秋", "冬", "通年"),
        "Urgency": select_options("Critical", "High", "Medium", "Low"),
        "Confidentiality": select_options("Public", "Internal", "Confidential"),
        "Usage Scope": multi_select_options(
            "Consumer App", "Enterprise", "Municipal Partnership", "Internal Only"
        ),
        "AI Generated": {"checkbox": {}},
        "Human Reviewed": {"checkbox": {}},
        "Last AI Update": {"date": {}},
        "Archived Date": {"date": {}},
        # Event / Culture / Local specific
        "Popularity Score": {"number": {"format": "number"}},
        "Cultural Value Score": {"number": {"format": "number"}},
        "Visitor Suitability Score": {"number": {"format": "number"}},
        # Trend specific
        "Platform": select_options("Instagram", "Threads", "X", "YouTube"),
        "Trend Signal Strength": {"number": {"format": "number"}},
        # Gap specific
        "Gap Type": select_options(
            "Content Gap", "Translation Gap", "Region Gap", "Seasonal Gap", "Audience Gap",
            "Trust Gap", "Freshness Gap", "Experience Gap", "Trend Gap", "Legal Gap"
        ),
        "Metric / Evidence": {"rich_text": {}},
        "Affected Audience": multi_select_options(
            "観光客", "在住外国人", "留学生", "技能実習生", "特定技能", "永住者",
            "高度人材", "外国籍社員", "家族", "子ども", "企業担当者", "自治体", "日本人"
        ),
        "Affected Season": multi_select_options("春", "夏", "秋", "冬", "通年"),
        "Suggested Action": {"rich_text": {}},
        # Opportunity specific
        "Opportunity Type": select_options(
            "Seasonal Peak", "Trending Now", "Event Proximity", "Regional Momentum", "Audience Surge"
        ),
        "Opportunity Window Start": {"date": {}},
        "Opportunity Window End": {"date": {}},
        "Opportunity Score": {"number": {"format": "number"}},
        # User specific
        "Signal Volume": {"number": {"format": "number"}},
        # Relations to DBs that already exist
        "Related Article": {
            "relation": {"database_id": articles_db_id, "type": "dual_property", "dual_property": {}}
        },
        "Related Research": {
            "relation": {"database_id": research_db_id, "type": "dual_property", "dual_property": {}}
        },
        "Related Source Library": {
            "relation": {"database_id": source_library_db_id, "type": "dual_property", "dual_property": {}}
        },
        "Related Editorial Calendar Entry": {
            "relation": {"database_id": editorial_calendar_db_id, "type": "dual_property", "dual_property": {}}
        },
    }

    body = {
        "parent": {"type": "page_id", "page_id": page_id},
        "icon": {"type": "emoji", "emoji": "🧠"},
        "title": [{"type": "text", "text": {"content": "Experience Intelligence"}}],
        "properties": properties,
    }

    db = notion_request(token, "POST", "/databases", body)
    db_id = db["id"]
    print(f"Created database. EXPERIENCE_INTELLIGENCE_DB_ID = {db_id}")

    # self-relation now that we know the db's own id
    print("Adding self-relation 'Related Signal'...")
    notion_request(token, "PATCH", f"/databases/{db_id}", {
        "properties": {
            "Related Signal": {
                "relation": {"database_id": db_id, "type": "dual_property", "dual_property": {}}
            }
        }
    })
    print("Self-relation added.")

    # Try a Formula for Days Until Opportunity Expires; fall back to Number if rejected
    print("Attempting to add 'Days Until Opportunity Expires' as a Formula...")
    try:
        notion_request(token, "PATCH", f"/databases/{db_id}", {
            "properties": {
                "Days Until Opportunity Expires": {
                    "formula": {
                        "expression": 'dateBetween(prop("Opportunity Window End"), now(), "days")'
                    }
                }
            }
        })
        print("Formula accepted.")
        expires_is_formula = True
    except RuntimeError as e:
        print(f"Formula rejected by API ({e}); falling back to a plain Number for manual/automation use.")
        notion_request(token, "PATCH", f"/databases/{db_id}", {
            "properties": {"Days Until Opportunity Expires": {"number": {"format": "number"}}}
        })
        expires_is_formula = False

    # Test records: one Gap, one Opportunity
    print("Looking up an Article test page to reference...")
    art_q = notion_request(token, "POST", f"/databases/{articles_db_id}/query", {})
    art_results = art_q.get("results", [])
    article_test_page_id = art_results[0]["id"] if art_results else None

    print("Creating Gap test record...")
    gap_props = {
        "Title": {"title": [{"text": {"content": "【テスト】留学生向けアルバイト規定の記事が不足"}}]},
        "Intelligence Type": {"select": {"name": "Gap"}},
        "Description": {"rich_text": [{"text": {"content": "留学生の資格外活動許可に関する検索が多いが、該当記事が存在しない。"}}]},
        "Status": {"select": {"name": "New"}},
        "Priority": {"select": {"name": "High"}},
        "Urgency": {"select": {"name": "High"}},
        "Gap Type": {"select": {"name": "Content Gap"}},
        "Metric / Evidence": {"rich_text": [{"text": {"content": "検索件数: 想定342件/月、該当記事0件（テスト値）"}}]},
        "Affected Audience": {"multi_select": [{"name": "留学生"}]},
        "Suggested Action": {"rich_text": [{"text": {"content": "資格外活動許可の申請方法・上限時間についての記事を作成する"}}]},
        "Confidentiality": {"select": {"name": "Internal"}},
        "Usage Scope": {"multi_select": [{"name": "Consumer App"}]},
        "AI Generated": {"checkbox": True},
        "Human Reviewed": {"checkbox": False},
    }
    if article_test_page_id:
        gap_props["Related Article"] = {"relation": [{"id": article_test_page_id}]}
    gap_page = notion_request(token, "POST", "/pages", {"parent": {"database_id": db_id}, "properties": gap_props})
    print(f"Gap test record created: {gap_page['id']}")

    print("Creating Opportunity test record...")
    opp_props = {
        "Title": {"title": [{"text": {"content": "【テスト】紅葉シーズン到来、京都の紅葉記事の好機"}}]},
        "Intelligence Type": {"select": {"name": "Opportunity"}},
        "Description": {"rich_text": [{"text": {"content": "紅葉シーズンのピークが近く、SNSでの話題性も高い（テスト値）。"}}]},
        "Status": {"select": {"name": "New"}},
        "Priority": {"select": {"name": "High"}},
        "Urgency": {"select": {"name": "High"}},
        "Opportunity Type": {"select": {"name": "Seasonal Peak"}},
        "Opportunity Window Start": {"date": {"start": "2026-11-01"}},
        "Opportunity Window End": {"date": {"start": "2026-11-30"}},
        "Opportunity Score": {"number": 78},
        "Season": {"multi_select": [{"name": "秋"}]},
        "Confidentiality": {"select": {"name": "Internal"}},
        "Usage Scope": {"multi_select": [{"name": "Consumer App"}]},
        "AI Generated": {"checkbox": True},
        "Human Reviewed": {"checkbox": False},
    }
    opp_page = notion_request(token, "POST", "/pages", {"parent": {"database_id": db_id}, "properties": opp_props})
    print(f"Opportunity test record created: {opp_page['id']}")

    set_env_value(ENV_PATH, "EXPERIENCE_INTELLIGENCE_DB_ID", db_id)
    print("Wrote EXPERIENCE_INTELLIGENCE_DB_ID to .env")
    print(f"Days Until Opportunity Expires implemented as: {'Formula' if expires_is_formula else 'Number (manual/automation)'}")
    print("DONE.")


if __name__ == "__main__":
    main()
