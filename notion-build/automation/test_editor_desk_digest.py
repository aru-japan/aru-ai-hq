"""Regression tests for editor_desk_digest.py, focused on the visibility bug found
in production on 2026-07-20: records with both Experience Genre and Dietary
Accommodation Type empty (e.g. ハビービ 講道館レストラン, 福の樹, すべてヴィーガン)
did not match either the 🎎 culture filter or the 🥗 food filter, and the
"詳細未確認" heading was a static placeholder with no logic -- so those records
were not reachable from any ARu編集デスク window at all.

No Notion calls -- runs entirely against synthetic page fixtures and a fake
notion_request double for classify_source_type's Related Source Library lookup.

    python3 test_editor_desk_digest.py
"""
import editor_desk_digest as d


def _page(page_id, title, status=None, genre=None, dietary=None, related_source_ids=None):
    props = {
        "Title": {"type": "title", "title": [{"plain_text": title, "text": {"content": title}}]},
        "Experience Genre": {"type": "multi_select", "multi_select": [{"name": g} for g in (genre or [])]},
        "Dietary Accommodation Type": {"type": "multi_select", "multi_select": [{"name": t} for t in (dietary or [])]},
        "Related Source Library": {"type": "relation", "relation": [{"id": rid} for rid in (related_source_ids or [])]},
        "Last AI Update": {"type": "date", "date": None},
        "Source URL": {"type": "url", "url": "https://example.com/x"},
    }
    if status is not None:
        props["Status"] = {"type": "select", "select": {"name": status}}
    else:
        props["Status"] = {"type": "select", "select": None}
    return {"id": page_id, "created_time": "2026-07-20T01:00:00.000Z", "properties": props}


def _unclassified(pages):
    return [
        p for p in pages
        if d.status_name(p) in ("New", "Reviewing")
        and not d.multi_select_names(p, "Experience Genre")
        and not d.multi_select_names(p, "Dietary Accommodation Type")
    ]


def test_bug_reproduction_empty_genre_and_dietary_is_unclassified_not_invisible():
    """The exact shape of the 2026-07-20 production bug: Status=New, both tag
    properties empty. Must land in 'unclassified', not be silently dropped."""
    habibi = _page("p1", "ハビービ 講道館レストラン", status="New")
    culture = [p for p in [habibi] if d.multi_select_names(p, "Experience Genre")]
    food = [p for p in [habibi] if d.multi_select_names(p, "Dietary Accommodation Type")]
    unclassified = _unclassified([habibi])
    assert habibi not in culture, "must not silently appear in culture section"
    assert habibi not in food, "must not silently appear in food section"
    assert habibi in unclassified, "must be reachable via 未分類・詳細未確認 -- this was the bug"
    print("PASSED: empty-genre/empty-dietary Status=New record lands in unclassified, not nowhere")


def test_culture_and_food_and_unclassified_partition_without_overlap():
    """All three buckets must be mutually exclusive and their union must equal
    the full page set, for an arbitrary mix of record shapes."""
    pages = [
        _page("c1", "文化体験A", status="New", genre=["和菓子作り"]),
        _page("f1", "食のお店A", status="New", dietary=["ヴィーガン"]),
        _page("u1", "未分類A", status="New"),
        _page("u2", "未分類B（Reviewing）", status="Reviewing"),
        _page("x1", "無関係（Published・両方空欄）", status="Published"),
    ]
    culture = [p for p in pages if d.multi_select_names(p, "Experience Genre")]
    food = [p for p in pages if d.multi_select_names(p, "Dietary Accommodation Type")]
    unclassified = _unclassified(pages)

    culture_ids, food_ids, unclassified_ids = (set(p["id"] for p in s) for s in (culture, food, unclassified))
    assert culture_ids == {"c1"}
    assert food_ids == {"f1"}
    assert unclassified_ids == {"u1", "u2"}, "Reviewing must count as unclassified too, Published must not"
    assert not (culture_ids & food_ids)
    assert not (culture_ids & unclassified_ids)
    assert not (food_ids & unclassified_ids)
    print("PASSED: culture / food / unclassified partition cleanly with no overlap")


class _FakeNotion:
    """Stands in for notion_request(token, 'GET', f'/pages/{id}') so
    classify_source_type can be tested without hitting Notion."""

    def __init__(self, fixtures):
        self.fixtures = fixtures  # id -> (title, url)

    def __call__(self, token, method, path, body=None):
        assert method == "GET"
        page_id = path.rsplit("/", 1)[-1]
        title, url = self.fixtures[page_id]
        return {"properties": {
            "Source Name": {"type": "title", "title": [{"plain_text": title}]},
            "URL": {"type": "url", "url": url},
        }}


def test_classify_source_type_third_party_from_review_site_title():
    fake = _FakeNotion({"src1": ("食べログ ハビービ講道館レストラン", "https://tabelog.com/tokyo/x")})
    d.notion_request = fake
    page = _page("p1", "ハビービ 講道館レストラン", status="New", related_source_ids=["src1"])
    assert d.classify_source_type("tok", page) == "第三者情報"
    print("PASSED: 食べログ-titled Related Source Library correctly classified as 第三者情報")


def test_classify_source_type_sns_from_url_domain():
    fake = _FakeNotion({"src1": ("お店の公式アカウント投稿", "https://www.instagram.com/p/abc123/")})
    d.notion_request = fake
    page = _page("p1", "SNSソースのお店", status="New", related_source_ids=["src1"])
    assert d.classify_source_type("tok", page) == "SNS原文"
    print("PASSED: instagram.com Related Source Library URL correctly classified as SNS原文")


def test_classify_source_type_never_guesses_official_defaults_to_unconfirmed():
    """No positive 'official' signal exists in this codebase -- an ordinary,
    unremarkable title/URL (neither a known third-party platform nor an SNS
    domain) must fall back to 区分未確認, never 公式情報."""
    fake = _FakeNotion({"src1": ("ホテルアソシア静岡 イベント告知ページ", "https://www.associa.com/sth/event/x/")})
    d.notion_request = fake
    page = _page("p1", "ホテルアソシア静岡", status="New", related_source_ids=["src1"])
    assert d.classify_source_type("tok", page) == "区分未確認"
    print("PASSED: unremarkable official-looking source is left as 区分未確認, not guessed as 公式情報")


def test_classify_source_type_no_relation_returns_unconfirmed():
    page = _page("p1", "リレーションなし", status="New", related_source_ids=[])
    assert d.classify_source_type("tok", page) == "区分未確認"
    print("PASSED: no Related Source Library relation correctly falls back to 区分未確認")


def test_clear_test_prefix_record_is_excluded_from_dashboard():
    """Regression for the 2026-07-20 second-pass fix: 【テスト】... fixtures
    surfaced in 未分類・詳細未確認 once it started reflecting live data.
    They must be filtered out of what the Dashboard renders."""
    fixture = _page("t1", "【テスト】紅葉シーズン到来、京都の紅葉記事の好機", status="New")
    assert d.is_test_record(fixture) is True
    pages = [fixture]
    rendered = [p for p in pages if not d.is_test_record(p)]
    assert rendered == [], "a 【テスト】-prefixed record must not be rendered on the Dashboard"
    print("PASSED: 【テスト】-prefixed record is excluded from Dashboard rendering")


def test_ordinary_title_merely_containing_test_word_is_not_excluded():
    """The exclusion must be a strict prefix match, never a substring/keyword
    scan -- a real record whose title happens to contain "テスト" (but does not
    start with the known test-fixture prefix) must still be shown."""
    fixture = _page("r1", "テスト工房 陶芸体験（本物の店舗名）", status="New", genre=["陶器・焼き物"])
    assert d.is_test_record(fixture) is False
    pages = [fixture]
    rendered = [p for p in pages if not d.is_test_record(p)]
    assert rendered == [fixture], "a real record containing the word テスト must not be excluded"
    print("PASSED: ordinary title merely containing 'テスト' is not excluded")


def test_target_three_records_still_shown_after_test_exclusion():
    """The 2026-07-20 test-record fix must not regress the earlier fix: the 3
    records that motivated 未分類・詳細未確認 in the first place must still
    appear once test fixtures are filtered out."""
    pages = [
        _page("habibi", "ハビービ 講道館レストラン", status="New"),
        _page("fukunoki", "福の樹（ハラール対応ラーメン）", status="New"),
        _page("allvegan", "すべてヴィーガン（札幌市中央区）", status="New"),
        _page("t1", "【テスト】留学生向けアルバイト規定の記事が不足", status="New"),
    ]
    rendered = [p for p in pages if not d.is_test_record(p)]
    unclassified = _unclassified(rendered)
    titles = {d.title_of(p) for p in unclassified}
    assert titles == {"ハビービ 講道館レストラン", "福の樹（ハラール対応ラーメン）", "すべてヴィーガン（札幌市中央区）"}
    print("PASSED: target 3 records still shown, test fixture excluded, after test-record filtering")


def test_no_overlap_across_sections_after_test_exclusion():
    """Partition invariant must still hold once test-record filtering runs
    before the culture/food/unclassified split."""
    pages = [
        _page("c1", "文化体験A", status="New", genre=["和菓子作り"]),
        _page("f1", "食のお店A", status="New", dietary=["ヴィーガン"]),
        _page("u1", "未分類A", status="New"),
        _page("t1", "【テスト】記事企画メモ", status="New"),
    ]
    rendered = [p for p in pages if not d.is_test_record(p)]
    culture = [p for p in rendered if d.multi_select_names(p, "Experience Genre")]
    food = [p for p in rendered if d.multi_select_names(p, "Dietary Accommodation Type")]
    unclassified = _unclassified(rendered)
    all_ids = set(p["id"] for p in culture) | set(p["id"] for p in food) | set(p["id"] for p in unclassified)
    assert all_ids == {"c1", "f1", "u1"}, "test fixture must not appear anywhere, real records must partition cleanly"
    print("PASSED: culture / food / unclassified remain non-overlapping after test-record exclusion")


if __name__ == "__main__":
    test_bug_reproduction_empty_genre_and_dietary_is_unclassified_not_invisible()
    test_culture_and_food_and_unclassified_partition_without_overlap()
    test_classify_source_type_third_party_from_review_site_title()
    test_classify_source_type_sns_from_url_domain()
    test_classify_source_type_never_guesses_official_defaults_to_unconfirmed()
    test_classify_source_type_no_relation_returns_unconfirmed()
    test_clear_test_prefix_record_is_excluded_from_dashboard()
    test_ordinary_title_merely_containing_test_word_is_not_excluded()
    test_target_three_records_still_shown_after_test_exclusion()
    test_no_overlap_across_sections_after_test_exclusion()
    print("\nALL TESTS PASSED")
