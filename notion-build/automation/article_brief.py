"""Article Brief content model (Reader Need / Source / Evidence / Claim / Brief
completion), per docs/Article-Brief-Specification-v1.0.md.

Pure parsing/formatting logic only -- no Notion API calls in this module, so it can
be exercised with local text fixtures. All fields live inside Research's existing
`Editor's Notes` rich_text; no new database, property, or relation is introduced.

IMPORTANT (2026-07-19 correction, per Rei's review): completion is reported in two
explicitly separate stages, and this module never writes anything back to Notion:

  - Mechanical Check: only what can be verified without human judgement (Sec 2-5
    below). Semantic match (cond 1) and the Sec.4.4 Reported conditions / Sec.13
    freshness confirmation (cond 4) can NEVER be resolved to "OK" by this code --
    at best they are surfaced as REVIEW, prompting a human to look at them.
  - Final Brief Status: "執筆可能" only if the Mechanical Check is not blocked
    (cond 2/3/5 = OK, cond 4 != NG) AND the editor has themselves written
    "Brief Status: 執筆可能" at the end of Editor's Notes. Nothing in this file
    (or in article_brief_init.py / generate_article_pipeline.py) ever writes that
    line -- it is editor-authored text, read-only from this module's perspective.
"""
import re

EMPTY_TEMPLATE = """## Reader Need
- Who:\x20
- Context:\x20
- Pain:\x20
- Outcome:\x20

## Claims

### Claim 1
- Statement:\x20
- Status: Proposed

### Evidence 1
- Supports: Claim 1
- Evidence:\x20
- Source:\x20
- Location:\x20
- Evidence Level:\x20
"""

UNADOPTED_CLAIM_STATUSES = {"Rejected", "Superseded"}
UNRESOLVED_CLAIM_STATUSES = {"Conflicted", "Needs Review"}
WEAK_EVIDENCE_LEVELS = {"Rumor", "AI Suggested", ""}
_STATUS_RANK = {"OK": 0, "REVIEW": 1, "NG": 2}

# 2026-07-19 incident (two rounds): a Premium article generated from an approved
# Article Brief added a fabricated phone number, an outdated/unverified pension-
# eligibility figure, an invented employee-count threshold, and -- in the second
# round -- unverified background/rationale/purpose prose (why the system exists,
# postwar policy history, why rates differ by prefecture) that contained no
# numbers or banned terms, so it survived the first version of the deterministic
# check. STRICT_GENERATION_RULES and grounding_check()/semantic_grounding_check()
# below are the fix: a hard instruction at generation time (Public Information
# Strict Mode, per Rei's 2026-07-20 correction), and two independent post-
# generation audits -- deterministic (patterns) and semantic (sentence-level,
# AI-judged) -- either of which can force Review Result to Fail regardless of
# score. The three principles below are the complete, unified rule set; do not
# add a fourth without Rei's explicit instruction.
STRICT_GENERATION_RULES = """
【Public Information Strict Mode -- 公共情報に適用する3原則（必ず守ること）】
1. 一次情報および承認済みEvidenceにないことは書かないこと。
2. 確認できない情報は、表現を弱めて残すのではなく、記事本文から完全に除外すること
   （「〜とされています」「一般的に」「通常」等への言い換えで残すことも禁止）。
3. Freshnessが確認されていない情報を、最新情報として使用しないこと。

具体的には次を厳守すること：
- Article BriefのClaimとEvidenceに含まれる事実だけを使用すること。
- AIの一般知識で説明を補わないこと。数字・年・期限・電話番号・手続き・必要書類・歴史・対象条件を推測しないこと。
- 見出しを埋めるため、または文字数を満たすために、情報を創作・補完しないこと。
- 各Claimの背景・理由・目的・沿革（なぜその制度があるか、なぜその数値になるか等）は、
  それ自体を裏付けるEvidenceがない限り一切書かないこと。Evidenceに根拠がないセクション・
  段落は、無理に埋めず省略すること。文章が短くなっても構わない。
- 承認済みの複数の数値を独自に合算・計算した数値（例：2つの料率の合計）を新たに提示しないこと。
- 「完全ガイド」「必ず」「すべて」など、根拠以上に断定する表現を使わないこと。
"""


def _field(block_text, field_name):
    # NOTE: the whitespace after ":" must not use \s* -- \s matches newlines too,
    # so an empty/blank value would otherwise swallow the following line(s) and
    # bleed into the next field (caught in testing: an empty "Source:" line was
    # capturing the entire next "Location:" line as its own value).
    m = re.search(rf"^-\s*{re.escape(field_name)}:[ \t]*(.*)$", block_text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def parse_editor_notes(text):
    """Parse the Article-Brief-Specification-v1.0.md Sec.2/Sec.4 notation out of an
    Editor's Notes rich_text string. Missing sections simply come back empty -- this
    must not raise on old-style Research records that predate the format."""
    text = text or ""
    result = {"reader_need": None, "claims": [], "evidence": [], "brief_status_line": ""}

    rn_match = re.search(r"##\s*Reader Need\s*(.*?)(?=\n##|\Z)", text, re.DOTALL)
    if rn_match:
        block = rn_match.group(1)
        result["reader_need"] = {
            "who": _field(block, "Who"),
            "context": _field(block, "Context"),
            "pain": _field(block, "Pain"),
            "outcome": _field(block, "Outcome"),
        }
        if not any(result["reader_need"].values()):
            result["reader_need"] = None

    claims_match = re.search(r"##\s*Claims\s*(.*)\Z", text, re.DOTALL)
    if claims_match:
        block = claims_match.group(1)
        parts = re.split(r"(?=###\s*(?:Claim|Evidence)\s+\d+)", block)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            head = re.match(r"###\s*(Claim|Evidence)\s+(\d+)", part)
            if not head:
                continue
            kind, num = head.group(1), head.group(2)
            if kind == "Claim":
                statement = _field(part, "Statement")
                status = _field(part, "Status")
                if not statement and not status:
                    continue
                result["claims"].append({"id": f"Claim {num}", "statement": statement, "status": status})
            else:
                fields = {
                    "supports": _field(part, "Supports"),
                    "evidence": _field(part, "Evidence"),
                    "source": _field(part, "Source"),
                    "location": _field(part, "Location"),
                    "evidence_level": _field(part, "Evidence Level"),
                }
                if not any(fields.values()):
                    continue
                result["evidence"].append({"id": f"Evidence {num}", **fields})

    status_match = re.search(r"^Brief Status:\s*(.*)$", text, re.MULTILINE)
    if status_match:
        result["brief_status_line"] = status_match.group(1).strip()

    return result


def format_for_prompt(parsed):
    """Render the parsed brief as plain text to inject into the AI Writer Agent
    prompt alongside the raw Research Summary (additive -- never replaces the
    existing Summary-only path)."""
    if not parsed or (not parsed.get("reader_need") and not parsed.get("claims")):
        return ""

    lines = []
    rn = parsed.get("reader_need")
    if rn:
        lines.append("[Reader Need]")
        lines.append(f"- 読者: {rn.get('who', '')}")
        lines.append(f"- 状況: {rn.get('context', '')}")
        lines.append(f"- 困りごと: {rn.get('pain', '')}")
        lines.append(f"- 読了後の状態: {rn.get('outcome', '')}")

    evidence_by_claim = {}
    for ev in parsed.get("evidence", []):
        evidence_by_claim.setdefault(ev.get("supports", ""), []).append(ev)

    adopted = [c for c in parsed.get("claims", []) if c.get("status") not in UNADOPTED_CLAIM_STATUSES]
    if adopted:
        lines.append("\n[採用するClaims]")
        for c in adopted:
            lines.append(f"- {c.get('statement', '')}（Status: {c.get('status', '')}）")
            for ev in evidence_by_claim.get(c["id"], []):
                lines.append(
                    f"  - 根拠: {ev.get('evidence', '')} "
                    f"[Source: {ev.get('source', '')} / {ev.get('location', '')} / "
                    f"Evidence Level: {ev.get('evidence_level', '')}]"
                )

    return "\n".join(lines)


def _evidence_status(ev, source_exists_fn):
    """Traceability (Sec 3.1, feeds cond 3) is checked separately in check_completion;
    this is reliability only (feeds cond 4). Returns (status, note) where status is
    one of OK / REVIEW / NG. Reported and freshness-uncertain Official/Verified can
    only ever reach REVIEW here -- never OK -- because Sec.4.4's conditions and
    Sec.13's freshness rule require judgement this code cannot perform."""
    level = ev.get("evidence_level", "")
    if level in WEAK_EVIDENCE_LEVELS:
        return "NG", f"{ev['id']}: Evidence Level='{level or '(未記入)'}' はRumor/AI Suggested相当のため採用不可"
    if level == "Reported":
        return "REVIEW", f"{ev['id']}: Reportedのため§4.4の採用条件（Official情報の不在／発信主体／掲載日／具体的根拠／複数Source裏付け）を編集者が確認"
    if level in ("Official", "Verified"):
        return "REVIEW", f"{ev['id']}: {level}だが鮮度確認（Operating-Manual §13）を編集者が確認"
    return "NG", f"{ev['id']}: 未知のEvidence Level '{level}'"


def _worst(statuses):
    if not statuses:
        return "NG"
    return max(statuses, key=lambda s: _STATUS_RANK[s])


def check_completion(parsed, source_exists_fn=None, freshness_confirmed=None):
    """Mechanical Check against Article-Brief-Specification-v1.0.md Sec.6, split
    from the Final Brief Status per Rei's 2026-07-19 correction (see module
    docstring). `freshness_confirmed`: True if Operating-Manual Sec.13's freshness
    rule has been independently confirmed fresh for this Research record, False if
    confirmed stale, None if not evaluated -- None is treated the same as "not yet
    confirmed" (REVIEW), never assumed fresh.
    """
    reader_need = parsed.get("reader_need")
    claims = parsed.get("claims", [])
    evidence = parsed.get("evidence", [])
    evidence_by_claim = {}
    for ev in evidence:
        evidence_by_claim.setdefault(ev.get("supports", ""), []).append(ev)

    mech = {}

    # (1) Reader Need <-> Claim: existence of both sides can be mechanically
    # confirmed, but the semantic match itself can never be -- always REVIEW at
    # best, NG if a required side is simply missing.
    has_outcome = bool(reader_need and reader_need.get("outcome"))
    has_claims = bool(claims)
    if has_outcome and has_claims:
        mech["1_reader_need_answered"] = {
            "status": "REVIEW",
            "note": "Reader Need(Outcome)とClaimは存在する。意味的に対応しているかは編集者が確認（§6①）",
        }
    else:
        missing = []
        if not has_outcome:
            missing.append("Reader Need Outcome")
        if not has_claims:
            missing.append("Claim")
        mech["1_reader_need_answered"] = {"status": "NG", "note": f"必須項目が不足: {', '.join(missing)}"}

    # (2) Claim <- Evidence: fully mechanical (Supports + Status=Supported)
    unsupported = [c["id"] for c in claims
                   if c.get("status") == "Supported" and not evidence_by_claim.get(c["id"])]
    if not claims:
        mech["2_claim_supported_by_evidence"] = {"status": "NG", "note": "Claimが1件もない"}
    elif unsupported:
        mech["2_claim_supported_by_evidence"] = {"status": "NG", "note": f"EvidenceがないままSupportedのClaim: {unsupported}"}
    else:
        mech["2_claim_supported_by_evidence"] = {"status": "OK", "note": "OK"}

    # (3) Evidence -> Source traceable: fully mechanical (Source + Location present,
    # and Source resolves to a real Source Library record when a lookup is given)
    untraceable = []
    for ev in evidence:
        title = ev.get("source", "")
        if not title or not ev.get("location"):
            untraceable.append(ev["id"])
        elif source_exists_fn is not None and not source_exists_fn(title):
            untraceable.append(ev["id"])
    if not evidence:
        mech["3_evidence_traceable_to_source"] = {"status": "NG", "note": "Evidenceが1件もない"}
    elif untraceable:
        mech["3_evidence_traceable_to_source"] = {"status": "NG", "note": f"Source/Locationが未確認のEvidence: {untraceable}"}
    else:
        mech["3_evidence_traceable_to_source"] = {"status": "OK", "note": "OK"}

    # (4) Source reliability + freshness: Reported and freshness-unconfirmed
    # Official/Verified can only reach REVIEW, never OK, by this code alone.
    if not evidence:
        mech["4_source_confidence_and_freshness"] = {"status": "NG", "note": "Evidenceが1件もない"}
    else:
        per_evidence = [_evidence_status(ev, source_exists_fn) for ev in evidence]
        statuses = [s for s, _ in per_evidence]
        notes = [n for _, n in per_evidence]
        overall = _worst(statuses)
        if overall == "OK" and freshness_confirmed is not True:
            overall = "REVIEW"
            notes.append("Research全体の鮮度（Operating-Manual §13）がまだ確認されていない")
        elif overall == "OK" and freshness_confirmed is False:
            overall = "REVIEW"
            notes.append("Research全体の鮮度（Operating-Manual §13）が「要更新」のため確認が必要")
        mech["4_source_confidence_and_freshness"] = {"status": overall, "note": "; ".join(notes)}

    # (5) No unresolved Conflicted/Needs Review claims -- fully mechanical
    unresolved = [c["id"] for c in claims if c.get("status") in UNRESOLVED_CLAIM_STATUSES]
    mech["5_no_unresolved_claims"] = (
        {"status": "NG", "note": f"未解決のClaim: {unresolved}"} if unresolved
        else {"status": "OK", "note": "OK"}
    )

    # Mechanical gate for Final Brief Status: cond 2/3/5 must be OK, cond 4 must
    # not be NG (REVIEW is allowed through to the editor's own sign-off), and
    # cond 1 never gates this (it is always REVIEW/NG, by design -- see docstring).
    mechanical_ready = (
        bool(claims)
        and mech["2_claim_supported_by_evidence"]["status"] == "OK"
        and mech["3_evidence_traceable_to_source"]["status"] == "OK"
        and mech["4_source_confidence_and_freshness"]["status"] != "NG"
        and mech["5_no_unresolved_claims"]["status"] == "OK"
    )

    brief_status_line = parsed.get("brief_status_line", "")
    if not mechanical_ready:
        final_status = "材料不足"
        final_note = "機械判定（②③④⑤）を満たしていません。Mechanical Checkの各項目を確認してください。"
    elif brief_status_line.startswith("執筆可能"):
        final_status = "執筆可能"
        final_note = "機械判定を満たし、編集者がEditor's Notesに「Brief Status: 執筆可能」を記入済み。"
    elif brief_status_line.startswith("材料不足"):
        final_status = "材料不足"
        final_note = f"機械判定は満たしているが、編集者自身が材料不足と記録している: {brief_status_line}"
    else:
        final_status = "編集者確認待ち"
        final_note = "機械判定（②③④⑤）は満たしていますが、Editor's Notesに編集者記入の「Brief Status: 執筆可能」がまだありません。"

    return {
        "mechanical_check": mech,
        "final_brief_status": final_status,
        "final_brief_status_note": final_note,
    }


# --- Grounding Check (2026-07-19) ---------------------------------------------
# Deterministic, pattern-based -- NOT full semantic fact-checking. It reliably
# catches the shapes of the 2026-07-19 incident (an added number/period/phone
# number/procedural or historical detail not present in the approved Brief), and
# generalizes to different digits/phrasing of the same shape (changing "25年"
# to "23年" is still caught, since the check is "does this number appear
# anywhere in the Brief's own Evidence text", not a literal string match).
# It will NOT catch a subtler prose hallucination that uses no numbers and no
# listed term -- human review remains required, same as everywhere else in this
# project's Constitution-level human-approval-gate principle.

_TERMINAL_MARKERS = ("。", "」", "』", "）", ")", "！", "!", "？", "?", "…")
_URL_TAIL = re.compile(r"https?://\S+$")


def is_body_truncated(body):
    """Heuristic: a real finished ARu article body ends with terminal punctuation,
    a closing bracket/quote, or -- since a Sources section legitimately ends on a
    bare URL -- a URL. A trailing "、" (comma) is deliberately NOT accepted as
    terminal: that is exactly the shape of the 2026-07-19 truncation incident
    (body cut off mid-list: "...都道府県、年齢、"), not a valid sentence ending."""
    tail = (body or "").rstrip()
    if not tail:
        return True
    if _URL_TAIL.search(tail):
        return False
    return not tail.endswith(_TERMINAL_MARKERS)


_UNIT_ALIASES = [("ヶ月", "月"), ("か月", "月"), ("カ月", "月"), ("％", "%")]
# "40歳から64歳まで" and "40～64歳" say the same thing in different grammar;
# without this, a body using "〜" for a range already present in Evidence as
# "AからBまで" gets a false-positive Unsupported flag (found in the 2026-07-19
# regeneration: Evidence said "40歳から64歳までの方", body said "40～64歳").
_RANGE_WORDS_TO_TILDE = re.compile(r"(\d+)歳から(\d+)歳まで")


def _normalize(s):
    for a, b in _UNIT_ALIASES:
        s = s.replace(a, b)
    # "〜" (U+301C WAVE DASH) and "～" (U+FF5E FULLWIDTH TILDE) are visually
    # identical and used interchangeably in Japanese text; without collapsing
    # them to one, "40～64歳" (body) vs "40〜64歳" (this module's own range
    # substitution below) would silently fail to match as the same string.
    s = s.replace("～", "〜")
    s = _RANGE_WORDS_TO_TILDE.sub(r"\1〜\2歳", s)
    return re.sub(r"\s+", "", s)


def _date_variants(iso_date):
    """Generate common surface forms of an ISO date so "today" (which is always
    legitimate to state as the info-as-of date) isn't flagged just because its
    kanji rendering doesn't literally appear in the Brief's Evidence text."""
    if not iso_date:
        return set()
    y, m, d = iso_date.split("-")
    m, d = str(int(m)), str(int(d))
    return {
        iso_date, f"{y}年{m}月{d}日", f"{y}年{int(m):02d}月{int(d):02d}日",
        f"{y}/{m}/{d}", f"{y}{int(m):02d}{int(d):02d}",
    }


# Three numeric shapes are checked in priority order (each masks its own span so
# later, looser scans don't re-split it into misleading bare fragments):
#   1. full calendar dates ("2026年7月20日") -- checked against Evidence AND,
#      when supplied, against today's date (always legitimate to state)
#   2. calendar-style ranges ("4月〜6月", unit BEFORE the separator on both
#      sides) -- must be compared as one whole token, otherwise a naive scan
#      re-extracts the bare "6月" and wrongly matches unrelated Evidence text
#      like "加入期間が6月以上" (6 months of enrollment, not the month of June)
#   3. everything else (single numbers, "1〜2週間"-style ranges where the unit
#      comes only at the end, phone numbers)
_FULL_DATE_TOKEN = re.compile(r"\d{4}年\d{1,2}月\d{1,2}日")
_RANGE_TOKEN = re.compile(
    r"\d+(?:ヶ|か|カ)?(?:月|年|日|歳)\s*[〜～\-]\s*\d+(?:ヶ|か|カ)?(?:月|年|日|歳)"
    r"|\d+歳から\d+歳まで"  # same range, spelled out in words instead of a tilde
)
_NUMBER_TOKEN = re.compile(
    r"\d+(?:\.\d+)?(?:\s*[〜～\-]\s*\d+(?:\.\d+)?)?"
    r"\s*(?:%|％|歳|年|ヶ月|か月|カ月|月|日|週間|万円|円|人)?"
)
_PHONE_TOKEN = re.compile(r"0\d{1,4}-\d{1,4}-\d{3,4}")


def _mask(text, span):
    chars = list(text)
    for i in range(*span):
        chars[i] = "＊"
    return "".join(chars)

# Procedural/historical proper nouns that, if present in the body but nowhere in
# the Brief's own Evidence text, indicate added unverified specifics rather than
# only using what was approved. Deliberately excludes generic words (e.g.
# "従業員") that would false-positive on legitimate Evidence text -- the numeric
# check already catches invented figures like "従業員5人以上" via the "5人" token.
_PROCEDURAL_TERMS = [
    "年金手帳", "転出届", "マイナンバーカード", "コールセンター", "ダイヤル",
    "必要書類", "保険証", "高度経済成長", "職業安定所",
]
_OVERCLAIM_PHRASES = ["完全ガイド", "必ず", "すべての", "絶対に"]
_OVERGENERALIZE_PATTERN = re.compile(r"どの.{0,20}(?:でも|も).{0,15}(?:対象|該当)")
_TYPE_AGNOSTIC_PATTERN = re.compile(r"(?:種類|区分|在留資格)を問わ")

# 2026-07-20 second incident: background/rationale/purpose prose (why the system
# exists, postwar policy history, why rates differ by prefecture, why the lump-
# sum-withdrawal system was created) contains no numbers and no procedural proper
# noun, so the checks above never see it -- yet it's exactly the kind of AI
# general-knowledge padding Public Information Strict Mode Principle 1 bans. Any
# sentence containing one of these framing markers is flagged outright; there is
# no legitimate way to explain "why"/history/purpose without it being either (a)
# directly quoted from an Evidence block (rare for this kind of Brief) or (b)
# added general knowledge -- so the marker itself is treated as disqualifying.
_EXPLANATION_MARKERS = [
    "背景", "という考え方", "政策判断", "生まれた理由", "存在する理由", "設けられ",
    "反映した仕組み", "という原則", "権利を持つ", "支える仕組み", "を反映",
    "経済成長期", "戦後", "を想定して", "不公正", "配慮として", "という理念",
    "由来", "整備されました", "労働政策の原則", "考え方が基本",
]
_SENTENCE_SPLIT = re.compile(r"(?<=[。！？])")


def grounding_check(body, parsed_brief, today=None):
    """Audit a generated article body against its Article Brief. `today` (ISO
    date, e.g. "2026-07-20") exempts the info-as-of date the article is required
    to state -- otherwise stating today's date correctly still gets flagged just
    because its digits don't appear in Evidence text about the *Sources'* own
    dates. Returns {"supported": [...], "unsupported": [...], "overclaiming":
    [...]}. Safe to Pass only when both "unsupported" and "overclaiming" are empty.
    """
    evidence = parsed_brief.get("evidence", []) if parsed_brief else []
    claims = parsed_brief.get("claims", []) if parsed_brief else []
    reader_need = parsed_brief.get("reader_need") if parsed_brief else None

    evidence_text = " ".join(
        " ".join([ev.get("evidence", ""), ev.get("source", ""), ev.get("location", ""), ev.get("evidence_level", "")])
        for ev in evidence
    )
    claim_text = " ".join(c.get("statement", "") for c in claims)
    reader_need_text = " ".join(v for v in reader_need.values()) if reader_need else ""
    brief_text_norm = _normalize(evidence_text + " " + claim_text + " " + reader_need_text)
    today_variants = {_normalize(v) for v in _date_variants(today)}

    body = body or ""
    supported, unsupported = [], []
    working = body

    for m in _FULL_DATE_TOKEN.finditer(body):
        token = m.group(0)
        norm = _normalize(token)
        if norm in brief_text_norm or norm in today_variants:
            supported.append(token)
        else:
            unsupported.append(f"数値/期間: '{token}'")
        working = _mask(working, m.span())

    for m in _RANGE_TOKEN.finditer(working):
        token = m.group(0)
        if _normalize(token) in brief_text_norm:
            supported.append(token)
        else:
            unsupported.append(f"数値/期間: '{token}'")
        working = _mask(working, m.span())

    for m in _NUMBER_TOKEN.finditer(working):
        token = m.group(0).strip()
        if not re.search(r"\d", token):
            continue
        norm = _normalize(token)
        if norm in brief_text_norm or norm in today_variants:
            supported.append(token)
        else:
            unsupported.append(f"数値/期間: '{token}'")

    for m in _PHONE_TOKEN.finditer(body):
        token = m.group(0)
        if _normalize(token) in brief_text_norm:
            supported.append(token)
        else:
            unsupported.append(f"電話番号: '{token}'")

    for term in _PROCEDURAL_TERMS:
        if term in body and term not in evidence_text and term not in claim_text:
            unsupported.append(f"手続き・歴史・対象条件: '{term}'")

    for sentence in _SENTENCE_SPLIT.split(body):
        if any(marker in sentence for marker in _EXPLANATION_MARKERS):
            unsupported.append(f"背景・理由・目的の説明: '{sentence.strip()[:60]}'")

    overclaiming = [p for p in _OVERCLAIM_PHRASES if p in body]
    if _OVERGENERALIZE_PATTERN.search(body):
        overclaiming.append("Claimを広げた断定（「どの…でも対象」等の一般化表現）")
    if _TYPE_AGNOSTIC_PATTERN.search(body):
        overclaiming.append("Claimを広げた断定（「種類/在留資格を問わず」等の一般化表現）")

    return {"supported": supported, "unsupported": unsupported, "overclaiming": overclaiming}


# --- Semantic Grounding Check (2026-07-20) ------------------------------------
# Complements grounding_check() (deterministic patterns) with a sentence-level,
# AI-judged pass: for every sentence in the body, ask whether it maps onto a
# specific Claim/Evidence ID. Catches prose the deterministic layer cannot --
# background/rationale/procedural claims phrased in ways not on the marker list.
# `complete_fn` is injectable (defaults to ai_gateway.complete) specifically so
# regression tests can supply a canned response and test the parsing/aggregation
# logic deterministically, without depending on a live model call.

def _default_complete_fn(prompt, max_tokens=1500):
    import ai_gateway
    return ai_gateway.complete(prompt, max_tokens=max_tokens)


def build_semantic_grounding_prompt(body, parsed_brief):
    claims = parsed_brief.get("claims", []) if parsed_brief else []
    evidence = parsed_brief.get("evidence", []) if parsed_brief else []
    brief_lines = []
    for c in claims:
        brief_lines.append(f"{c['id']}: {c.get('statement', '')}")
    for ev in evidence:
        brief_lines.append(f"{ev['id']} (supports {ev.get('supports', '')}): {ev.get('evidence', '')}")
    brief_text = "\n".join(brief_lines)

    return f"""あなたはARu編集部のファクトチェッカーです。以下の「承認済みArticle Brief」だけを根拠として、
「記事本文」を1文ずつ判定してください。

判定基準（厳格に。Public Information Strict Modeに従うこと）：
- その文が、承認済みのいずれかのClaim/Evidenceの内容（本文だけでなく、そのEvidence本文中に
  明記されている日付・時期・数値などの付随情報も含む）と対応していれば SUPPORTED。
  Evidence本文に書かれている情報を、そのまま言い換えているだけの文はSUPPORTEDである。
- SUPPORTEDと判定するのは「Evidence本文に本当に書かれているか」で判断し、
  「詳しすぎる」「具体的すぎる」という理由だけでUNSUPPORTEDにしないこと。
- 背景・理由・目的・沿革の説明、未承認の数値の合算・計算、未承認の手続き・窓口案内、
  一般化した断定（「〜を問わず」「どの〜でも」等）、その他Article Briefに全く記載のない
  情報を追加している場合にのみ UNSUPPORTEDとすること。
- 単なる接続語・見出し・出典一覧（Sourcesセクション）は判定不要（SKIPと出力）。

承認済みArticle Brief：
{brief_text}

記事本文：
{body}

出力形式（1行につき1文、このまま出力し他の説明を付けないこと）：
SUPPORTED | <Claim/Evidence ID> | <文の要約（30文字程度）>
UNSUPPORTED | - | <文の要約（30文字程度）>
SKIP | - | <文の要約（30文字程度）>
"""


def parse_semantic_grounding_response(text):
    supported, unsupported = [], []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue
        verdict, ref, summary = parts[0].upper(), parts[1], parts[2]
        if verdict.startswith("SUPPORTED"):
            supported.append(f"{ref}: {summary}")
        elif verdict.startswith("UNSUPPORTED"):
            unsupported.append(summary)
        # SKIP is intentionally dropped
    return {"supported": supported, "unsupported": unsupported}


def semantic_grounding_check(body, parsed_brief, complete_fn=None):
    """AI-judged sentence-to-Claim/Evidence mapping. Returns
    {"supported": ["Claim 1: ...", ...], "unsupported": ["...", ...]}.
    Safe to Pass only when "unsupported" is empty. Requires a live model call
    (via complete_fn, default ai_gateway.complete) unless a fake is injected."""
    if not parsed_brief or not (parsed_brief.get("reader_need") or parsed_brief.get("claims")):
        return {"supported": [], "unsupported": []}
    complete_fn = complete_fn or _default_complete_fn
    prompt = build_semantic_grounding_prompt(body, parsed_brief)
    _provider, text = complete_fn(prompt, max_tokens=1800)
    return parse_semantic_grounding_response(text)
