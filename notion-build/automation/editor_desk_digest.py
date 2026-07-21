"""ARu編集デスク｜今日の情報 -- a new, separate marker-bounded section on the
Dashboard page (2026-07-20). Does NOT touch the existing AI Command Center
section, its own MARKER_START/END, or any of the 9 pre-existing numbered
sections -- this section owns its own pair of markers and only ever rewrites
what sits between them, exactly like ai_command_center.py's pattern.

Scope for this run: three subsections have an actual approved design and are
populated with live data -- 🎎 日本文化体験, 🥗 食の安心・お店情報, and
（2026-07-20追記）未分類・詳細未確認. The remaining 5 headings Rei asked to
reserve a slot for (今日の新着 / 本日開催・近日開催 / 変更・中止・期限切れ /
深い記事候補 / Rei確認待ち) are written as explicit "準備中" placeholders --
no cross-DB aggregation logic has been designed or approved for them yet, so
nothing is guessed here.

未分類・詳細未確認 (added 2026-07-20): Experience Genre と Dietary
Accommodation Type がともに空欄のまま Status=New/Reviewing で残っている
レコードは、以前は🎎🥗どちらの抽出条件にも該当せずどの窓からも見えなかった
（Reiが発見した表示漏れ）。このセクションはその欠落を埋めるための実データ
接続で、タグを推測して埋めることはしない。情報元の区分は Related Source
Library の紐付け先タイトル/URLに含まれる既知の第三者・SNSプラットフォーム名
から判定し、判定できない場合は "区分未確認" のまま表示する（"公式情報"と
断定するための積極的シグナルは扱わない -- 消去法で公式だと推測しないため）。

Test-record exclusion (added 2026-07-20, second pass): once 未分類・詳細
未確認 started reflecting live data, two pre-existing internal test fixtures
(titled "【テスト】...", created 2026-07-12, unrelated to the food/culture
work) surfaced in the Dashboard for the first time. These are excluded from
every section by an explicit title-prefix allowlist (TEST_TITLE_PREFIXES) --
not deleted, not Status-changed, still fully present in Experience
Intelligence. The match is a strict startswith() against a short, explicit
prefix list, never a substring/keyword scan -- a normal record whose title or
body merely contains the word "テスト" must not be caught by this. A third
test fixture (Event Calendar "【テスト】京都 東福寺 紅葉ライトアップ",
related to the same test Experience Intelligence record) was found during the
2026-07-20 cross-DB culture-window audit and is excluded the same way.

🎎 日本文化体験 (redesigned 2026-07-20, cross-DB): storage location per record
is unchanged (通年→Experience Intelligence, 期間限定→Event Calendar, 情報源→
Source Library) -- nothing is copied into a new DB or a new property. A
record counts as culture if Intelligence Type=Culture OR Experience Genre is
non-empty (the OR is itself a fix: the old filter used Genre alone and missed
3 records tagged Culture with no Genre value). Event Calendar's own Type=
文化イベント is deliberately NOT trusted as a standalone signal -- a
same-day audit found most of its 12 records are international-exchange
seminars, not hands-on culture experiences, and none of them link back to any
Experience Intelligence record. Those 12 are shown as a separate, explicitly
unconfirmed "文化・交流イベント候補｜内容確認待ち" bucket (split into
still-open vs 終了・過去 by Status) rather than being merged into the
confirmed list. "公式情報" is only ever shown for the small, individually
verified CONFIRMED_OFFICIAL_SOURCE_PAGE_IDS allowlist -- Source Type=観光協会
or Verification Status=Verified alone are not sufficient per Rei's
instruction, since neither proves the linked URL is the venue's own domain.

"深い記事候補" is deliberately never computed as a yes/no judgment. Rei
corrected this explicitly: Related Research being set only means the record
has been linked into the Research pipeline, not that AI decided it deserves
a deep article. Every place that signal is shown, it is labeled "Research
連携済み".

"今日の新着" bucketing for the two live subsections is based on Notion's own
created_time (converted to JST), because Experience Intelligence has no
dedicated "発見日" property -- Last AI Update is reused elsewhere as
"最終確認日" and is not a discovery-date field.

Counts are computed fresh from the live Experience Intelligence database
every time this script runs; nothing is hardcoded. Re-run this script to
refresh the numbers after new records are added.
"""
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from notion_api import load_env, notion_request, query_database

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
JST = timezone(timedelta(hours=9))

MARKER_START = "📋 ARu編集デスク｜今日の情報（自動生成セクション開始 -- 以下は毎回自動更新されます。手動編集しないでください）"
MARKER_END = "📋 ARu編集デスク｜今日の情報（自動生成セクション終了）"

PLACEHOLDER_HEADINGS = [
    "今日の新着",
    "本日開催・近日開催",
    "変更・中止・期限切れ",
]
PLACEHOLDER_HEADINGS_AFTER = [
    "深い記事候補",
    "Rei確認待ち",
]

THIRD_PARTY_SOURCE_MARKERS = [
    "食べログ", "tabelog", "ぐるなび", "gnavi", "retty",
    "ホットペッパー", "hotpepper", "vegewel", "a4jp",
    "トリップアドバイザー", "tripadvisor", "まとめ", "ガイド", "guide", "review",
]
SNS_SOURCE_MARKERS = ["instagram.com", "twitter.com", "x.com", "facebook.com", "tiktok.com"]

# Explicit, exact-prefix allowlist of known internal test-fixture titles.
# Deliberately NOT a substring/keyword match -- a real record whose title or
# Description happens to contain the word "テスト" must not be excluded.
# "【テスト" (no closing bracket) is intentional: it catches both "【テスト】..."
# (Experience Intelligence/Event Calendar fixtures) and "【テスト・...】" (the
# Story Bank fixture naming style found 2026-07-20), via a single prefix.
TEST_TITLE_PREFIXES = ["【テスト"]


def is_test_record(page):
    title = title_of(page) or ""
    return any(title.startswith(prefix) for prefix in TEST_TITLE_PREFIXES)


def log(msg):
    print(msg)


def rt(text, link=None, bold=False):
    obj = {"content": str(text)[:2000]}
    if link:
        obj["link"] = {"url": link}
    entry = {"text": obj}
    if bold:
        entry["annotations"] = {"bold": True}
    return [entry]


def title_of(page):
    for _, v in page.get("properties", {}).items():
        if v.get("type") == "title":
            return "".join(t.get("plain_text", "") for t in v.get("title", []))
    return None


def page_url(page_id):
    return "https://www.notion.so/" + page_id.replace("-", "")


def created_date_jst(page):
    ts = page.get("created_time")
    if not ts:
        return None
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(JST)
    return dt.date()


def multi_select_names(page, prop_name):
    val = page.get("properties", {}).get(prop_name, {})
    if val.get("type") != "multi_select":
        return []
    return [o["name"] for o in val.get("multi_select", [])]


def select_name(page, prop_name):
    val = page.get("properties", {}).get(prop_name, {})
    if val.get("type") != "select":
        return None
    s = val.get("select")
    return s.get("name") if s else None


def status_name(page):
    val = page.get("properties", {}).get("Status", {})
    if val.get("type") == "select":
        s = val.get("select")
        return s.get("name") if s else None
    if val.get("type") == "status":
        s = val.get("status")
        return s.get("name") if s else None
    return None


def last_ai_update_days_ago(page):
    val = page.get("properties", {}).get("Last AI Update", {})
    d = val.get("date")
    if not d or not d.get("start"):
        return None
    dt = datetime.fromisoformat(d["start"]).replace(tzinfo=JST) if "T" not in d["start"] else \
        datetime.fromisoformat(d["start"])
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=JST)
    now = datetime.now(JST)
    return (now - dt.astimezone(JST)).days


def needs_recheck(page):
    if status_name(page) == "Reviewing":
        return True
    days = last_ai_update_days_ago(page)
    return days is not None and days > 90


def card_line(page):
    title = title_of(page)
    region = select_name(page, "Region") or "未確認"
    status = status_name(page) or "-"
    genre = ", ".join(multi_select_names(page, "Experience Genre")) or None
    dietary = ", ".join(multi_select_names(page, "Dietary Accommodation Type")) or None
    tag = genre or dietary or "-"
    return f"{title} ｜ {region} ｜ {tag} ｜ 確認状態: {status}"


# Individually verified (2026-07-20 cross-DB audit) records where the linked
# Source Library URL's own domain/operator name was confirmed to match the
# venue itself. This is a short, explicit allowlist -- Source Type=観光協会 or
# Verification Status=Verified alone are NOT sufficient evidence of "official"
# per Rei's instruction; those values only gate entry into this allowlist
# after a human (or a prior session's direct WebFetch) confirmed the domain
# actually belongs to the venue. Never grown automatically.
CONFIRMED_OFFICIAL_SOURCE_PAGE_IDS = {
    "3a2157f0-f15d-8135-be43-f2311684b1c3",  # 庵an東京 (Experience Intelligence)
    "3a2157f0-f15d-81f2-93cb-ddf6ee25f779",  # 阿波友禅工場 (Experience Intelligence)
    "3a2157f0-f15d-811b-87df-ef2606d43212",  # 体験農園みとか (Experience Intelligence)
    "3a2157f0-f15d-81ba-8716-d04f68d6bd66",  # 中込農園 (Experience Intelligence)
    "3a2157f0-f15d-81df-b4da-da87658cb9a9",  # 中込農園 シャインマスカット狩り (Event Calendar)
    "3a2157f0-f15d-81d0-8b9c-de5c489ba99c",  # 中込農園 黒系ぶどう狩り (Event Calendar)
    "3a2157f0-f15d-81cb-af39-eee73f15e8a0",  # 体験農園みとか ぶどう狩り (Event Calendar)
    # 2026-07-20, culture batch 1 (8 venues) -- 6 of 8 confirmed as the venue's
    # own domain (name/operator matches the URL directly). The remaining 2
    # (二風谷アイヌ文化博物館, 有田ポーセリンパーク) are deliberately NOT
    # listed here: their Source URL is a town portal / tourism-association
    # page, not the venue's own site, so classify_source_type's conservative
    # default applies to them instead.
    "3a3157f0-f15d-8170-9e54-cf73347e817f",  # 大館曲げわっぱ協同組合
    "3a3157f0-f15d-81f9-9be6-f5f0ee49041a",  # 陶あん（京焼・清水焼）
    "3a3157f0-f15d-8137-8d70-c2bdd2dbba37",  # 金継工房 鹿田喜造漆店
    "3a3157f0-f15d-81a2-bfca-e81c1c905efa",  # 夢幻庵備前焼工房
    "3a3157f0-f15d-8178-80e9-e40c6885fd0b",  # 石州和紙会館
    "3a3157f0-f15d-81d4-8793-e526401f1bc4",  # 沖縄空手会館
}


def classify_culture_source(token, page):
    if page["id"] in CONFIRMED_OFFICIAL_SOURCE_PAGE_IDS:
        return "公式情報"
    return classify_source_type(token, page)


def is_culture_ei(page):
    """Intelligence Type=Culture OR Experience Genre non-empty -- the OR is the
    2026-07-20 fix: the old filter (Experience Genre alone) missed 3 records
    (体験農園みとか／中込農園／あんざい果樹園) that were tagged
    Intelligence Type=Culture but never got an Experience Genre value."""
    return select_name(page, "Intelligence Type") == "Culture" or bool(multi_select_names(page, "Experience Genre"))


def related_experience_intelligence_ids(ec_page):
    rel = ec_page.get("properties", {}).get("Related Experience Intelligence", {})
    return [r["id"] for r in rel.get("relation", [])] if rel.get("type") == "relation" else []


def related_research_ids(page):
    rel = page.get("properties", {}).get("Related Research", {})
    return [r["id"] for r in rel.get("relation", [])] if rel.get("type") == "relation" else []


def is_person_ei(page):
    """Experience Intelligence.Intelligence Type=User -- the agreed storage
    location for 日本で活躍する外国人・人物とお店 (2026-07-20). No new
    property or database; person/shop candidates are ordinary Experience
    Intelligence pages distinguished only by this existing select value."""
    return select_name(page, "Intelligence Type") == "User"


def culture_card_runs(page, db_label, status_kind, next_action, source_type):
    title = title_of(page) or "(無題)"
    region = select_name(page, "Region") or "未確認"
    genre_names = multi_select_names(page, "Experience Genre")
    genre = ", ".join(genre_names) if genre_names else "未確認"
    status = status_name(page) or "-"
    last_ai = page.get("properties", {}).get("Last AI Update", {}).get("date")
    last_ai_str = last_ai["start"] if last_ai else "未確認"
    event_date = page.get("properties", {}).get("Event Date", {}).get("date")
    schedule = event_date.get("start", "未確認") if event_date else "通年・常設"
    source_url = page.get("properties", {}).get("Source URL", {}).get("url")

    runs = [{"text": {"content": title, "link": {"url": page_url(page["id"])}}}]
    runs.append({"text": {"content": (
        f" ｜ 状態: {status_kind} ｜ 地域: {region} ｜ ジャンル: {genre} ｜ "
        f"開催日/営業形態: {schedule} ｜ 確認状態: {status} ｜ 最終確認日: {last_ai_str} ｜ "
        f"情報元の区分: {source_type} ｜ 保存先: {db_label} ｜ 次に確認: {next_action} ｜ Source: "
    )}})
    if source_url:
        runs.append({"text": {"content": source_url, "link": {"url": source_url}}})
    else:
        runs.append({"text": {"content": "未確認"}})
    return runs


def _toggle(label, count, children):
    if not children:
        children = [{"paragraph": {"rich_text": rt("該当レコードなし")}}]
    return {"toggle": {"rich_text": rt(f"{label}（{count}件）"), "children": children}}


def compute_culture_buckets(token, ei_pages, ec_pages, source_library_pages):
    """Pure computation, shared by Dashboard's build_culture_section and
    Home's consolidated digest -- the bucket logic must only ever be written
    once. Returns plain lists (and a source_type lookup function) so callers
    can render them however they like."""
    culture_ei = [p for p in ei_pages if is_culture_ei(p)]
    culture_ei_ids = {p["id"] for p in culture_ei}

    period_ec = [p for p in ec_pages
                 if any(rid in culture_ei_ids for rid in related_experience_intelligence_ids(p))]
    period_ec_ids = {p["id"] for p in period_ec}

    # C. 低確度候補: Type=文化イベントだが、Culture系Experience Intelligenceとの
    # 関連がないレコード。2026-07-20監査で、この12件の実体の多くが国際交流・
    # 啓発イベント（ハンズオンの日本文化体験ではない）と判明したため、
    # タイトルやTypeの値だけで文化体験と確定せず、常に「候補」として扱う。
    low_confidence = [p for p in ec_pages
                       if select_name(p, "Type") == "文化イベント" and p["id"] not in period_ec_ids]
    ended_low_confidence = [p for p in low_confidence if status_name(p) in ("Completed", "Cancelled")]
    ended_ids = {p["id"] for p in ended_low_confidence}
    pending_low_confidence = [p for p in low_confidence if p["id"] not in ended_ids]

    culture_source_library = [p for p in source_library_pages if select_name(p, "Category") == "Culture"]

    def sl_has_ei_link(p):
        rel = p.get("properties", {}).get("Related to Experience Intelligence (Related Source Library)", {})
        return bool(rel.get("relation")) if rel.get("type") == "relation" else False

    source_only = [p for p in culture_source_library if not sl_has_ei_link(p)]

    research_linked_ei_ids = {p["id"] for p in culture_ei if related_research_ids(p)}
    research_linked = (
        [p for p in culture_ei if p["id"] in research_linked_ei_ids]
        + [p for p in period_ec if any(rid in research_linked_ei_ids for rid in related_experience_intelligence_ids(p))]
    )

    pending_ei = [p for p in culture_ei if status_name(p) in ("New", "Reviewing")]
    pending_ec_period = [p for p in period_ec if status_name(p) == "Planning"]
    rei_pending = pending_ei + pending_ec_period + pending_low_confidence

    today = datetime.now(JST).date()
    all_candidates = culture_ei + period_ec + low_confidence
    today_new = [p for p in all_candidates if created_date_jst(p) == today]

    # Cache classify_culture_source (each call may fetch a related Source
    # Library page) so records rendered in more than one bucket (e.g. a
    # pending 低確度候補 shown both under its own bucket and under Rei確認待ち)
    # only trigger one Notion read.
    source_type_cache = {}

    def cached_source_type(p):
        if p["id"] not in source_type_cache:
            source_type_cache[p["id"]] = classify_culture_source(token, p)
        return source_type_cache[p["id"]]

    return {
        "culture_ei": culture_ei, "culture_ei_ids": culture_ei_ids,
        "period_ec": period_ec, "period_ec_ids": period_ec_ids,
        "low_confidence": low_confidence,
        "ended_low_confidence": ended_low_confidence,
        "pending_low_confidence": pending_low_confidence,
        "source_only": source_only,
        "research_linked": research_linked,
        "pending_ei": pending_ei, "pending_ec_period": pending_ec_period,
        "rei_pending": rei_pending, "today_new": today_new,
        "cached_source_type": cached_source_type,
        "related_experience_intelligence_ids": related_experience_intelligence_ids,
    }


def build_culture_section(token, ei_pages, ec_pages, source_library_pages):
    """Cross-DB 🎎 日本文化体験 window (2026-07-20 redesign). Does not copy any
    record into a new DB -- every card links back to its own original
    Experience Intelligence / Event Calendar / Source Library page. Storage
    location is unchanged: 通年 stays in Experience Intelligence, 期間限定 stays
    in Event Calendar, undecided Web/Source finds stay in Source Library.
    """
    bk = compute_culture_buckets(token, ei_pages, ec_pages, source_library_pages)
    culture_ei, culture_ei_ids = bk["culture_ei"], bk["culture_ei_ids"]
    period_ec = bk["period_ec"]
    low_confidence = bk["low_confidence"]
    ended_low_confidence = bk["ended_low_confidence"]
    pending_low_confidence = bk["pending_low_confidence"]
    source_only = bk["source_only"]
    research_linked = bk["research_linked"]
    pending_ei, pending_ec_period = bk["pending_ei"], bk["pending_ec_period"]
    rei_pending, today_new = bk["rei_pending"], bk["today_new"]
    cached_source_type = bk["cached_source_type"]

    blocks = []
    blocks.append({"heading_3": {"rich_text": rt("🎎 日本文化体験")}})
    blocks.append({"callout": {
        "rich_text": rt(
            f"今日見つけた文化体験: {len(today_new)}件（各DBのcreated_time基準・JST） / "
            f"Rei確認待ち: {len(rei_pending)}件（Status=New/Reviewing/Planning等、まだ確定していないもの。公開可否の判断ではありません） / "
            f"通年・常設: {len(culture_ei)}件 / 期間限定: {len(period_ec)}件 / "
            f"文化・交流イベント候補: {len(low_confidence)}件（うち終了済み{len(ended_low_confidence)}件）"
        ),
        "icon": {"type": "emoji", "emoji": "🎎"}, "color": "yellow_background",
    }})

    # 通年・通常営業の体験（期間限定企画があれば、施設の下に入れ子で表示）
    facility_children = []
    for p in culture_ei:
        source_type = cached_source_type(p)
        runs = culture_card_runs(p, "Experience Intelligence", "常設", "情報の鮮度再確認（最終確認日を参照）", source_type)
        facility_children.append({"paragraph": {"rich_text": runs}})
        for q in period_ec:
            if p["id"] in related_experience_intelligence_ids(q):
                q_source_type = cached_source_type(q)
                q_runs = culture_card_runs(q, "Event Calendar", "期間限定（このEIの企画）", "開催内容・日程の最新確認", q_source_type)
                q_runs[0]["text"]["content"] = "　└ " + q_runs[0]["text"]["content"]
                facility_children.append({"paragraph": {"rich_text": q_runs}})
    blocks.append(_toggle("通年・通常営業の体験 一覧", len(culture_ei), facility_children))

    # 期間限定・近日開催（施設ごとの入れ子とは別に、期間限定企画だけを平坦に一覧化）
    period_children = [
        {"paragraph": {"rich_text": culture_card_runs(p, "Event Calendar", "期間限定", "開催内容・日程の最新確認", cached_source_type(p))}}
        for p in period_ec
    ]
    blocks.append(_toggle("期間限定・近日開催 一覧", len(period_ec), period_children))

    # 文化・交流イベント候補｜内容確認待ち（低確度、進行中/未確定のみ）
    candidate_children = [
        {"paragraph": {"rich_text": culture_card_runs(
            p, "Event Calendar", "文化・交流イベント候補｜内容確認待ち",
            "文化体験か国際交流イベントかの内容確認", cached_source_type(p))}}
        for p in pending_low_confidence
    ]
    blocks.append(_toggle("文化・交流イベント候補｜内容確認待ち 一覧", len(pending_low_confidence), candidate_children))

    # 終了・過去の候補（削除しない、アーカイブとして保持）
    ended_children = [
        {"paragraph": {"rich_text": culture_card_runs(
            p, "Event Calendar", "終了", "アーカイブとして保持のみ、対応不要", cached_source_type(p))}}
        for p in ended_low_confidence
    ]
    blocks.append(_toggle("終了・過去の候補 一覧", len(ended_low_confidence), ended_children))

    # 情報源のみ確認済み（Source Library Category=CultureでEI/EC未接続のもの）
    source_only_children = []
    for p in source_only:
        title = title_of(p) or "(無題)"
        region = select_name(p, "Region") or "未確認"
        verif = select_name(p, "Verification Status") or "未確認"
        url = p.get("properties", {}).get("URL", {}).get("url")
        runs = [{"text": {"content": title, "link": {"url": page_url(p["id"])}}}]
        runs.append({"text": {"content": (
            f" ｜ 地域: {region} ｜ Verification Status: {verif} ｜ 保存先: Source Library ｜ "
            f"次に確認: Experience Intelligence/Event Calendarへの登録要否を判断 ｜ Source: "
        )}})
        runs.append({"text": {"content": url, "link": {"url": url}}} if url else {"text": {"content": "未確認"}})
        source_only_children.append({"paragraph": {"rich_text": runs}})
    blocks.append(_toggle("情報源のみ確認済み 一覧", len(source_only), source_only_children))

    # Research連携済み（Related Research設定済みという意味。AIによる候補判定ではない）
    research_children = []
    for p in research_linked:
        db_label = "Experience Intelligence" if p["id"] in culture_ei_ids else "Event Calendar"
        research_children.append({"paragraph": {"rich_text": culture_card_runs(
            p, db_label, "Research連携済み", "深掘り記事化の判断", cached_source_type(p))}})
    blocks.append(_toggle("Research連携済み 一覧", len(research_linked), research_children))

    # Rei確認待ち（常設・期間限定・低確度候補のうち未確定のものを横断表示）
    pending_children = []
    for p in pending_ei:
        pending_children.append({"paragraph": {"rich_text": culture_card_runs(
            p, "Experience Intelligence", "常設・要確認", "登録内容の最終確認", cached_source_type(p))}})
    for p in pending_ec_period:
        pending_children.append({"paragraph": {"rich_text": culture_card_runs(
            p, "Event Calendar", "期間限定・要確認", "開催内容の最終確認", cached_source_type(p))}})
    for p in pending_low_confidence:
        pending_children.append({"paragraph": {"rich_text": culture_card_runs(
            p, "Event Calendar", "候補・要確認", "文化体験か国際交流イベントかの内容確認", cached_source_type(p))}})
    blocks.append(_toggle("Rei確認待ち 一覧", len(rei_pending), pending_children))

    return blocks


def person_card_runs(token, page, next_action):
    """Experience Intelligence.Intelligence Type=User records store their
    structured fields inside Description (## Public Profile / ## Source /
    ## Public Business Information / ## Verification Notes), same pattern as
    the food-store records -- no new properties. This card only surfaces the
    properties that do exist (Title, Region, Status, Last AI Update, Source
    URL) plus a link to the record; the structured Description itself is read
    directly in Notion, not duplicated into the digest text."""
    title = title_of(page) or "(無題)"
    region = select_name(page, "Region") or "未確認"
    status = status_name(page) or "-"
    last_ai = page.get("properties", {}).get("Last AI Update", {}).get("date")
    last_ai_str = last_ai["start"] if last_ai else "未確認"
    source_url = page.get("properties", {}).get("Source URL", {}).get("url")
    source_type = classify_source_type(token, page)

    runs = [{"text": {"content": title, "link": {"url": page_url(page["id"])}}}]
    runs.append({"text": {"content": (
        f" ｜ 地域: {region} ｜ 確認状態: {status} ｜ 最終確認日: {last_ai_str} ｜ "
        f"情報元の区分: {source_type} ｜ 次に確認: {next_action} ｜ Source: "
    )}})
    runs.append({"text": {"content": source_url, "link": {"url": source_url}}} if source_url
                 else {"text": {"content": "未確認"}})
    return runs


def compute_people_buckets(ei_pages):
    people = [p for p in ei_pages if is_person_ei(p)]
    today = datetime.now(JST).date()
    today_new = [p for p in people if created_date_jst(p) == today]
    pending = [p for p in people if status_name(p) in ("New", "Reviewing")]
    return {"people": people, "today_new": today_new, "pending": pending}


def build_people_section(token, ei_pages):
    bk = compute_people_buckets(ei_pages)
    people, today_new, pending = bk["people"], bk["today_new"], bk["pending"]

    blocks = []
    blocks.append({"heading_3": {"rich_text": rt("🌏 日本で活躍する外国人・人物とお店")}})
    blocks.append({"callout": {
        "rich_text": rt(
            f"今日見つけた候補: {len(today_new)}件（created_time基準・JST） / "
            f"Rei確認待ち: {len(pending)}件（Status=New/Reviewing。公開可否の判断ではありません） / "
            f"登録件数: {len(people)}件（Intelligence Type=User）"
        ),
        "icon": {"type": "emoji", "emoji": "🌏"}, "color": "blue_background",
    }})

    all_children = [
        {"paragraph": {"rich_text": person_card_runs(token, p, "掲載可否の判断に必要な情報を確認")}}
        for p in people
    ]
    blocks.append(_toggle("人物・お店 一覧", len(people), all_children))

    pending_children = [
        {"paragraph": {"rich_text": person_card_runs(token, p, "登録内容の最終確認")}}
        for p in pending
    ]
    blocks.append(_toggle("Rei確認待ち 一覧", len(pending), pending_children))

    return blocks


def compute_food_buckets(ei_pages):
    food = [p for p in ei_pages if multi_select_names(p, "Dietary Accommodation Type")]
    today = datetime.now(JST).date()
    today_new = [p for p in food if created_date_jst(p) == today]
    pending = [p for p in food if status_name(p) in ("New", "Reviewing")]

    def has_tag(p, *tags):
        names = multi_select_names(p, "Dietary Accommodation Type")
        return any(t in names for t in tags)

    halal_cert = [p for p in food if has_tag(p, "ハラール認証（認証機関・有効性確認済み）")]
    muslim_friendly = [p for p in food if has_tag(p, "ムスリムフレンドリー（店舗・提供者による表記）")]
    veg_vegan = [p for p in food if has_tag(p, "ベジタリアン", "ヴィーガン")]
    avoid_pork_alcohol = [p for p in food if has_tag(p, "豚肉不使用（ハラール認証未確認）", "アルコール不使用の記載あり")]
    gluten_allergy = [p for p in food if has_tag(p, "グルテンフリーの記載あり", "アレルギー情報・相談対応の記載あり")]
    other_religious = [p for p in food if has_tag(
        p, "プラントベース", "ペスカタリアン", "コーシャ対応の記載あり", "ジャイナ教徒向け",
        "ヒンドゥー教徒向け", "その他の宗教・食習慣対応")]
    # "新規オープン・リニューアル" is intentionally NOT computed this run.
    # Intelligence Type=Local means "regional information", not "newly
    # opened" -- Rei explicitly rejected that reuse as inaccurate. No
    # existing property can determine "new opening" correctly, so this view
    # stays a placeholder until a dedicated property is proposed and
    # approved separately.
    recheck = [p for p in food if needs_recheck(p)]
    research_linked = [p for p in food
                        if p.get("properties", {}).get("Related Research", {}).get("relation")]

    return {
        "food": food, "today_new": today_new, "pending": pending,
        "halal_cert": halal_cert, "muslim_friendly": muslim_friendly, "veg_vegan": veg_vegan,
        "avoid_pork_alcohol": avoid_pork_alcohol, "gluten_allergy": gluten_allergy,
        "other_religious": other_religious, "recheck": recheck, "research_linked": research_linked,
    }


def build_food_section(ei_pages):
    bk = compute_food_buckets(ei_pages)
    food, today_new, pending = bk["food"], bk["today_new"], bk["pending"]
    halal_cert, muslim_friendly, veg_vegan = bk["halal_cert"], bk["muslim_friendly"], bk["veg_vegan"]
    avoid_pork_alcohol, gluten_allergy = bk["avoid_pork_alcohol"], bk["gluten_allergy"]
    other_religious, recheck, research_linked = bk["other_religious"], bk["recheck"], bk["research_linked"]

    blocks = []
    blocks.append({"heading_3": {"rich_text": rt("🥗 食の安心・お店情報")}})
    blocks.append({"callout": {
        "rich_text": rt(
            f"今日見つけたお店: {len(today_new)}件（Notion Created time基準・JST） / "
            f"Rei確認待ち: {len(pending)}件（Status=New または Reviewing。まだReiが最終確認していない候補という意味で、営業内容の安全保証ではありません）"
        ),
        "icon": {"type": "emoji", "emoji": "🥗"}, "color": "green_background",
    }})
    filter_children = [
        {"paragraph": {"rich_text": rt(f"ハラール認証店（認証機関確認済みのみ）: {len(halal_cert)}件")}},
        {"paragraph": {"rich_text": rt(f"ムスリムフレンドリー（店舗・提供者による表記）: {len(muslim_friendly)}件")}},
        {"paragraph": {"rich_text": rt(f"ベジタリアン・ヴィーガン: {len(veg_vegan)}件")}},
        {"paragraph": {"rich_text": rt(f"豚肉・アルコールを避けたい人向け: {len(avoid_pork_alcohol)}件")}},
        {"paragraph": {"rich_text": rt(f"グルテンフリーの記載・アレルギー情報／相談対応の記載: {len(gluten_allergy)}件")}},
        {"paragraph": {"rich_text": rt(f"その他の宗教・食習慣への対応: {len(other_religious)}件")}},
        {"paragraph": {"rich_text": rt("新規オープン・リニューアル: 準備中（判定に使える既存プロパティがないため今回は実装せず。必要なら専用プロパティを別途提案します）")}},
        {"paragraph": {"rich_text": rt(f"営業状況の再確認が必要（Last AI Update 90日超 または Status=Reviewing）: {len(recheck)}件")}},
        {"paragraph": {"rich_text": rt(f"Research連携済み（Related Research設定済みという意味で、AIによる候補判定ではありません）: {len(research_linked)}件")}},
    ]
    blocks.append({"toggle": {"rich_text": rt("絞り込みビュー"), "children": filter_children}})

    card_children = []
    for p in food:
        card_children.append({"paragraph": {"rich_text": rt(card_line(p), link=page_url(p["id"]))}})
    if not card_children:
        card_children = [{"paragraph": {"rich_text": rt(
            "該当レコードなし（Dietary Accommodation Typeが設定されたレコードがまだありません。既存4件は未設定のまま維持しています）"
        )}}]
    blocks.append({"toggle": {"rich_text": rt(f"食の安心・お店情報 一覧（{len(food)}件）"), "children": card_children}})

    return blocks


def classify_source_type(token, page):
    """Reads only the linked Related Source Library page's title/URL -- no
    schema fetch, no keyword guessing beyond well-known third-party/SNS
    platform names. Never returns "公式情報" from a positive keyword match;
    that classification is intentionally left to Rei via direct review,
    since there is no reliable existing signal that proves a source is
    official. Defaults to "区分未確認" whenever nothing matches.
    """
    rel = page.get("properties", {}).get("Related Source Library", {})
    ids = [r["id"] for r in rel.get("relation", [])] if rel.get("type") == "relation" else []
    if not ids:
        return "区分未確認"
    for rid in ids:
        rp = notion_request(token, "GET", f"/pages/{rid}")
        rtitle = ""
        rurl = ""
        for _, v in rp.get("properties", {}).items():
            if v.get("type") == "title":
                rtitle = "".join(t.get("plain_text", "") for t in v.get("title", []))
            if v.get("type") == "url" and v.get("url"):
                rurl = v["url"]
        combined = (rtitle + " " + rurl).lower()
        if any(m.lower() in combined for m in SNS_SOURCE_MARKERS):
            return "SNS原文"
        if any(m.lower() in combined for m in THIRD_PARTY_SOURCE_MARKERS):
            return "第三者情報"
    return "区分未確認"


def compute_unclassified(ei_pages):
    # is_culture_ei also catches Intelligence Type=Culture records whose
    # Experience Genre is empty (体験農園みとか／中込農園／あんざい果樹園) --
    # those now belong to the 🎎 culture section (2026-07-20 fix) and must not
    # also show up here, or the same record would appear in two sections.
    # is_person_ei (Intelligence Type=User) is excluded the same way (2026-07-20
    # second addition) -- person/shop candidates belong to 🌏, not here.
    return [
        p for p in ei_pages
        if status_name(p) in ("New", "Reviewing")
        and not multi_select_names(p, "Experience Genre")
        and not multi_select_names(p, "Dietary Accommodation Type")
        and not is_culture_ei(p)
        and not is_person_ei(p)
    ]


def build_unclassified_section(token, ei_pages):
    unclassified = compute_unclassified(ei_pages)

    blocks = []
    blocks.append({"heading_3": {"rich_text": rt("未分類・詳細未確認")}})
    blocks.append({"callout": {
        "rich_text": rt(
            f"{len(unclassified)}件 -- Experience GenreとDietary Accommodation Typeがともに空欄で、"
            "Status=New/Reviewingのレコードです。文化体験・食情報・その他のどれに分類するか確認が必要です。"
            "タグは推測で設定していません。Reiが元情報（Source URL）を確認して分類してください。"
        ),
        "icon": {"type": "emoji", "emoji": "❔"}, "color": "gray_background",
    }})

    card_children = []
    for p in unclassified:
        title = title_of(p) or "(無題)"
        status = status_name(p) or "-"
        created = created_date_jst(p)
        created_str = created.isoformat() if created else "-"
        last_ai = p.get("properties", {}).get("Last AI Update", {}).get("date")
        last_ai_str = last_ai["start"] if last_ai else "未確認"
        source_url = p.get("properties", {}).get("Source URL", {}).get("url")
        source_type = classify_source_type(token, p)

        runs = [{"text": {"content": title, "link": {"url": page_url(p["id"])}}}]
        runs.append({"text": {"content": (
            f" ｜ Status: {status} ｜ 作成日: {created_str} ｜ 最終確認日: {last_ai_str} ｜ "
            f"情報元の区分: {source_type} ｜ Source: "
        )}})
        if source_url:
            runs.append({"text": {"content": source_url, "link": {"url": source_url}}})
        else:
            runs.append({"text": {"content": "未確認"}})
        card_children.append({"paragraph": {"rich_text": runs}})

    if not card_children:
        card_children = [{"paragraph": {"rich_text": rt("該当レコードなし")}}]
    blocks.append({"toggle": {
        "rich_text": rt(f"未分類・詳細未確認 一覧（{len(unclassified)}件）"),
        "children": card_children,
    }})

    return blocks


def _rich_text_value(page, prop_name):
    v = page.get("properties", {}).get(prop_name, {})
    if v.get("type") != "rich_text":
        return ""
    return "".join(t.get("plain_text", "") for t in v.get("rich_text", []))


def _checkbox_value(page, prop_name):
    v = page.get("properties", {}).get(prop_name, {})
    return bool(v.get("checkbox")) if v.get("type") == "checkbox" else False


def _story_status(page):
    return select_name(page, "Story Status")


def _generated_article_ids(page):
    rel = page.get("properties", {}).get("Generated Article", {})
    return [r["id"] for r in rel.get("relation", [])] if rel.get("type") == "relation" else []


def _story_bank_research_ids(page):
    # Story Bank's relation to Research is named differently from Experience
    # Intelligence's "Related Research" -- using related_research_ids() here
    # would silently always return [] (wrong property name) and this bug
    # existed for one local dry-run before being caught: it under-counted
    # "既存記事への導線あり" by exactly the 2 QA cards linked to Research but
    # not yet to a Converted Article (#4, #10).
    rel = page.get("properties", {}).get("Related to Research「記事候補」 (Related QA)", {})
    return [r["id"] for r in rel.get("relation", [])] if rel.get("type") == "relation" else []


def _next_review_overdue(page):
    v = page.get("properties", {}).get("Next Review", {})
    d = v.get("date")
    if not d or not d.get("start"):
        return False
    try:
        dt = datetime.fromisoformat(d["start"])
    except ValueError:
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=JST)
    return dt.astimezone(JST).date() < datetime.now(JST).date()


def qa_card_runs(page, status_label):
    question = _rich_text_value(page, "QA Question") or title_of(page) or "(質問未設定)"
    story_status = _story_status(page) or "-"
    stage = select_name(page, "Production Stage") or "未設定"
    source_status = select_name(page, "Source Status") or "未確認"
    premium = "対象" if _checkbox_value(page, "Premium Candidate") else "対象外"
    has_answer = "あり" if _rich_text_value(page, "Short Answer").strip() else "未作成"

    runs = [{"text": {"content": question, "link": {"url": page_url(page["id"])}}}]
    runs.append({"text": {"content": (
        f" ｜ 状態: {status_label} ｜ Story Status: {story_status} ｜ Production Stage: {stage} ｜ "
        f"回答: {has_answer} ｜ Source Status: {source_status} ｜ Premium候補: {premium}"
    )}})
    return runs


def _related_sources_ids(page):
    rel = page.get("properties", {}).get("Related Sources", {})
    return [r["id"] for r in rel.get("relation", [])] if rel.get("type") == "relation" else []


def qa_next_action(page):
    """A suggested next step only -- never an action taken or a publish
    decision. Ordered by what actually blocks progress: an unwritten answer
    blocks everything else, so it always wins; an unconfirmed Source is the
    next blocker; only once both exist does "which existing article" or
    "approve/hold" become the live question."""
    if not _rich_text_value(page, "Short Answer").strip():
        return "回答案を確認・作成する"
    if select_name(page, "Source Status") in ("Unverified", "Needs Recheck"):
        return "一次情報でSourceを確認する"
    if _story_bank_research_ids(page) or _generated_article_ids(page):
        return "既存記事へ誘導するか、DEEP記事候補へ送るか判断する"
    story_status = _story_status(page)
    if story_status == "New":
        return "内容を確認し、承認するか修正するか判断する"
    if story_status == "Approved":
        return "掲載するか見送るか判断する"
    return "状況を確認する"


def compute_qa_buckets(token, story_pages):
    """❓ QAカード・提供情報一覧 (2026-07-20). Story Bank is the existing DB --
    no new database. Only records with a non-empty QA Question count as QA
    candidates, so the 22 existing 花火大会 (fireworks) records (none of
    which have QA Question filled in) are excluded automatically, per Rei's
    instruction not to treat them as foreign-resident QA content. Their
    Status/properties are never touched here (read-only digest).
    """
    qa = [p for p in story_pages if _rich_text_value(p, "QA Question").strip()]
    today = datetime.now(JST).date()
    today_new = [p for p in qa if created_date_jst(p) == today]

    answer_pending = [p for p in qa if not _rich_text_value(p, "Short Answer").strip()]
    source_pending = [p for p in qa if select_name(p, "Source Status") in ("Unverified", "Needs Recheck")]
    ready = [p for p in qa if _story_status(p) == "Approved"]
    delivered = [p for p in qa if _story_status(p) == "Published"]
    needs_update = [p for p in qa if _next_review_overdue(p) or select_name(p, "Source Status") == "Needs Recheck"]
    premium_candidates = [p for p in qa if _checkbox_value(p, "Premium Candidate")]
    linked_to_research = [p for p in qa if _story_bank_research_ids(p) or _generated_article_ids(p)]

    published_ids = set()
    for p in qa:
        for aid in _generated_article_ids(p):
            ap = notion_request(token, "GET", f"/pages/{aid}")
            pub = ap.get("properties", {}).get("Publishing Status", {}).get("select")
            if pub and pub.get("name") == "Published":
                published_ids.add(p["id"])
                break
    published = [p for p in qa if p["id"] in published_ids]

    return {
        "qa": qa, "today_new": today_new, "answer_pending": answer_pending,
        "source_pending": source_pending, "ready": ready, "delivered": delivered,
        "needs_update": needs_update, "premium_candidates": premium_candidates,
        "published": published, "linked_to_research": linked_to_research,
    }


QA_CARD_PAGE_ID = "3a2157f0-f15d-8139-8e8c-c5ca906141be"
QA_DESK_MARKER_START = "❓ QAカード作業机（自動生成セクション開始 -- 以下は毎回自動更新されます。手動編集しないでください）"
QA_DESK_MARKER_END = "❓ QAカード作業机（自動生成セクション終了）"


def _linked_page_title(token, page_id):
    p = notion_request(token, "GET", f"/pages/{page_id}")
    return title_of(p) or "(無題)"


# Classification against the ARu app's already-published QA cards, per
# Rei's own review of 20 app screenshots (relayed via chat transcript,
# 2026-07-21) -- NOT derived from any Notion property, and NOT a claim that
# these Story Bank records themselves are published. Matching requires
# human judgment (same question vs. related-but-different scope), which no
# existing property captures, so this is a small explicit lookup rather
# than an automated matcher. Story Status is never touched by this table --
# it only changes what this page displays.
QA_APP_MATCH_CANDIDATES = {
    # Story Bank page id -> the app screenshot's question text (as transcribed)
    "3a3157f0-f15d-81c3-88b7-e377d26d7b73": "地震が来た！どうすればいい？",
    "3a3157f0-f15d-817d-b140-d9f9e061b396": "携帯（スマートフォン）を契約するには？",
}
QA_APP_RELATED_DIFFERENT = {
    # Story Bank page id -> (app screenshot question text, why it's not the same question)
    "3a3157f0-f15d-8156-8653-f885bb449a69": (
        "日本に住み始めたら何をするの？",
        "住み始めの手続き全般と、住民登録の場所は質問範囲が異なる"),
    "3a3157f0-f15d-819d-b3df-f12426bb6862": (
        "健康保険って何？",
        "制度説明と、保険証がない場合の受診方法は別"),
    "3a3157f0-f15d-8185-8cf7-e8ea66f9a9cf": (
        "日本のゴミの分け方を知りたい。",
        "分別方法の説明と、確認先（自治体サイト等）を尋ねる質問は異なる"),
    "3a3157f0-f15d-81a1-8666-d797646c6d45": (
        "保証人・礼金・敷金って何？",
        "用語説明と、保証人がいない場合の解決方法は別"),
    "3a3157f0-f15d-8183-8022-db3efb53110d": (
        "病院で使う日本語は？",
        "医療機関の探し方と、日本語フレーズは別"),
    "3a3157f0-f15d-8134-83c4-d4cd06bda971": (
        "子供の保育園・学校への入学はどうしたらいい？",
        "保育園と公立学校は制度・所管・対象年齢が異なるため同一視しない"),
    "3a3157f0-f15d-81be-a5a7-e82caece0588": (
        "母国の運転免許は日本でそのまま使えるの？",
        "日本で使える条件と、切替手続きは別"),
}


def qa_desk_toggle(token, page, app_note=None):
    """One QA candidate = one toggle, closed by default, holding every field
    Rei asked for so the theme desk needs no other page or database open.
    Nothing here is fabricated: an empty Short Answer/Related Sources/Notes
    shows as an explicit unconfirmed state, never a guessed value.
    app_note, when given, is an extra line about the app-screenshot
    comparison -- purely informational, never a Story Status change."""
    question = _rich_text_value(page, "QA Question") or title_of(page) or "(質問未設定)"
    short_answer = _rich_text_value(page, "Short Answer").strip()
    notes = _rich_text_value(page, "Notes").strip()
    source_status = select_name(page, "Source Status") or "未確認"
    story_status = _story_status(page) or "-"
    next_action = qa_next_action(page)

    source_ids = _related_sources_ids(page)
    research_ids = _story_bank_research_ids(page)
    article_ids = _generated_article_ids(page)

    published_label = "未接続"
    if article_ids:
        for aid in article_ids:
            ap = notion_request(token, "GET", f"/pages/{aid}")
            pub = ap.get("properties", {}).get("Publishing Status", {}).get("select")
            pub_name = pub.get("name") if pub else "未確認"
            published_label = f"{_linked_page_title(token, aid)}（Publishing Status: {pub_name}）"
            break

    title_runs = [{"text": {"content": question, "link": {"url": page_url(page["id"])}}}]
    title_runs.append({"text": {"content": (
        f" ｜ Story Status: {story_status} ｜ Source: {source_status} ｜ "
        f"回答: {'あり' if short_answer else '未作成'}"
    )}})

    children = []

    def bold_label(label):
        return {"text": {"content": f"{label}: "}, "annotations": {"bold": True}}

    children.append({"paragraph": {"rich_text": [bold_label("質問本文"), {"text": {"content": question}}]}})
    children.append({"paragraph": {"rich_text": [
        bold_label("回答案"),
        {"text": {"content": short_answer if short_answer else "回答案未作成"}},
    ]}})
    children.append({"paragraph": {"rich_text": [
        bold_label("根拠となる一次情報"),
        {"text": {"content": notes if notes else "根拠未確認（一次情報での確認前）"}},
    ]}})

    source_runs = [bold_label("Source")]
    if source_ids:
        for sid in source_ids:
            sp = notion_request(token, "GET", f"/pages/{sid}")
            sp_props = sp.get("properties", {})
            s_title = title_of(sp) or "(無題)"
            s_url = sp_props.get("URL", {}).get("url")
            if s_url:
                source_runs.append({"text": {"content": f"{s_title}（"}})
                source_runs.append({"text": {"content": s_url, "link": {"url": s_url}}})
                source_runs.append({"text": {"content": "） "}})
            else:
                source_runs.append({"text": {"content": f"{s_title}（URL未確認） "}})
    else:
        source_runs.append({"text": {"content": "Source未接続（Related Sourcesが未設定）"}})
    children.append({"paragraph": {"rich_text": source_runs}})

    children.append({"paragraph": {"rich_text": [bold_label("Source確認状態"), {"text": {"content": source_status}}]}})

    research_runs = [bold_label("関連する既存Research・Article")]
    if research_ids or article_ids:
        titles = []
        for rid in research_ids:
            titles.append(f"[Research] {_linked_page_title(token, rid)}")
        for aid in article_ids:
            titles.append(f"[Article] {_linked_page_title(token, aid)}")
        research_runs.append({"text": {"content": "、".join(titles)}})
    else:
        research_runs.append({"text": {"content": "なし"}})
    children.append({"paragraph": {"rich_text": research_runs}})

    children.append({"paragraph": {"rich_text": [
        bold_label("公開・掲載状態"),
        {"text": {"content": f"Story Status={story_status} ｜ 接続先Article: {published_label}"}},
    ]}})

    needs_update_label = "要更新" if (_next_review_overdue(page) or source_status == "Needs Recheck") else "更新不要"
    children.append({"paragraph": {"rich_text": [bold_label("更新が必要か"), {"text": {"content": needs_update_label}}]}})

    children.append({"paragraph": {"rich_text": [
        {"text": {"content": "▶ Reiが次に行う作業: ", "link": None}, "annotations": {"bold": True, "color": "purple"}},
        {"text": {"content": next_action}},
    ]}})
    children.append({"paragraph": {"rich_text": [
        {"text": {"content": "元レコードを開く", "link": {"url": page_url(page["id"])}}},
    ]}})

    if app_note:
        children.append({"paragraph": {"rich_text": [
            {"text": {"content": "📱 アプリ画面との関係: "}, "annotations": {"bold": True, "color": "blue"}},
            {"text": {"content": app_note}},
        ]}})

    return {"toggle": {"rich_text": title_runs, "children": children}}


def build_qa_desk_blocks(env):
    """The QA theme desk (2026-07-20 redesign): the pink 'QAカード' callout on
    Home still links to this same page id (unchanged) -- what changed is this
    page's own content, from a static description + a linked-database view
    into a live work desk. Reuses compute_qa_buckets, the same function the
    (now-removed) Home mega-window and the untouched Dashboard both rely on --
    one computation, three possible renderings.

    2026-07-21: split into 3 sections reflecting Rei's screenshot review --
    🔗 candidates matching an already-published app card (Story Status left
    untouched; this is a comparison candidate, not a publication claim),
    💡 new proposals confirmed different from any related app card, and
    ⚠️ records this particular screenshot set couldn't confirm either way
    (never treated as "not published").
    """
    token = env["NOTION_TOKEN"]
    pages = _fetch_common_pages(env)
    story_pages = pages["story_pages"]
    bk = compute_qa_buckets(token, story_pages)
    qa = bk["qa"]

    match_candidates = [p for p in qa if p["id"] in QA_APP_MATCH_CANDIDATES]
    related_different = [p for p in qa if p["id"] in QA_APP_RELATED_DIFFERENT]
    classified_ids = set(QA_APP_MATCH_CANDIDATES) | set(QA_APP_RELATED_DIFFERENT)
    unconfirmed_range = [p for p in qa if p["id"] not in classified_ids]

    summary = (
        f"QA候補: {len(qa)}件 / 🔗アプリ掲載済みQAとの照合候補: {len(match_candidates)}件 / "
        f"💡これからのQA提案: {len(related_different)}件 / ⚠️アプリ掲載状況の確認待ち: {len(unconfirmed_range)}件 / "
        f"回答作成待ち: {len(bk['answer_pending'])}件 / Source確認待ち: {len(bk['source_pending'])}件"
    )

    blocks = [{"callout": {
        "rich_text": rt(summary),
        "icon": {"type": "emoji", "emoji": "❓"}, "color": "purple_background",
    }}]

    blocks.append({"paragraph": {"rich_text": rt(
        "🔗 アプリ掲載済みQAとの照合候補 -- アプリ側のQAカードは掲載済みですが、"
        "このStory Bankレコード自体が掲載済みと確定したわけではありません。Story Statusは変更していません。",
        bold=True,
    )}})
    for p in match_candidates:
        app_text = QA_APP_MATCH_CANDIDATES[p["id"]]
        blocks.append(qa_desk_toggle(token, p, app_note=f"アプリ側の表示文（転記）: 「{app_text}」。同一内容の照合候補。"))
    if not match_candidates:
        blocks.append({"paragraph": {"rich_text": rt("該当レコードなし")}})

    blocks.append({"paragraph": {"rich_text": rt(
        "💡 これからのQA提案 -- アプリに関連テーマのカードはありますが、知りたい内容が異なる新しい質問です。",
        bold=True,
    )}})
    for p in related_different:
        app_text, reason = QA_APP_RELATED_DIFFERENT[p["id"]]
        blocks.append(qa_desk_toggle(
            token, p, app_note=f"アプリに関連テーマのカードあり（転記: 「{app_text}」）。別質問と判断した理由: {reason}"))
    if not related_different:
        blocks.append({"paragraph": {"rich_text": rt("該当レコードなし")}})

    blocks.append({"paragraph": {"rich_text": rt(
        "⚠️ アプリ掲載状況の確認待ち -- 今回の画像範囲では確認できないため、未掲載とは断定しません。",
        bold=True,
    )}})
    for p in unconfirmed_range:
        blocks.append(qa_desk_toggle(token, p, app_note="今回の画像範囲では対応するアプリカードを確認できていません（未掲載と断定しない）。"))
    if not unconfirmed_range:
        blocks.append({"paragraph": {"rich_text": rt("該当レコードなし")}})

    return blocks


def write_to_qa_desk(env, blocks):
    """Same marker delete-and-reinsert pattern as write_to_dashboard/
    write_to_home, but targets the QA card page and inserts after its 3
    existing static description paragraphs (kept, never touched) and before
    the old linked-database block, which is left in place as a fallback raw
    view -- not deleted, per Rei's instruction not to remove existing
    detail-page content."""
    token = env["NOTION_TOKEN"]
    page_id = QA_CARD_PAGE_ID

    results = _fetch_all_children(token, page_id)

    start_idx = end_idx = None
    last_paragraph_idx = None
    for i, b in enumerate(results):
        text = _block_plain_text(b)
        if text == QA_DESK_MARKER_START:
            start_idx = i
        elif text == QA_DESK_MARKER_END:
            end_idx = i
        elif b["type"] == "paragraph" and start_idx is None:
            last_paragraph_idx = i

    if start_idx is not None and end_idx is not None and end_idx > start_idx:
        log(f"Found existing QA desk markers (start={start_idx}, end={end_idx}); refreshing in place.")
        for b in results[start_idx + 1:end_idx]:
            notion_request(token, "DELETE", f"/blocks/{b['id']}")
        anchor = results[start_idx]["id"]
        for i in range(0, len(blocks), 90):
            chunk = blocks[i:i + 90]
            _, anchor = _append_children(token, page_id, chunk, after=anchor)
    else:
        if last_paragraph_idx is None:
            raise RuntimeError("Could not find the QA page's existing description paragraphs -- refusing to guess.")
        log("No existing QA desk markers found; inserting after the 3 static description paragraphs.")
        start_marker = {"callout": {"rich_text": rt(QA_DESK_MARKER_START), "icon": {"type": "emoji", "emoji": "❓"}}}
        end_marker = {"callout": {"rich_text": rt(QA_DESK_MARKER_END), "icon": {"type": "emoji", "emoji": "❓"}}}
        anchor = results[last_paragraph_idx]["id"]
        all_new = [start_marker] + blocks + [end_marker]
        for i in range(0, len(all_new), 90):
            chunk = all_new[i:i + 90]
            _, anchor = _append_children(token, page_id, chunk, after=anchor)

    return page_id


def build_qa_section(token, story_pages):
    bk = compute_qa_buckets(token, story_pages)
    qa, today_new = bk["qa"], bk["today_new"]
    answer_pending, source_pending = bk["answer_pending"], bk["source_pending"]
    ready, delivered = bk["ready"], bk["delivered"]
    needs_update, premium_candidates, published = bk["needs_update"], bk["premium_candidates"], bk["published"]

    blocks = []
    blocks.append({"heading_3": {"rich_text": rt("❓ QAカード・提供情報一覧")}})
    blocks.append({"callout": {
        "rich_text": rt(
            f"今日追加した質問: {len(today_new)}件（created_time基準・JST） / "
            f"QAカード候補（全件）: {len(qa)}件 / 回答作成待ち: {len(answer_pending)}件 / "
            f"Source確認待ち: {len(source_pending)}件"
        ),
        "icon": {"type": "emoji", "emoji": "❓"}, "color": "purple_background",
    }})

    for label, items, count_label in [
        ("回答作成待ち", answer_pending, "回答作成待ち"),
        ("Source確認待ち", source_pending, "Source確認待ち"),
        ("掲載準備中（Story Status=Approved）", ready, "掲載準備中"),
        ("ARuアプリへ提供済み（Story Status=Published）", delivered, "提供済み"),
        ("掲載済み（Generated ArticleがPublished）", published, "掲載済み"),
        ("更新が必要（Next Review超過 または Source Status=Needs Recheck）", needs_update, "更新が必要"),
        ("Premium記事候補", premium_candidates, "Premium候補"),
    ]:
        children = [{"paragraph": {"rich_text": qa_card_runs(p, count_label)}} for p in items]
        blocks.append(_toggle(f"{label} 一覧", len(items), children))

    return blocks


def event_card_runs(page, status_label):
    title = title_of(page) or "(無題)"
    location = _rich_text_value(page, "Location") or "未確認"
    status = status_name(page) or "-"
    event_date = page.get("properties", {}).get("Event Date", {}).get("date")
    date_str = event_date.get("start") if event_date else "未確認"
    source_url = page.get("properties", {}).get("Source URL", {}).get("url")
    runs = [{"text": {"content": title, "link": {"url": page_url(page["id"])}}}]
    runs.append({"text": {"content": (
        f" ｜ 状態: {status_label} ｜ 所在地: {location} ｜ 開催日: {date_str} ｜ "
        f"確認状態: {status} ｜ 保存先: Event Calendar ｜ Source: "
    )}})
    runs.append({"text": {"content": source_url, "link": {"url": source_url}}} if source_url
                 else {"text": {"content": "未確認"}})
    return runs


def _event_date_of(page):
    d = page.get("properties", {}).get("Event Date", {}).get("date")
    if not d or not d.get("start"):
        return None
    try:
        return datetime.fromisoformat(d["start"].split("T")[0]).date()
    except ValueError:
        return None


def compute_event_calendar_buckets(ec_pages):
    """🎉 イベント・催し. Covers ALL Event Calendar records (not only the ones
    already surfaced by 🎎 culture's 期間限定/低確度候補 buckets) -- this is a
    new, independent dimension over the same DB, not a duplicate computation
    of the culture logic."""
    today = datetime.now(JST).date()

    cancelled = [p for p in ec_pages if status_name(p) == "Cancelled"]
    cancelled_ids = {p["id"] for p in cancelled}

    def is_expired(p):
        if status_name(p) == "Completed":
            return True
        d = _event_date_of(p)
        return d is not None and d < today

    expired = [p for p in ec_pages if p["id"] not in cancelled_ids and is_expired(p)]
    expired_ids = {p["id"] for p in expired}

    remaining = [p for p in ec_pages if p["id"] not in cancelled_ids and p["id"] not in expired_ids]
    today_events = [p for p in remaining if _event_date_of(p) == today]
    today_ids = {p["id"] for p in today_events}
    upcoming = [p for p in remaining
                if p["id"] not in today_ids and _event_date_of(p) is not None and _event_date_of(p) > today]
    upcoming_ids = {p["id"] for p in upcoming}
    unconfirmed = [p for p in remaining if p["id"] not in today_ids and p["id"] not in upcoming_ids]

    created_today = [p for p in ec_pages if created_date_jst(p) == today]

    return {
        "cancelled": cancelled, "expired": expired, "today": today_events,
        "upcoming": upcoming, "unconfirmed": unconfirmed, "today_new": created_today,
    }


def article_card_runs(page, status_label, db_label):
    title = title_of(page) or "(無題)"
    status = select_name(page, "Status") or select_name(page, "Publishing Status") or "-"
    last_ai = page.get("properties", {}).get("Last AI Update", {}).get("date")
    last_ai_str = last_ai["start"] if last_ai else "未確認"
    runs = [{"text": {"content": title, "link": {"url": page_url(page["id"])}}}]
    runs.append({"text": {"content": (
        f" ｜ 状態: {status_label} ｜ Status: {status} ｜ 最終確認日: {last_ai_str} ｜ 保存先: {db_label}"
    )}})
    return runs


def compute_articles_research_buckets(research_pages, articles_pages):
    """📝 記事・Premium候補. Research.Status=New/Reviewing map to the
    pre-Article-Brief stages; Articles' own Status/Review Result/Publishing
    Status/Freshness Status (all existing exact option values, nothing
    guessed) cover the drafting-through-published stages."""
    brief_in_progress = [p for p in research_pages if status_name(p) == "Reviewing"]
    ready_to_write = [p for p in research_pages if status_name(p) == "New"]

    ai_draft = [p for p in articles_pages if select_name(p, "Status") == "AI Draft"]
    human_review = [p for p in articles_pages if select_name(p, "Status") == "Human Review"]
    needs_revision = [p for p in articles_pages if select_name(p, "Review Result") == "Needs Revision"]
    needs_update = [p for p in articles_pages
                    if select_name(p, "Publishing Status") == "Needs Update"
                    or select_name(p, "Freshness Status") == "Needs Update"]
    published = [p for p in articles_pages if select_name(p, "Publishing Status") == "Published"]

    today = datetime.now(JST).date()
    today_new = [p for p in (research_pages + articles_pages) if created_date_jst(p) == today]

    return {
        "brief_in_progress": brief_in_progress, "ready_to_write": ready_to_write,
        "ai_draft": ai_draft, "human_review": human_review, "needs_revision": needs_revision,
        "needs_update": needs_update, "published": published, "today_new": today_new,
    }


def cross_cutting_card_runs(page, db_label, reason):
    title = title_of(page) or "(無題)"
    status = (status_name(page) or select_name(page, "Story Status")
              or select_name(page, "Publishing Status") or "-")
    source_url = page.get("properties", {}).get("Source URL", {}).get("url")
    runs = [{"text": {"content": title, "link": {"url": page_url(page["id"])}}}]
    runs.append({"text": {"content": f" ｜ 理由: {reason} ｜ Status: {status} ｜ 保存先: {db_label} ｜ Source: "}})
    runs.append({"text": {"content": source_url, "link": {"url": source_url}}} if source_url
                 else {"text": {"content": "未確認"}})
    return runs


def build_cross_cutting_buckets(culture_bk, food_bk, people_bk, qa_bk, ec_bk, ar_bk):
    """今日の新着 / 変更・中止・期限切れ / 掲載済み・提供済み must show each
    record at most once (Rei's priority order: 変更中止期限切れ > Rei確認待ち >
    本日近日開催 > 回答記事作成待ち > 今日の新着 > その他). Domain toggles
    (QA/文化体験/イベント/人物/食/未分類/記事) are NOT deduped against this --
    they always show their own complete list, per Rei's explicit instruction
    that summary/cross-cutting views and full per-domain lists must not be
    conflated. Built in priority order; each take() call skips ids already
    claimed by a higher-priority bucket.
    """
    seen_ids = set()

    def take(items, db_label, reason):
        out = []
        for p in items:
            if p["id"] in seen_ids:
                continue
            seen_ids.add(p["id"])
            out.append((p, db_label, reason))
        return out

    cancelled_expired = (
        take(culture_bk["ended_low_confidence"], "Event Calendar", "文化・交流イベント候補の終了")
        + take(ec_bk["cancelled"], "Event Calendar", "イベント中止")
        + take(ec_bk["expired"], "Event Calendar", "イベント終了・期限切れ")
        + take(food_bk["recheck"], "Experience Intelligence", "営業状況の再確認が必要")
        + take(ar_bk["needs_update"], "Articles", "記事の更新が必要")
    )

    published_delivered = (
        take(qa_bk["delivered"], "Story Bank", "ARuアプリへ提供済み")
        + take(qa_bk["published"], "Story Bank", "QAカード掲載済み")
        + take(ar_bk["published"], "Articles", "記事掲載済み")
    )

    today_candidates = (
        take(culture_bk["today_new"], "Experience Intelligence/Event Calendar", "文化体験の新着")
        + take(food_bk["today_new"], "Experience Intelligence", "食の安心の新着")
        + take(people_bk["today_new"], "Experience Intelligence", "人物・お店の新着")
        + take(qa_bk["today_new"], "Story Bank", "QAカードの新着")
        + take(ec_bk["today_new"], "Event Calendar", "イベントの新着")
        + take(ar_bk["today_new"], "Research/Articles", "記事・Researchの新着")
    )

    return cancelled_expired, published_delivered, today_candidates


HOME_MARKER_START = "📋 ARu編集デスク｜すべての情報（自動生成セクション開始 -- 以下は毎回自動更新されます。手動編集しないでください）"
HOME_MARKER_END = "📋 ARu編集デスク｜すべての情報（自動生成セクション終了）"


def _sub_bucket(label, items, render_fn):
    """A bold pseudo-header paragraph followed by that sub-bucket's full
    record list -- deliberately NOT a nested toggle-within-toggle. Notion's
    append-children API does not reliably support more than one level of
    nested children per request, and Home is Rei's primary daily screen, so
    this trades a little visual nesting for a write that cannot partially
    fail. A record is never trimmed to "first N"; every sub-bucket's full
    list is always included here."""
    out = [{"paragraph": {"rich_text": rt(f"▪ {label}（{len(items)}件）", bold=True)}}]
    if items:
        out.extend({"paragraph": {"rich_text": render_fn(p)}} for p in items)
    else:
        out.append({"paragraph": {"rich_text": rt("該当レコードなし")}})
    return out


def _domain_toggle(label, count, sub_buckets):
    """sub_buckets: list of (label, items, render_fn) -- flattened into one
    toggle's children via _sub_bucket, so the whole domain opens as a single
    click and shows every sub-state in full."""
    children = []
    for sub_label, items, render_fn in sub_buckets:
        children.extend(_sub_bucket(sub_label, items, render_fn))
    return _toggle(label, count, children)


def build_home_digest_blocks(env):
    """📋 ARu編集デスク｜すべての情報 -- the single Home consolidation window
    (2026-07-20). Reuses the exact same compute_*_buckets functions Dashboard
    calls (via _fetch_common_pages) -- Home and Dashboard can never disagree
    on a count because they share the same code, not just the same data.
    Renders as ONE callout containing all toggles as its children (never as
    separate top-level colored callouts), per Rei's explicit instruction.
    """
    token = env["NOTION_TOKEN"]
    pages = _fetch_common_pages(env)
    ei_pages, ec_pages = pages["ei_pages"], pages["ec_pages"]
    source_library_pages, story_pages = pages["source_library_pages"], pages["story_pages"]
    research_pages, articles_pages = pages["research_pages"], pages["articles_pages"]

    culture_bk = compute_culture_buckets(token, ei_pages, ec_pages, source_library_pages)
    food_bk = compute_food_buckets(ei_pages)
    people_bk = compute_people_buckets(ei_pages)
    qa_bk = compute_qa_buckets(token, story_pages)
    ec_bk = compute_event_calendar_buckets(ec_pages)
    ar_bk = compute_articles_research_buckets(research_pages, articles_pages)
    unclassified = compute_unclassified(ei_pages)

    cancelled_expired, published_delivered, today_candidates = build_cross_cutting_buckets(
        culture_bk, food_bk, people_bk, qa_bk, ec_bk, ar_bk)

    total_rei_pending = (
        len(culture_bk["rei_pending"]) + len(food_bk["pending"]) + len(people_bk["pending"])
        + len(qa_bk["answer_pending"]) + len(unclassified)
    )
    total_upcoming = len(ec_bk["today"]) + len(ec_bk["upcoming"])

    summary_text = (
        f"今日の新着: {len(today_candidates)}件 / Rei確認待ち: {total_rei_pending}件 / "
        f"本日・近日開催: {total_upcoming}件 / 更新・期限切れ: {len(cancelled_expired)}件"
    )

    def render_cross(items):
        return [{"paragraph": {"rich_text": cross_cutting_card_runs(p, db, reason)}} for p, db, reason in items]

    culture_source_type = culture_bk["cached_source_type"]
    culture_full_list = culture_bk["culture_ei"] + culture_bk["period_ec"]

    toggles = []
    toggles.append(_toggle("▸ 今日の新着", len(today_candidates), render_cross(today_candidates)))

    toggles.append(_domain_toggle(f"▸ ❓ QAカード", len(qa_bk["qa"]), [
        ("回答作成待ち", qa_bk["answer_pending"], lambda p: qa_card_runs(p, "回答作成待ち")),
        ("Source確認待ち", qa_bk["source_pending"], lambda p: qa_card_runs(p, "Source確認待ち")),
        ("既存記事への導線あり", qa_bk["linked_to_research"], lambda p: qa_card_runs(p, "既存記事への導線あり")),
        ("掲載準備中", qa_bk["ready"], lambda p: qa_card_runs(p, "掲載準備中")),
        ("掲載済み", qa_bk["published"], lambda p: qa_card_runs(p, "掲載済み")),
        ("更新が必要", qa_bk["needs_update"], lambda p: qa_card_runs(p, "更新が必要")),
    ]))

    toggles.append(_domain_toggle(f"▸ 🎎 日本文化体験", len(culture_full_list), [
        ("通年・通常営業", culture_bk["culture_ei"],
         lambda p: culture_card_runs(p, "Experience Intelligence", "常設", "情報の鮮度再確認", culture_source_type(p))),
        ("期間限定", culture_bk["period_ec"],
         lambda p: culture_card_runs(p, "Event Calendar", "期間限定", "開催内容確認", culture_source_type(p))),
        ("内容確認待ち", culture_bk["pending_low_confidence"],
         lambda p: culture_card_runs(p, "Event Calendar", "候補・要確認", "内容確認", culture_source_type(p))),
        ("終了・過去候補", culture_bk["ended_low_confidence"],
         lambda p: culture_card_runs(p, "Event Calendar", "終了", "アーカイブ保持のみ", culture_source_type(p))),
        ("Rei確認待ち", culture_bk["pending_ei"] + culture_bk["pending_ec_period"] + culture_bk["pending_low_confidence"],
         lambda p: culture_card_runs(
             p, "Experience Intelligence" if p["id"] in culture_bk["culture_ei_ids"] else "Event Calendar",
             "要確認", "最終確認", culture_source_type(p))),
    ]))

    toggles.append(_domain_toggle(f"▸ 🎉 イベント・催し", len(ec_pages), [
        ("本日開催", ec_bk["today"], lambda p: event_card_runs(p, "本日開催")),
        ("近日開催", ec_bk["upcoming"], lambda p: event_card_runs(p, "近日開催")),
        ("変更・中止", ec_bk["cancelled"], lambda p: event_card_runs(p, "中止")),
        ("終了・期限切れ", ec_bk["expired"], lambda p: event_card_runs(p, "終了")),
        ("詳細未確認", ec_bk["unconfirmed"], lambda p: event_card_runs(p, "詳細未確認")),
    ]))

    toggles.append(_domain_toggle(f"▸ 🌏 日本で活躍する外国人・人物とお店", len(people_bk["people"]), [
        ("人物・店舗", people_bk["people"], lambda p: person_card_runs(token, p, "掲載可否の判断に必要な情報を確認")),
        ("Rei確認待ち", people_bk["pending"], lambda p: person_card_runs(token, p, "登録内容の最終確認")),
    ]))

    toggles.append(_domain_toggle(f"▸ 🥗 食の安心・お店情報", len(food_bk["food"]), [
        ("ハラール認証", food_bk["halal_cert"], lambda p: rt(card_line(p), link=page_url(p["id"]))),
        ("ムスリムフレンドリー", food_bk["muslim_friendly"], lambda p: rt(card_line(p), link=page_url(p["id"]))),
        ("ベジタリアン・ヴィーガン", food_bk["veg_vegan"], lambda p: rt(card_line(p), link=page_url(p["id"]))),
        ("その他の食事条件", food_bk["gluten_allergy"] + food_bk["other_religious"] + food_bk["avoid_pork_alcohol"],
         lambda p: rt(card_line(p), link=page_url(p["id"]))),
        ("営業状況の再確認", food_bk["recheck"], lambda p: rt(card_line(p), link=page_url(p["id"]))),
    ]))

    def unclassified_runs(p):
        title = title_of(p) or "(無題)"
        status = status_name(p) or "-"
        source_url = p.get("properties", {}).get("Source URL", {}).get("url")
        source_type = classify_source_type(token, p)
        runs = [{"text": {"content": title, "link": {"url": page_url(p["id"])}}}]
        runs.append({"text": {"content": f" ｜ Status: {status} ｜ 情報元の区分: {source_type} ｜ Source: "}})
        runs.append({"text": {"content": source_url, "link": {"url": source_url}}} if source_url
                     else {"text": {"content": "未確認"}})
        return runs

    toggles.append(_toggle("▸ 🔎 未分類・詳細未確認", len(unclassified),
                            [{"paragraph": {"rich_text": unclassified_runs(p)}} for p in unclassified]))

    toggles.append(_domain_toggle("▸ 📝 記事・Premium候補", 0, [
        ("Article Brief作成中", ar_bk["brief_in_progress"], lambda p: article_card_runs(p, "Article Brief作成中", "Research")),
        ("執筆可能", ar_bk["ready_to_write"], lambda p: article_card_runs(p, "執筆可能", "Research")),
        ("AI Draft", ar_bk["ai_draft"], lambda p: article_card_runs(p, "AI Draft", "Articles")),
        ("人間確認待ち", ar_bk["human_review"], lambda p: article_card_runs(p, "人間確認待ち", "Articles")),
        ("Needs Revision", ar_bk["needs_revision"], lambda p: article_card_runs(p, "Needs Revision", "Articles")),
        ("更新が必要", ar_bk["needs_update"], lambda p: article_card_runs(p, "更新が必要", "Articles")),
        ("掲載済み", ar_bk["published"], lambda p: article_card_runs(p, "掲載済み", "Articles")),
    ]))

    toggles.append(_toggle("▸ 変更・中止・期限切れ", len(cancelled_expired), render_cross(cancelled_expired)))
    toggles.append(_toggle("▸ 掲載済み・提供済み", len(published_delivered), render_cross(published_delivered)))

    # Returned as (callout_shell, toggles) rather than one deeply nested
    # object: write_to_home() creates the callout with only the summary
    # paragraph first, then appends each toggle to it individually. Every
    # single API call this produces nests at most one level (a toggle plus
    # its own paragraph children) -- the same shape already proven safe
    # throughout this project, rather than risking an unverified 3-level
    # nested create (callout > toggle > paragraph) in one shot on Rei's
    # primary daily screen.
    callout_shell = {
        "callout": {
            "rich_text": rt("📋 ARu編集デスク｜すべての情報　-- 下のトグルを開くと、その分野の全件をここで確認できます"),
            "icon": {"type": "emoji", "emoji": "📋"},
            "color": "gray_background",
            "children": [{"paragraph": {"rich_text": rt(summary_text)}}],
        }
    }
    return callout_shell, toggles


# ARu Studio Home page id. Not in notion-build/.env (only Dashboard/Editor
# Home/AI Command Center page ids live there) -- kept as an explicit constant
# here, same treatment as Dashboard's TOP_ANCHOR_BLOCK_ID below.
ARU_STUDIO_HOME_PAGE_ID = "3a2157f0-f15d-816f-a87b-e41634d860e3"


def write_to_home(env, callout_shell, toggles):
    """Same delete-and-reinsert-in-place pattern as write_to_dashboard, but
    targets ARu Studio Home and inserts (on first run) directly after the
    '今日使う窓' heading -- before every existing callout, per Rei's
    instruction that the consolidated window comes first.

    Staged construction: create the marker pair + the callout shell (with
    only its summary paragraph) in one call, then append each toggle
    individually to the callout's own block id. No single API call ever
    nests more than one level deep (a toggle plus its own paragraph
    children).
    """
    token = env["NOTION_TOKEN"]
    page_id = ARU_STUDIO_HOME_PAGE_ID

    results = _fetch_all_children(token, page_id)

    start_idx = end_idx = None
    today_kado_heading_idx = None
    for i, b in enumerate(results):
        text = _block_plain_text(b)
        if text == HOME_MARKER_START:
            start_idx = i
        elif text == HOME_MARKER_END:
            end_idx = i
        elif text == "今日使う窓" and b["type"] == "heading_2":
            today_kado_heading_idx = i

    if start_idx is not None and end_idx is not None and end_idx > start_idx:
        log(f"Found existing Home markers (start={start_idx}, end={end_idx}); refreshing in place.")
        for b in results[start_idx + 1:end_idx]:
            notion_request(token, "DELETE", f"/blocks/{b['id']}")
        anchor = results[start_idx]["id"]
        created, anchor = _append_children(token, page_id, [callout_shell], after=anchor)
    else:
        if today_kado_heading_idx is None:
            raise RuntimeError("Could not find '今日使う窓' heading on Home -- refusing to guess an insertion point.")
        log("No existing Home markers found; inserting right after the '今日使う窓' heading.")
        start_marker = {"callout": {"rich_text": rt(HOME_MARKER_START), "icon": {"type": "emoji", "emoji": "📋"}}}
        end_marker = {"callout": {"rich_text": rt(HOME_MARKER_END), "icon": {"type": "emoji", "emoji": "📋"}}}
        anchor = results[today_kado_heading_idx]["id"]
        created, anchor = _append_children(token, page_id, [start_marker, callout_shell, end_marker], after=anchor)

    callout_id = created[0]["id"] if start_idx is not None else created[1]["id"]

    for tog in toggles:
        notion_request(token, "PATCH", f"/blocks/{callout_id}/children", {"children": [tog]})

    return page_id, callout_id


def _fetch_common_pages(env):
    """Single shared fetch+test-exclusion point for every DB the digest reads,
    used identically by Dashboard's build_section_blocks and Home's
    build_home_digest_blocks -- so the two surfaces can never compute
    different numbers for the same underlying data (2026-07-20)."""
    token = env["NOTION_TOKEN"]
    raw = {
        "ei_pages": query_database(token, env["EXPERIENCE_INTELLIGENCE_DB_ID"]),
        "ec_pages": query_database(token, env["EVENT_CALENDAR_DB_ID"]),
        "source_library_pages": query_database(token, env["SOURCE_LIBRARY_DB_ID"]),
        "story_pages": query_database(token, env["STORY_BANK_DB_ID"]),
        "research_pages": query_database(token, env["RESEARCH_DB_ID"]),
        "articles_pages": query_database(token, env["ARTICLES_DB_ID"]),
    }
    return {k: [p for p in v if not is_test_record(p)] for k, v in raw.items()}


def build_section_blocks(env):
    token = env["NOTION_TOKEN"]
    pages = _fetch_common_pages(env)
    ei_pages, ec_pages = pages["ei_pages"], pages["ec_pages"]
    source_library_pages, story_pages = pages["source_library_pages"], pages["story_pages"]

    blocks = []
    blocks.append({"heading_2": {"rich_text": rt("ARu編集デスク｜今日の情報")}})
    blocks.append({"callout": {
        "rich_text": rt(
            "Reiが毎日確認する統合編集画面です。今回実装済みなのは🎎日本文化体験、🥗食の安心・お店情報、"
            "未分類・詳細未確認、❓QAカード・提供情報一覧、🌏日本で活躍する外国人・人物とお店の5項目。"
            "他の3項目は準備中（クロスDB集計ロジックが未設計のため、勝手な自動判定はしていません）。"
        ),
        "icon": {"type": "emoji", "emoji": "📋"}, "color": "gray_background",
    }})

    for h in PLACEHOLDER_HEADINGS:
        blocks.append({"heading_3": {"rich_text": rt(h)}})
        blocks.append({"paragraph": {"rich_text": rt("準備中（今回のスコープ外）")}})

    blocks.extend(build_culture_section(token, ei_pages, ec_pages, source_library_pages))

    blocks.extend(build_people_section(token, ei_pages))

    blocks.extend(build_food_section(ei_pages))

    blocks.extend(build_qa_section(token, story_pages))

    blocks.extend(build_unclassified_section(token, ei_pages))

    for h in PLACEHOLDER_HEADINGS_AFTER:
        blocks.append({"heading_3": {"rich_text": rt(h)}})
        if h == "深い記事候補":
            blocks.append({"paragraph": {"rich_text": rt(
                "準備中。自動判定はしていません。各サブセクション内の「Research連携済み」件数（Related Research設定済み）を参照してください。"
            )}})
        else:
            blocks.append({"paragraph": {"rich_text": rt("準備中（今回のスコープ外）")}})

    return blocks


def _block_plain_text(b):
    rt_list = b.get(b["type"], {}).get("rich_text")
    if not rt_list:
        return None
    return "".join(x.get("plain_text", "") for x in rt_list)


def _append_children(token, page_id, children_batch, after=None):
    body = {"children": children_batch}
    if after:
        body["after"] = after
    result = notion_request(token, "PATCH", f"/blocks/{page_id}/children", body)
    results = result.get("results") or []
    return results, (results[-1]["id"] if results else after)


def _fetch_all_children(token, page_id):
    all_blocks = []
    cursor = None
    while True:
        url = f"/blocks/{page_id}/children?page_size=100"
        if cursor:
            url += f"&start_cursor={cursor}"
        resp = notion_request(token, "GET", url)
        all_blocks.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return all_blocks


TOP_ANCHOR_BLOCK_ID = "b19de78f-67dd-4890-99e4-950e66b16f8f"  # "見やすいARu Studio Homeへ →" callout on Dashboard


def write_to_dashboard(env, blocks):
    token = env["NOTION_TOKEN"]
    page_id = env["DASHBOARD_PAGE_ID"]

    results = _fetch_all_children(token, page_id)

    start_idx = end_idx = None
    for i, b in enumerate(results):
        text = _block_plain_text(b)
        if text == MARKER_START:
            start_idx = i
        elif text == MARKER_END:
            end_idx = i

    culture_heading_block_id = None

    if start_idx is not None and end_idx is not None and end_idx > start_idx:
        log(f"Found existing ARu編集デスク markers (start={start_idx}, end={end_idx}); refreshing in place.")
        for b in results[start_idx + 1:end_idx]:
            notion_request(token, "DELETE", f"/blocks/{b['id']}")
        anchor = results[start_idx]["id"]
        for i in range(0, len(blocks), 90):
            chunk = blocks[i:i + 90]
            created, anchor = _append_children(token, page_id, chunk, after=anchor)
            for j, cb in enumerate(created):
                if _block_plain_text(cb) == "🎎 日本文化体験":
                    culture_heading_block_id = cb["id"]
    else:
        log("No existing ARu編集デスク markers found; inserting right after the "
            "'見やすいARu Studio Homeへ' callout (top of Dashboard), before existing sections.")
        start_marker = {"callout": {"rich_text": rt(MARKER_START), "icon": {"type": "emoji", "emoji": "📋"}}}
        end_marker = {"callout": {"rich_text": rt(MARKER_END), "icon": {"type": "emoji", "emoji": "📋"}}}
        all_new = [start_marker] + blocks + [end_marker]
        anchor = TOP_ANCHOR_BLOCK_ID
        for i in range(0, len(all_new), 90):
            chunk = all_new[i:i + 90]
            created, anchor = _append_children(token, page_id, chunk, after=anchor)
            for cb in created:
                if _block_plain_text(cb) == "🎎 日本文化体験":
                    culture_heading_block_id = cb["id"]

    return page_id, culture_heading_block_id


def main():
    env = load_env(ENV_PATH)
    blocks = build_section_blocks(env)
    page_id, culture_heading_block_id = write_to_dashboard(env, blocks)
    log(f"Done. Dashboard page: {page_id}")
    # This block id changes on every refresh (the whole section between the
    # markers is deleted and rewritten) -- do not use it for an external
    # deep link that needs to survive future runs. ARu Studio Home's 🎎
    # callout links to the stable page URL instead, for this reason.
    log(f"🎎 日本文化体験 heading block id (this run only, not stable): {culture_heading_block_id}")
    return culture_heading_block_id


def main_home():
    """Writes ONLY the new Home consolidated window -- never touches
    Dashboard, and (per this run) never touches any existing Home callout
    either; it only inserts/refreshes the content between HOME_MARKER_START
    and HOME_MARKER_END."""
    env = load_env(ENV_PATH)
    callout_shell, toggles = build_home_digest_blocks(env)
    page_id, callout_id = write_to_home(env, callout_shell, toggles)
    log(f"Done. Home page: {page_id}, callout block id: {callout_id}")
    return page_id, callout_id


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "home":
        main_home()
    else:
        main()
