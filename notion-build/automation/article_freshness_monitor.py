"""Article Freshness Monitor -- Version 4 prep.

Runs daily against the existing Articles database (no new database). For every
Article, computes how many days have passed since it was last verified and
compares that against a review interval based on Update Level:

    Level 1 (event/culture/travel/lifestyle/news/trend): 90 days
    Level 2 (law/system): 30 days
    Level 3: LEVEL_3_INTERVAL_DAYS days (configurable, recommended 14-30)

If an Article exceeds its interval, it is flagged: Freshness Status=Needs
Update, Days Since Verification is saved, and a Freshness Urgency Score
(percentage of the interval consumed) is stored so the Dashboard's "Update
Needed" section can sort by urgency without needing a separate Alerts
database -- the flagged Article record IS the alert.

Independently of the time-based check, this script also cross-checks Law
Update (Update Status=Confirmed/Reflecting to Article), Source Monitor
(Change Detected=true), and Event Calendar (Status=Cancelled) for changes
linked to an Article via their existing relations, and force-flags those
Articles (with an AI-generated one-line recommendation explaining why) even
if their time-based interval hasn't elapsed yet.
"""
import os
import sys
import time
import datetime

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
REPO_ROOT = os.path.dirname(NOTION_BUILD_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from notion_api import load_env, notion_request, query_database, get_prop  # noqa: E402
import ai_gateway  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")

# Level 3 interval is configurable: change this single value (recommended range 14-30).
LEVEL_3_INTERVAL_DAYS = 30

FRESHNESS_INTERVALS = {
    1: 90,
    2: 30,
    3: max(14, min(30, LEVEL_3_INTERVAL_DAYS)),
}

# External-signal overrides (Law Update / Source Monitor / Event Calendar) always outrank
# a purely time-based overdue item, however overdue, so they sort to the very top.
FORCE_FLAG_URGENCY_SCORE = 150

LAW_UPDATE_TRIGGER_STATUSES = {"Confirmed", "Reflecting to Article"}
EVENT_CALENDAR_TRIGGER_STATUSES = {"Cancelled"}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def ensure_schema(token, articles_db_id):
    notion_request(token, "PATCH", f"/databases/{articles_db_id}", {
        "properties": {
            "Freshness Status": {"select": {"options": [
                {"name": "Fresh", "color": "green"},
                {"name": "Needs Update", "color": "red"},
            ]}},
            "Days Since Verification": {"number": {}},
            "Freshness Urgency Score": {"number": {}},
            "Freshness Checked Date": {"date": {}},
            "Freshness Note": {"rich_text": {}},
        }
    })


def parse_date(date_str):
    if not date_str:
        return None
    return datetime.date.fromisoformat(date_str[:10])


def get_baseline_date(page):
    """Priority: explicit verification > last review > publish date > record creation."""
    for prop_name in ("Last Verified Date", "Review Date", "Published Date"):
        raw = get_prop(page, prop_name, "date")
        parsed = parse_date(raw)
        if parsed:
            return parsed, prop_name
    created = page.get("created_time")
    if created:
        return parse_date(created), "Created Time"
    return None, None


def get_interval(update_level):
    return FRESHNESS_INTERVALS.get(update_level, FRESHNESS_INTERVALS[1])


def check_article(page, today):
    title = get_prop(page, "Title", "title")
    update_level = get_prop(page, "Update Level", "number") or 1
    baseline_date, baseline_source = get_baseline_date(page)
    if baseline_date is None:
        return None

    days_since = (today - baseline_date).days
    interval = get_interval(update_level)
    urgency_score = round(days_since / interval * 100) if interval else 0
    needs_update = days_since > interval

    return {
        "id": page["id"], "title": title, "update_level": update_level,
        "days_since": days_since, "interval": interval, "urgency_score": urgency_score,
        "needs_update": needs_update, "baseline_source": baseline_source,
    }


def find_law_update_signals(token, law_update_db_id):
    """article_id -> list of (law_name, impact_summary) for confirmed-but-unreflected law changes."""
    pages = query_database(token, law_update_db_id, filter_obj={
        "or": [{"property": "Update Status", "select": {"equals": s}} for s in LAW_UPDATE_TRIGGER_STATUSES]
    })
    signals = {}
    for page in pages:
        law_name = get_prop(page, "Law Name", "title") or "(無題の法改正)"
        impact = get_prop(page, "Impact Summary", "rich_text") or ""
        for article_id in get_prop(page, "Affected Articles", "relation"):
            signals.setdefault(article_id, []).append(("Law Update", law_name, impact))
    return signals


def find_event_calendar_signals(token, event_calendar_db_id):
    """article_id -> list of (event_name, note) for cancelled events with a linked Article."""
    pages = query_database(token, event_calendar_db_id, filter_obj={
        "or": [{"property": "Status", "select": {"equals": s}} for s in EVENT_CALENDAR_TRIGGER_STATUSES]
    })
    signals = {}
    for page in pages:
        event_name = get_prop(page, "Event Name", "title") or "(無題のイベント)"
        for article_id in get_prop(page, "Related Article", "relation"):
            signals.setdefault(article_id, []).append(("Event Calendar", event_name, "イベントが中止（Status=Cancelled）"))
    return signals


def find_source_monitor_signals(token, source_monitor_db_id, research_db_id):
    """article_id -> list of (source_name, diff_summary) via Source Monitor -> Research -> Articles.

    Two independent paths to Research, merged (ARu Intelligence Phase 1):
    (a) Source Monitor.Triggered Research -- set when sync_source_monitor_to_research.py
        auto-drafted a new Research record for this change.
    (b) Source Monitor.Source -> Source Library.Related Research -- catches Research a
        human already linked to that source *before* this change was detected, which
        (a) alone would miss since Triggered Research is never retroactively backfilled.
    """
    pages = query_database(token, source_monitor_db_id, filter_obj={
        "property": "Change Detected", "checkbox": {"equals": True}
    })
    signals = {}
    for page in pages:
        monitor_name = get_prop(page, "Monitor Entry", "title") or "(無題の監視エントリ)"
        diff_summary = get_prop(page, "Diff Summary", "rich_text") or get_prop(page, "Change Summary", "rich_text") or ""

        research_ids = set(get_prop(page, "Triggered Research", "relation"))
        for source_id in get_prop(page, "Source", "relation"):
            try:
                source_page = notion_request(token, "GET", f"/pages/{source_id}")
            except RuntimeError:
                continue
            research_ids.update(get_prop(source_page, "Related Research", "relation"))

        for research_id in research_ids:
            try:
                research_page = notion_request(token, "GET", f"/pages/{research_id}")
            except RuntimeError:
                continue
            for article_id in get_prop(research_page, "Converted Article", "relation"):
                signals.setdefault(article_id, []).append(("Source Monitor", monitor_name, diff_summary))
    return signals


def generate_recommendation_note(reasons):
    """reasons: list of (source_type, name, summary). Returns a short AI-written internal note."""
    lines = [f"- [{src}] {name}: {summary}" for src, name, summary in reasons]
    prompt = (
        "あなたはARu編集部の編集アシスタントです。以下は、記事に関連する外部情報源で検知された変化のリストです。\n"
        "この記事を再レビューすべき理由を、編集者向けの内部メモとして1〜2文の簡潔な日本語でまとめてください。\n"
        "読者向けの文章ではありません。前置きや挨拶は不要です。\n\n"
        + "\n".join(lines)
    )
    try:
        _, text = ai_gateway.complete(prompt, max_tokens=200)
        return text.strip()
    except Exception as e:
        return f"外部情報源で変化を検知したため再レビューを推奨（AI要約生成に失敗: {e}）。詳細: {lines[0] if lines else ''}"


def main():
    env = load_env(ENV_PATH)
    token = env["NOTION_TOKEN"]
    articles_db = env["ARTICLES_DB_ID"]
    today = datetime.date.today()

    log("Ensuring Articles DB schema has Freshness properties...")
    ensure_schema(token, articles_db)

    log("Collecting cross-DB change signals (Law Update / Source Monitor / Event Calendar)...")
    law_signals = find_law_update_signals(token, env["LAW_UPDATE_DB_ID"])
    event_signals = find_event_calendar_signals(token, env["EVENT_CALENDAR_DB_ID"])
    source_signals = find_source_monitor_signals(token, env["SOURCE_MONITOR_DB_ID"], env["RESEARCH_DB_ID"])
    log(f"  Law Update signals: {len(law_signals)} article(s)")
    log(f"  Event Calendar signals: {len(event_signals)} article(s)")
    log(f"  Source Monitor signals: {len(source_signals)} article(s)")

    combined_signals = {}
    for signals in (law_signals, event_signals, source_signals):
        for article_id, reasons in signals.items():
            combined_signals.setdefault(article_id, []).extend(reasons)

    log("Querying all Articles (excluding Archived)...")
    pages = query_database(token, articles_db, filter_obj={
        "property": "Status", "select": {"does_not_equal": "Archived"}
    })
    log(f"  {len(pages)} article(s) to check")

    checked = 0
    time_based_flagged = 0
    signal_flagged = 0
    fresh_count = 0
    skipped_no_baseline = 0
    by_level = {1: 0, 2: 0, 3: 0}

    for page in pages:
        result = check_article(page, today)
        if result is None:
            skipped_no_baseline += 1
            log(f"  SKIP (no baseline date): {get_prop(page, 'Title', 'title')}")
            continue

        checked += 1
        by_level[result["update_level"]] = by_level.get(result["update_level"], 0) + 1

        props = {
            "Days Since Verification": {"number": result["days_since"]},
            "Freshness Urgency Score": {"number": result["urgency_score"]},
            "Freshness Checked Date": {"date": {"start": today.isoformat()}},
        }

        reasons = combined_signals.get(result["id"])
        if reasons:
            props["Freshness Status"] = {"select": {"name": "Needs Update"}}
            props["Freshness Urgency Score"] = {"number": max(result["urgency_score"], FORCE_FLAG_URGENCY_SCORE)}
            props["Freshness Note"] = {"rich_text": [{"text": {"content": generate_recommendation_note(reasons)}}]}
            signal_flagged += 1
            log(f"  NEEDS UPDATE (external signal, {len(reasons)} reason(s)): {result['title']}")
        elif result["needs_update"]:
            props["Freshness Status"] = {"select": {"name": "Needs Update"}}
            props["Freshness Note"] = {"rich_text": [{"text": {
                "content": f"定期レビュー期限超過（Update Level {result['update_level']}、基準日={result['baseline_source']}、{result['interval']}日を{result['days_since'] - result['interval']}日超過）"
            }}]}
            time_based_flagged += 1
            log(f"  NEEDS UPDATE (overdue {result['days_since']}/{result['interval']}d): {result['title']}")
        else:
            props["Freshness Status"] = {"select": {"name": "Fresh"}}
            props["Freshness Note"] = {"rich_text": []}
            fresh_count += 1

        notion_request(token, "PATCH", f"/pages/{result['id']}", {"properties": props})

    log("")
    log("=" * 70)
    log(f"DONE. Checked {checked}/{len(pages)} articles ({skipped_no_baseline} skipped, no baseline date).")
    log(f"  Fresh: {fresh_count}")
    log(f"  Needs Update (time-based, overdue): {time_based_flagged}")
    log(f"  Needs Update (external signal): {signal_flagged}")
    log(f"  Total Needs Update: {time_based_flagged + signal_flagged}")
    log(f"  By Update Level checked: L1={by_level.get(1, 0)} L2={by_level.get(2, 0)} L3={by_level.get(3, 0)}")


if __name__ == "__main__":
    main()
