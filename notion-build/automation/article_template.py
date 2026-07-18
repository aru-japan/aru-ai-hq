"""ARu Official Article Template -- single source of truth.

G3-A (Article Template Framework, standard-only): this module is now
organized around a TEMPLATES registry so that a future template (e.g. an
Event-specific one, G3-B) can be added as a second entry without touching
this file's existing behavior. This phase intentionally registers exactly
one template, "standard" -- no other template exists yet.

The public names below (SECTION_ORDER, PRIMARY_SECTIONS, SECONDARY_SECTIONS,
PREMIUM_SECTION, SOURCES_SECTION, MANDATORY_SECTIONS,
ARU_ARTICLE_TEMPLATE_INSTRUCTIONS) are unchanged in name, value, and object
identity from before this refactor -- they are views onto
TEMPLATES["standard"], not independent definitions, so every existing
consumer (generate_article_pipeline.py, reviewer_agent.py,
render_article_layout.py, template_migration_report.py) keeps working
without any change on their side. parse_body_sections()/validate_sections()
gained an optional `template=` argument (default "standard") so a future
template can be parsed/validated the same way; every existing call site
omits it and therefore behaves exactly as before.

Replaces the prior duplication between generate_article_pipeline.py's
ARU_ARTICLE_TEMPLATE_INSTRUCTIONS and render_article_layout.py's own copy of
SECTION_ORDER -- both now import from here. This is a brand-quality
standardization (Rei's 11-item official structure), not a new database or a
new pipeline: Title stays the existing page-title property, Related Articles
and Last Updated stay driven by existing properties (Knowledge Links,
Last Verified Date), and everything else is still one Body rich_text blob
with `**Heading**` markers, exactly as before.

Body-parsed sections (8): Basic Answer, More Details, Cultural Background,
ARu Tip, Things to Know, FAQ, Premium Section, Sources.
Property-driven (not in Body): Title (existing title property), Related
Articles (existing Knowledge Links relation), Last Updated (existing
Last Verified Date / Updated Date properties).
"""
import re
import difflib

PREMIUM_ENRICHMENT_PLACEHOLDER = "この記事にはまだ十分なプレミアム情報がありません。編集者による追加取材・加筆が必要です。"
SOURCES_VERIFICATION_PLACEHOLDER = "出典は編集部による確認が必要です（自動生成時点で検証済みの一次情報源が見つかりませんでした）。"

_STANDARD_INSTRUCTIONS = """記事は必ず以下のARu公式テンプレート（8セクション）の構成で書いてください。各セクションの見出しはそのまま太字（**見出し**）で示し、8つすべてを含めてください。

1. **Basic Answer** — 3〜5行程度の短い直接回答。まずユーザーが知りたい結論を先に示す、無料部分として単独で読める内容にする
2. **More Details** — 基本回答だけでは分からない主な説明・背景・具体例・実際の文脈
3. **Cultural Background** — この話題の背景にある日本独自の文化的理由・社会的背景・慣習・歴史・考え方（ARuの核となる差別化要素）
4. **ARu Tip** — 外国籍の住民・訪日者向けの実践的なアドバイス。具体的で行動につながる内容にし、Basic Answerの繰り返しは避ける。**このセクションは必須——省略しないこと**
5. **Things to Know** — 重要な注意点、地域や施設によって対応が異なる場合の説明、よくある誤解、ローカルルール
6. **FAQ** — 外国籍ユーザーが実際に聞きそうな現実的な質問を3〜5件、Q&A形式で
7. **Premium Section** — 該当する場合のみ、以下のような実用的価値を追加する内容を含める：具体的な場所・タイミング・費用・予約方法・アクセス・現地マナー・よくある間違い・あまり知られていない情報・次に取るべき行動。**確信を持てる情報がない場合は絶対に内容を創作しないこと**。その場合は代わりに「{premium_placeholder}」とだけ書く
8. **Sources** — 公式・信頼できる情報源（政府・自治体・公式団体等を優先）を記載する。**出典を捏造しないこと**。リサーチ内容に実際の一次情報源の記載がない場合は、代わりに「{sources_placeholder}」とだけ書く

Title・Related Articles・Last Updatedは本文（Body）には含めない——これらはNotionの既存プロパティ（記事タイトル・Knowledge Links・Last Verified Date）から自動的に扱われる。""".format(
    premium_placeholder=PREMIUM_ENRICHMENT_PLACEHOLDER,
    sources_placeholder=SOURCES_VERIFICATION_PLACEHOLDER,
)

TEMPLATES = {
    "standard": {
        "section_order": [
            "Basic Answer",
            "More Details",
            "Cultural Background",
            "ARu Tip",
            "Things to Know",
            "FAQ",
            "Premium Section",
            "Sources",
        ],
        # Always visible in the main page flow.
        "primary_sections": ["Basic Answer", "More Details", "Cultural Background", "ARu Tip", "Things to Know"],
        # Folded into the existing "その他の詳細" toggle.
        "secondary_sections": ["FAQ"],
        # Rendered in its own distinct toggle -- premium content is conceptually
        # separate from the free sections above, not just "more of the same detail."
        "premium_section": "Premium Section",
        # Rendered as a visible (non-toggled) heading -- trust/credibility signal,
        # not something to hide behind a click for a platform built on "Decode Japan."
        "sources_section": "Sources",
        # ARu Tip must always be present; the pipeline warns loudly if it's missing
        # rather than silently generating an incomplete article.
        "mandatory_sections": ["ARu Tip"],
        "instructions": _STANDARD_INSTRUCTIONS,
    },
}


def get_template(name="standard"):
    """Look up a registered article template definition by name."""
    return TEMPLATES[name]


# Backward-compatible module-level exports. Every existing consumer imports
# these names directly; they are views onto TEMPLATES["standard"] (same list
# objects, same string), not independent definitions, so nothing about their
# value or identity changed as part of this refactor.
SECTION_ORDER = TEMPLATES["standard"]["section_order"]
PRIMARY_SECTIONS = TEMPLATES["standard"]["primary_sections"]
SECONDARY_SECTIONS = TEMPLATES["standard"]["secondary_sections"]
PREMIUM_SECTION = TEMPLATES["standard"]["premium_section"]
SOURCES_SECTION = TEMPLATES["standard"]["sources_section"]
MANDATORY_SECTIONS = TEMPLATES["standard"]["mandatory_sections"]
ARU_ARTICLE_TEMPLATE_INSTRUCTIONS = TEMPLATES["standard"]["instructions"]

_HEADING_RE = re.compile(r"\*\*\s*([^\*]{2,80}?)\s*\*\*")


def _normalize(text):
    text = text.strip().lower()
    text = re.sub(r"[?？:：]+$", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _match_canonical(raw_heading, canonical_by_normalized):
    norm = _normalize(raw_heading)
    if norm in canonical_by_normalized:
        return canonical_by_normalized[norm]
    close = difflib.get_close_matches(norm, canonical_by_normalized.keys(), n=1, cutoff=0.6)
    if close:
        return canonical_by_normalized[close[0]]
    return None


def parse_body_sections(body_text, template="standard"):
    """Best-effort split of a template's Body text into {canonical_name: content}.
    Unrecognized bold spans are ignored. Missing sections are simply absent from
    the returned dict -- callers must .get() rather than assume all sections exist.

    `template` selects which registered template's section list to parse
    against (default "standard"); every existing call site omits this
    argument and therefore parses against the standard 8 sections exactly as
    before this function was parametrized.

    Only bold spans that resolve to a canonical section name are treated as
    section boundaries -- inline bold emphasis inside a section's own content
    (e.g. AI-written bullet labels like "**浴衣を着てみましょう**：...") is
    real content, not a new heading, and must not truncate the section it
    appears in. A prior version used *every* bold span as a boundary
    candidate regardless of whether it resolved to a canonical name, which
    silently cut off any section whose body text happened to contain inline
    bold formatting."""
    if not body_text:
        return {}

    section_order = TEMPLATES[template]["section_order"]
    canonical_by_normalized = {_normalize(s): s for s in section_order}

    canonical_matches = []
    for m in _HEADING_RE.finditer(body_text):
        canonical = _match_canonical(m.group(1), canonical_by_normalized)
        if canonical and canonical not in {c for c, _, _ in canonical_matches}:
            canonical_matches.append((canonical, m.start(), m.end()))

    sections = {}
    for i, (canonical, _, heading_end) in enumerate(canonical_matches):
        start = heading_end
        end = canonical_matches[i + 1][1] if i + 1 < len(canonical_matches) else len(body_text)
        content = body_text[start:end].strip()
        if content:
            sections[canonical] = content
    return sections


def validate_sections(sections, template="standard"):
    """Returns (missing, mandatory_missing) -- both lists of canonical section
    names for the given template (default "standard"). mandatory_missing is a
    subset of missing, restricted to that template's mandatory sections
    (currently just ARu Tip for "standard")."""
    section_order = TEMPLATES[template]["section_order"]
    mandatory_sections = TEMPLATES[template]["mandatory_sections"]
    missing = [s for s in section_order if s not in sections]
    mandatory_missing = [s for s in mandatory_sections if s not in sections]
    return missing, mandatory_missing
