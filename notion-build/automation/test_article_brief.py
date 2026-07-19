"""Regression tests for article_brief.py, focused on the traceability bug found in
production on 2026-07-19: an Evidence block whose `Source:` field bundles two
Source titles into one string (joined by "／") looked "OK" under a permissive
`source_exists_fn=lambda t: True` test double, but is untraceable against the real
Source Library, where no single record's title equals that bundled string.

No Notion calls -- runs entirely against a fixed real-title fixture (the 6 Source
Library records actually created for the 外国人の社会保険 Research record on
2026-07-19), so it exercises exact-match lookup behavior instead of masking it.

    python3 test_article_brief.py
"""
import article_brief as ab

# The 6 real Source Library titles created in production for this Research record.
REAL_SOURCE_TITLES = {
    "日本年金機構 外国人従業員を雇用したときの手続き",
    "日本年金機構 脱退一時金制度について",
    "協会けんぽ東京支部 保険料率案内",
    "協会けんぽ 介護保険料率",
    "協会けんぽ 都道府県毎の保険料率",
    "日本年金機構 保険料の計算方法について",
}


def real_titles_exists_fn(title):
    """Simulates the real Source Library exact-match query
    (query_database(..., filter_obj={"property": "Source Name", "title": {"equals": title}}))
    without hitting Notion -- exact string equality against the fixture set."""
    return title in REAL_SOURCE_TITLES


RN = """## Reader Need
- Who: A
- Context: B
- Pain: C
- Outcome: D
"""


def test_bundled_source_is_ng():
    """A single Evidence whose Source field bundles two titles with '／' must be
    flagged NG -- this is the exact shape of the 2026-07-19 production bug."""
    text = RN + """
## Claims

### Claim 1
- Statement: dummy claim
- Status: Supported

### Evidence 1
- Supports: Claim 1
- Evidence: dummy evidence text
- Source: 協会けんぽ東京支部 保険料率案内／協会けんぽ 介護保険料率
- Location: 見出しA／見出しB
- Evidence Level: Official
"""
    parsed = ab.parse_editor_notes(text)
    result = ab.check_completion(parsed, source_exists_fn=real_titles_exists_fn, freshness_confirmed=True)
    status = result["mechanical_check"]["3_evidence_traceable_to_source"]["status"]
    assert status == "NG", f"expected NG for a bundled '／'-joined Source title, got {status}"
    print("PASSED: bundled Source ('A／B') correctly detected as NG against real titles")


def test_split_into_two_single_source_evidence_is_ok():
    """The 2026-07-19 fix: splitting the same two facts into two Evidence blocks,
    each pointing at exactly one real Source Library title, must pass."""
    text = RN + """
## Claims

### Claim 1
- Statement: dummy claim
- Status: Supported

### Evidence 1
- Supports: Claim 1
- Evidence: 協会けんぽ東京支部の2026年度健康保険料率は9.85%
- Source: 協会けんぽ東京支部 保険料率案内
- Location: 2026年度の健康保険料率等について
- Evidence Level: Official

### Evidence 2
- Supports: Claim 1
- Evidence: 介護保険第2号被保険者には全国一律の介護保険料率1.62%が加わる
- Source: 協会けんぽ 介護保険料率
- Location: 一般被保険者／介護保険第2号被保険者の説明
- Evidence Level: Official
"""
    parsed = ab.parse_editor_notes(text)
    result = ab.check_completion(parsed, source_exists_fn=real_titles_exists_fn, freshness_confirmed=True)
    status = result["mechanical_check"]["3_evidence_traceable_to_source"]["status"]
    assert status == "OK", f"expected OK once split into two single-Source Evidence blocks, got {status}"
    print("PASSED: two Evidence blocks, each single-Source, correctly detected as OK")


def test_permissive_mock_would_have_masked_the_bug():
    """Documents *why* this was missed before: source_exists_fn=lambda t: True
    (used in earlier ad hoc testing) accepts any string, including a bundled one,
    so it never exercises the exact-match failure mode real Notion data hits."""
    text = RN + """
## Claims

### Claim 1
- Statement: dummy claim
- Status: Supported

### Evidence 1
- Supports: Claim 1
- Evidence: dummy evidence text
- Source: 協会けんぽ東京支部 保険料率案内／協会けんぽ 介護保険料率
- Location: 見出しA／見出しB
- Evidence Level: Official
"""
    parsed = ab.parse_editor_notes(text)
    permissive_result = ab.check_completion(parsed, source_exists_fn=lambda t: True, freshness_confirmed=True)
    real_result = ab.check_completion(parsed, source_exists_fn=real_titles_exists_fn, freshness_confirmed=True)
    assert permissive_result["mechanical_check"]["3_evidence_traceable_to_source"]["status"] == "OK"
    assert real_result["mechanical_check"]["3_evidence_traceable_to_source"]["status"] == "NG"
    print("PASSED: confirmed the permissive lambda masks exactly this bug -- real-title fixtures are required")


# --- 2026-07-19 second incident: Grounding Check regression tests ------------
# A generated Premium article added a fabricated phone number, an unverified/
# outdated pension-eligibility figure, an invented employee-count threshold, and
# other specifics nowhere in the approved Article Brief. Each of the 10 phrases
# below reproduces one concrete failure shape; every one must be flagged when
# the Brief itself doesn't contain the fact -- and, per Rei's explicit
# instruction, a body can't dodge detection just by changing the digits.

FULL_BRIEF_TEXT = RN + """
## Claims

### Claim 1
- Statement: 健康保険・厚生年金保険の適用事業所に常時使用され、加入要件を満たす外国人は、国籍に関わらず被保険者となる。
- Status: Supported

### Evidence 1
- Supports: Claim 1
- Evidence: 健康保険・厚生年金保険の適用事業所に常時雇用される外国人は、国籍や性別、賃金の額等に関係なく被保険者となる
- Source: 日本年金機構 外国人従業員を雇用したときの手続き
- Location: 加入要件見出し
- Evidence Level: Official

### Claim 2
- Statement: 日本国籍を持たない方が公的年金の加入資格を喪失して日本を出国した場合、所定の要件をすべて満たせば、原則として日本に住所を有しなくなった日から2年以内に脱退一時金を請求できる。
- Status: Supported

### Evidence 2
- Supports: Claim 2
- Evidence: 日本国籍を有しない、公的年金制度の被保険者でない、加入期間が6月以上、老齢年金の受給資格期間を満たしていない、日本国内に住所を有していない等の支給要件がある。
- Source: 日本年金機構 脱退一時金制度について
- Location: 支給対象者の条件見出し
- Evidence Level: Official

### Claim 3
- Statement: 2021年4月以降に、国民年金の保険料納付済期間または厚生年金保険の被保険者期間がある場合、脱退一時金の支給額計算に用いる月数の上限は60月（5年）となる。それより前のみの場合は36月（3年）が上限となる。
- Status: Supported

### Evidence 3
- Supports: Claim 3
- Evidence: 2021年4月以降に保険料納付がある場合、計算に用いる月数の上限が36月から60月へ引き上げ
- Source: 日本年金機構 脱退一時金制度について
- Location: 支給額計算の上限月数見出し
- Evidence Level: Official

### Claim 4
- Statement: 協会けんぽ東京支部に加入する方の場合、2026年度の健康保険料率は9.85％。介護保険第2号被保険者に該当する方には、全国一律の介護保険料率1.62％が加わる
- Status: Supported

### Evidence 4
- Supports: Claim 4
- Evidence: 協会けんぽ東京支部の2026年度健康保険料率は9.85％で、2026年3月分（4月納付分）から適用される
- Source: 協会けんぽ東京支部 保険料率案内
- Location: 2026年度の健康保険料率等について
- Evidence Level: Official

### Evidence 5
- Supports: Claim 4
- Evidence: 介護保険第2号被保険者に該当する40歳から64歳までの方は、医療にかかる保険料率に全国一律の介護保険料率1.62％が加わる
- Source: 協会けんぽ 介護保険料率
- Location: 一般被保険者／介護保険第2号被保険者の説明
- Evidence Level: Official
"""

_REGRESSION_PHRASES = [
    ("従業員5人以上", "健康保険・厚生年金保険の適用事業所（従業員5人以上の企業）に常時雇用される外国人は被保険者となります。"),
    ("1〜2週間以内", "保険証は通常入社から1〜2週間以内に本人に渡されます。"),
    ("年金手帳", "転職の際に年金手帳を紛失しないことが重要です。"),
    ("1960年代", "日本の社会保険制度は1960年代の高度経済成長期に整備されました。"),
    ("25年以上", "老齢年金の受給資格期間（通常25年以上）を満たしていない場合に該当します。"),
    ("0570-05-1165", "日本年金機構の全国共通ダイヤル 0570-05-1165 にご相談ください。"),
    ("4月〜6月", "毎年4月〜6月の給与平均に基づいて標準報酬月額を決定し直す仕組みです。"),
    ("標準報酬月額25万円の計算例", "標準報酬月額が25万円の場合、控除額は約12,300円です。"),
    ("市町村への転出届", "帰国前に市町村へ転出届を提出することが必要です。"),
    ("どの在留資格でも対象", "技能実習、特定技能、技術人文知識国際業務など、どの在留資格で働いていても対象になります。"),
]


def test_all_2026_07_19_unsupported_phrases_are_flagged():
    parsed = ab.parse_editor_notes(FULL_BRIEF_TEXT)
    for label, snippet in _REGRESSION_PHRASES:
        gc = ab.grounding_check(snippet, parsed)
        flagged = bool(gc["unsupported"]) or bool(gc["overclaiming"])
        assert flagged, f"'{label}' should have been flagged Unsupported/overclaiming but wasn't: {gc}"
    print(f"PASSED: all {len(_REGRESSION_PHRASES)} known 2026-07-19 unsupported phrases are flagged")


def test_changing_the_digits_does_not_evade_detection():
    """Rei's explicit anti-gaming requirement: this must catch "Briefにない数値"
    as a category, not just the literal "25年" string -- changing the number
    must not let a fabricated figure slip through."""
    parsed = ab.parse_editor_notes(FULL_BRIEF_TEXT)
    for years in ("17年以上", "23年以上", "30年以上"):
        gc = ab.grounding_check(f"老齢年金の受給資格期間（通常{years}）を満たしていない場合に該当します。", parsed)
        assert gc["unsupported"], f"changing the figure to '{years}' should still be flagged, got {gc}"
    # same for a phone number with different digits
    gc = ab.grounding_check("お問い合わせは 0120-123-4567 まで。", parsed)
    assert gc["unsupported"], f"a different phone number should still be flagged, got {gc}"
    print("PASSED: varying the digits/phone number does not evade detection")


def test_grounded_facts_from_the_real_brief_are_not_flagged():
    """Positive control: legitimate facts actually in the approved Brief must
    not be falsely flagged -- otherwise the check would be too strict to use."""
    parsed = ab.parse_editor_notes(FULL_BRIEF_TEXT)
    grounded_text = (
        "協会けんぽ東京支部の2026年度健康保険料率は9.85%で、介護保険第2号被保険者には1.62%が加わります。"
        "脱退一時金の計算上限は2021年4月以降60月です。加入期間が6月以上必要です。請求は2年以内に行います。"
    )
    gc = ab.grounding_check(grounded_text, parsed)
    assert not gc["unsupported"], f"grounded facts should not be flagged, got {gc['unsupported']}"
    assert not gc["overclaiming"], f"grounded facts should not be flagged, got {gc['overclaiming']}"
    print("PASSED: real grounded facts produce zero false positives")


def test_age_range_phrasing_equivalence():
    """'40歳から64歳まで' (Evidence's own wording) and '40～64歳' (a body's likely
    phrasing of the same fact) must be treated as equivalent -- caught as a real
    false positive during the 2026-07-19 regeneration."""
    parsed = ab.parse_editor_notes(FULL_BRIEF_TEXT)
    gc = ab.grounding_check("介護保険第2号被保険者に該当する40～64歳の方には介護保険料が加わります。", parsed)
    assert not gc["unsupported"], f"age-range phrasing should not false-positive, got {gc}"
    print("PASSED: '40〜64歳' matches Evidence's '40歳から64歳まで' wording")


def test_age_range_spelled_out_in_words():
    """The body may echo Evidence's own '...から...まで' wording verbatim rather
    than switching to a tilde -- that must also be recognized as grounded,
    not just the tilde form covered by test_age_range_phrasing_equivalence."""
    parsed = ab.parse_editor_notes(FULL_BRIEF_TEXT)
    gc = ab.grounding_check("40歳から64歳までの方には介護保険料が加わります。", parsed)
    assert not gc["unsupported"], f"'40歳から64歳まで' (Evidence's own wording) should not be flagged, got {gc}"
    print("PASSED: '40歳から64歳まで' spelled out in words is recognized as grounded")


def test_today_date_exemption():
    """Stating the required info-as-of date correctly must not be flagged just
    because its digits don't appear in Evidence (which only has the *Sources'*
    own dates) -- but only when the caller actually supplies today's date."""
    parsed = ab.parse_editor_notes(FULL_BRIEF_TEXT)
    text = "本記事の情報は2026年7月20日時点で確認されたものです。"
    with_today = ab.grounding_check(text, parsed, today="2026-07-20")
    without_today = ab.grounding_check(text, parsed)
    assert not with_today["unsupported"], f"today's date should be exempt when supplied, got {with_today}"
    assert without_today["unsupported"], "without the today= hint it should still flag (confirms it's not silently permissive)"
    print("PASSED: today's date is exempt only when explicitly supplied")


def test_computed_sum_still_flagged_for_human_review():
    """9.85% + 1.62% = 11.47% is arithmetically sound but not literally in the
    Brief -- deliberately still flagged as a gray-area item for a human to
    confirm, rather than silently auto-accepted as 'just math'."""
    parsed = ab.parse_editor_notes(FULL_BRIEF_TEXT)
    gc = ab.grounding_check("健康保険料率9.85%に介護保険料率1.62%を加えると合計11.47%になります。", parsed)
    assert any("11.47" in u for u in gc["unsupported"]), f"computed sum should still surface for review, got {gc}"
    print("PASSED: a derived/computed figure not literally in the Brief is still surfaced")


# --- 2026-07-20 second incident: background/rationale/purpose paraphrases ----
# Each of these reproduces one of the specific removals Rei requested from the
# regenerated article -- none contain a number or a listed procedural noun, so
# only the explanation-marker/generalization detectors (not the numeric ones)
# can catch them.

_EXPLANATION_PARAPHRASES = [
    ("労働政策の原則としての一般化", "この仕組みは、雇用契約がある限りすべての労働者を社会保障制度で守るという日本の労働政策の原則に基づいています。"),
    ("同水準の保障を受ける権利", "外国人労働者も日本人と同じ水準の保障を受ける権利を持つとされています。"),
    ("在留資格の種類を問わない一般化", "在留資格の種類を問わず、加入要件を満たせば被保険者となります。"),
    ("戦後の経済成長期と労使折半の結びつけ", "労使折半という仕組みは、戦後日本の経済成長期の政策判断に由来します。"),
    ("都道府県差の理由説明", "健康保険料率が都道府県で異なるのは、各地域の医療費の水準を反映した仕組みだからです。"),
    ("介護保険制度の背景・目的", "介護保険制度は、高齢化する社会全体で介護費用を支える仕組みとして設けられました。"),
    ("脱退一時金制度が作られた理由", "脱退一時金制度は、保険料を払ったまま何も返さないのは不公正だという考え方に基づいて作られました。"),
]


def test_explanation_and_generalization_paraphrases_are_flagged():
    parsed = ab.parse_editor_notes(FULL_BRIEF_TEXT)
    for label, sentence in _EXPLANATION_PARAPHRASES:
        gc = ab.grounding_check(sentence, parsed)
        flagged = bool(gc["unsupported"]) or bool(gc["overclaiming"])
        assert flagged, f"'{label}' should have been flagged as background/rationale/generalization, got {gc}"
    print(f"PASSED: all {len(_EXPLANATION_PARAPHRASES)} background/rationale/purpose paraphrases are flagged")


def test_semantic_check_parses_a_canned_response_without_a_live_model_call():
    """Tests the parsing/aggregation logic deterministically via an injected fake
    -- semantic_grounding_check() itself needs a live model in real use, but its
    output-parsing must be independently, reliably testable."""
    parsed = ab.parse_editor_notes(FULL_BRIEF_TEXT)

    canned_response = (
        "SUPPORTED | Claim 1 | 適用事業所の外国人は国籍問わず被保険者\n"
        "UNSUPPORTED | - | すべての労働者を守るという労働政策の原則\n"
        "SKIP | - | 見出しのみ\n"
        "UNSUPPORTED | - | 戦後の経済成長期に整備された制度\n"
    )

    def fake_complete_fn(prompt, max_tokens=1800):
        assert "Claim 1" in prompt  # confirms the Brief was actually included in the prompt
        return ("fake-provider", canned_response)

    result = ab.semantic_grounding_check("(本文はダミー、fake_complete_fnが応答を差し替える)", parsed, complete_fn=fake_complete_fn)
    assert len(result["supported"]) == 1
    assert len(result["unsupported"]) == 2
    assert "SKIP" not in " ".join(result["unsupported"])
    print("PASSED: semantic_grounding_check correctly parses a canned SUPPORTED/UNSUPPORTED/SKIP response")


def test_semantic_check_skips_when_no_brief_exists():
    """Old-style Research records with no Article Brief must not trigger a
    (pointless, costly) model call at all."""
    parsed = ab.parse_editor_notes("この記事は在留資格の更新について書く予定。")
    calls = []

    def fake_complete_fn(prompt, max_tokens=1800):
        calls.append(prompt)
        return ("fake-provider", "SUPPORTED | Claim 1 | should not be called")

    result = ab.semantic_grounding_check("some body", parsed, complete_fn=fake_complete_fn)
    assert calls == [], "should not call the model when there is no Article Brief"
    assert result == {"supported": [], "unsupported": []}
    print("PASSED: semantic_grounding_check makes no model call when no Article Brief exists")


def test_old_style_research_backward_compatibility():
    """Research records that predate the Article Brief format (plain free-text
    Editor's Notes, no '## Reader Need' / '## Claims') must fall through
    gracefully everywhere -- no crash, no phantom Brief, no prompt injection --
    exactly as generate_article_pipeline.py's run_article() relies on."""
    old_notes = "この記事は在留資格の更新について書く予定。念のため入管に確認する。"

    parsed = ab.parse_editor_notes(old_notes)
    assert parsed["reader_need"] is None
    assert parsed["claims"] == []
    assert parsed["evidence"] == []
    assert parsed["brief_status_line"] == ""

    assert ab.format_for_prompt(parsed) == "", "no Article Brief text should be injected into the Writer prompt"

    result = ab.check_completion(parsed, source_exists_fn=lambda t: True, freshness_confirmed=True)
    assert result["final_brief_status"] == "材料不足"

    gc = ab.grounding_check("何か適当な本文。", parsed)
    assert gc == {"supported": [], "unsupported": [], "overclaiming": []}

    print("PASSED: old-style (pre-Article-Brief) Research falls through gracefully everywhere")


def test_truncation_detection():
    assert ab.is_body_truncated("これは記事の本文で、都道府県、年齢、") is True
    assert ab.is_body_truncated("これは記事の本文です。") is False
    assert ab.is_body_truncated("https://www.nenkin.go.jp/service/kounen/hokenryo/nofu/20121026.html") is False
    print("PASSED: truncation detection (mid-sentence cutoff vs. proper ending vs. URL ending)")


if __name__ == "__main__":
    test_bundled_source_is_ng()
    test_split_into_two_single_source_evidence_is_ok()
    test_permissive_mock_would_have_masked_the_bug()
    test_all_2026_07_19_unsupported_phrases_are_flagged()
    test_changing_the_digits_does_not_evade_detection()
    test_grounded_facts_from_the_real_brief_are_not_flagged()
    test_age_range_phrasing_equivalence()
    test_age_range_spelled_out_in_words()
    test_today_date_exemption()
    test_computed_sum_still_flagged_for_human_review()
    test_explanation_and_generalization_paraphrases_are_flagged()
    test_semantic_check_parses_a_canned_response_without_a_live_model_call()
    test_semantic_check_skips_when_no_brief_exists()
    test_old_style_research_backward_compatibility()
    test_truncation_detection()
    print("\nALL TESTS PASSED")
