"""ARu Studio v4.1 Editorial Intelligence -- Stage 1: Schema.

Adds only what's missing from Story Bank / Articles / Source Monitor / Law
Update (checked live against each DB before writing), per Rei's 2026-07-19
directive: prefer extending an existing property/relation over adding a new
one, and reuse existing Version 4 assets (the 13-value Audience taxonomy,
the 7-value Category taxonomy, Freshness/Publishing Status) wherever a
matching concept already exists rather than inventing a parallel one.

Deliberately NOT touched, because an existing property already covers the
request (see docs/Automation-Scripts.md "ARu Studio v4.1" section for the
full reuse table):
  Story Bank : Status(->Story Status), Related Articles(->Generated Article)
  Articles   : Related Story/Related QA(->Related to Story Bank), Related Law
               Update(->Related to Law Update), Target Persona(->Audience),
               Last Reviewed(->Last Verified Date), Last Updated(->Updated Date)
  Source Mon.: Source Name/Category/URL/Authority/Check Frequency/Reliability
               (->rollups from the existing "Source" relation, not duplicated
               storage), Last Checked(->Checked At)
  Law Update : Affected Persona(->Impact Scope), Official Source/Related
               Sources(->Official Notice URL / Related Source Library),
               Affected Translations(->Affected Translation), Urgency wording
               kept as Critical/High/Medium/Low for system-wide consistency

Idempotent: safe to re-run. Existing properties are left untouched; existing
select options are never removed or renamed, only appended to.
"""
import os
from notion_api import load_env, notion_request

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")

AUDIENCE_OPTIONS = ["観光客", "在住外国人", "留学生", "技能実習生", "特定技能", "永住者",
                    "高度人材", "外国籍社員", "家族", "子ども", "企業担当者", "自治体", "日本人"]
CATEGORY_OPTIONS = ["法律・制度", "イベント", "日本文化", "旅行情報", "生活情報", "ニュース", "トレンド"]
SENSITIVITY_OPTIONS = ["Low", "Medium", "High", "Critical"]
UPDATE_FREQUENCY_OPTIONS = ["Daily", "Weekly", "Monthly", "Quarterly", "Biannual", "Event-Based"]


def get_db(token, db_id):
    return notion_request(token, "GET", f"/databases/{db_id}")


def add_missing(token, db_id, db, new_props):
    current = set(db["properties"].keys())
    to_add = {name: schema for name, schema in new_props.items() if name not in current}
    if to_add:
        notion_request(token, "PATCH", f"/databases/{db_id}", {"properties": to_add})
    return list(to_add.keys())


def extend_select_options(token, db_id, db, prop_name, new_option_names):
    prop = db["properties"].get(prop_name)
    if prop is None or prop["type"] != "select":
        raise SystemExit(f"expected existing select property '{prop_name}' on {db_id}, found: {prop}")
    existing_options = prop["select"]["options"]
    existing_names = {o["name"] for o in existing_options}
    additions = [n for n in new_option_names if n not in existing_names]
    if additions:
        notion_request(token, "PATCH", f"/databases/{db_id}", {
            "properties": {
                prop_name: {"select": {"options": existing_options + [{"name": n} for n in additions]}}
            }
        })
    return additions


def main():
    env = load_env(ENV_PATH)
    token = env["NOTION_TOKEN"]

    story_bank_id = env["STORY_BANK_DB_ID"]
    articles_id = env["ARTICLES_DB_ID"]
    source_monitor_id = env["SOURCE_MONITOR_DB_ID"]
    law_update_id = env["LAW_UPDATE_DB_ID"]

    report = []

    # ---- Story Bank: QA-card-origin fields ----
    db = get_db(token, story_bank_id)
    added = add_missing(token, story_bank_id, db, {
        "Content Category": {"select": {"options": [{"name": n} for n in [
            "在留・ビザ", "留学生", "仕事・アルバイト", "生活手続", "住居", "医療・保険",
            "食事制限", "交通", "災害・防災", "日本文化・マナー", "子育て・教育",
            "観光・イベント", "日本語", "お金・税金"]]}},
        "Audience": {"multi_select": {"options": [{"name": n} for n in AUDIENCE_OPTIONS]}},
        "Problem": {"rich_text": {}},
        "Search Intent": {"rich_text": {}},
        "QA Question": {"rich_text": {}},
        "Short Answer": {"rich_text": {}},
        "Article Needed": {"checkbox": {}},
        "Deep Article Needed": {"checkbox": {}},
        "Information Sensitivity": {"select": {"options": [{"name": n} for n in SENSITIVITY_OPTIONS]}},
        "Dietary Restriction Type": {"multi_select": {"options": [{"name": n} for n in [
            "Vegetarian", "Vegan", "Halal", "No Pork", "Food Allergy", "Religious Dietary Needs"]]}},
        "Update Frequency": {"select": {"options": [{"name": n} for n in UPDATE_FREQUENCY_OPTIONS]}},
        "Last Reviewed": {"date": {}},
        "Next Review": {"date": {}},
    })
    report.append(("Story Bank properties added", added))

    # ---- Articles: Content Type + update-tracking fields ----
    db = get_db(token, articles_id)
    added = add_missing(token, articles_id, db, {
        "Content Type": {"select": {"options": [{"name": n} for n in [
            "Headline", "Basic Article", "Deep Guide", "Premium", "Update Notice"]]}},
        "Information Sensitivity": {"select": {"options": [{"name": n} for n in SENSITIVITY_OPTIONS]}},
        "Next Review": {"date": {}},
        "Update Frequency": {"select": {"options": [{"name": n} for n in UPDATE_FREQUENCY_OPTIONS]}},
        "Previous Information": {"rich_text": {}},
        "Current Information": {"rich_text": {}},
        "Change Reason": {"rich_text": {}},
        "Current Validity": {"select": {"options": [{"name": n} for n in [
            "Current", "Review Due", "Outdated", "Under Review", "Archived"]]}},
    })
    report.append(("Articles properties added", added))
    db = get_db(token, articles_id)
    ext = extend_select_options(token, articles_id, db, "Status", ["Updating", "Approval Required"])
    report.append(("Articles.Status options added", ext))

    # ---- Source Monitor: routing field + rollups from existing Source relation ----
    db = get_db(token, source_monitor_id)
    added = add_missing(token, source_monitor_id, db, {
        "Target Category": {"select": {"options": [{"name": n} for n in CATEGORY_OPTIONS]}},
        "Last Modified Detected": {"date": {}},
        "Source Category": {"rollup": {"relation_property_name": "Source", "rollup_property_name": "Category", "function": "show_original"}},
        "Official URL": {"rollup": {"relation_property_name": "Source", "rollup_property_name": "URL", "function": "show_original"}},
        "Check Frequency": {"rollup": {"relation_property_name": "Source", "rollup_property_name": "Check Frequency", "function": "show_original"}},
        "Reliability": {"rollup": {"relation_property_name": "Source", "rollup_property_name": "Trust Score", "function": "show_original"}},
        "Authority": {"rollup": {"relation_property_name": "Source", "rollup_property_name": "Source Type", "function": "show_original"}},
    })
    report.append(("Source Monitor properties added", added))
    db = get_db(token, source_monitor_id)
    ext = extend_select_options(token, source_monitor_id, db, "Status", ["Active", "Paused", "Check Required"])
    report.append(("Source Monitor.Status options added", ext))

    # ---- Law Update: used as the update queue ----
    db = get_db(token, law_update_id)
    added = add_missing(token, law_update_id, db, {
        "Update Type": {"select": {"options": [{"name": n} for n in [
            "New Law", "Amendment", "Repeal", "Fee Change", "Deadline Change",
            "Requirement Change", "Clarification"]]}},
        "Announcement Date": {"date": {}},
        "Previous Rule": {"rich_text": {}},
        "New Rule": {"rich_text": {}},
        "Difference Summary": {"rich_text": {}},
        "Affected Category": {"select": {"options": [{"name": n} for n in CATEGORY_OPTIONS]}},
        "Reviewed By": {"people": {}},
        "Reviewed Date": {"date": {}},
        "Published Date": {"date": {}},
        "Notes": {"rich_text": {}},
    })
    report.append(("Law Update properties added", added))
    db = get_db(token, law_update_id)
    ext = extend_select_options(token, law_update_id, db, "Update Status", ["No Action Required", "Approval Required"])
    report.append(("Law Update.Update Status options added", ext))

    print("=" * 70)
    print("Schema Migration Report -- ARu Studio v4.1 Editorial Intelligence (Stage 1)")
    print("=" * 70)
    for label, items in report:
        print(f"{label}: {len(items)} -> {items}")


if __name__ == "__main__":
    main()
