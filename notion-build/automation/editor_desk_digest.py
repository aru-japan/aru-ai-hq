"""ARu編集デスク｜今日の情報 -- a new, separate marker-bounded section on the
Dashboard page (2026-07-20). Does NOT touch the existing AI Command Center
section, its own MARKER_START/END, or any of the 9 pre-existing numbered
sections -- this section owns its own pair of markers and only ever rewrites
what sits between them, exactly like ai_command_center.py's pattern.

Scope for this run: only the two subsections that have an actual approved
design (🎎 日本文化体験 and 🥗 食の安心・お店情報) are populated with live
data. The other 6 headings Rei asked to reserve a slot for (今日の新着 /
本日開催・近日開催 / 変更・中止・期限切れ / 詳細未確認 / 深い記事候補 /
Rei確認待ち) are written as explicit "準備中" placeholders -- no cross-DB
aggregation logic has been designed or approved for them yet, so nothing is
guessed here.

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
    "詳細未確認",
    "深い記事候補",
    "Rei確認待ち",
]


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


def build_culture_section(ei_pages):
    culture = [p for p in ei_pages if multi_select_names(p, "Experience Genre")]
    today = datetime.now(JST).date()
    today_new = [p for p in culture if created_date_jst(p) == today]
    pending = [p for p in culture if status_name(p) in ("New", "Reviewing")]
    research_linked = [p for p in culture
                        if p.get("properties", {}).get("Related Research", {}).get("relation")]
    recheck = [p for p in culture if needs_recheck(p)]

    by_region = {}
    by_genre = {}
    reservation_yes = []
    lang_yes = []
    family_yes = []
    unconfirmed = []
    for p in culture:
        r = select_name(p, "Region") or "未確認"
        by_region.setdefault(r, []).append(p)
        for g in multi_select_names(p, "Experience Genre"):
            by_genre.setdefault(g, []).append(p)
        resv = select_name(p, "Reservation Status")
        if resv and resv not in ("記載なし", "未確認"):
            reservation_yes.append(p)
        lang_names = multi_select_names(p, "Language Support")
        # "日本語のみと記載" is a confirmed answer but means the opposite of
        # multilingual support -- must not be counted alongside the
        # positive tags, or "多言語ページあり" silently includes Japanese-only
        # records.
        if any(n in ("多言語Webページあり", "現地外国語対応を公式確認済み", "多言語予約対応") for n in lang_names):
            lang_yes.append(p)
        fam = select_name(p, "Family Participation Status")
        if fam and fam not in ("記載なし", "未確認"):
            family_yes.append(p)
        if status_name(p) in ("New", "Reviewing"):
            unconfirmed.append(p)

    blocks = []
    blocks.append({"heading_3": {"rich_text": rt("🎎 日本文化体験")}})
    blocks.append({"callout": {
        "rich_text": rt(
            f"今日見つけた文化体験: {len(today_new)}件（Notion Created time基準・JST） / "
            f"Rei確認待ち: {len(pending)}件（Status=New または Reviewing。まだReiが最終確認していない候補という意味で、公開可否の判断ではありません） / "
            f"全国の文化体験: {len(culture)}件（Experience Genre設定済み）"
        ),
        "icon": {"type": "emoji", "emoji": "🎎"}, "color": "yellow_background",
    }})
    filter_children = []
    filter_children.append({"paragraph": {"rich_text": rt(
        f"地域別: " + ", ".join(f"{k}={len(v)}" for k, v in sorted(by_region.items())) if by_region else "該当なし"
    )}})
    filter_children.append({"paragraph": {"rich_text": rt(
        f"ジャンル別: " + ", ".join(f"{k}={len(v)}" for k, v in sorted(by_genre.items())) if by_genre else "該当なし"
    )}})
    filter_children.append({"paragraph": {"rich_text": rt(f"予約情報あり: {len(reservation_yes)}件")}})
    filter_children.append({"paragraph": {"rich_text": rt(f"多言語ページあり: {len(lang_yes)}件")}})
    filter_children.append({"paragraph": {"rich_text": rt(f"家族で参加できる（公式確認・条件あり含む）: {len(family_yes)}件")}})
    filter_children.append({"paragraph": {"rich_text": rt(f"詳細未確認（Status=New/Reviewing）: {len(unconfirmed)}件")}})
    filter_children.append({"paragraph": {"rich_text": rt(f"Research連携済み（旧称: 深い記事候補。Related Research設定済みという意味で、AIによる候補判定ではありません）: {len(research_linked)}件")}})
    filter_children.append({"paragraph": {"rich_text": rt(f"営業・提供状況の再確認が必要（Last AI Update 90日超 または Status=Reviewing）: {len(recheck)}件")}})
    blocks.append({"toggle": {"rich_text": rt("絞り込みビュー"), "children": filter_children}})

    card_children = []
    for p in culture:
        card_children.append({"paragraph": {"rich_text": rt(card_line(p), link=page_url(p["id"]))}})
    if not card_children:
        card_children = [{"paragraph": {"rich_text": rt("該当レコードなし")}}]
    blocks.append({"toggle": {"rich_text": rt(f"全国の文化体験 一覧（{len(culture)}件）"), "children": card_children}})

    return blocks


def build_food_section(ei_pages):
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


def build_section_blocks(env):
    token = env["NOTION_TOKEN"]
    ei_pages = query_database(token, env["EXPERIENCE_INTELLIGENCE_DB_ID"])

    blocks = []
    blocks.append({"heading_2": {"rich_text": rt("ARu編集デスク｜今日の情報")}})
    blocks.append({"callout": {
        "rich_text": rt(
            "Reiが毎日確認する統合編集画面です。今回実装済みなのは🎎日本文化体験と🥗食の安心・お店情報のみ。"
            "他の6項目は準備中（クロスDB集計ロジックが未設計のため、勝手な自動判定はしていません）。"
        ),
        "icon": {"type": "emoji", "emoji": "📋"}, "color": "gray_background",
    }})

    for h in PLACEHOLDER_HEADINGS:
        blocks.append({"heading_3": {"rich_text": rt(h)}})
        blocks.append({"paragraph": {"rich_text": rt("準備中（今回のスコープ外）")}})

    blocks.extend(build_culture_section(ei_pages))

    blocks.extend(build_food_section(ei_pages))

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


if __name__ == "__main__":
    main()
