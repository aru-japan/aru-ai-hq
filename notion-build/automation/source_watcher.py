"""Source Watcher -- ARu Intelligence Phase 1 + Phase 2 (Source Library Expansion).

Phase 1 built the detection engine: nothing in this repo had ever actually
fetched an external URL and detected whether an official source changed.
`Source Monitor.Change Detected` had always been a manually-set checkbox.
Everything downstream of it -- Research auto-draft
(`sync_source_monitor_to_research.py`), Article force-flagging
(`article_freshness_monitor.py`), Publishing Center, and the Dashboard/AI
Command Center's Source Monitor Alerts sections -- already existed and was
already tested; it had simply never been fed real data.

Phase 2 scales that engine from "1 test source" to "however many Source
Library holds" and sharpens what "changed" means:
    Source Library (existing DB, static ledger of trusted sources)
      -> for each due source with a real URL, fetch + fingerprint its text
      -> unchanged (fingerprint within tolerance): just update Last Checked
      -> changed: create a Source Monitor record (Change Detected=true,
         Impact Level from the source's Importance, AI-written Diff Summary,
         AI-classified Update Classification) and update Source Library's
         Last Checked + Last Content Hash

Schema changes (all additive, nothing removed or renamed):
  Source Library: Last Content Hash (Phase 1), Category / Country / Region /
    City / Importance / Last Check Error (Phase 2)
  Source Monitor: Update Classification (Phase 2)
`Importance` (Critical/High/Medium/Low) supersedes the older Tier+Source Type
inference as the authoritative priority signal -- Tier stays on the schema,
unremoved, used only as a fallback for any record that predates Importance.

Government/regulatory sources are flagged only -- this script never creates
or touches a Law Update record, and never creates Research/Articles/
Translation/SNS Queue records either. A human decides what happens next
(Constitution's human-review-first stance). The editor sees the flag via the
existing Dashboard "Source Monitor Alerts" / new "Critical Source Updates"
sections and AI Command Center.
"""
import os
import re
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
from source_categories import SOURCE_CATEGORIES, UPDATE_CLASSIFICATIONS  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")

USER_AGENT = "ARuHQ-SourceWatcher/0.2 (+https://github.com/aru-japan/aru-ai-hq; contact: ARu editorial team)"
FETCH_TIMEOUT_SECONDS = 15
REQUEST_DELAY_SECONDS = 1.5
MAX_SOURCES_PER_RUN = 50

CHECK_FREQUENCY_DAYS = {"Daily": 1, "Weekly": 7, "Monthly": 30, "Quarterly": 90}

IMPORTANCE_LEVELS = ["Critical", "High", "Medium", "Low"]
IMPORTANCE_SORT_ORDER = {name: i for i, name in enumerate(IMPORTANCE_LEVELS)}
DEFAULT_IMPORTANCE_FOR_SORT = "Medium"

COUNTRY_OPTIONS = ["Japan", "Other / International"]
REGION_OPTIONS = ["北海道", "東北", "関東", "中部", "近畿", "中国", "四国", "九州・沖縄", "全国", "海外"]

# Legacy fallback only (pre-Importance records): Tier + Source Type -> Impact Level.
GOVERNMENT_SOURCE_TYPES = {"政府", "自治体"}

# SimHash fingerprint: near-duplicate detection instead of exact-hash comparison,
# so incidental page noise (ad swaps, timestamps, visitor counters) doesn't
# register as a "change." A genuine content edit moves many bits; cosmetic
# noise moves only a few. Threshold is a tunable heuristic, not a solved
# problem -- expect it to need adjustment once more real sources are observed.
SIMHASH_BITS = 64
SIMHASH_CHANGE_THRESHOLD = 2
SHINGLE_SIZE = 5

_COUNTER_LIKE_RE = re.compile(r"\d{1,3}(,\d{3})*\s*(件|人|回|PV|アクセス|views?|visits?)", re.IGNORECASE)
_DATE_LIKE_RE = re.compile(
    r"\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?|\d{1,2}:\d{2}(:\d{2})?"
)


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _select_options(*names):
    return {"select": {"options": [{"name": n} for n in names]}}


def ensure_schema(token, source_library_db_id, source_monitor_db_id):
    notion_request(token, "PATCH", f"/databases/{source_library_db_id}", {
        "properties": {
            "Last Content Hash": {"rich_text": {}},
            "Last Check Error": {"rich_text": {}},
            "Category": _select_options(*SOURCE_CATEGORIES),
            "Country": _select_options(*COUNTRY_OPTIONS),
            "Region": _select_options(*REGION_OPTIONS),
            "City": {"rich_text": {}},
            "Importance": _select_options(*IMPORTANCE_LEVELS),
        }
    })
    notion_request(token, "PATCH", f"/databases/{source_monitor_db_id}", {
        "properties": {
            "Update Classification": _select_options(*UPDATE_CLASSIFICATIONS),
        }
    })


class _TextExtractor(HTMLParser):
    """Minimal stdlib-only HTML-to-text extractor: drops script/style/nav/footer
    tags and collects the rest as plain text. Not a full readability algorithm --
    good enough to make the fingerprint meaningfully sensitive to content
    changes rather than markup noise."""

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


def normalize_for_fingerprint(text):
    """Strip patterns that are pure noise for change-detection purposes:
    timestamps/dates and visitor-counter-like numbers. Best-effort, not
    perfect -- documented as a known limitation."""
    text = _DATE_LIKE_RE.sub(" ", text)
    text = _COUNTER_LIKE_RE.sub(" ", text)
    return " ".join(text.split())


def compute_shingles(text, k=SHINGLE_SIZE):
    words = text.split()
    if len(words) < k:
        return [text] if text else []
    return [" ".join(words[i:i + k]) for i in range(len(words) - k + 1)]


def simhash(text, bits=SIMHASH_BITS):
    """64-bit near-duplicate fingerprint via bit-majority voting over shingle
    hashes. Two texts that differ only in incidental noise (an ad, a
    timestamp, a visitor count) produce fingerprints a small Hamming distance
    apart; genuinely different content diverges in many bits."""
    shingles = compute_shingles(normalize_for_fingerprint(text))
    if not shingles:
        return "0" * (bits // 4)

    votes = [0] * bits
    for shingle in shingles:
        digest = hashlib.blake2b(shingle.encode("utf-8"), digest_size=bits // 8).digest()
        value = int.from_bytes(digest, "big")
        for b in range(bits):
            if (value >> b) & 1:
                votes[b] += 1
            else:
                votes[b] -= 1

    fingerprint = 0
    for b in range(bits):
        if votes[b] > 0:
            fingerprint |= (1 << b)
    return format(fingerprint, f"0{bits // 4}x")


def is_valid_fingerprint(hex_str):
    return bool(hex_str) and len(hex_str) == SIMHASH_BITS // 4 and all(c in "0123456789abcdef" for c in hex_str.lower())


def hamming_distance(hex_a, hex_b):
    return bin(int(hex_a, 16) ^ int(hex_b, 16)).count("1")


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

    # Importance-first: as Source Library grows, a per-run cap must never
    # starve Critical sources behind a long tail of Low-importance ones.
    due.sort(key=lambda p: IMPORTANCE_SORT_ORDER.get(
        get_prop(p, "Importance", "select") or DEFAULT_IMPORTANCE_FOR_SORT,
        IMPORTANCE_SORT_ORDER[DEFAULT_IMPORTANCE_FOR_SORT],
    ))
    return due, skipped_no_url, skipped_not_due


def derive_impact_level(importance, source_type, tier):
    """Importance (set directly by the editor per source) is authoritative.
    Falls back to the older Tier+Source Type inference only for records that
    predate the Importance property, so nothing already in Source Library
    breaks."""
    if importance in IMPORTANCE_SORT_ORDER:
        return importance
    if tier == "高" and source_type in GOVERNMENT_SOURCE_TYPES:
        return "Critical"
    if tier == "高":
        return "High"
    if tier == "中":
        return "Medium"
    return "Low"


def generate_diff_summary(source_name, new_text):
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


def classify_update(source_name, category, diff_text):
    """AI-classify a detected change into one of UPDATE_CLASSIFICATIONS.
    Validated against the known list -- a hallucinated/unparseable label
    falls back to "General News" rather than being saved as-is."""
    options = "\n".join(f"- {c}" for c in UPDATE_CLASSIFICATIONS)
    prompt = f"""あなたはARu編集部の情報源モニタリング担当です。以下は、公式情報源「{source_name}」（カテゴリ: {category or "不明"}）で検知された変化の内容です。

この変化を、以下の分類から最も適切な1つに分類してください。

選択肢（このリストの表記そのままで、他の説明なしで出力すること）：
{options}

変化の内容：
{diff_text[:1000]}

出力形式（このまま、他の説明は付けないこと）：
CLASSIFICATION: <選択肢のいずれか>
"""
    try:
        _, text = ai_gateway.complete(prompt, max_tokens=50)
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("CLASSIFICATION:"):
                name = line[len("CLASSIFICATION:"):].strip()
                if name in UPDATE_CLASSIFICATIONS:
                    return name
    except Exception:
        pass
    return "General News"


def process_source(token, source_library_db_id, source_monitor_db_id, page, today, stats):
    source_id = page["id"]
    source_name = get_prop(page, "Source Name", "title")
    url = get_prop(page, "URL", "url")
    tier = get_prop(page, "Tier", "select")
    source_type = get_prop(page, "Source Type", "select")
    category = get_prop(page, "Category", "select")
    importance = get_prop(page, "Importance", "select")
    stored_fingerprint = get_prop(page, "Last Content Hash", "rich_text")

    log(f"  Checking: {source_name} ({url})")
    text, error = fetch_source_text(url)

    if error:
        log(f"    ERROR: {error}")
        notion_request(token, "PATCH", f"/pages/{source_id}", {
            "properties": {
                "Last Checked": {"date": {"start": today.isoformat()}},
                "Last Check Error": {"rich_text": [{"text": {"content": error[:2000]}}]},
            }
        })
        stats["errored"] += 1
        return

    new_fingerprint = simhash(text)
    legacy_format = bool(stored_fingerprint) and not is_valid_fingerprint(stored_fingerprint)

    if not stored_fingerprint or legacy_format:
        reason = "legacy hash format, re-baselining" if legacy_format else "first check"
        log(f"    baseline established ({reason})")
        notion_request(token, "PATCH", f"/pages/{source_id}", {
            "properties": {
                "Last Checked": {"date": {"start": today.isoformat()}},
                "Last Content Hash": {"rich_text": [{"text": {"content": new_fingerprint}}]},
                "Last Check Error": {"rich_text": []},
            }
        })
        stats["baseline"] += 1
        return

    distance = hamming_distance(new_fingerprint, stored_fingerprint)
    if distance <= SIMHASH_CHANGE_THRESHOLD:
        log(f"    unchanged (hamming distance {distance})")
        notion_request(token, "PATCH", f"/pages/{source_id}", {
            "properties": {
                "Last Checked": {"date": {"start": today.isoformat()}},
                "Last Check Error": {"rich_text": []},
            }
        })
        stats["unchanged"] += 1
        return

    log(f"    CHANGE DETECTED (hamming distance {distance})")
    impact_level = derive_impact_level(importance, source_type, tier)
    diff_summary = generate_diff_summary(source_name, text)
    update_classification = classify_update(source_name, category, diff_summary)

    notion_request(token, "POST", "/pages", {
        "parent": {"database_id": source_monitor_db_id},
        "properties": {
            "Monitor Entry": {"title": [{"text": {"content": f"{source_name} 変更検知 {today.isoformat()}"}}]},
            "Source": {"relation": [{"id": source_id}]},
            "Checked At": {"date": {"start": today.isoformat()}},
            "Check Method": {"select": {"name": "Scraping"}},
            "Change Detected": {"checkbox": True},
            "Change Type": {"select": {"name": "Updated"}},
            "Update Classification": {"select": {"name": update_classification}},
            "Impact Level": {"select": {"name": impact_level}},
            "Diff Summary": {"rich_text": [{"text": {"content": diff_summary[:2000]}}]},
            "Status": {"select": {"name": "Changed"}},
            "AI Generated": {"checkbox": True},
        },
    })
    notion_request(token, "PATCH", f"/pages/{source_id}", {
        "properties": {
            "Last Checked": {"date": {"start": today.isoformat()}},
            "Last Content Hash": {"rich_text": [{"text": {"content": new_fingerprint}}]},
            "Last Check Error": {"rich_text": []},
        }
    })
    stats["changed"] += 1


def main():
    env = load_env(ENV_PATH)
    token = env["NOTION_TOKEN"]
    source_library_db = env["SOURCE_LIBRARY_DB_ID"]
    source_monitor_db = env["SOURCE_MONITOR_DB_ID"]
    today = datetime.date.today()

    log("Ensuring Source Library / Source Monitor schema (Phase 1 + Phase 2 properties)...")
    ensure_schema(token, source_library_db, source_monitor_db)

    log("Finding due sources (Status=Active, URL set, Check Frequency interval elapsed)...")
    due, skipped_no_url, skipped_not_due = get_due_sources(token, source_library_db, today)
    log(f"  {len(due)} due (sorted Critical->Low), {skipped_no_url} skipped (no URL), {skipped_not_due} skipped (not due)")

    if len(due) > MAX_SOURCES_PER_RUN:
        log(f"  Capping this run to {MAX_SOURCES_PER_RUN} of {len(due)} due sources (politeness cap, highest Importance first)")
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
