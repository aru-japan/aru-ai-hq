"""ARu Official Article Template -- single source of truth.

G3-A (Article Template Framework, standard-only) organized this module
around a TEMPLATES registry so a future template could be added as a second
entry without touching the standard template's existing behavior.

G3-B adds that second entry: "event", for Category="イベント" content
(Option 1 scope -- built against the existing Event Calendar/Research
schema, no new Notion properties. Facts this template can't yet source from
a dedicated property, such as exact cost or confirmed English support,
are handled the same way Premium Section/Sources already handle
uncertainty: the model is instructed to write an explicit "not confirmed"
placeholder per item rather than fabricate or omit the section).
`template_for_category(category)` centralizes the Category -> template
name mapping so every consumer resolves it the same way.

The public names below (SECTION_ORDER, PRIMARY_SECTIONS, SECONDARY_SECTIONS,
PREMIUM_SECTION, SOURCES_SECTION, MANDATORY_SECTIONS,
ARU_ARTICLE_TEMPLATE_INSTRUCTIONS) remain views onto TEMPLATES["standard"]
specifically -- they still exist, unchanged, for any code that hasn't been
made template-aware. parse_body_sections()/validate_sections() take an
optional `template=` argument (default "standard"); every pre-G3-B call site
omits it and therefore behaves exactly as before G3-B, too.

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
BEFORE_YOU_GO_UNCERTAIN_PLACEHOLDER = "現地公式サイト等での要確認事項です（自動生成時点で確認できませんでした）。"
FOOD_SAFETY_UNCERTAIN_PLACEHOLDER = "この項目は店舗・製造元・公式情報源への個別確認が必須です（自動生成時点では安全性を断定できません）。"

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

_EVENT_INSTRUCTIONS = """記事は必ず以下のARu Eventテンプレート（8セクション）の構成で書いてください。各セクションの見出しはそのまま太字（**見出し**）で示し、8つすべてを含めてください。標準テンプレート（Basic Answer等）とは異なるセクション名です——標準テンプレートの見出しを使わないこと。

1. **Before You Go** — 日時・場所・費用・予約要否・現金対応・英語対応・荒天時の対応方針など、読者が行く前に知っておくべき実用的な事実を簡潔な箇条書きで示す。**このセクションは必須——省略しないこと**。費用・現金対応・英語対応など、情報源に明記がなく確信が持てない項目は、断定せず項目ごとに「{before_you_go_placeholder}」と書くこと。**捏造しないこと**
2. **What to Expect** — このイベント・体験の内容、雰囲気、見どころ
3. **Cultural Background** — このイベントの背景にある日本独自の文化的理由・歴史・慣習（ARuの核となる差別化要素）
4. **Who This Is For** — 観光客／在住外国人／家族連れ／学生など、どのような読者に向いているかを示す
5. **ARu Tip** — 外国籍の住民・訪日者向けの実践的なアドバイス（穴場、混雑回避等）。Before You Goの繰り返しは避ける。**このセクションは必須——省略しないこと**
6. **Cautions & Accessibility** — 荒天時の中止基準、混雑レベル、バリアフリー対応等の注意点
7. **Premium Section** — 該当する場合のみ、穴場スポット・詳しい交通手段・タイミングの助言等の実用的付加価値を含める。**確信を持てる情報がない場合は絶対に内容を創作しないこと**。その場合は代わりに「{premium_placeholder}」とだけ書く
8. **Sources** — 公式・信頼できる情報源（イベント公式サイト・実行委員会・自治体観光協会等を優先）を記載する。**出典を捏造しないこと**。実際の一次情報源の記載がない場合は、代わりに「{sources_placeholder}」とだけ書く

Title・Related Articles・Last Updatedは本文（Body）には含めない——これらはNotionの既存プロパティ（記事タイトル・Knowledge Links・Last Verified Date）から自動的に扱われる。""".format(
    before_you_go_placeholder=BEFORE_YOU_GO_UNCERTAIN_PLACEHOLDER,
    premium_placeholder=PREMIUM_ENRICHMENT_PLACEHOLDER,
    sources_placeholder=SOURCES_VERIFICATION_PLACEHOLDER,
)

_HEADLINE_INSTRUCTIONS = """記事は必ず以下のARu Headlineテンプレート（4セクション）の構成で書いてください。目を引く短い記事——Basic Articleより短く、フックで惹きつけて即座に核心の回答を返す。各セクションの見出しはそのまま太字（**見出し**）で示すこと。

1. **Hook** — 1〜2文で読者の関心を掴む導入。問いかけ・意外性のある事実など
2. **Basic Answer** — 3〜5行の直接回答
3. **ARu Tip** — 実践的アドバイス。**このセクションは必須——省略しないこと**
4. **Sources** — 公式・信頼できる情報源。**捏造しないこと**。なければ「{sources_placeholder}」とだけ書く

Title・Related Articles・Last Updatedは本文（Body）には含めない。""".format(
    sources_placeholder=SOURCES_VERIFICATION_PLACEHOLDER,
)

_DEEP_GUIDE_INSTRUCTIONS = """記事は必ず以下のARu Deep Guideテンプレート（10セクション）の構成で書いてください。Basic Articleより深く、手順・実例・よくある失敗まで踏み込んだPremium級の内容にする。各セクションの見出しはそのまま太字（**見出し**）で示すこと。

1. **Basic Answer** — 短い直接回答
2. **More Details** — 背景・具体例
3. **Cultural Background** — 日本独自の文化的背景
4. **Step-by-Step Guide** — 実際の手順を番号付きで具体的に。**このセクションは必須——省略しないこと**
5. **ARu Tip** — 実践的アドバイス。**このセクションは必須——省略しないこと**
6. **Common Mistakes** — 外国籍ユーザーが陥りやすい失敗・誤解
7. **Things to Know** — 注意点、地域差
8. **FAQ** — Q&A形式で3〜5件
9. **Premium Section** — 該当する場合のみ、より詳しい実用情報。**確信を持てる情報がない場合は絶対に内容を創作しないこと**。その場合は「{premium_placeholder}」とだけ書く
10. **Sources** — 公式・信頼できる情報源。**捏造しないこと**。なければ「{sources_placeholder}」とだけ書く

Title・Related Articles・Last Updatedは本文（Body）には含めない。""".format(
    premium_placeholder=PREMIUM_ENRICHMENT_PLACEHOLDER,
    sources_placeholder=SOURCES_VERIFICATION_PLACEHOLDER,
)

_PREMIUM_INSTRUCTIONS = """記事は必ず以下のARu Premiumテンプレート（6セクション）の構成で書いてください。記事全体がPremium層のコンテンツである前提——内部に別途「おまけのPremium Section」は設けない。各セクションの見出しはそのまま太字（**見出し**）で示すこと。

1. **Premium Overview** — このPremium記事が提供する価値の要約
2. **Detailed Walkthrough** — 詳細な解説・手順
3. **Insider Tips** — 一般には知られていない実用的な情報
4. **Cultural Background** — 日本独自の文化的背景
5. **ARu Tip** — 実践的アドバイス。**このセクションは必須——省略しないこと**
6. **Sources** — 公式・信頼できる情報源。**捏造しないこと**。なければ「{sources_placeholder}」とだけ書く

Title・Related Articles・Last Updatedは本文（Body）には含めない。""".format(
    sources_placeholder=SOURCES_VERIFICATION_PLACEHOLDER,
)

_UPDATE_NOTICE_INSTRUCTIONS = """記事は必ず以下のARu Update Noticeテンプレート（6セクション）の構成で書いてください。この記事はArticlesの既存プロパティ Previous Information／Current Information／Change Reason（Law Updateまたは編集判断により設定済み）を根拠とすること——本文で新しい事実を創作しないこと。各セクションの見出しはそのまま太字（**見出し**）で示すこと。

1. **What Changed** — Previous Information→Current Informationの差分を要約する。**このセクションは必須——省略しないこと**
2. **Why It Changed** — Change Reasonプロパティにもとづく変更理由
3. **What This Means For You** — 読者（在留外国人・留学生等）にとっての実際の影響
4. **ARu Tip** — 実践的アドバイス。**このセクションは必須——省略しないこと**
5. **Premium Section** — 該当する場合のみ、より詳しい実務対応。**確信を持てる情報がない場合は絶対に内容を創作しないこと**。その場合は「{premium_placeholder}」とだけ書く
6. **Sources** — 公式・信頼できる情報源（Related Source Library等）。**捏造しないこと**。なければ「{sources_placeholder}」とだけ書く

Title・Related Articles・Last Updatedは本文（Body）には含めない。""".format(
    premium_placeholder=PREMIUM_ENRICHMENT_PLACEHOLDER,
    sources_placeholder=SOURCES_VERIFICATION_PLACEHOLDER,
)

_FOOD_RESTRICTION_INSTRUCTIONS = """記事は必ず以下のARu Food Restriction Supportテンプレート（8セクション）の構成で書いてください。食事制限・アレルギー・宗教上の制約は誤りが読者の健康・信仰に直接影響する領域——確信を持てない安全性の判断は絶対に断定しないこと。各セクションの見出しはそのまま太字（**見出し**）で示すこと。

1. **対象となる食事制限** — Vegetarian/Vegan/Halal/No Pork/Food Allergy/Religious Dietary Needs等、対象を明記する。**このセクションは必須——省略しないこと**
2. **日本で注意する食材** — 日本の食文化で見落とされがちな該当食材
3. **見落としやすい原材料** — だし（動物性）、みりん・料理酒（アルコール）等、気づきにくい原材料
4. **店舗で確認する質問** — 店舗・製造元に確認すべき具体的な質問リスト
5. **日本語での伝え方** — 実際に使える日本語フレーズ（例文）
6. **表示の見方** — 日本の食品表示・メニュー表示の読み方
7. **緊急時の対応** — 誤って摂取した場合の対応。**このセクションは必須——省略しないこと**
8. **公式または信頼できる情報源** — 政府・団体・公式認証機関等。**出典を捏造しないこと**。確信が持てない安全性の判断は、断定せず「{food_safety_placeholder}」と書くこと。なければ「{sources_placeholder}」とだけ書く

最終確認日は本文（Body）には含めない——既存プロパティ（Last Verified Date）から扱う。Title・Related Articlesも同様に本文には含めない。""".format(
    food_safety_placeholder=FOOD_SAFETY_UNCERTAIN_PLACEHOLDER,
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
    "event": {
        "section_order": [
            "Before You Go",
            "What to Expect",
            "Cultural Background",
            "Who This Is For",
            "ARu Tip",
            "Cautions & Accessibility",
            "Premium Section",
            "Sources",
        ],
        "primary_sections": ["Before You Go", "What to Expect", "Cultural Background", "Who This Is For", "ARu Tip"],
        # Folded into the same "その他の詳細" toggle render_article_layout.py
        # already renders for the standard template's FAQ.
        "secondary_sections": ["Cautions & Accessibility"],
        "premium_section": "Premium Section",
        "sources_section": "Sources",
        # Before You Go is this template's defining section (date/location/cost/
        # etc. is the entire reason an Event template exists rather than reusing
        # Standard); ARu Tip stays mandatory for brand consistency across every
        # template.
        "mandatory_sections": ["Before You Go", "ARu Tip"],
        "instructions": _EVENT_INSTRUCTIONS,
    },
    # ARu Studio v4.1 -- dispatched by Articles.Content Type rather than Category
    # (see template_for_content() below). Basic Article (Content Type's default)
    # deliberately has no entry here -- it maps straight back to "standard",
    # unchanged, exactly as every pre-v4.1 article already behaves.
    "headline": {
        "section_order": ["Hook", "Basic Answer", "ARu Tip", "Sources"],
        "primary_sections": ["Hook", "Basic Answer", "ARu Tip"],
        "secondary_sections": [],
        "premium_section": None,
        "sources_section": "Sources",
        "mandatory_sections": ["ARu Tip"],
        "instructions": _HEADLINE_INSTRUCTIONS,
    },
    "deep_guide": {
        "section_order": ["Basic Answer", "More Details", "Cultural Background", "Step-by-Step Guide",
                           "ARu Tip", "Common Mistakes", "Things to Know", "FAQ", "Premium Section", "Sources"],
        "primary_sections": ["Basic Answer", "More Details", "Cultural Background", "Step-by-Step Guide",
                              "ARu Tip", "Common Mistakes", "Things to Know"],
        "secondary_sections": ["FAQ"],
        "premium_section": "Premium Section",
        "sources_section": "Sources",
        "mandatory_sections": ["ARu Tip", "Step-by-Step Guide"],
        "instructions": _DEEP_GUIDE_INSTRUCTIONS,
    },
    "premium": {
        "section_order": ["Premium Overview", "Detailed Walkthrough", "Insider Tips", "Cultural Background",
                           "ARu Tip", "Sources"],
        "primary_sections": ["Premium Overview", "Detailed Walkthrough", "Insider Tips",
                              "Cultural Background", "ARu Tip"],
        "secondary_sections": [],
        # The whole article is already the Premium tier -- no separate inner
        # Premium Section on top of that.
        "premium_section": None,
        "sources_section": "Sources",
        "mandatory_sections": ["ARu Tip"],
        "instructions": _PREMIUM_INSTRUCTIONS,
    },
    "update_notice": {
        "section_order": ["What Changed", "Why It Changed", "What This Means For You", "ARu Tip",
                           "Premium Section", "Sources"],
        "primary_sections": ["What Changed", "Why It Changed", "What This Means For You", "ARu Tip"],
        "secondary_sections": [],
        "premium_section": "Premium Section",
        "sources_section": "Sources",
        "mandatory_sections": ["What Changed", "ARu Tip"],
        "instructions": _UPDATE_NOTICE_INSTRUCTIONS,
    },
    # Dispatched by Story Bank's Content Category = "食事制限" (see
    # template_for_content()), not by Content Type -- a topical template, not
    # a depth-tier one. Safety-critical content: two mandatory sections
    # instead of the usual one, and its own dedicated anti-fabrication
    # placeholder (FOOD_SAFETY_UNCERTAIN_PLACEHOLDER) since a wrong claim
    # here (e.g. "this is pork-free") can cause real harm, not just a stale
    # fact.
    "food_restriction": {
        "section_order": ["対象となる食事制限", "日本で注意する食材", "見落としやすい原材料",
                           "店舗で確認する質問", "日本語での伝え方", "表示の見方",
                           "緊急時の対応", "公式または信頼できる情報源"],
        "primary_sections": ["対象となる食事制限", "日本で注意する食材", "見落としやすい原材料",
                              "店舗で確認する質問", "日本語での伝え方", "表示の見方", "緊急時の対応"],
        "secondary_sections": [],
        "premium_section": None,
        "sources_section": "公式または信頼できる情報源",
        "mandatory_sections": ["対象となる食事制限", "緊急時の対応"],
        "instructions": _FOOD_RESTRICTION_INSTRUCTIONS,
    },
}

# QA Card Template: guidance for curating Story Bank's QA Question / Short
# Answer fields (plain properties, not a Body blob -- there is no
# parse_body_sections()/render step for these). Deliberately NOT wired into
# any auto-generation script: per the 2026-07-18 Story Bank content-ownership
# rule, ChatGPT curates Story Bank content and Claude Code only imports/
# implements -- this constant exists so a human editor (or ChatGPT, working
# from this same spec) has a single documented rubric, not so Claude Code can
# auto-fill QA Question/Short Answer itself.
QA_CARD_INSTRUCTIONS = """Story BankのQA Question／Short Answerを作成する際のガイドライン（AIによる自動生成には使用しない——ChatGPT側での企画・選定、または人間編集者による作成を想定）。

QA Question: ユーザーが実際に検索・質問しそうな形の一文（「〜できますか？」「〜はどうすればいい？」等の自然な疑問文）。ProblemフィールドとSearch Intentフィールドの内容と整合していること。

Short Answer: 3行以内の直接回答。Article Needed／Deep Article Neededの判断材料になる——この短答だけで実用上足りる場合はArticle Neededをオフのままにしてよい。"""

# Existing Article Revision Template: an editorial checklist for revising an
# already-published Article (as opposed to Law/Policy Update Template below,
# which is the public-facing article a reader sees). Process guidance, not
# an AI-generation instructions string.
EXISTING_ARTICLE_REVISION_CHECKLIST = """既存記事を改訂する際の編集チェックリスト。

1. Previous Informationへ、変更前の該当箇所をそのまま保存する（要約せず原文に近い形で）
2. Current Informationへ、変更後の内容を記載する
3. Change Reasonへ、変更理由を記載する（Law Updateが起点の場合はそのLaw Updateへのリンクも残す）
4. 本文（Body）を実際に書き換える
5. Current Validityを Review Due/Outdated から Current へ戻す（Law Update Pipelineのstep Hがこれを検知してVersion・Last Verified Dateを自動更新する）
6. Translation側にNeeds Re-Translation=trueが立っていないか確認する（Law Update Pipelineのstep Gが該当記事のTranslationに自動で立てる）"""


def get_template(name="standard"):
    """Look up a registered article template definition by name."""
    return TEMPLATES[name]


def template_for_category(category):
    """Maps an Article/Research Category to the template name that should
    generate/parse/render/migrate-check it. Centralized here so every
    consumer (generation, review, rendering, migration reporting) resolves
    the same Category -> template mapping rather than each re-implementing
    it -- a repeat of the Category/Sub Category naming-consistency lesson
    from the Architecture Specification."""
    if category == "イベント":
        return "event"
    return "standard"


def template_for_content(category, content_type=None, content_category=None):
    """ARu Studio v4.1: richer dispatch than template_for_category() alone,
    layering Content Type (Headline/Basic Article/Deep Guide/Premium/Update
    Notice) and Story Bank's Content Category ("食事制限") on top of it.

    Precedence: Content Category="食事制限" (a topical template) wins over
    Content Type (a depth-tier template) -- same relationship "event" already
    has over "standard" via template_for_category(). If neither applies,
    falls back to template_for_category(category) unchanged, so every
    existing article (Content Type unset, i.e. pre-v4.1) resolves exactly as
    before this function was added.
    """
    if content_category == "食事制限":
        return "food_restriction"
    if content_type == "Headline":
        return "headline"
    if content_type == "Deep Guide":
        return "deep_guide"
    if content_type == "Premium":
        return "premium"
    if content_type == "Update Notice":
        return "update_notice"
    return template_for_category(category)


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
