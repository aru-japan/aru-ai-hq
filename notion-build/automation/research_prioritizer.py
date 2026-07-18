"""Research Prioritizer -- ARu Intelligence Phase 3 (Editorial Intelligence).

Editorial Planner (Phase 2) answers "what topics are we missing?" and proposes
brand-new themes. This script answers a different question: **given the
Research records that already exist and are sitting in Status=New waiting for
a human to look at them, which ones deserve attention first?**

Fully deterministic, zero new Notion schema, zero extra AI Gateway calls --
every dimension is derived from properties Research already has (Category,
Season, Usage Scope, Evidence Level, created_time). This keeps scoring cheap
enough to recompute on every AI Command Center refresh and keeps the "why did
this rank highly" reasoning fully inspectable (no AI judgment call hidden
inside the score).

Five dimensions, each worth up to 20 points (composite score 0-100):
    Freshness            -- how recently this Research was discovered
    Foreign Resident Value -- how much this matters to someone actually living
                              in Japan, derived from Research.Category
    Tourism Value        -- how much this matters to a visitor, derived from
                              Research.Category
    Seasonal Relevance   -- does Research.Season match the actual current
                              season right now
    Premium Potential    -- does this look enterprise/municipal-partnership
                              worthy (Usage Scope) or high-trust (Evidence
                              Level), either of which suggests it could
                              support a paid/B2B offering later
"""
import os
import sys
import datetime

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
REPO_ROOT = os.path.dirname(NOTION_BUILD_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, AUTOMATION_DIR)

from notion_api import load_env, query_database, get_prop  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")

# Research.Category is the existing 7-value select that also drives Update
# Level gating elsewhere -- reused here, not redefined.
CATEGORY_RESIDENT_VALUE = {
    "法律・制度": "Critical",
    "生活情報": "High",
    "イベント": "Medium",
    "日本文化": "Medium",
    "ニュース": "Medium",
    "旅行情報": "Low",
    "トレンド": "Low",
}
CATEGORY_TOURISM_VALUE = {
    "旅行情報": "Critical",
    "イベント": "High",
    "日本文化": "High",
    "トレンド": "Medium",
    "ニュース": "Low",
    "法律・制度": "Low",
    "生活情報": "Low",
}
TIER_POINTS = {"Critical": 20, "High": 15, "Medium": 10, "Low": 5}

SEASON_BY_MONTH = {
    12: "冬", 1: "冬", 2: "冬",
    3: "春", 4: "春", 5: "春",
    6: "夏", 7: "夏", 8: "夏",
    9: "秋", 10: "秋", 11: "秋",
}

PREMIUM_USAGE_SCOPES = {"Enterprise", "Municipal Partnership"}
PREMIUM_EVIDENCE_LEVELS = {"Official", "Verified"}


def current_season(today=None):
    today = today or datetime.date.today()
    return SEASON_BY_MONTH[today.month]


def score_freshness(page, today):
    created = page.get("created_time")
    if not created:
        return 0, "作成日時不明"
    created_date = datetime.date.fromisoformat(created[:10])
    days = (today - created_date).days
    if days <= 1:
        return 20, f"発見から{days}日"
    if days <= 3:
        return 15, f"発見から{days}日"
    if days <= 7:
        return 10, f"発見から{days}日"
    if days <= 14:
        return 5, f"発見から{days}日"
    return 0, f"発見から{days}日（滞留）"


def score_resident_value(category):
    tier = CATEGORY_RESIDENT_VALUE.get(category, "Medium")
    return TIER_POINTS[tier], f"{category or '未分類'} → {tier}"


def score_tourism_value(category):
    tier = CATEGORY_TOURISM_VALUE.get(category, "Medium")
    return TIER_POINTS[tier], f"{category or '未分類'} → {tier}"


def score_seasonal_relevance(season_tags, today):
    now_season = current_season(today)
    if now_season in season_tags:
        return 20, f"今が{now_season}（該当）"
    if "通年" in season_tags:
        return 12, "通年扱い"
    if not season_tags:
        return 8, "季節指定なし"
    return 3, f"今は{now_season}だが対象外（{', '.join(season_tags)}向け）"


def score_premium_potential(usage_scope, evidence_level):
    if PREMIUM_USAGE_SCOPES & set(usage_scope):
        return 20, f"Usage Scope: {', '.join(usage_scope)}"
    if evidence_level in PREMIUM_EVIDENCE_LEVELS:
        return 12, f"Evidence Level: {evidence_level}"
    return 5, "標準"


def score_research(page, today=None):
    today = today or datetime.date.today()
    category = get_prop(page, "Category", "select")
    season_tags = get_prop(page, "Season", "multi_select") or []
    usage_scope = get_prop(page, "Usage Scope", "multi_select") or []
    evidence_level = get_prop(page, "Evidence Level", "select")

    freshness, freshness_note = score_freshness(page, today)
    resident, resident_note = score_resident_value(category)
    tourism, tourism_note = score_tourism_value(category)
    seasonal, seasonal_note = score_seasonal_relevance(season_tags, today)
    premium, premium_note = score_premium_potential(usage_scope, evidence_level)

    total = freshness + resident + tourism + seasonal + premium
    return {
        "id": page["id"],
        "topic": get_prop(page, "Topic", "title"),
        "total": total,
        "breakdown": {
            "Freshness": (freshness, freshness_note),
            "Foreign Resident Value": (resident, resident_note),
            "Tourism Value": (tourism, tourism_note),
            "Seasonal Relevance": (seasonal, seasonal_note),
            "Premium Potential": (premium, premium_note),
        },
    }


def rank_research_candidates(env, limit=10, today=None):
    token = env["NOTION_TOKEN"]
    pages = query_database(token, env["RESEARCH_DB_ID"], filter_obj={
        "property": "Status", "select": {"equals": "New"}
    })
    scored = [score_research(p, today) for p in pages]
    scored.sort(key=lambda s: s["total"], reverse=True)
    return scored[:limit], len(scored)


def print_report(scored, total_count):
    print("\n" + "=" * 70)
    print(f"📊 Research Prioritization -- Status=New {total_count}件中、上位{len(scored)}件")
    print("=" * 70)
    for i, s in enumerate(scored, 1):
        print(f"{i}. [{s['total']:3d}点] {s['topic']}")
        for label, (pts, note) in s["breakdown"].items():
            print(f"     {label}: {pts:2d}点 ({note})")
    print()


def main():
    env = load_env(ENV_PATH)
    scored, total_count = rank_research_candidates(env)
    print_report(scored, total_count)


if __name__ == "__main__":
    main()
