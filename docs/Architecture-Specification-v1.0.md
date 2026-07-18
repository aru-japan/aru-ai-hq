<title>ARu Studio Architecture Specification v1.0</title>

# ARu Studio Architecture Specification
### v1.0 — ARu Studioの権威あるアーキテクチャ仕様書

| | |
|---|---|
| **Status** | Active |
| **Date** | 2026-07-18 |
| **対象読者** | このリポジトリのアーキテクチャに関わるすべてのAI・人間 |
| **位置づけ** | 本書は「ARu Studioがどう構造化されているか（What／Why）」の権威ある仕様書。日々の運用手順は[Studio-Operating-Manual.md](./Studio-Operating-Manual.md)、編集運用SOPは[Operating-Manual.md](./Operating-Manual.md)、統治原則は[ARu Constitution](./ARu-Constitution.md)、実装カタログは[AI-Handover.md](./AI-Handover.md)・[Automation Scripts](./Automation-Scripts.md)を参照。矛盾する場合はARu Constitutionが最上位 |
| **成熟度の凡例** | ✅ 実装済み・実データで確認済み ／ 🔶 部分実装・一部のみ既存 ／ 🧭 設計合意済みだが未実装（本書はこれらも含めて権威ある仕様とするが、実装状況を偽らない） |

> 本書は、Version 4準備作業（Freshness Monitor〜ARu Intelligence Phase 3〜テンプレート再設計）と、その後の一連のアーキテクチャ議論（4レーンSource Discovery構想、Event Data Model、Knowledge Architecture、Category／Sub Category階層化）を1つの仕様書に統合したものである。**実装済みの内容と、合意はされたがまだ実装されていない内容を、成熟度タグで明確に区別する。**

---

## 1. Vision

ARu Studioは、ARu（外国籍の方が日本で安心して暮らし・旅行し・働けるようにサポートするAIプラットフォーム、コンセプト「Decode Japan」）を支える編集部の運営基盤である。

本書が定めるアーキテクチャの目的は、[Studio-Operating-Manual.md §9 Editorial Philosophy](./Studio-Operating-Manual.md#editorial-philosophy)が定義する4つの動詞——**Discover（発見）、Verify（検証）、Organize（整理）、Deliver（届ける）**——を、場当たり的な機能追加の集合ではなく、**一貫した知識アーキテクチャ**として実現することにある。

ARu Studioは「記事を作る工場」ではない。**日本についての検証済みの知識を継続的に蓄積し、その知識から複数の成果物（記事・翻訳・SNS投稿・将来的なプッシュ通知等）を生成し続ける、知識基盤**である。この一文が、本書全体の設計判断の基準になる。

---

## 2. Design Principles

### 既存の原則（[AI-Handover.md](./AI-Handover.md) ■ Design Principlesより、✅ 既に確立済み）

1. **Constitution First**：[ARu Constitution](./ARu-Constitution.md)が最上位の権威。コードとConstitutionが矛盾する場合、直すべきはコード
2. **No New Database**：新規データベースの追加は、Rei個別確認を経てからのみ。既存DB・既存プロパティの拡張をまず検討する
3. **Human Review First**：Update Level 2・3のコンテンツは、AIのスコアに関わらず人間の最終承認が必須。コードで強制される制約であり方針ではない
4. **Provider Agnostic**：AI呼び出しは`scripts/ai_gateway.py`経由。Claude/OpenAIどちらか一方に決め打ちしない
5. **Quality First**：生成コンテンツはArticle／Translation／SNSそれぞれ5観点でスコアリングしてから次工程へ進める

### 本書で新たに形式化する原則（🧭 一連のアーキテクチャ議論を通じて合意されたが、明文化は本書が初）

6. **Verify Once, Reuse Everywhere**：同じ事実（日時・場所・費用等）は1箇所でのみ検証し、そこから派生するすべての成果物（記事・SNS・プレミアム等）がその検証結果を再利用する。同じ事実を複数箇所で個別に検証し直さない
7. **Prefer Logical Unification Over Physical Consolidation**：複数のデータベースが同じ役割を果たす場合、物理的に1つのDBへ統合するのではなく、共通のプロパティ契約（Universal Properties）と生成ロジックで論理的に統一する。実データを持つ既存DBの統合は、意図しないデータ損失・リレーション破損のリスクを伴うため最終手段とする
8. **Deterministic Logic Over AI Judgment（Where Possible）**：優先順位付け・スコアリング等、機械的に計算可能な判断はAIに委ねず決定論的なロジックで行う（`research_prioritizer.py`／`editorial_planner.py`の既存設計と同じ考え方）。AIは事実の要約・生成に集中させ、意思決定そのものはコードかRei自身に委ねる
9. **Honest Maturity Labeling**：設計上の到達点（アーキテクチャの理想形）と、現在の実装状況は常に区別して記録する。実装されていない機能を実装済みであるかのように書かない（本書自体がこの原則の実践例）
10. **Don't Fabricate — Explicit "Not Confirmed" Over Guessing**：確認できない情報（英語対応の有無等）は、AIに推測させず「未確認」と明記する。Sourcesセクションの既存方針をシステム全体の原則へ一般化したもの

---

## 3. Knowledge Architecture

### 概要

ARu Studioの知識は、単一のデータベースではなく、**4つの専門化されたKnowledge Domain**に分散して保持される。これらを総称して**Knowledge Hub**と呼ぶ。Knowledge Hubは物理的な1つのテーブルではなく、**共通のUniversal Properties（5節）と生成パイプライン（7節）によって束ねられた論理的な集合**である（Design Principle 7）。

### 4つのKnowledge Domain（✅ 実データで確認済み。`notion-build/create_*.py`を実際に確認して記載）

| Knowledge Domain | 役割 | ライフサイクル（Status値） |
|---|---|---|
| **Experience Intelligence** | まだ記事化されていない信号——ギャップ・機会・トレンド・ユーザーの需要を発見する層。Knowledge Hubへの最も上流の入口 | New → Reviewing → Acknowledged → Actioned → Converted／Resolved／Rejected／**Expired** |
| **Research** | 記事化を検討する候補知識。最も汎用的な入口で、Categoryが7分類（法律・制度／イベント／日本文化／旅行情報／生活情報／ニュース／トレンド）と最も広い | New → Reviewing → Converted／Rejected |
| **Law Update** | 法改正・行政情報という高リスク領域専門のKnowledge Domain。コンプライアンス追跡に特化 | Monitoring → Confirmed → Reflecting to Article → Article Published → Archived |
| **Event Calendar** | 日付・場所を持つ体験（祭り・イベント・季節企画）専門のKnowledge Domain | Planning → Confirmed → Promoting → Completed／Cancelled |

**4つのライフサイクルの形はそれぞれ異なり、終端の意味も異なる**（例：Experience Intelligenceのみ「Expired」という時間経過による自然消滅の終端を持つ）。この違いこそが、4つを物理的に1つのDBへ統合すべきでない実証的な根拠である（Design Principle 7）。

### Knowledge Hubとしての統一（🧭 概念として合意済み、生成パイプライン側のドメイン非依存化はまだ実装されていない）

今日時点で、実際に稼働している生成パイプライン（`generate_article_pipeline.py`）はResearchを主たる入力として設計されている。Law Update・Event Calendarは、それぞれ`Affected Articles`／`Related Article`という形でArticlesと接続されているが、**Research→Articleのような専用の自動生成スクリプトは、Law Update・Event Calendarにはまだ存在しない**。「4つのDomainのどれから来た知識でも同じ生成ロジックで扱える」というKnowledge Hubの理想は、Universal Propertiesという土台（✅ 既に存在）の上に、まだ構築されていないドメイン非依存の生成層（🧭）として残っている。

### 既知の不整合（🔶 実装時に解消すべき項目として記録）

Articlesへのリレーション名が Domain ごとに異なる：Research＝`Converted Article`、Law Update＝`Affected Articles`、Event Calendar＝`Related Article`。ドメイン非依存の生成パイプラインを実装する際は、この命名差を吸収する薄いアダプタ層、または名称そのものの統一が必要になる。

---

## 4. Editorial Content Lifecycle

コンテンツが「発見」から「アーカイブ」までたどる全体の流れは、[Studio-Operating-Manual.md §9](./Studio-Operating-Manual.md#9-editorial-content-lifecycle)が権威ある定義であり、本書では重複させない。13段階（①Source Discovery〜⑬Archive）とその成熟度タグは同節を参照すること。

本書（Knowledge Architecture）との対応関係のみ、ここで明記する。

| Editorial Content Lifecycleの段階 | 対応するKnowledge Domain |
|---|---|
| ①Source Discovery | Source Library（Knowledge Domainの外、情報源そのものの台帳） |
| ②Research Candidate | Experience Intelligence（発見）→ Research（候補化） |
| ③Category Classification | Research（Category）／Law Update（Jurisdiction）／Event Calendar（Type）——各Domainが自身の分類体系を持つ |
| ⑤Standard Article・⑥Premium Article | Articles（4つのKnowledge Domainいずれからも生成され得る、7節参照） |
| ⑫Periodic Update・⑬Archive | Law Update（Archived状態あり）／Event Calendar（Completed／Cancelled、将来的なDormantモデルは9節参照） |

---

## 5. Universal Properties

4つのKnowledge Domainの実際のスキーマ（`create_research.py`／`create_law_update.py`／`create_event_calendar.py`／`create_experience_intelligence.py`）を比較し、共通性の実態を正確に記録する（✅ 実データ）。

### 完全に共通（4つ全てに存在）

`Record ID`（Domainごとに異なるprefix：RES／LAW／EVT／EXI）、`Tags`、`Priority`、`Urgency`、`Trust Score`、`Recommendation Score`、`AI Generated`、`Human Reviewed`、`Last AI Update`、`Confidentiality`、`Usage Scope`

### 概念は共通だが命名が異なる（🔶 要harmonization）

| 概念 | Research | Law Update | Event Calendar | Experience Intelligence |
|---|---|---|---|---|
| 対象読者 | `Audience` | `Impact Scope` | `Audience`／`Recommended Audience`（2つ存在） | `Audience`／`Affected Audience` |
| Articlesへの接続 | `Converted Article` | `Affected Articles` | `Related Article` | `Related Article` |

### 一部のDomainのみに存在（🔶 部分的な共通性）

| プロパティ | 存在するDomain |
|---|---|
| `QA Status`／`Verification Status`／`Review Level` | Research, Law Update のみ |
| `Season` | Research, Event Calendar, Experience Intelligence（Law Updateにはなし＝法改正に季節性は通常ないため妥当） |
| `Archived Date` | Law Update, Event Calendar, Experience Intelligence（Researchにはなし＝ResearchはConverted/Rejectedが終端でArchiveという概念自体がない） |
| `Related Constitution Version` | Research, Law Update, Event Calendar（Experience Intelligenceにはなし） |

**この非対称性は不具合ではなく、多くは各Domainの性質を正しく反映している**（例：Researchに`Archived Date`がないのは妥当）。ただし`Audience`／`Impact Scope`のような**同じ概念への異なる命名**は、ドメイン非依存の生成パイプラインを構築する際の障害になるため、6節・7節の実装時に統一を検討すべき項目として記録する。

---

## 6. Category & Sub Category Principles

### 現状（✅ 実データ）

Categoryという分類体系を持つのは現状**Researchのみ**（法律・制度／イベント／日本文化／旅行情報／生活情報／ニュース／トレンドの7値、フラットなSelect）。Event Calendarは`Type`という類似の役割を持つ独自分類（祭り／花火大会／フードフェス等9値）を持つ。Law Updateは`Jurisdiction`（国／都道府県／市区町村）という別の軸で分類する。Experience Intelligenceは`Intelligence Type`（Event／Culture／Trend／Local／Gap／Opportunity／User）を持つ。

### 課題

トップレベルのCategory値を「Medical」「Language」のように増やし続けると、粒度の粗い分類が無限に肥大化する（例：「法律・制度」1つに入管法・税法・労働法・健康保険法が同居する）。

### 提案する方向性（🧭 設計合意済み、未実装）

**Category（大分類、少数で安定）＋ Sub Category（Categoryごとに意味を持つ小分類）の2階層化**を、まずResearchに導入する。

- 例：`Category=法律・制度` → `Sub Category`候補：入管・ビザ／税務／労働／健康保険／年金 等
- 例：`Category=日本文化` → `Sub Category`候補：言語・コミュニケーション／作法・マナー／祭事・伝統 等（**Languageの置き場所**）
- 例：`Category=イベント` → `Sub Category`候補：観光・体験／コミュニティ／日本語交流／外国人支援／学生向け 等
- 例：`Category=トレンド` → `Sub Category`候補：SNSトレンド／人気スポット／季節グルメ／PR情報 等

### Sub Categoryと既存の議論との関係（重要な整理）

これまで議論した**「4レーン（Official／Events & Seasonal／User Needs／Trending & Lifestyle）」は分類軸ではなく発見メカニズムの軸であり、Category／Sub Categoryとは直交する**。レーンは「どうやって見つけたか」、Category／Sub Categoryは「何についての知識か」を表す。4レーン構想を別の分類体系として重ねる必要はなく、いずれの発見レーンから来た知識も、最終的にCategory／Sub Categoryのどこかに着地する。

### 技術的制約（✅ 既知の制約、AI-Handover.md Known Limitationsと同種）

NotionパブリックAPIには「親のSelect値に応じて子のSelect選択肢を絞り込む」機能がない。Sub Categoryを実装する場合、`source_categories.py`の`classify_update()`と同じパターン（Category→有効なSub Categoryのリストをコード側で保持し、AIの出力を検証・不正な組み合わせは却下する）が必須になる。

### 既存の`Tags`との役割分担

`Tags`（自由入力multi_select、4 Domain全てに既存）は横断的・その都度のラベル付けを担い続ける。Sub Categoryは安定した公式の階層を担う。両者に同じ役割を持たせない。

---

## 7. Generation Rules

### 既存の生成モデル（✅ 実装済み、チェーン型）

```
Research → Article（generate_article_pipeline.py article）
        → Translation（generate_article_pipeline.py translation）
        → SNS（generate_article_pipeline.py sns）
```
各段階は前段階の**出力**（主にArticle本文）を入力として次を生成する。

### 提案する追加モデル（🧭 設計合意済み、未実装：ハブ＆スポーク型）

日付・場所等の構造化された事実を持つコンテンツ（Event Calendar由来の知識が典型）では、チェーン型の代わりに、**単一の検証済みKnowledge Domainレコードから複数の成果物が並行して生成される**モデルを適用する。

```
Event Calendarレコード（単一の真実源）
   ├─→ Event Article（Articles、Event Article Template使用）
   ├─→ Premium Section（Articleの一部）
   ├─→ Instagram Post／Threads Post（SNS Queue）
   ├─→ Push Notification（実現性はSNS Queueの新Platform値として検討、8節参照）
   └─→ Event Calendarエントリ自体（＝この記録そのもの、生成不要）
```

**重要な非対称性**：Translationは他のスポークと同列ではない。Translationは常に**完成したArticle本文の子**であり（翻訳対象がプローズである以上、構造上Articleに従属する）、Knowledge Domainから直接並行生成できるSNS／Push／Premium Sectionとは性質が異なる。

### Verify Once, Reuse Everywhereの適用（Design Principle 6）

ハブ＆スポーク型では、事実の検証（日時・場所・現金対応・英語対応等）はKnowledge Domainレコードの段階で一度だけ行う。各成果物固有のレビュー（`reviewer_agent.py`のトーン・構成チェック、`sns_quality_reviewer.py`のプラットフォーム適合チェック）は個別に必要だが、**事実そのものを再検証する必要はない**。ただし、事実の誤りは全成果物へ同時に波及するため、Knowledge Domain段階での人間検証の重要性は従来のチェーン型より高くなる。

### Event Article Template（🧭 設計合意済み、未実装）

標準の8セクションテンプレート（Basic Answer／More Details／Cultural Background／ARu Tip［必須］／Things to Know／FAQ／Premium Section／Sources）は永続する疑問向けであり、日付を持つイベントには適さない。以下の8セクション構成を提案する。

| # | セクション | 標準との対応 |
|---|---|---|
| 1 | Before You Go［必須］ | Basic Answerを置き換え。日時・場所・費用・予約要否・現金対応・英語対応・荒天時対応を構造化して即座に提示 |
| 2 | What to Expect | More Detailsを改名 |
| 3 | Cultural Background | 不変 |
| 4 | Who This Is For | FAQを置き換え。観光客／在住者／学生／家族等の適合読者を明示 |
| 5 | ARu Tip［必須］ | 不変 |
| 6 | Cautions & Accessibility | Things to Knowを改名・特化 |
| 7 | Premium Section | 不変 |
| 8 | Sources［必須］ | 不変 |

「English Support」等、確認しようがない事実はDesign Principle 10に従い「未確認」をデフォルトとし、公式サイトに多言語対応の明記がある場合のみ「あり」と記載する。

### Dormant → Needs Update → Published（🧭 設計合意済み、未実装）

毎年開催されるイベントは`Archived`ではなく新設の`Dormant`状態を経由する。

```
Published（開催前〜開催中）→ Dormant（新設）→（次回開催時期が近づく）→ Needs Update（既存状態を再利用）→ Published（ループ）
```

「毎年恒例か」は AI に推測させず編集者が手動でRecurrenceを設定し、「次回開催時期」は前回開催日からの単純な日付計算（Design Principle 8）で見積もる。2年連続で復活しなかった場合も自動Archiveはせず、人間の判断を仰ぐ（Human Review First原則の拡張適用）。

---

## 8. Architectural Constraints

### Notion API起因の制約（✅ 既存、[AI-Handover.md](./AI-Handover.md) Known Limitationsより）

- View・Templateの作成・設定はAPIから不可能。手動設定が必須（[View-Template-Guide.md](./View-Template-Guide.md)）
- 既存Linked Viewの設定（Filter／Sort）はAPIから読み取れない
- ページのプロパティパネルのグループ化・折りたたみもAPIから設定不可
- Select型の子オプションを親の値で絞り込む機能がない（6節のSub Category実装時の制約）

### 組織的な制約（✅ 既存）

- **No New Database**：新規DB追加はRei個別確認が前提（Design Principle 2）
- **ARuアプリ本体はこのリポジトリの管理範囲外**：Push Notificationの実現可能性、アプリ内検索ログの利用可能性は、いずれもアプリ側の機能実装に依存し、このリポジトリからは制御できない
- **GitHubへのPushはこの実行環境から非対話認証できない**：人間が自身のターミナルで一度認証を通す必要がある（[Studio-Operating-Manual.md §4](./Studio-Operating-Manual.md#4-release-session)）

### ガバナンス上の制約（✅ 既存、Constitutionでコード上も強制）

- Update Level 2・3のコンテンツはAIスコアに関わらず人間の最終承認必須
- AIは公開（Published）そのものを実行しない
- 情報源を捏造しない。確認できない場合は「未確認」と明記する（Design Principle 10）

---

## 9. Future Extension Guidelines

### 4レーンSource Discoveryモデル（🧭 長期構想として保留、実運用による再検討待ち）

Official Sources／Events & Seasonal／User Needs／Trending & Lifestyleの4レーン構想は、Lane 1・Lane 2の実運用を数週間経てから再検討する方針で合意済み（Lane 0＝User Needs、Lane 3＝Trending & Lifestyleは保留中）。**この構想を「Version 5」と呼ばないこと**——[Roadmap.md](./Roadmap.md)が既にVersion 5「Global」（海外展開）を定義しているため、名称衝突を避ける必要がある。正式に着手する際は独立した名称（例：「Source Discovery Expansion」）を用いること。

### Category拡張の指針

新しい知識領域（Medical、Language等）が必要になった場合、**まずSub Categoryとして既存Categoryの下に置けないかを検討する**。トップレベルCategoryの追加は最終手段とする（6節）。

### 新規Knowledge Domainの指針

新しい知識領域が既存4 Domainのいずれにも収まらない場合でも、**新規データベースの作成より前に、既存Domainのプロパティ拡張で対応できないかを検討する**（Design Principle 2・7）。

### 既知の宿題（優先度順、実装時に着手）

1. Articlesへのリレーション名の統一（`Converted Article`／`Affected Articles`／`Related Article`）
2. `Audience`／`Impact Scope`の命名統一
3. Sub Categoryの正式な値リストの確定とコード側バリデーションの実装
4. Event Article Template・Before You Go・Dormantライフサイクルの実装（Lane 2パイロットの一部として）
5. Push Notificationの技術的実現可能性の調査（ARuアプリチームとの確認が前提）

---

## Appendix A – Glossary

本書内で使われる主要な建築用語を定義する。既存ドキュメントで定義済みの用語（Update Level、Constitution等）は参照のみとし、ここでは再定義しない。

| 用語 | 定義 |
|---|---|
| **Knowledge Hub** | Research／Law Update／Event Calendar／Experience Intelligenceの4つのKnowledge Domainを束ねる論理的な集合。物理的な単一DBではなく、共通のUniversal Propertiesと生成パイプラインによって成立する概念（3節） |
| **Knowledge Domain** | Knowledge Hubを構成する4つの専門データベースのそれぞれ（Research／Law Update／Event Calendar／Experience Intelligence）。各Domainは独自のライフサイクルとドメイン固有プロパティを持つ（3節） |
| **Universal Properties** | 4つのKnowledge Domainに（完全に、または部分的に）共通して存在するプロパティ群（`Record ID`／`Trust Score`／`Priority`等）。Knowledge Hubを論理的に束ねる土台（5節） |
| **Category／Sub Category** | コンテンツの内容領域を表す2階層の分類体系。Categoryは少数で安定した大分類、Sub Categoryはその下にぶら下がる細分類（6節） |
| **Lane（発見レーン）** | 知識をどうやって発見するかの軸（Official Sources／Events & Seasonal／User Needs／Trending & Lifestyle）。Category／Sub Categoryとは直交する別の軸であり、分類体系そのものではない（6節・9節） |
| **Chain Model（チェーン型生成）** | 既存の生成パイプラインの形。Research→Article→Translation→SNSのように、各段階が前段階の**出力**を入力として次を生成する（7節） |
| **Hub-and-Spoke Model（ハブ＆スポーク型生成）** | 提案されている生成モデル。単一の検証済みKnowledge Domainレコード（ハブ）から、Article・SNS・Push等の複数の成果物（スポーク）が並行して独立に生成される（7節） |
| **Verify Once, Reuse Everywhere** | 同じ事実は1箇所でのみ検証し、そこから派生する全成果物がその検証結果を再利用するという設計原則（Design Principle 6） |
| **Event Data Model** | Event（イベント）をArticleの一種ではなく、それ自体で構造化された知識単位として扱う設計。Content Data Modelへ一般化される前の、Events限定の初期構想（7節の前身） |
| **Event Article Template** | 標準8セクションテンプレートに代わる、イベント専用の8セクション構成（Before You Go／What to Expect等）。日付・場所を持つコンテンツに最適化されている（7節） |
| **Dormant（休眠状態）** | 毎年開催される等の反復イベントが、開催終了後にArchiveされず「次回開催時期まで眠る」状態を表す、提案中の新しいPublishing Status値（7節） |
| **成熟度インジケーター（✅／🔶／🧭）** | ある機能・設計が「実装済み」「部分実装」「設計合意済みだが未実装」のいずれかを示すタグ。[Studio-Operating-Manual.md §9](./Studio-Operating-Manual.md#9-editorial-content-lifecycle)で初めて導入され、本書全体で踏襲している |
| **No New Database（原則）** | 新規データベースの追加はRei個別確認を経てからのみ行うという既存の設計原則（Design Principle 2）。本書の複数の評価（Event Calendar汎用化の却下、物理統合の却下）の判断基準になっている |

---

## Appendix B – Architecture Decision Log

これまでのアーキテクチャ議論で下した主要な決定を、決定順に記録する。**却下された案も、なぜ却下したかを含めて残す**——同じ議論を将来繰り返さないための記録である。

| # | 決定事項 | ステータス | 根拠（要約） |
|---|---|---|---|
| 1 | 情報収集は「監視ベース」と「ギャップ分析ベース」の2レーンモデルとして整理する | **Accepted** | 既存の`source_watcher.py`（監視）と`coverage_analyzer.py`／`editorial_planner.py`（ギャップ分析）が、既にこの2つの性質で実装されていたため、新しい概念ではなく既存実装の正確な言語化として採用 |
| 2 | Source Library拡張は「Official Sources」優先、Visaは代替取得経路が必要、Trending Topicsは既存モデルに合わない | **Accepted（実装は未着手）** | 政府系サイトはページ差分検知モデルに適合するが、外務省（Visa）はbot対策でフェッチ不可、トレンド情報はランキング型データでページ差分モデル自体が適さない |
| 3 | Source Discoveryを4レーン（Official／Events & Seasonal／User Needs／Trending & Lifestyle）に拡張する | **Accepted as long-term concept（実装は保留）** | 単なる情報源監視の拡張ではなく、ARuを「日本発見エンジン」にするという編集方針の転換を反映するため、大きな設計変更として合意はするが、実運用の検証を経てから着手する方針に |
| 4 | 4レーン構想を「Version 5」と呼ぶ | **Rejected** | `Roadmap.md`が既にVersion 5「Global」（海外展開）を定義しており、名称衝突を避けるため。ARu Intelligence Phase 1〜3がVersion 4 Phaseとの衝突を避けた前例と同じ理由 |
| 5 | 直近はLane 1（Official）・Lane 2（Events & Seasonal）の強化のみに集中し、Lane 0（User Needs）・Lane 3（Trending & Lifestyle）は保留する | **Accepted** | 実運用データが少ない段階で4レーン全てに投資するより、既存アーキテクチャに適合するレーンから確実に価値を出す方が合理的と判断 |
| 6 | Lane 2のPilot Editorial Sessionとして、観光系5情報源（JNTO／GO TOKYO／隅田川花火大会実行委員会／京都市観光協会／大阪観光局）を選定する | **Accepted（WebFetch実在確認は未実施）** | 「quality over quantity」の方針のもと、全国／首都圏／単一象徴イベント／伝統文化／食文化という異なる編集価値を重複なくカバーするよう選定 |
| 7 | Community events・Support events向けにCLAIRを1情報源として追加し、Language exchange（国際交流基金）・Student events（JASSO）を個別に追加する（4カテゴリに対し+3情報源） | **Accepted（実装は未着手）** | Community eventsとSupport eventsは同じ地域国際化協会ネットワークが発信元であることが多く、4カテゴリ機械的に4情報源を割り当てるより実態に即した統合ができるため |
| 8 | 標準記事テンプレートとは別に、Event Article Template（8セクション）を新設する | **Accepted（未実装）** | イベントは「永続する疑問への回答」ではなく「日時・場所を持つ、期限のある実用情報」であり、標準テンプレートの前提と根本的に合わないため |
| 9 | 「Before You Go」チェックリストは独立セクションではなく、既存のQuick Factsへ統合する | **Accepted（未実装）** | 「チェックリスト」は"事実の一覧"であり"読み物"ではなく、Quick Factsとの役割重複が大きいため。標準テンプレートとの8セクション対称性も維持できる |
| 10 | 反復イベントは`Archived`ではなく新設の`Dormant`状態を経由し、次回開催時期には既存の`Needs Update`状態へ遷移させる | **Accepted（未実装）** | 「Reactivate」「Update」は既存の`Needs Update`＋人間レビューフローの再利用で足り、本当に新しい状態は`Dormant`1つで済むと判断したため |
| 11 | Event限定の「Event Data Model」を、単一の真実源から複数成果物を生成するハブ＆スポーク型として設計する | **Superseded by #13** | Events専用として妥当な設計だったが、後の議論でARuの全コンテンツ種別に一般化すべきという方針転換があったため、より広い「Content Data Model」構想に引き継がれた |
| 12 | 既存のEvent CalendarをそのままContent Hub（汎用知識ハブ）へ進化させる | **Rejected** | Event Calendarの中核プロパティ（`Event Date`／`Rain Policy`／`Repeat Schedule`）が本質的に日付を前提としており、Culture・Medical・Languageのような永続的な知識には構造的に適合しないため |
| 13 | Events限定のContent Data ModelをARuの全コンテンツ種別（Events／Laws／News／Culture／Medical／Travel／Daily Life／Language）に一般化する | **Accepted as direction** | 検証済み知識を単一の真実源から複数生成するという設計思想自体はEvents固有のものではなく、全コンテンツ種別に適用できる普遍的な価値があると判断 |
| 14 | Research／Law Update／Event Calendar／Experience Intelligenceを1つの物理データベースへ統合する | **Rejected** | 4つのライフサイクルの形・終端がそれぞれ異なり、無理に1つの`Status`へ統合すればいずれかの意味を歪める。実データを持つ既存DBの統合はデータ損失・リレーション破損のリスクも伴うため、Design Principle 7（論理統合を優先）を新設する根拠になった |
| 15 | 4つのKnowledge Domainを「Knowledge Architecture」として正式に形式化し、共通層はDBではなくUniversal Propertiesと生成パイプラインであると明記する | **Accepted** | 各DBの実際のStatus値の違いが物理統合を避けるべき実証的根拠になり、かつ既にUniversal Propertiesという共通の土台が実データとして存在していたため、新しい統合を作るのではなくこの事実を正式なアーキテクチャとして認めることにした |
| 16 | トップレベルCategoryを増やし続けるのではなく、Category＋Sub Categoryの階層構造を導入する | **Accepted as direction（未実装）** | Medical／Languageの置き場所問題と、4レーン議論で出たCommunity/Language Exchange/Support/Student events・Trending & Lifestyleの置き場所問題を、新しい分類体系を足すことなく1つの階層構造で同時に解消できるため |
| 17 | 本仕様書（`Architecture-Specification-v1.0.md`）を権威あるアーキテクチャ仕様として作成する | **Accepted** | これまでの議論で蓄積された設計判断が、複数のチャットのやり取りにのみ存在し、どこにも参照可能な形で記録されていなかったため。実装済みと未実装を成熟度タグで区別する形で1つの文書に統合した |

---

*ARu HQ / Decode Japan — ARu Studio Architecture Specification v1.0 — 2026-07-18*
