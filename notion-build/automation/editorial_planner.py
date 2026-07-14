"""AI Editorial Planner -- Version 4 Phase 2.

Coverage Analyzer (coverage_analyzer.py) answers "what's missing?". This script
answers the next question: "what should I actually assign next?" It turns the
same coverage data into a prioritized, concrete editorial plan -- and can create
the Research records to act on it.

1. Reads Coverage Analysis data (reuses coverage_analyzer.aggregate() against the
   live Articles DB -- there is no separate stored "Coverage Analysis result" to
   read, the source of truth is always the current Articles DB).
2. Detects zero-coverage topics, low-coverage topics, and high-impact topics by
   combining article count with each Life Topic's real-life impact tier
   (life_topics.LIFE_TOPIC_IMPACT) -- a Critical topic with 3 articles still
   needs attention; a Low-impact topic with 1 article does not.
3. For each flagged topic, computes a deterministic 1-5 star priority (auditable,
   not left to the AI), then asks AI Gateway for the qualitative part: a reason,
   2-3 suggested article titles, and an expected Category (validated against the
   7 real Category values; Update Level is derived deterministically from that
   Category via generate_article_pipeline.compute_update_level, not guessed).
4. `--generate-research` creates real Research DB records (Status=New, Evidence
   Level=AI Suggested, Discovery Method=Gap Engine -- both already-existing select
   options, no schema change) for the selected plan items' suggested titles, so
   they surface in the Dashboard's existing "Today's Research" section for review.

No new database. Renders a CLI report and a dedicated "Editorial Planner" Notion
page (same table/summary-page pattern as Coverage Analysis).
"""
import os
import sys
import time
import argparse

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
REPO_ROOT = os.path.dirname(NOTION_BUILD_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, AUTOMATION_DIR)

from notion_api import load_env, notion_request, query_database, get_prop, set_env_value  # noqa: E402
import ai_gateway  # noqa: E402
import generate_article_pipeline as gap  # noqa: E402
from life_topics import LIFE_TOPICS, LIFE_TOPIC_IMPACT, DEFAULT_CATEGORY_FOR_TOPIC  # noqa: E402
from coverage_analyzer import aggregate, empty_bucket  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")

VALID_CATEGORIES = gap.LEVEL_1_CATEGORIES | gap.LEVEL_2_CATEGORIES

# A topic is included in the plan if its article count is at or below this
# threshold for its impact tier -- Critical topics stay "in need of attention"
# even with a few articles; Low-impact topics only flag when essentially empty.
INCLUSION_THRESHOLD = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}

PRIORITY_BY_STARS = {5: "High", 4: "High", 3: "Medium", 2: "Low", 1: "Low"}
URGENCY_BY_STARS = {5: "Critical", 4: "High", 3: "Medium", 2: "Low", 1: "Low"}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def compute_stars(impact, count):
    if impact == "Critical":
        if count == 0:
            return 5
        if count <= 2:
            return 4
        return 3
    if impact == "High":
        if count == 0:
            return 4
        if count <= 2:
            return 3
        return 2
    if impact == "Medium":
        if count == 0:
            return 3
        return 2
    return 1  # Low impact, only reached when count <= INCLUSION_THRESHOLD["Low"] == 1


def build_candidates(topic_stats):
    candidates = []
    for topic in LIFE_TOPICS:
        impact = LIFE_TOPIC_IMPACT[topic]
        b = topic_stats.get(topic, empty_bucket())
        count = b["count"]
        if count <= INCLUSION_THRESHOLD[impact]:
            candidates.append({
                "topic": topic, "impact": impact, "count": count,
                "stars": compute_stars(impact, count),
            })
    candidates.sort(key=lambda c: (-c["stars"], c["count"]))
    return candidates


def generate_plan_content(candidates):
    """Single AI call for the whole plan: reason / suggested titles / category per
    candidate topic. Returns candidates augmented with 'reason', 'titles', 'category'."""
    if not candidates:
        return []

    lines = []
    for c in candidates:
        lines.append(f"- {c['topic']}（現在{c['count']}件、影響度={c['impact']}、優先度{c['stars']}/5）")
    candidates_text = "\n".join(lines)
    category_list = "／".join(sorted(VALID_CATEGORIES))

    prompt = f"""あなたはARu（外国籍の方向け日本生活サポートメディア、コンセプト「Decode Japan」）の編集会議アシスタントです。
以下は、コンテンツが手薄またはリスクが高いと判定された生活トピックの一覧です（優先度が高い順）。

{candidates_text}

各トピックについて、次の記事化を具体的に検討できるよう、以下の情報を出力してください。
出力はこのフォーマットのまま、他の説明は付けないこと。トピックの区切りは "---" のみの行にすること。

TOPIC: <トピック名。入力のトピック名と完全一致させること>
REASON: <なぜ今このトピックの記事が必要か。読者の具体的な困りごとに触れて1〜2文で>
TITLE: <具体的な記事タイトル案。読者が実際に検索しそうな質問形式が望ましい>
TITLE: <具体的な記事タイトル案（1件目とは異なる切り口）>
CATEGORY: <以下のいずれか1つ：{category_list}>
---
"""
    _, text = ai_gateway.complete(prompt, max_tokens=2000)
    parsed = parse_plan(text)

    by_topic = {p["topic"]: p for p in parsed}
    result = []
    for c in candidates:
        p = by_topic.get(c["topic"], {})
        category = p.get("category")
        if category not in VALID_CATEGORIES:
            category = DEFAULT_CATEGORY_FOR_TOPIC[c["topic"]]
        titles = p.get("titles") or [f"{c['topic']}について知っておくべきこと"]
        result.append({
            **c,
            "reason": p.get("reason") or "コンテンツが手薄なため優先的な追加を推奨。",
            "titles": titles,
            "category": category,
            "update_level": gap.compute_update_level(category),
        })
    return result


def parse_plan(text):
    """Parse the TOPIC:/REASON:/TITLE:/CATEGORY: blocks, separated by '---' lines."""
    valid_topics = set(LIFE_TOPICS)
    blocks, current = [], None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line == "---":
            continue
        if line.startswith("TOPIC:"):
            if current:
                blocks.append(current)
            name = line[len("TOPIC:"):].strip()
            current = {"topic": name if name in valid_topics else None, "reason": "", "titles": [], "category": None}
            continue
        if current is None:
            continue
        if line.startswith("REASON:"):
            current["reason"] = line[len("REASON:"):].strip()
        elif line.startswith("TITLE:"):
            t = line[len("TITLE:"):].strip()
            if t:
                current["titles"].append(t)
        elif line.startswith("CATEGORY:"):
            current["category"] = line[len("CATEGORY:"):].strip()
    if current:
        blocks.append(current)
    return [b for b in blocks if b["topic"]]


# --- rendering ---

def stars_str(n):
    return "★" * n + "☆" * (5 - n)


def print_report(plan):
    print("\n" + "=" * 70)
    print("📝 Editorial Planner — 優先編集プラン")
    print("=" * 70)
    if not plan:
        print("  (現時点で優先的に追加すべきトピックはありません)")
        return
    for item in plan:
        print(f"\n{stars_str(item['stars'])}  Priority {item['stars']}/5  ({item['impact']}影響度, 現在{item['count']}件)")
        print(f"Topic: {item['topic']}")
        print(f"Reason: {item['reason']}")
        print("Suggested article titles:")
        for t in item["titles"]:
            print(f"  - {t}")
        print(f"Expected Update Level: {item['update_level']}")
        print(f"Expected Category: {item['category']}")
    print()


def rt(text):
    return [{"text": {"content": str(text)[:2000]}}]


def build_page_blocks(plan):
    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    blocks = [
        {"heading_1": {"rich_text": rt("📝 Editorial Planner")}},
        {"paragraph": {"rich_text": rt(f"最終更新: {now}（editorial_planner.py、優先度が高い順）")}},
        {"paragraph": {"rich_text": rt("Research作成: python3 editorial_planner.py --generate-research （--topics \"トピック名,トピック名\" または --limit N で選択可）")}},
        {"divider": {}},
    ]
    if not plan:
        blocks.append({"paragraph": {"rich_text": rt("現時点で優先的に追加すべきトピックはありません。")}})
        return blocks

    for item in plan:
        blocks.append({"heading_2": {"rich_text": rt(f"{stars_str(item['stars'])} Priority {item['stars']}/5 — {item['topic']}")}})
        blocks.append({"paragraph": {"rich_text": rt(f"Reason: {item['reason']}")}})
        blocks.append({"paragraph": {"rich_text": rt("Suggested article titles:")}})
        for t in item["titles"]:
            blocks.append({"bulleted_list_item": {"rich_text": rt(t)}})
        blocks.append({"paragraph": {"rich_text": rt(f"Expected Update Level: {item['update_level']}　|　Expected Category: {item['category']}")}})
        blocks.append({"divider": {}})
    return blocks


def get_or_create_page(env):
    token = env["NOTION_TOKEN"]
    page_id = env.get("EDITORIAL_PLANNER_PAGE_ID")
    if page_id:
        try:
            page = notion_request(token, "GET", f"/pages/{page_id}")
            if not page.get("archived"):
                return page_id
        except RuntimeError:
            pass

    page = notion_request(token, "POST", "/pages", {
        "parent": {"page_id": env["ARU_STUDIO_PAGE_ID"]},
        "properties": {"title": {"title": rt("Editorial Planner")}},
    })
    set_env_value(ENV_PATH, "EDITORIAL_PLANNER_PAGE_ID", page["id"])
    log(f"Created new Editorial Planner page: {page['id']}")
    return page["id"]


def clear_page(token, page_id):
    children = notion_request(token, "GET", f"/blocks/{page_id}/children?page_size=100")
    for b in children.get("results", []):
        notion_request(token, "DELETE", f"/blocks/{b['id']}")


def write_page(env, blocks):
    token = env["NOTION_TOKEN"]
    page_id = get_or_create_page(env)
    log("Clearing previous Editorial Planner page content...")
    clear_page(token, page_id)
    for i in range(0, len(blocks), 90):
        notion_request(token, "PATCH", f"/blocks/{page_id}/children", {"children": blocks[i:i + 90]})
    return page_id


# --- Generate Research action ---

def generate_research(env, plan, topics=None, limit=None):
    token = env["NOTION_TOKEN"]
    research_db = env["RESEARCH_DB_ID"]

    selected = plan
    if topics:
        wanted = {t.strip() for t in topics.split(",") if t.strip()}
        selected = [item for item in plan if item["topic"] in wanted]
    elif limit:
        selected = plan[:limit]

    if not selected:
        log("No plan items selected for Research generation.")
        return []

    created = []
    for item in selected:
        priority = PRIORITY_BY_STARS[item["stars"]]
        urgency = URGENCY_BY_STARS[item["stars"]]
        for title in item["titles"]:
            props = {
                "Topic": {"title": rt(title)},
                "Category": {"select": {"name": item["category"]}},
                "Summary": {"rich_text": rt(f"{item['reason']}（Editorial Plannerによる自動提案。Life Topic: {item['topic']}、Priority {item['stars']}/5）")},
                "Evidence Level": {"select": {"name": "AI Suggested"}},
                "Status": {"select": {"name": "New"}},
                "Priority": {"select": {"name": priority}},
                "Discovery Method": {"select": {"name": "Gap Engine"}},
                "Urgency": {"select": {"name": urgency}},
                "AI Generated": {"checkbox": True},
                "Human Reviewed": {"checkbox": False},
            }
            page = notion_request(token, "POST", "/pages", {
                "parent": {"database_id": research_db}, "properties": props
            })
            log(f"  Research created: {page['id']} - {title[:50]} (Topic={item['topic']}, Priority={priority})")
            created.append(page["id"])
    return created


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate-research", action="store_true", help="Create Research records for the plan's suggested titles")
    parser.add_argument("--topics", default=None, help="Comma-separated Life Topic names to select (default: all plan items)")
    parser.add_argument("--limit", type=int, default=None, help="Only the top N plan items by priority (ignored if --topics is set)")
    args = parser.parse_args()

    env = load_env(ENV_PATH)
    token = env["NOTION_TOKEN"]
    articles_db = env["ARTICLES_DB_ID"]

    log("Querying all Articles (excluding Archived)...")
    pages = query_database(token, articles_db, filter_obj={
        "property": "Status", "select": {"does_not_equal": "Archived"}
    })
    log(f"  {len(pages)} article(s)")

    topic_stats = aggregate(pages, lambda p: get_prop(p, "Life Topics", "multi_select"))
    candidates = build_candidates(topic_stats)
    log(f"Flagged {len(candidates)} topic(s) for the editorial plan")

    log("Generating plan content via AI Gateway...")
    plan = generate_plan_content(candidates)

    print_report(plan)

    blocks = build_page_blocks(plan)
    log("Writing Editorial Planner Notion page...")
    page_id = write_page(env, blocks)
    log(f"Editorial Planner page: {page_id}")

    if args.generate_research:
        log("Generating Research records for selected plan items...")
        created = generate_research(env, plan, topics=args.topics, limit=args.limit)
        log(f"DONE. Created {len(created)} Research record(s).")
    else:
        log("DONE. (Run with --generate-research to create Research records for these ideas.)")


if __name__ == "__main__":
    main()
