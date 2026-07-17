"""Source Watcher -- ARu Intelligence Phase 1.

Builds the one missing piece in an otherwise-already-built pipeline: nothing
in this repo has ever actually fetched an external URL and detected whether
an official source changed. `Source Monitor.Change Detected` has always been
a manually-set checkbox. Everything downstream of it -- Research auto-draft
(`sync_source_monitor_to_research.py`), Article force-flagging
(`article_freshness_monitor.py`), Publishing Center, and the Dashboard/AI
Command Center's Source Monitor Alerts sections -- already exists and is
already tested; it has simply never been fed real data.

This script closes that gap and nothing else:
    Source Library (existing DB, static ledger of trusted sources)
      -> for each due source with a real URL, fetch + hash its text
      -> unchanged: just update Last Checked
      -> changed: create a Source Monitor record (Change Detected=true,
         Impact Level, AI-written Diff Summary) and update Source Library's
         Last Checked + Last Content Hash

Only one schema change anywhere: `Last Content Hash` (rich_text) added to
Source Library, so the previous-content fingerprint survives between runs
and across machines (Notion-synced, not a local file).

Government/regulatory sources are flagged only -- this script never creates
or touches a Law Update record. Law Update carries Update Level 2/3 legal
weight; a human decides whether one is warranted (Constitution's human-
review-first stance). The editor sees the flag via the existing Dashboard
"Source Monitor Alerts" section and AI Command Center.
"""
import os
import sys
import time
import html
import hashlib
import datetime
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
REPO_ROOT = os.path.dirname(NOTION_BUILD_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, AUTOMATION_DIR)

from notion_api import load_env, notion_request, query_database, get_prop  # noqa: E402
import ai_gateway  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")

USER_AGENT = "ARuHQ-SourceWatcher/0.1 (+https://github.com/aru-japan/aru-ai-hq; contact: ARu editorial team)"
FETCH_TIMEOUT_SECONDS = 15
REQUEST_DELAY_SECONDS = 1.5
MAX_SOURCES_PER_RUN = 20

CHECK_FREQUENCY_DAYS = {"Daily": 1, "Weekly": 7, "Monthly": 30, "Quarterly": 90}

# Tier + Source Type -> Impact Level, applied only when a change is detected.
GOVERNMENT_SOURCE_TYPES = {"政府", "自治体"}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def ensure_schema(token, source_library_db_id):
    notion_request(token, "PATCH", f"/databases/{source_library_db_id}", {
        "properties": {
            "Last Content Hash": {"rich_text": {}},
        }
    })


class _TextExtractor(HTMLParser):
    """Minimal stdlib-only HTML-to-text extractor: drops script/style/nav/footer
    tags and collects the rest as plain text. Not a full readability algorithm --
    good enough to make full-page hashing meaningfully sensitive to content
    changes rather than markup noise, which is the only thing Phase 1 needs."""

    SKIP_TAGS = {"script", "style", "nav", "footer", "noscript"}

    def __init__(self):
        super().__init__()
        self._skip_depth = 0
        self.chunks = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth == 0:
            stripped = data.strip()
            if stripped:
                self.chunks.append(stripped)


def extract_text(html_content):
    parser = _TextExtractor()
    parser.feed(html_content)
    text = " ".join(parser.chunks)
    text = html.unescape(text)
    return " ".join(text.split())


def check_robots_allowed(url):
    try:
        parts = urllib.parse.urlparse(url)
        robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(USER_AGENT, url)
    except Exception:
        # If robots.txt can't be read, default to allowed rather than blocking
        # a legitimate government source over a transient robots.txt fetch issue.
        return True


def fetch_source_text(url):
    """Returns (text, error). error is None on success."""
    if not check_robots_allowed(url):
        return None, "robots.txt disallows fetching this URL"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT_SECONDS) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            raw = resp.read().decode(charset, errors="replace")
        return extract_text(raw), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return None, f"URLError: {e.reason}"
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def compute_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_date(date_str):
    if not date_str:
        return None
    return datetime.date.fromisoformat(date_str[:10])


def is_due(page, today):
    url = get_prop(page, "URL", "url")
    if not url:
        return False, None
    freq = get_prop(page, "Check Frequency", "select")
    interval = CHECK_FREQUENCY_DAYS.get(freq, 7)
    last_checked = parse_date(get_prop(page, "Last Checked", "date"))
    if last_checked is None:
        return True, url
    return (today - last_checked).days >= interval, url


def get_due_sources(token, source_library_db_id, today):
    pages = query_database(token, source_library_db_id, filter_obj={
        "property": "Status", "select": {"equals": "Active"}
    })
    due = []
    skipped_no_url = 0
    skipped_not_due = 0
    for page in pages:
        due_flag, url = is_due(page, today)
        if not url:
            skipped_no_url += 1
            continue
        if due_flag:
            due.append(page)
        else:
            skipped_not_due += 1
    return due, skipped_no_url, skipped_not_due


def derive_impact_level(source_type, tier):
    if tier == "高" and source_type in GOVERNMENT_SOURCE_TYPES:
        return "Critical"
    if tier == "高":
        return "High"
    if tier == "中":
        return "Medium"
    return "Low"


def generate_diff_summary(source_name, old_hash_existed, new_text):
    excerpt = new_text[:1500]
    prompt = (
        "あなたはARu編集部の情報源モニタリング担当です。以下は、監視対象の公式情報源のページから取得した最新の本文抜粋です。\n"
        f"情報源名: {source_name}\n"
        "このページの内容が前回チェック時から変化したことを検知しました。編集者が「何を確認すべきか」を判断できるよう、"
        "このページの主な内容を1〜2文の簡潔な日本語で要約してください（前置き・挨拶は不要）。\n\n"
        f"{excerpt}"
    )
    try:
        _, text = ai_gateway.complete(prompt, max_tokens=200)
        return text.strip()
    except Exception as e:
        return f"変化を検知（AI要約生成に失敗: {e}）。ページ抜粋: {excerpt[:200]}"


def process_source(token, source_library_db_id, source_monitor_db_id, page, today, stats):
    source_id = page["id"]
    source_name = get_prop(page, "Source Name", "title")
    url = get_prop(page, "URL", "url")
    tier = get_prop(page, "Tier", "select")
    source_type = get_prop(page, "Source Type", "select")
    stored_hash = get_prop(page, "Last Content Hash", "rich_text")

    log(f"  Checking: {source_name} ({url})")
    text, error = fetch_source_text(url)

    if error:
        log(f"    ERROR: {error}")
        notion_request(token, "PATCH", f"/pages/{source_id}", {
            "properties": {"Last Checked": {"date": {"start": today.isoformat()}}}
        })
        stats["errored"] += 1
        return

    new_hash = compute_hash(text)

    if not stored_hash:
        log("    baseline established (first check)")
        notion_request(token, "PATCH", f"/pages/{source_id}", {
            "properties": {
                "Last Checked": {"date": {"start": today.isoformat()}},
                "Last Content Hash": {"rich_text": [{"text": {"content": new_hash}}]},
            }
        })
        stats["baseline"] += 1
        return

    if new_hash == stored_hash:
        log("    unchanged")
        notion_request(token, "PATCH", f"/pages/{source_id}", {
            "properties": {"Last Checked": {"date": {"start": today.isoformat()}}}
        })
        stats["unchanged"] += 1
        return

    log("    CHANGE DETECTED")
    impact_level = derive_impact_level(source_type, tier)
    diff_summary = generate_diff_summary(source_name, True, text)

    notion_request(token, "POST", "/pages", {
        "parent": {"database_id": source_monitor_db_id},
        "properties": {
            "Monitor Entry": {"title": [{"text": {"content": f"{source_name} 変更検知 {today.isoformat()}"}}]},
            "Source": {"relation": [{"id": source_id}]},
            "Checked At": {"date": {"start": today.isoformat()}},
            "Check Method": {"select": {"name": "Scraping"}},
            "Change Detected": {"checkbox": True},
            "Change Type": {"select": {"name": "Updated"}},
            "Impact Level": {"select": {"name": impact_level}},
            "Diff Summary": {"rich_text": [{"text": {"content": diff_summary[:2000]}}]},
            "Status": {"select": {"name": "Changed"}},
            "AI Generated": {"checkbox": True},
        },
    })
    notion_request(token, "PATCH", f"/pages/{source_id}", {
        "properties": {
            "Last Checked": {"date": {"start": today.isoformat()}},
            "Last Content Hash": {"rich_text": [{"text": {"content": new_hash}}]},
        }
    })
    stats["changed"] += 1


def main():
    env = load_env(ENV_PATH)
    token = env["NOTION_TOKEN"]
    source_library_db = env["SOURCE_LIBRARY_DB_ID"]
    source_monitor_db = env["SOURCE_MONITOR_DB_ID"]
    today = datetime.date.today()

    log("Ensuring Source Library schema has Last Content Hash...")
    ensure_schema(token, source_library_db)

    log("Finding due sources (Status=Active, URL set, Check Frequency interval elapsed)...")
    due, skipped_no_url, skipped_not_due = get_due_sources(token, source_library_db, today)
    log(f"  {len(due)} due, {skipped_no_url} skipped (no URL), {skipped_not_due} skipped (not due)")

    if len(due) > MAX_SOURCES_PER_RUN:
        log(f"  Capping this run to {MAX_SOURCES_PER_RUN} of {len(due)} due sources (politeness cap)")
        due = due[:MAX_SOURCES_PER_RUN]

    stats = {"baseline": 0, "unchanged": 0, "changed": 0, "errored": 0}
    for i, page in enumerate(due):
        process_source(token, source_library_db, source_monitor_db, page, today, stats)
        if i < len(due) - 1:
            time.sleep(REQUEST_DELAY_SECONDS)

    log("")
    log("=" * 70)
    log(f"DONE. Checked {len(due)} source(s): "
        f"baseline={stats['baseline']} unchanged={stats['unchanged']} "
        f"changed={stats['changed']} errored={stats['errored']}")
    log(f"Skipped: {skipped_no_url} (no URL), {skipped_not_due} (not due)")


if __name__ == "__main__":
    main()
