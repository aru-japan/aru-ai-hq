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
    sns_queue_db_id = env.get("SNS_QUEUE_DB_ID", "")

    missing = [
        name for name, val in [
            ("NOTION_TOKEN", token), ("ARU_STUDIO_PAGE_ID", page_id),
            ("ARTICLES_DB_ID", articles_db_id), ("SNS_QUEUE_DB_ID", sns_queue_db_id),
        ] if not val
    ]
    if missing:
        print(f"ERROR: missing in .env: {missing}")
        sys.exit(1)

    print("Creating 'Story Bank' database under ARu Studio page...")

    properties = {
        "Title": {"title": {}},
        # Reuses Research's existing 7-value Category taxonomy (Architecture-
        # Specification-v1.0.md Sec.6) rather than inventing a new one -- Story
        # Bank sits upstream of every Knowledge Domain, so it uses the same
        # shared classification, not its own.
        "Category": select_options(
            "法律・制度", "イベント", "日本文化", "旅行情報", "生活情報", "ニュース", "トレンド"
        ),
        # Intentionally starts with only the one value this session's dataset
        # needs. Notion lets any script/user add a new option on write, so
        # this grows organically as non-firework Stories are added later --
        # it is not meant to be a complete enumeration today.
        "Subcategory": select_options("花火大会"),
        "Season": multi_select_options("春", "夏", "秋", "冬", "通年"),
        # Same 9-region + 全国/海外 breakdown already used by Source Library,
        # for cross-DB consistency.
        "Region": select_options(
            "北海道", "東北", "関東", "中部", "近畿", "中国", "四国", "九州・沖縄", "全国", "海外"
        ),
        # Defined low-to-high (C, B, A, S) so Notion's "descending" sort shows
        # S first -- the exact inverse-order bug found and fixed in the
        # Dashboard's Priority/Urgency fields on 2026-07-16 (AI-Handover.md
        # Known Limitations); applying that lesson here instead of
        # re-discovering it.
        "Priority": select_options("C", "B", "A", "S"),
        "Target User": select_options("Resident", "Tourist", "Both"),
        "Evergreen": {"checkbox": {}},
        "Premium Candidate": {"checkbox": {}},
        "Event Month": multi_select_options(
            "1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"
        ),
        # Mirrors the existing Verification Status vocabulary (Research/Law
        # Update) rather than inventing new wording for the same concept.
        "Source Status": select_options("Unverified", "Verified", "Needs Recheck"),
        # Coarse pipeline stage. Deliberately not one option per pipeline
        # step (Story Bank -> QA Card -> Article -> Deep Guide -> SNS) --
        # QA Card and Deep Guide have no defined storage model yet (see
        # Sec.6/App. Open Questions, User-Journey-Architecture-v1.0.md), so
        # per-stage tracking for those two is deferred rather than faked.
        "Story Status": select_options("New", "Approved", "In Production", "Published", "Archived"),
        # Real relations to DBs that already exist. QA Card and Deep Guide
        # relations are NOT added here -- there is nothing to point them at
        # yet (no dedicated database or property model decided for either).
        "Generated Article": {
            "relation": {
                "database_id": articles_db_id,
                "type": "dual_property",
                "dual_property": {},
            }
        },
        "Related SNS Posts": {
            "relation": {
                "database_id": sns_queue_db_id,
                "type": "dual_property",
                "dual_property": {},
            }
        },
    }

    body = {
        "parent": {"type": "page_id", "page_id": page_id},
        "icon": {"type": "emoji", "emoji": "📚"},
        "title": [{"type": "text", "text": {"content": "Story Bank"}}],
        "properties": properties,
    }

    db = notion_request(token, "POST", "/databases", body)
    db_id = db["id"]
    print(f"Created database. STORY_BANK_DB_ID = {db_id}")

    print("Creating 1 test record (schema/relation smoke test only, not real content)...")
    props = {
        "Title": {"title": [{"text": {"content": "【テスト・Story Bank検証用】隅田川花火大会"}}]},
        "Category": {"select": {"name": "イベント"}},
        "Subcategory": {"select": {"name": "花火大会"}},
        "Season": {"multi_select": [{"name": "夏"}]},
        "Region": {"select": {"name": "関東"}},
        "Priority": {"select": {"name": "S"}},
        "Target User": {"select": {"name": "Both"}},
        "Evergreen": {"checkbox": False},
        "Premium Candidate": {"checkbox": True},
        "Event Month": {"multi_select": [{"name": "7月"}]},
        "Source Status": {"select": {"name": "Needs Recheck"}},
        "Story Status": {"select": {"name": "New"}},
    }
    page = notion_request(token, "POST", "/pages", {"parent": {"database_id": db_id}, "properties": props})
    print(f"Test page created: {page['id']}")
    print("NOTE: this test record should be archived once real Fireworks Top 50 data is loaded.")

    set_env_value(ENV_PATH, "STORY_BANK_DB_ID", db_id)
    print("Wrote STORY_BANK_DB_ID to .env")
    print("DONE.")


if __name__ == "__main__":
    main()
