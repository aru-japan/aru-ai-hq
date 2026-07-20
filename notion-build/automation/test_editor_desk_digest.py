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


def _page(page_id, title, status=None, genre=None, dietary=None, related_source_ids=None,
          intelligence_type=None, related_research_ids=None):
    props = {
        "Title": {"type": "title", "title": [{"plain_text": title, "text": {"content": title}}]},
        "Experience Genre": {"type": "multi_select", "multi_select": [{"name": g} for g in (genre or [])]},
        "Dietary Accommodation Type": {"type": "multi_select", "multi_select": [{"name": t} for t in (dietary or [])]},
        "Related Source Library": {"type": "relation", "relation": [{"id": rid} for rid in (related_source_ids or [])]},
        "Related Research": {"type": "relation", "relation": [{"id": rid} for rid in (related_research_ids or [])]},
        "Last AI Update": {"type": "date", "date": None},
        "Source URL": {"type": "url", "url": "https://example.com/x"},
        "Intelligence Type": {"type": "select", "select": {"name": intelligence_type} if intelligence_type else None},
    }
    if status is not None:
        props["Status"] = {"type": "select", "select": {"name": status}}
    else:
        props["Status"] = {"type": "select", "select": None}
    return {"id": page_id, "created_time": "2026-07-20T01:00:00.000Z", "properties": props}


def _ec_page(page_id, title, status=None, etype=None, related_ei_ids=None, related_source_ids=None):
    props = {
        "Event Name": {"type": "title", "title": [{"plain_text": title, "text": {"content": title}}]},
        "Type": {"type": "select", "select": {"name": etype} if etype else None},
        "Related Experience Intelligence": {"type": "relation", "relation": [{"id": rid} for rid in (related_ei_ids or [])]},
        "Related Source Library": {"type": "relation", "relation": [{"id": rid} for rid in (related_source_ids or [])]},
        "Last AI Update": {"type": "date", "date": None},
        "Source URL": {"type": "url", "url": "https://example.com/ec"},
        "Event Date": {"type": "date", "date": None},
    }
    if status is not None:
        props["Status"] = {"type": "select", "select": {"name": status}}
    else:
        props["Status"] = {"type": "select", "select": None}
    return {"id": page_id, "created_time": "2026-07-20T01:00:00.000Z", "properties": props}


def _story_page(page_id, title, qa_question="", short_answer="", story_status=None,
                 source_status=None, premium=False, next_review=None):
    props = {
        "Title": {"type": "title", "title": [{"plain_text": title, "text": {"content": title}}]},
        "QA Question": {"type": "rich_text", "rich_text": [{"plain_text": qa_question}] if qa_question else []},
        "Short Answer": {"type": "rich_text", "rich_text": [{"plain_text": short_answer}] if short_answer else []},
        "Story Status": {"type": "select", "select": {"name": story_status} if story_status else None},
        "Source Status": {"type": "select", "select": {"name": source_status} if source_status else None},
        "Premium Candidate": {"type": "checkbox", "checkbox": premium},
        "Generated Article": {"type": "relation", "relation": []},
        "Next Review": {"type": "date", "date": {"start": next_review} if next_review else None},
    }
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


def test_is_culture_ei_catches_intelligence_type_culture_without_genre():
    """Reproduces the 2026-07-20 cross-DB audit finding: 体験農園みとか／
    中込農園／あんざい果樹園 were tagged Intelligence Type=Culture but never
    got an Experience Genre value, so the old Genre-only filter missed them."""
    p = _page("mitoka", "体験農園みとか", status="New", intelligence_type="Culture")
    assert d.multi_select_names(p, "Experience Genre") == []
    assert d.is_culture_ei(p) is True
    print("PASSED: Intelligence Type=Culture with empty Experience Genre is still recognized as culture")


def test_unclassified_excludes_intelligence_type_culture_records():
    """The record from the previous test must not also appear in 未分類・
    詳細未確認 -- it now belongs to 🎎, and must not be shown in two sections."""
    p = _page("mitoka", "体験農園みとか", status="New", intelligence_type="Culture")
    unclassified = [
        q for q in [p]
        if d.status_name(q) in ("New", "Reviewing")
        and not d.multi_select_names(q, "Experience Genre")
        and not d.multi_select_names(q, "Dietary Accommodation Type")
        and not d.is_culture_ei(q)
    ]
    assert unclassified == [], "an Intelligence Type=Culture record must not double-list in 未分類・詳細未確認"
    print("PASSED: Intelligence Type=Culture record is excluded from 未分類・詳細未確認")


def test_period_ec_requires_relation_to_culture_ei_not_type_value():
    """A real-world shape: 中込農園 黒系ぶどう狩り has Type=季節イベント (not
    文化イベント) but IS related to a culture-tagged Experience Intelligence
    record -- it must land in period_ec via the relation, regardless of Type."""
    ei = _page("nakagomi", "中込農園", status="New", intelligence_type="Culture")
    ec_linked = _ec_page("nakagomi_grape", "中込農園 黒系ぶどう狩り", status="Planning",
                          etype="季節イベント", related_ei_ids=["nakagomi"])
    culture_ei_ids = {ei["id"]}
    period_ec = [p for p in [ec_linked] if any(
        rid in culture_ei_ids for rid in d.related_experience_intelligence_ids(p))]
    assert period_ec == [ec_linked]
    print("PASSED: Event Calendar record with Type≠文化イベント but related to a culture EI still counts as 期間限定")


def test_low_confidence_excludes_records_linked_to_culture_ei():
    """A Type=文化イベント record that IS related to a culture EI must not
    also be counted as a low-confidence (unlinked) candidate."""
    ei = _page("anan", "庵an東京", status="New", intelligence_type="Culture")
    ec_linked = _ec_page("anan_event", "庵an東京 特別企画", status="Planning",
                          etype="文化イベント", related_ei_ids=["anan"])
    ec_unlinked = _ec_page("seminar", "モントリオールの日", status="Completed",
                            etype="文化イベント", related_ei_ids=[])
    culture_ei_ids = {ei["id"]}
    ec_pages = [ec_linked, ec_unlinked]
    period_ec_ids = {p["id"] for p in ec_pages
                     if any(rid in culture_ei_ids for rid in d.related_experience_intelligence_ids(p))}
    low_confidence = [p for p in ec_pages
                      if d.select_name(p, "Type") == "文化イベント" and p["id"] not in period_ec_ids]
    assert [p["id"] for p in low_confidence] == ["seminar"]
    print("PASSED: Type=文化イベント record linked to a culture EI is excluded from low-confidence candidates")


def test_low_confidence_splits_pending_vs_ended():
    completed = _ec_page("done", "写真展「歴史や文化から学ぶ平和」", status="Completed", etype="文化イベント")
    planning = _ec_page("open", "Have a Chat!（アメリカ）", status="Planning", etype="文化イベント")
    low_confidence = [completed, planning]
    ended = [p for p in low_confidence if d.status_name(p) in ("Completed", "Cancelled")]
    pending = [p for p in low_confidence if p["id"] not in {q["id"] for q in ended}]
    assert [p["id"] for p in ended] == ["done"]
    assert [p["id"] for p in pending] == ["open"]
    print("PASSED: 低確度候補 correctly splits into 終了・過去 vs 内容確認待ち by Status")


def test_official_source_allowlist_is_explicit_not_inferred():
    """classify_culture_source must return 公式情報 only for the explicit
    CONFIRMED_OFFICIAL_SOURCE_PAGE_IDS allowlist, and must fall through to
    classify_source_type (never guessing 公式情報) for anything else -- even
    a page whose linked Source Library entry looks superficially official."""
    fake = _FakeNotion({"src1": ("観光協会の一般ページ", "https://example-tourism-board.jp/")})
    d.notion_request = fake

    allowlisted = _page("3a2157f0-f15d-8135-be43-f2311684b1c3", "庵an東京", status="New",
                         related_source_ids=["src1"])
    assert d.classify_culture_source("tok", allowlisted) == "公式情報"

    not_allowlisted = _page("some-other-id", "別の施設", status="New", related_source_ids=["src1"])
    assert d.classify_culture_source("tok", not_allowlisted) == "区分未確認", (
        "a page not in the explicit allowlist must never be auto-classified as 公式情報, "
        "even if its related source looks official"
    )
    print("PASSED: 公式情報 is only ever returned for the explicit allowlist, never inferred")


def test_is_test_record_excludes_event_calendar_fixture_too():
    """The 2026-07-20 audit found a 3rd test fixture in Event Calendar
    ('【テスト】京都 東福寺 紅葉ライトアップ'), related to the known test EI
    record. is_test_record must catch it via its own 'Event Name' title."""
    ec_fixture = _ec_page("ec_test", "【テスト】京都 東福寺 紅葉ライトアップ", status="Confirmed")
    assert d.is_test_record(ec_fixture) is True
    print("PASSED: is_test_record excludes an Event Calendar fixture via its own title property")


def test_culture_buckets_partition_without_overlap():
    """Full-shape regression: culture_ei, period_ec, and low_confidence
    (pending + ended) must never share a page id."""
    ei_culture = _page("ei1", "阿波友禅工場", status="New", intelligence_type="Culture")
    ei_other = _page("ei2", "ハビービ", status="New", dietary=["ヴィーガン"])
    ec_period = _ec_page("ec1", "阿波友禅工場 特別企画", status="Planning",
                          etype="季節イベント", related_ei_ids=["ei1"])
    ec_candidate_open = _ec_page("ec2", "やさしい日本語キャラバン", status="Planning", etype="文化イベント")
    ec_candidate_ended = _ec_page("ec3", "写真展", status="Completed", etype="文化イベント")

    ei_pages = [ei_culture, ei_other]
    ec_pages = [ec_period, ec_candidate_open, ec_candidate_ended]

    culture_ei = [p for p in ei_pages if d.is_culture_ei(p)]
    culture_ei_ids = {p["id"] for p in culture_ei}
    period_ec = [p for p in ec_pages if any(
        rid in culture_ei_ids for rid in d.related_experience_intelligence_ids(p))]
    period_ec_ids = {p["id"] for p in period_ec}
    low_confidence = [p for p in ec_pages
                      if d.select_name(p, "Type") == "文化イベント" and p["id"] not in period_ec_ids]

    assert [p["id"] for p in culture_ei] == ["ei1"]
    assert [p["id"] for p in period_ec] == ["ec1"]
    assert sorted(p["id"] for p in low_confidence) == ["ec2", "ec3"]
    culture_ids = culture_ei_ids | period_ec_ids | {p["id"] for p in low_confidence}
    assert len(culture_ids) == len(culture_ei) + len(period_ec) + len(low_confidence), "must not overlap"
    print("PASSED: 通年 / 期間限定 / 低確度候補 buckets partition cleanly with no overlap")


def test_broadened_test_prefix_catches_story_bank_naming_style():
    """2026-07-20: Story Bank's own test fixtures use a different naming style
    ("【テスト・Dashboard View動作確認】...", "【テスト・Story Bank検証用】...")
    than the "【テスト】" fixtures found earlier in Experience Intelligence/
    Event Calendar. The broadened "【テスト" prefix (no closing bracket) must
    catch both styles via a single rule."""
    fixture_a = _story_page("t1", "【テスト・Dashboard View動作確認】この行が見えれば①は成功")
    fixture_b = _story_page("t2", "【テスト・Story Bank検証用】隅田川花火大会")
    fixture_c = _page("t3", "【テスト】紅葉シーズン到来、京都の紅葉記事の好機", status="New")
    assert d.is_test_record(fixture_a) is True
    assert d.is_test_record(fixture_b) is True
    assert d.is_test_record(fixture_c) is True
    print("PASSED: broadened 【テスト prefix catches both 【テスト】 and 【テスト・...】 naming styles")


def test_qa_section_excludes_records_with_empty_qa_question():
    """Story Bank's 22 existing 花火大会 (fireworks) records have no QA
    Question filled in at all -- they must not be treated as QA candidates,
    per Rei's explicit instruction that they are not foreign-resident QA
    content and must stay out of the QA window's extraction target."""
    fireworks = _story_page("fw1", "隅田川花火大会", qa_question="")
    real_qa = _story_page("qa1", "住民登録はどこで行いますか", qa_question="日本に引っ越したら、住民登録はどこで行いますか？")
    story_pages = [fireworks, real_qa]
    qa = [p for p in story_pages if d._rich_text_value(p, "QA Question").strip()]
    assert [p["id"] for p in qa] == ["qa1"], "empty-QA-Question fireworks record must be excluded from QA candidates"
    print("PASSED: QA section extraction target excludes records with empty QA Question (花火大会22件)")


def test_qa_section_buckets_reflect_story_status_and_source_status():
    answer_pending = _story_page("q1", "Q1", qa_question="質問1", short_answer="", story_status="New")
    ready = _story_page("q2", "Q2", qa_question="質問2", short_answer="回答あり",
                         story_status="Approved", source_status="Verified")
    delivered = _story_page("q3", "Q3", qa_question="質問3", short_answer="回答あり",
                             story_status="Published", source_status="Verified")
    needs_recheck = _story_page("q4", "Q4", qa_question="質問4", short_answer="回答あり",
                                 story_status="New", source_status="Needs Recheck")
    premium = _story_page("q5", "Q5", qa_question="質問5", short_answer="回答あり",
                           story_status="New", premium=True)
    qa = [answer_pending, ready, delivered, needs_recheck, premium]

    answer_pending_ids = [p["id"] for p in qa if not d._rich_text_value(p, "Short Answer").strip()]
    ready_ids = [p["id"] for p in qa if d._story_status(p) == "Approved"]
    delivered_ids = [p["id"] for p in qa if d._story_status(p) == "Published"]
    needs_update_ids = [p["id"] for p in qa if select_status_needs_recheck(p)]
    premium_ids = [p["id"] for p in qa if d._checkbox_value(p, "Premium Candidate")]

    assert answer_pending_ids == ["q1"]
    assert ready_ids == ["q2"]
    assert delivered_ids == ["q3"]
    assert needs_update_ids == ["q4"]
    assert premium_ids == ["q5"]
    print("PASSED: QA buckets (回答作成待ち／掲載準備中／提供済み／更新が必要／Premium候補) reflect Story Status/Source Status correctly")


def select_status_needs_recheck(page):
    return d.select_name(page, "Source Status") == "Needs Recheck" or d._next_review_overdue(page)


def test_is_person_ei_and_unclassified_exclusion():
    """Reproduces the intended 2026-07-20 People-window design: Intelligence
    Type=User records must be recognized by is_person_ei, and must not
    double-list in 未分類・詳細未確認 even though Experience Genre and
    Dietary Accommodation Type are both empty for a person/shop record."""
    person = _page("person1", "武道家 山田太郎（仮）", status="New", intelligence_type="User")
    assert d.is_person_ei(person) is True
    unclassified = [
        q for q in [person]
        if d.status_name(q) in ("New", "Reviewing")
        and not d.multi_select_names(q, "Experience Genre")
        and not d.multi_select_names(q, "Dietary Accommodation Type")
        and not d.is_culture_ei(q)
        and not d.is_person_ei(q)
    ]
    assert unclassified == [], "an Intelligence Type=User record must not double-list in 未分類・詳細未確認"
    print("PASSED: Intelligence Type=User is recognized as a person/shop record and excluded from 未分類・詳細未確認")


def test_people_section_does_not_overlap_culture_or_food():
    """Full-shape regression: culture, food, and people buckets (all three
    drawn from the same Experience Intelligence table) must never share a
    page id, even though all three now rely on Intelligence Type / Experience
    Genre / Dietary Accommodation Type read from the same records."""
    culture = _page("c1", "阿波友禅工場", status="New", intelligence_type="Culture")
    food = _page("f1", "ハビービ", status="New", dietary=["ヴィーガン"])
    person = _page("p1", "職人 佐藤花子（仮）", status="New", intelligence_type="User")
    ei_pages = [culture, food, person]

    culture_ids = {p["id"] for p in ei_pages if d.is_culture_ei(p)}
    food_ids = {p["id"] for p in ei_pages if d.multi_select_names(p, "Dietary Accommodation Type")}
    people_ids = {p["id"] for p in ei_pages if d.is_person_ei(p)}

    assert culture_ids == {"c1"}
    assert food_ids == {"f1"}
    assert people_ids == {"p1"}
    assert not (culture_ids & food_ids)
    assert not (culture_ids & people_ids)
    assert not (food_ids & people_ids)
    print("PASSED: 🎎文化体験 / 🥗食の安心 / 🌏人物・お店 buckets remain mutually exclusive")


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
    test_is_culture_ei_catches_intelligence_type_culture_without_genre()
    test_unclassified_excludes_intelligence_type_culture_records()
    test_period_ec_requires_relation_to_culture_ei_not_type_value()
    test_low_confidence_excludes_records_linked_to_culture_ei()
    test_low_confidence_splits_pending_vs_ended()
    test_official_source_allowlist_is_explicit_not_inferred()
    test_is_test_record_excludes_event_calendar_fixture_too()
    test_culture_buckets_partition_without_overlap()
    test_broadened_test_prefix_catches_story_bank_naming_style()
    test_qa_section_excludes_records_with_empty_qa_question()
    test_qa_section_buckets_reflect_story_status_and_source_status()
    test_is_person_ei_and_unclassified_exclusion()
    test_people_section_does_not_overlap_culture_or_food()
    print("\nALL TESTS PASSED")
