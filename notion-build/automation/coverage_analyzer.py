"""Coverage Analyzer.

Lets the editor-in-chief (Rei) decide in ~5 minutes each morning what to add or
update, by answering two questions:

1. カテゴリ分析 -- for each Life Topic (see life_topics.py), how many articles
   exist, when were they last touched, how fresh are they, what Update Level mix
   do they have, and how many are still waiting on review.
2. 不足分析 -- given that breakdown (including topics with zero articles), what's
   missing, what should be prioritized, and ~10 concrete new article themes --
   judged against what a foreign resident/visitor in Japan actually needs, not
   just against the current article count.

No new database: aggregates the existing Articles DB using Life Topics (multi-
select) and reuses Freshness Status / Update Level / Review Result already
maintained by article_freshness_monitor.py and reviewer_agent.py. Renders both a
CLI report and a dedicated "Coverage Analysis" Notion page (real table blocks,
not a manual-linked-view placeholder, since this is a computed summary rather
than a live filtered view of records).
"""
import os
import re
import sys
import time
import datetime
from collections import defaultdict

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
REPO_ROOT = os.path.dirname(NOTION_BUILD_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, AUTOMATION_DIR)

from notion_api import load_env, notion_request, query_database, get_prop, set_env_value  # noqa: E402
import ai_gateway  # noqa: E402
from life_topics import LIFE_TOPICS  # noqa: E402
from article_freshness_monitor import get_baseline_date  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def ensure_schema(token, articles_db_id):
    notion_request(token, "PATCH", f"/databases/{articles_db_id}", {
        "properties": {
            "Life Topics": {"multi_select": {"options": [{"name": t} for t in LIFE_TOPICS]}},
        }
    })


def empty_bucket():
    return {
        "count": 0, "latest_date": None,
        "fresh": 0, "needs_update": 0, "freshness_unset": 0,
        "level_1": 0, "level_2": 0, "level_3": 0,
        "review_waiting": 0,
    }


def aggregate(pages, key_fn):
    """key_fn(page) -> list of bucket keys this page belongs to (may be empty)."""
    buckets = defaultdict(empty_bucket)
    for page in pages:
        keys = key_fn(page)
        if not keys:
            continue

        freshness = get_prop(page, "Freshness Status", "select")
        update_level = get_prop(page, "Update Level", "number") or 1
        review_result = get_prop(page, "Review Result", "select")
        baseline_date, _ = get_baseline_date(page)

        for key in keys:
            b = buckets[key]
            b["count"] += 1
            if baseline_date and (b["latest_date"] is None or baseline_date > b["latest_date"]):
                b["latest_date"] = baseline_date
            if freshness == "Fresh":
                b["fresh"] += 1
            elif freshness == "Needs Update":
                b["needs_update"] += 1
            else:
                b["freshness_unset"] += 1
            if update_level == 1:
                b["level_1"] += 1
            elif update_level == 2:
                b["level_2"] += 1
            elif update_level == 3:
                b["level_3"] += 1
            if review_result != "Pass":
                b["review_waiting"] += 1
    return buckets


def generate_gap_analysis(topic_stats):
    """topic_stats: dict of topic -> bucket (includes zero-count topics)."""
    lines = []
    for topic in LIFE_TOPICS:
        b = topic_stats.get(topic, empty_bucket())
        lines.append(f"- {topic}: {b['count']}件")
    counts_text = "\n".join(lines)

    prompt = f"""あなたはARu（外国籍の方向け日本生活サポートメディア、コンセプト「Decode Japan」）の編集アシスタントです。
以下は、現在の記事数を生活トピック別に集計したものです。

{counts_text}

これは単なる記事数の集計です。あなたの仕事は、**単純に件数が少ないトピックを機械的に挙げるのではなく**、
「外国籍の方が日本で生活する上で本当に必要な情報が十分網羅されているか」という視点で分析することです。
例えば、件数がゼロ、または少数でも実際には緊急性・生活への影響度が高いトピック（医療、災害、子育て、介護など）は特に重視してください。

以下の3つを出力してください（このまま、他の説明は付けないこと）。

MISSING: <不足している、または手薄なトピック名。記事数0〜少数かつ重要度が高いものを優先。1行に1つ、5〜8件>
PRIORITY: <特に優先して追加すべきトピック> - <なぜ優先すべきか、1文の理由>
（PRIORITY行を3〜5件）
THEME: <具体的な新規記事テーマ案（読者が実際に検索しそうな質問形式が望ましい）>
（THEME行を10件、複数のトピックにまたがるよう分散させること）
"""
    _, text = ai_gateway.complete(prompt, max_tokens=1200)
    missing, priority, themes = parse_gap_analysis(text)
    return missing, priority, themes, text


def parse_gap_analysis(text):
    """Robust to two shapes Claude tends to produce:
    (a) 'MISSING: item' on one line per item, or
    (b) 'MISSING:' header alone, followed by bare item lines until the next header.
    Also splits a comma/読点-joined single line into separate items."""
    missing, priority, themes = [], [], []
    mode = None
    for raw_line in text.splitlines():
        line = raw_line.strip().lstrip("-").strip()
        if not line:
            continue
        for prefix, bucket, name in (("MISSING:", missing, "missing"), ("PRIORITY:", priority, "priority"), ("THEME:", themes, "themes")):
            if line.startswith(prefix):
                mode = name
                rest = line[len(prefix):].strip()
                if rest:
                    (missing if name == "missing" else priority if name == "priority" else themes).extend(
                        [x.strip() for x in re.split(r"[、,]", rest) if x.strip()] if name == "missing" else [rest]
                    )
                break
        else:
            if mode == "missing":
                missing.extend([x.strip() for x in re.split(r"[、,]", line) if x.strip()])
            elif mode == "priority":
                priority.append(line)
            elif mode == "themes":
                themes.append(line)
    return missing, priority, themes


# --- rendering ---

def rt(text):
    return [{"text": {"content": str(text)[:2000]}}]


def table_row(cells):
    return {"table_row": {"cells": [rt(c) for c in cells]}}


def stats_table(stats, order):
    header = ["トピック", "記事数", "直近更新", "Fresh/Needs Update", "L1/L2/L3", "Review待ち"]
    rows = [table_row(header)]
    for key in order:
        b = stats.get(key, empty_bucket())
        latest = b["latest_date"].isoformat() if b["latest_date"] else "-"
        rows.append(table_row([
            key, b["count"], latest,
            f"{b['fresh']}/{b['needs_update']}",
            f"{b['level_1']}/{b['level_2']}/{b['level_3']}",
            b["review_waiting"],
        ]))
    return {
        "table": {
            "table_width": len(header),
            "has_column_header": True,
            "has_row_header": True,
            "children": rows,
        }
    }


def build_page_blocks(topic_stats, category_stats, missing, priority, themes, raw_ai_text):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    topic_order = sorted(LIFE_TOPICS, key=lambda t: topic_stats.get(t, empty_bucket())["count"])
    category_order = sorted(category_stats.keys(), key=lambda c: category_stats[c]["count"])

    blocks = [
        {"heading_1": {"rich_text": rt("📊 Coverage Analysis")}},
        {"paragraph": {"rich_text": rt(f"最終更新: {now}（coverage_analyzer.py、記事数の少ない順に表示）")}},
        {"divider": {}},
        {"heading_2": {"rich_text": rt("① Life Topic別 内訳")}},
        {"paragraph": {"rich_text": rt("外国籍の方の生活ニーズに基づく22トピックでの分類（1記事が複数トピックに紐づく場合あり）")}},
        stats_table(topic_stats, topic_order),
        {"divider": {}},
        {"heading_2": {"rich_text": rt("② 既存Category別 内訳（参考）")}},
        {"paragraph": {"rich_text": rt("Update Levelを決定する既存の7分類。参考情報として掲載")}},
        stats_table(category_stats, category_order),
        {"divider": {}},
        {"heading_2": {"rich_text": rt("🔴 不足しています")}},
    ]

    if missing:
        blocks += [{"bulleted_list_item": {"rich_text": rt(m)}} for m in missing]
    else:
        blocks.append({"paragraph": {"rich_text": rt("(なし)")}})

    blocks += [
        {"divider": {}},
        {"heading_2": {"rich_text": rt("🟡 優先して追加すべきトピック")}},
    ]
    if priority:
        blocks += [{"bulleted_list_item": {"rich_text": rt(p)}} for p in priority]
    else:
        blocks.append({"paragraph": {"rich_text": rt("(なし)")}})

    blocks += [
        {"divider": {}},
        {"heading_2": {"rich_text": rt("✏️ おすすめ新規記事テーマ")}},
    ]
    if themes:
        blocks += [{"numbered_list_item": {"rich_text": rt(t)}} for t in themes]
    else:
        blocks.append({"paragraph": {"rich_text": rt("(なし)")}})

    return blocks


def get_or_create_page(env):
    token = env["NOTION_TOKEN"]
    page_id = env.get("COVERAGE_ANALYSIS_PAGE_ID")
    if page_id:
        try:
            page = notion_request(token, "GET", f"/pages/{page_id}")
            if not page.get("archived"):
                return page_id
        except RuntimeError:
            pass

    page = notion_request(token, "POST", "/pages", {
        "parent": {"page_id": env["ARU_STUDIO_PAGE_ID"]},
        "properties": {"title": {"title": rt("Coverage Analysis")}},
    })
    set_env_value(ENV_PATH, "COVERAGE_ANALYSIS_PAGE_ID", page["id"])
    log(f"Created new Coverage Analysis page: {page['id']}")
    return page["id"]


def clear_page(token, page_id):
    children = notion_request(token, "GET", f"/blocks/{page_id}/children?page_size=100")
    for b in children.get("results", []):
        notion_request(token, "DELETE", f"/blocks/{b['id']}")


def write_page(env, blocks):
    token = env["NOTION_TOKEN"]
    page_id = get_or_create_page(env)
    log("Clearing previous Coverage Analysis page content...")
    clear_page(token, page_id)
    # Notion allows up to 100 children per append call.
    for i in range(0, len(blocks), 90):
        notion_request(token, "PATCH", f"/blocks/{page_id}/children", {"children": blocks[i:i + 90]})
    return page_id


def print_report(topic_stats, category_stats, missing, priority, themes):
    print("\n" + "=" * 70)
    print("① Life Topic別 内訳（記事数の少ない順）")
    print("=" * 70)
    for topic in sorted(LIFE_TOPICS, key=lambda t: topic_stats.get(t, empty_bucket())["count"]):
        b = topic_stats.get(topic, empty_bucket())
        latest = b["latest_date"].isoformat() if b["latest_date"] else "-"
        print(f"  {topic:12s} 記事数={b['count']:3d}  直近更新={latest}  "
              f"Fresh/Needs={b['fresh']}/{b['needs_update']}  "
              f"L1/L2/L3={b['level_1']}/{b['level_2']}/{b['level_3']}  Review待ち={b['review_waiting']}")

    print("\n" + "=" * 70)
    print("② 既存Category別 内訳（参考）")
    print("=" * 70)
    for cat in sorted(category_stats.keys(), key=lambda c: category_stats[c]["count"]):
        b = category_stats[cat]
        print(f"  {cat}: {b['count']}件")

    print("\n" + "=" * 70)
    print("🔴 不足しています")
    print("=" * 70)
    for m in missing:
        print(f"  ・{m}")

    print("\n" + "=" * 70)
    print("🟡 優先して追加すべきトピック")
    print("=" * 70)
    for p in priority:
        print(f"  ・{p}")

    print("\n" + "=" * 70)
    print("✏️ おすすめ新規記事テーマ")
    print("=" * 70)
    for i, t in enumerate(themes, 1):
        print(f"  {i}. {t}")
    print()


def main():
    env = load_env(ENV_PATH)
    token = env["NOTION_TOKEN"]
    articles_db = env["ARTICLES_DB_ID"]

    log("Ensuring Articles DB schema has Life Topics property...")
    ensure_schema(token, articles_db)

    log("Querying all Articles (excluding Archived)...")
    pages = query_database(token, articles_db, filter_obj={
        "property": "Status", "select": {"does_not_equal": "Archived"}
    })
    log(f"  {len(pages)} article(s)")

    topic_stats = aggregate(pages, lambda p: get_prop(p, "Life Topics", "multi_select"))
    category_stats = aggregate(pages, lambda p: [get_prop(p, "Category", "select")] if get_prop(p, "Category", "select") else [])

    log("Running AI gap analysis...")
    missing, priority, themes, raw_text = generate_gap_analysis(topic_stats)
    log(f"  Missing: {len(missing)}, Priority: {len(priority)}, Themes: {len(themes)}")

    print_report(topic_stats, category_stats, missing, priority, themes)

    blocks = build_page_blocks(topic_stats, category_stats, missing, priority, themes, raw_text)
    log("Writing Coverage Analysis Notion page...")
    page_id = write_page(env, blocks)
    log(f"DONE. Coverage Analysis page: {page_id}")


if __name__ == "__main__":
    main()
