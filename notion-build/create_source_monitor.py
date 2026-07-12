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
    source_library_db_id = env.get("SOURCE_LIBRARY_DB_ID", "")
    research_db_id = env.get("RESEARCH_DB_ID", "")
    ei_db_id = env.get("EXPERIENCE_INTELLIGENCE_DB_ID", "")

    missing = [
        name for name, val in [
            ("NOTION_TOKEN", token), ("ARU_STUDIO_PAGE_ID", page_id),
            ("SOURCE_LIBRARY_DB_ID", source_library_db_id),
            ("RESEARCH_DB_ID", research_db_id),
            ("EXPERIENCE_INTELLIGENCE_DB_ID", ei_db_id),
        ] if not val
    ]
    if missing:
        print(f"ERROR: missing in .env: {missing}")
        sys.exit(1)

    print("Creating 'Source Monitor' database under ARu Studio page...")

    properties = {
        "Monitor Entry": {"title": {}},
        "Source": {
            "relation": {"database_id": source_library_db_id, "type": "dual_property", "dual_property": {}}
        },
        "Checked At": {"date": {}},
        "Check Method": select_options("RSS", "Webhook", "Scraping", "API", "Manual"),
        "Change Detected": {"checkbox": {}},
        "Change Type": select_options("New", "Updated", "Deleted", "Policy Change", "Emergency"),
        "Impact Level": select_options("Critical", "High", "Medium", "Low"),
        "Diff Summary": {"rich_text": {}},
        "Status": select_options("OK", "Error", "Changed", "Needs Attention"),
        "Next Check Due": {"date": {}},
        "Error Log": {"rich_text": {}},
        "Record ID": {"unique_id": {"prefix": "MON"}},
        "AI Generated": {"checkbox": {}},
        "Confidentiality": select_options("Public", "Internal", "Confidential"),
        "Triggered Research": {
            "relation": {"database_id": research_db_id, "type": "dual_property", "dual_property": {}}
        },
        "Triggered Signal": {
            "relation": {"database_id": ei_db_id, "type": "dual_property", "dual_property": {}}
        },
    }

    body = {
        "parent": {"type": "page_id", "page_id": page_id},
        "icon": {"type": "emoji", "emoji": "📡"},
        "title": [{"type": "text", "text": {"content": "Source Monitor"}}],
        "properties": properties,
    }

    db = notion_request(token, "POST", "/databases", body)
    db_id = db["id"]
    print(f"Created database. SOURCE_MONITOR_DB_ID = {db_id}")

    # Find existing test records to link (hub demonstration: Source -> Monitor -> Signal)
    print("Looking up Source Library test record...")
    src_q = notion_request(token, "POST", f"/databases/{source_library_db_id}/query", {})
    src_results = src_q.get("results", [])
    source_test_page_id = src_results[0]["id"] if src_results else None

    print("Looking up Experience Intelligence Gap test record...")
    ei_q = notion_request(token, "POST", f"/databases/{ei_db_id}/query", {})
    ei_results = ei_q.get("results", [])
    gap_signal_id = None
    for r in ei_results:
        it = r["properties"].get("Intelligence Type", {}).get("select")
        if it and it.get("name") == "Gap":
            gap_signal_id = r["id"]
            break

    print("Creating 1 test record (hub demonstration: Source -> Monitor -> Signal)...")
    props = {
        "Monitor Entry": {"title": [{"text": {"content": "【テスト】出入国在留管理庁サイトの更新検知"}}]},
        "Checked At": {"date": {"start": "2026-07-12"}},
        "Check Method": {"select": {"name": "Manual"}},
        "Change Detected": {"checkbox": True},
        "Change Type": {"select": {"name": "Policy Change"}},
        "Impact Level": {"select": {"name": "High"}},
        "Diff Summary": {"rich_text": [{"text": {"content": "【テスト】資格外活動許可の上限時間に関する記載が更新された、という想定のテストデータ。"}}]},
        "Status": {"select": {"name": "Changed"}},
        "AI Generated": {"checkbox": False},
        "Confidentiality": {"select": {"name": "Internal"}},
    }
    if source_test_page_id:
        props["Source"] = {"relation": [{"id": source_test_page_id}]}
    if gap_signal_id:
        props["Triggered Signal"] = {"relation": [{"id": gap_signal_id}]}

    page = notion_request(token, "POST", "/pages", {"parent": {"database_id": db_id}, "properties": props})
    print(f"Test page created: {page['id']}")
    print(f"Linked Source: {'yes' if source_test_page_id else 'NOT FOUND'}")
    print(f"Linked Triggered Signal (Gap): {'yes' if gap_signal_id else 'NOT FOUND'}")

    set_env_value(ENV_PATH, "SOURCE_MONITOR_DB_ID", db_id)
    print("Wrote SOURCE_MONITOR_DB_ID to .env")
    print("DONE.")


if __name__ == "__main__":
    main()
