"""Duplicate Prevention Report -- Version 4 Phase 4.

Reads today's events from duplicate_guard.py's local log and reports on how the
"1 Research Topic = 1 Article" rule performed today: how many Articles were
actually generated, how many topics were caught and skipped before generation,
and at what pipeline stage each one already existed.

Renders a CLI report and a dedicated "Duplicate Prevention" Notion page (same
computed-summary-page pattern as Coverage Analysis / Editorial Planner), linked
from a new Dashboard section.

Known limitation: the underlying log (automation/logs/duplicate_prevention.jsonl)
is local to whichever machine ran the generation scripts -- it is not synced to
Notion or Git. "Today's" counts only reflect activity from this machine.
"""
import os
import sys
import json
import time
import datetime

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
REPO_ROOT = os.path.dirname(NOTION_BUILD_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, AUTOMATION_DIR)

from notion_api import load_env, notion_request, set_env_value  # noqa: E402
from duplicate_guard import LOG_PATH  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def read_today_events():
    if not os.path.exists(LOG_PATH):
        return []
    today = datetime.date.today().isoformat()
    events = []
    with open(LOG_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("timestamp", "").startswith(today):
                events.append(e)
    return events


def summarize(events):
    generated = [e for e in events if e.get("event") == "Generated"]
    skipped = [e for e in events if e.get("event") == "Already Exists"]
    return generated, skipped


def print_report(generated, skipped):
    print("\n" + "=" * 70)
    print("🛡 Duplicate Prevention -- 本日のレポート")
    print("=" * 70)
    print(f"本日の生成件数: {len(generated)}")
    print(f"生成スキップ件数: {len(skipped)}")
    print(f"重複検知件数: {len(skipped)}")
    if skipped:
        print("\nAlready Exists一覧:")
        for s in skipped:
            print(f"  - {s.get('topic')} (段階: {s.get('stage')})")
    else:
        print("\n重複なし ✅")
    print()


def rt(text):
    return [{"text": {"content": str(text)[:2000]}}]


def build_page_blocks(generated, skipped):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    blocks = [
        {"heading_1": {"rich_text": rt("🛡 Duplicate Prevention")}},
        {"paragraph": {"rich_text": rt(f"最終更新: {now}（duplicate_prevention_report.py。「1 Research Topic = 1 Article」の実施状況）")}},
        {"divider": {}},
        {"paragraph": {"rich_text": rt(f"本日の生成件数: {len(generated)}")}},
        {"paragraph": {"rich_text": rt(f"生成スキップ件数: {len(skipped)}")}},
        {"paragraph": {"rich_text": rt(f"重複検知件数: {len(skipped)}")}},
        {"divider": {}},
        {"heading_2": {"rich_text": rt("Already Exists一覧")}},
    ]
    if skipped:
        for s in skipped:
            blocks.append({"bulleted_list_item": {"rich_text": rt(f"{s.get('topic')}（段階: {s.get('stage')}）")}})
    else:
        blocks.append({"paragraph": {"rich_text": rt("重複なし ✅")}})
    return blocks


def get_or_create_page(env):
    token = env["NOTION_TOKEN"]
    page_id = env.get("DUPLICATE_PREVENTION_PAGE_ID")
    if page_id:
        try:
            page = notion_request(token, "GET", f"/pages/{page_id}")
            if not page.get("archived"):
                return page_id
        except RuntimeError:
            pass

    page = notion_request(token, "POST", "/pages", {
        "parent": {"page_id": env["ARU_STUDIO_PAGE_ID"]},
        "properties": {"title": {"title": rt("Duplicate Prevention")}},
    })
    set_env_value(ENV_PATH, "DUPLICATE_PREVENTION_PAGE_ID", page["id"])
    log(f"Created new Duplicate Prevention page: {page['id']}")
    return page["id"]


def clear_page(token, page_id):
    children = notion_request(token, "GET", f"/blocks/{page_id}/children?page_size=100")
    for b in children.get("results", []):
        notion_request(token, "DELETE", f"/blocks/{b['id']}")


def write_page(env, blocks):
    token = env["NOTION_TOKEN"]
    page_id = get_or_create_page(env)
    log("Clearing previous Duplicate Prevention page content...")
    clear_page(token, page_id)
    for i in range(0, len(blocks), 90):
        notion_request(token, "PATCH", f"/blocks/{page_id}/children", {"children": blocks[i:i + 90]})
    return page_id


def main():
    env = load_env(ENV_PATH)
    events = read_today_events()
    generated, skipped = summarize(events)
    print_report(generated, skipped)

    blocks = build_page_blocks(generated, skipped)
    log("Writing Duplicate Prevention Notion page...")
    page_id = write_page(env, blocks)
    log(f"DONE. Duplicate Prevention page: {page_id}")


if __name__ == "__main__":
    main()
