<title>ARu HQ Notion Database Builder — Build Spec v1</title>

# ARu HQ Notion Database Builder
### Build Phase — Phase 1 Spec

| | |
|---|---|
| **Status** | In Progress — Phase A **Design Freeze**。Phase B1（Experience Intelligence／Source Library／Source Monitor／Editorial Calendar）設計完了、レビュー待ち |
| **Date** | 2026-07-12 |
| **Source of truth** | [ARu Constitution v2.0.0](./aru-constitution.md) ＋ ARu HQ データベース設計書（本文中は「ER Design」と表記）|
| **Goal** | ①〜⑩を確定させたのち、Claude Codeが Notion API を叩いて一括生成できるスキーマ（JSON/スクリプト）に落とし込む |

> このドキュメントは1回で完成させない。①から⑩まで、1項目ずつ確認を取りながら埋めていく。Claude Codeによる自動生成は、全項目が確定してから着手する。

---

## 進行状況

| # | 項目 | 状態 |
|---|---|---|
| ① | Database一覧 | ✅ 確定 |
| ①.5 | Universal Properties（共通基盤） | ✅ 確定 |
| ② | Property一覧（DB固有） | 🔒 Phase A = Design Freeze／🔶 Phase B着手 |
| ③ | Relation | ⏳ 未着手 |
| ④ | Rollup | ⏳ 未着手 |
| ⑤ | Formula | ⏳ 未着手 |
| ⑥ | Select一覧 | ⏳ 未着手 |
| ⑦ | Status一覧 | ⏳ 未着手 |
| ⑧ | View一覧 | ⏳ 未着手 |
| ⑨ | Template一覧 | ⏳ 未着手 |
| ⑩ | Dashboard構成 | ⏳ 未着手 |

**②の進め方**：全17DBを順番に作るのではなく、重要度順にフェーズへ分割する。

- **Phase A（Core）— 🔒 Design Freeze**：Article／Research／Translation。①〜⑩を完成させ、承認済み。以後、Phase Aへの変更は本ドキュメントの改訂プロセス（ARu Constitution §17/§20と同じ考え方）を経てのみ行う。
- **Phase B（進行中）**：残り13DBを以下の順で設計する。
  - **B1**：Experience Intelligence, Source Library, Source Monitor, Editorial Calendar — ✅ ①〜⑩設計完了、レビュー待ち
  - **B2**：AI Agents, Prompt Library, Automation
  - **B3**：Law Update, Event Calendar, SNS Queue
  - **B4**：Language Master, Region Master
  - **B5**：Mentor, Dashboard

Editorial Calendar（新設DB、詳細は①参照）はB1に含めて設計する。Experience Intelligenceの「User Intelligence」が検出したコンテンツギャップ・季節性シグナルを、実際の編集スケジュールに変換する役割のため、Experience Intelligenceと同時に設計するのが自然と判断した。

---

## ① Database一覧

ER Design v1.2（Article／Translationの親子構造、Update Level 1〜3、Language Master等）をそのままNotionのDB構成に落とす。今回の指示で以下を反映した。

- **Experience Intelligence** を独自定義のCore Databaseとして確定（詳細は本節末尾）
- **Source Library** に `Source Type` を追加（`Tier` とは別プロパティとして併存）
- **Source Monitor** を新設

### Public / Core（公開層）

| Database | 役割 |
|---|---|
| **Article** | 日本語マスター記事。唯一の公開DB |
| **Translation** | Articleの子DB。言語ごとの翻訳・レビュー・公開状況を管理 |

### Core Intelligence（ARu独自の競争優位性）

| Database | 役割 |
|---|---|
| **Experience Intelligence** | 「今、日本で何を体験すると価値が高いか」をAIが提案するための統合インテリジェンス層。Event／Culture／Trend／Local／Userの5シグナルを1つのDBに統合する |

### Pipeline（記事の生成フローに直結）

| Database | 役割 |
|---|---|
| **Research** | AIによる一次リサーチ。Articleの前段 |
| **Source Library** | 信頼できる情報源のマスター台帳（静的） |
| **Source Monitor**（新設） | Source Libraryの各情報源を定期チェックした稼働ログ（動的）。変更検知の記録 |
| **Law Update** | 法改正・制度変更の専用トラッカー。Significanceを保持 |
| **Event Calendar** | 祭り・フードフェス・地域イベントの専用DB（日付・会場を持つ構造化イベントデータ） |
| **SNS Queue** | Instagram／Threads／Xへの配信キュー |

### Reference（マスタデータ）

| Database | 役割 |
|---|---|
| **Language Master** | 対応言語の一覧。新言語追加の起点 |
| **Region Master**（新設） | 地域の階層マスタ（Country→Region→Prefecture→City→Ward→Area/Spot）。Knowledge Graphの地域軸 |

### Engine Room（編集部の運転席）

| Database | 役割 |
|---|---|
| **AI Agents** | Research／Writer／Translator／SNS／SEO／QC等、AI担当の役割台帳 |
| **Prompt Library** | 各AI Agentの指示書の版管理 |
| **Automation** | n8n等のワークフロー定義と実行ログ |
| **Editorial Calendar**（新設） | 編集部が「いつ・どんな記事を書くか」を管理する編集計画DB。Event Calendar（世の中の実イベント）とは別物。AIの記事不足・季節性分析の受け皿 |

### People（人・信頼）

| Database | 役割 |
|---|---|
| **Mentor** | 専門メンターの台帳。監修・レビュー・承認の担い手 |

### Reporting（読み取り専用）

| Database | 役割 |
|---|---|
| **Dashboard** | 全DBのロールアップを集約する報告レイヤー（Experience Intelligenceの集計も含む） |

**合計：17 Databases**

---

### Editorial Calendar（詳細）

**Event Calendarと混同しないこと。** Event Calendarは「世の中で実際に起きる祭り・イベント」を記録する。Editorial Calendarは「編集部が、いつ、どんな記事を書くか」という**内部の編集計画**を記録する。両者はしばしば連動する（例：ある祭りのEvent Calendarエントリを見て、その2週間前にEditorial Calendarへ「紹介記事を書く」という計画を立てる）が、別の概念であり別のDBとして分離する。

**役割**：AIが「記事が足りていないテーマ」「季節的に今書くべきテーマ」を分析するための受け皿。Experience Intelligence（特にUser Intelligence／Trend Intelligence）が検出したギャップやシグナルを、実行可能な編集タスクへ変換する。

**主要プロパティ**

| Property | Type | 説明 |
|---|---|---|
| Planned Topic | Title | 予定している記事テーマ |
| Category | Select | 想定カテゴリ（role:category） |
| Planned Date | Date | 執筆開始または公開目標日 |
| Status | Select | Idea → Planned → In Progress → Drafted → Published → Skipped/Cancelled |
| Gap Type | **Rollup ← Source Signal.Gap Type** | Knowledge Gap Engineの10種のGap Type（Content/Translation/Region/Seasonal/Audience/Trust/Freshness/Experience/Trend/Legal）をそのまま継承。手動Selectではなく参照元からのRollupとし、二重管理を避ける |
| Linked Article | Relation → Article | 実際に書かれた記事（着手後にリンク） |
| Linked Research | Relation → Research | 元になったリサーチ（あれば） |
| Source Signal | Relation → Experience Intelligence | このプランのきっかけになったsignal |
| Assigned Owner | Relation → Mentor | 担当編集者 |
| Assigned AI Agent | Relation → AI Agents | 執筆・調査を担当するAI |
| Audience / Region / Season | Universal（Multi-select/Relation） | Article側と同じ語彙を使用し、後でLinked Articleへそのまま引き継ぐ |
| Urgency | Universal（Select） | 季節逃し・法改正の施行日接近などをUrgency=Criticalとして扱う |

**Relation**：Article（双方向）、Research（双方向）、Experience Intelligence（双方向）、Mentor（双方向）、AI Agents（双方向）

**View例**：カレンダー表示（Planned Date）、Gap Type別ボード、「季節を逃しそうな計画」フィルタ（Season該当期間が近いのにStatus=Idea/Planned）

**Automation例**：Experience Intelligence（User/Trend）が新しいsignalを検出 → Editorial Calendarへ自動でIdeaレコードを起票。Planned Dateの30日前になってもStatus=Ideaのまま → Owner／編集長へリマインド。

---

### Region Master（詳細）

地域は単なる地名タグではなく、ARuの**知識の軸（Knowledge Graphの一次元）**として扱う。自治体・観光協会・旅行会社・企業との連携、地域別ダッシュボード・おすすめ・イベント・記事・法改正・文化情報のすべてが、この1つのマスタを起点に横断できるようにする。

**階層構造（Region Type）**

```
Country（国）
  ↓
Region（地方）── 北海道／東北／関東／中部／近畿／中国／四国／九州／沖縄
  ↓
Prefecture（都道府県）
  ↓
City（市区町村）
  ↓
Ward（区）── 政令指定都市の区など、必要な場合のみ
  ↓
Area / Spot（エリア／スポット）── 任意。例：浅草、渋谷スクランブル交差点
```

各レコードは `Parent Region`（自己Relation）で1つ上の階層と繋がり、木構造を形成する。

**プロパティ**

| Property | 型 | 説明 |
|---|---|---|
| **Official Name** | Title | 正式名称（日本語） |
| **English Name** | Text | 英語表記 |
| **Slug** | Text/Formula | URL・API連携用のスラッグ（例：`shibuya-ku`） |
| **Region Type** | Select | Country／Region／Prefecture／City／Ward／Area |
| **Parent Region** | Relation（自己） | 1つ上の階層。全国が唯一のルート（Parent Regionなし） |
| **Region Code** | Text | 行政区画コード等（JIS等）。外部GIS/Analytics連携用 |
| **Latitude / Longitude** | Number | 地図表示・GIS連携用の緯度経度 |
| **Timezone** | Select | 現状すべて `Asia/Tokyo` だが、将来の国際展開を見越して保持 |
| **Population** | Number（任意） | 人口。都道府県・市区町村レベルで入力 |
| **Tourism URL** | URL | 観光協会等の公式観光ページ |
| **Official Website** | URL | 自治体等の公式サイト |
| **Official SNS** | Text（複数URL可） | 公式SNSアカウントへのリンク一覧 |
| **JNTO Page** | URL | JNTO（日本政府観光局）における当該地域のページ（Notion外部のためRelationではなくURLとして保持） |
| **Visit Japan Page** | URL | Visit Japan Web等の公式ページ（同上、URLとして保持） |

> **補足**：「JNTO Relation」「Visit Japan Relation」は、NotionのRelationプロパティが同一ワークスペース内のDB同士しか接続できないため、外部の政府観光システムへは **URLプロパティ** として実装する。将来これらの機関とAPI連携する場合は、Automation DB側にその連携定義を持たせる。

**他DBとのRelation**

Region Masterは、Article・Experience Intelligence・Event Calendar・Law Update・Research・Source Libraryの6DBすべてから `Region`（複数選択可）としてRelationされる。Universal Properties §7で仮置きしていた `Region` プロパティは、これで正式にRelation型として確定する。

**Knowledge Graphとしての実装メモ**

Notionのロールアップは1ホップまでしか遡れないため、「東京都のダッシュボード」に渋谷区・新宿区タグの記事も含めたい場合、木構造をそのまま辿るクエリはNotion単体ではできない。10年運用を見据え、以下の方式で解決する。

- Region Masterに `Ancestor Path`（Formula）を持たせ、「全国 > 関東 > 東京都 > 渋谷区」のようなパス文字列を自動生成する。
- 各コンテンツDBのRegion Relationには、タグ付けされた地域そのものに加え、Automation（n8n）がParent Regionを遡って**祖先地域も自動的に追加**する（例：記事に「渋谷区」を付けると、自動で「東京都」「関東」「全国」も併せてRelationされる）。
- これにより、Dashboardは「Region = 東京都を含む記事」を単純なRelationフィルタだけで集計でき、木構造の再帰探索をリアルタイムに行う必要がなくなる。

---

### Experience Intelligence（詳細）

「利用者が知りたいこと」と「日本が伝えたいこと」をつなぐAIインテリジェンス層。**Event Calendarのようなイベント管理DBではない。** Articleと同じ設計思想（1つのDB＋分類プロパティで複数の性質を統合する）を踏襲し、`Intelligence Type` によって6つのシグナルを1つのDBへ統合する。

| Intelligence Type | 内容 |
|---|---|
| **Event** | 祭り・花火大会・フードフェス・蚤の市・マルシェ・地域/季節/期間限定イベント。Event Calendarの構造化データを重複させず、「今それを取り上げる価値」を評価してEvent Calendarへ関連づける |
| **Culture** | 茶道・書道・神社参拝・寺院体験・温泉・着物・和食など、特定の日付に縛られない通年の日本文化体験 |
| **Trend** | Instagram／Threads／X／YouTubeで話題になっている場所・体験のシグナル |
| **Local** | 自治体・観光協会・商店街・地域メディアが発信する、地域固有の魅力 |
| **Gap**（新設） | Knowledge Gap Engineが検出する10種類の知識ギャップ。詳細は本節末尾 |
| **User** | 利用者の検索・AI相談内容・メンター相談内容・記事閲覧履歴・保存・評価を匿名集計した、編集部への提案（「記事が足りない」「この地域情報が人気」等） |

**Relation構成（すべて双方向）**

| 相手DB | 関係の意味 |
|---|---|
| **Research** | Experience Intelligenceが「調査に値する」と判定したsignalがResearchを生む／逆にResearchの過程で見つかった体験価値がここに記録される |
| **Article** | このsignalがすでに記事化されているか、記事化候補かを追跡する |
| **Source Library** | Local／Culture Intelligenceの出典（自治体・観光協会・地域メディア等） |
| **Source Monitor** | Source変化の検知がこのsignalの発生トリガーになった場合のリンク |
| **SNS Queue** | Trend Intelligenceの元になったSNS投稿、またはこのsignalから生成すべきSNS投稿 |
| **Dashboard** | 「注目地域トップN」「コンテンツギャップ件数」等のロールアップ元。Dashboard側からのRelationとして実装し、Rollupの起点にする |
| **Editorial Calendar**（新設・追加） | User／Trend Intelligenceが検出したギャップやシグナルが、実際の編集スケジュールに変換される際のリンク元 |

---

### Knowledge Gap Engine（Experience Intelligenceの中核機能）

**理念**：Knowledge Gap Engineは分析ツールではなく、ARu編集部の**「編集会議AI」**である。AIの役割は記事を書くことではなく、「次に何を書くべきか」「何を更新すべきか」「どこに情報不足があるか」を、毎日、編集長（Rei）へ提案することにある。

検出結果は `Intelligence Type = Gap` のExperience Intelligenceレコードとして記録される。Gap固有のプロパティは以下の通り（Intelligence Type=Gapのときのみ意味を持つ）。

| Property | Type | 説明 |
|---|---|---|
| **Gap Type** | Select | 下記10種類 |
| **Gap Severity** | Universal `Urgency` を流用（Critical/High/Medium/Low） | Legal Gapは検出時に自動でCriticalとなる |
| **Metric / Evidence** | Text | 検出根拠の数値・事実（例：「検索342件/月、該当記事0件」「Trust Score 32」「施行日2026-08-01、記事未更新」） |
| **Affected Region** | Relation → Region Master | Region Gap／地域性のあるExperience Gap・Seasonal Gapで使用 |
| **Affected Language** | Relation → Language Master | Translation Gapで使用 |
| **Affected Audience** | Multi-select（Audience語彙を流用） | Audience Gapで使用 |
| **Affected Season** | Multi-select（Season語彙を流用） | Seasonal Gapで使用 |
| **Related Article** | Relation → Article | Trust Gap／Freshness Gap／Legal Gapで、対象となっている既存記事 |
| **Related Law Update** | Relation → Law Update | Legal Gapで、原因となった法改正 |
| **Related Signal** | Relation → Experience Intelligence（自己） | Experience Gap／Trend Gapで、記事化されていないEvent/Culture/Local/Trendレコードへのリンク |
| **Suggested Action** | Text（AI生成） | 「英語・ベトナム語版を優先翻訳」「長崎県の文化記事を追加」等、具体的な提案 |
| **Status** | Select（New→Acknowledged→Actioned→Resolved） | Actionedになると、Editorial Calendarへのレコードが必ず1件紐づく |
| **Proposed Editorial Calendar Entry** | Relation → Editorial Calendar | AIが提案した編集タスク |

**10種のGap Typeと検出ロジック**

| # | Gap Type | 検出ロジック（概要） | 主な参照元 |
|---|---|---|---|
| ① | Content Gap | User Intelligence（検索・AI相談ログ）で頻出するテーマを、既存Articleのカテゴリ・タグと突き合わせ、一致する記事がなければ検出 | Experience Intelligence(User), Article |
| ② | Translation Gap | ArticleのTranslation Progressが低い、または特定言語（Region/Audience上重要な言語）だけ未翻訳の場合に検出 | Article, Translation, Language Master |
| ③ | Region Gap | Region別のArticle件数（Ancestor Path集計）を比較し、著しく手薄な地域を検出 | Article, Region Master |
| ④ | Seasonal Gap | 直近4〜8週間で迎える季節・Event Calendarの季節イベントに対し、対応するArticle/Experience Intelligence(Event)が記事化されていない場合に検出 | Event Calendar, Experience Intelligence(Event), Article |
| ⑤ | Audience Gap | Audience別のArticle件数分布を比較し、著しく手薄な対象者層を検出 | Article |
| ⑥ | Trust Gap | Article.Trust Scoreが閾値（目安50）を下回った場合に検出。優先更新候補として扱う | Article |
| ⑦ | Freshness Gap | Article.Verification Status=Needs Recheck、またはLast Verified DateがConstitution §11の再確認周期（Update Level 2/3は90日）を超過した場合に検出 | Article |
| ⑧ | Experience Gap | Experience Intelligence(Event/Culture/Local)のうちVisitor Suitability Score／Popularity Scoreが高いのに Related Article が空のものを検出 | Experience Intelligence(Event/Culture/Local) |
| ⑨ | Trend Gap | Experience Intelligence(Trend)のうちTrend Signal Strengthが高いのに、直近のSNS Queue投稿もRelated Articleも存在しない場合に検出。時間経過で鮮度が落ちるため短いTTLで扱う | Experience Intelligence(Trend), SNS Queue |
| ⑩ | Legal Gap | Law Update.Effective Dateが到来済み、またはArticle.Updated DateがLaw Update.Effective Dateより古い場合に検出。**最優先。検出時にGap Severity=Critical、Constitution §12 Emergency Update Rulesを自動的に参照** | Law Update, Article |

> ③⑦⑩の一部は、Law Update（Phase B3）・Region Masterの祖先タグ付け自動化（Phase B4）が完成して初めてフルに動く。**スキーマとルールは今確定し、実際のn8n実装はそれぞれのDBが完成した段階で有効化する。**

**Dashboardへの自動集約**：Gap Type別件数、Severity別件数、「Legal Gapアラート」（Critical件数が1件でもあれば最上部に表示）を、Dashboard（Phase B5）の専用セクションとしてロールアップする。

**Editorial Calendarへの自動提案**：Status=Actionedになったタイミングで、Editorial Calendarへ Status=Idea のレコードを自動生成し、`Source Signal` にこのGapレコードをリンクする。Editorial Calendar.Gap Typeは、独自にSelectで持たせるのではなく、**Source Signal（Experience Intelligence）からのRollupに変更する**（Phase B1のEditorial Calendar仕様を修正：単一の情報源からGap Typeを継承し、表記の二重管理を避ける）。

**担当エージェント**：Knowledge Gap Engineの実行主体として、AI Agent Constitutionに **Gap Analysis Agent**（9番目のAI Agent）を追加した（詳細は[ARu AI Agent Constitution v1.1.0](./aru-ai-agent-constitution.md)を参照）。

---

## Universal Properties（共通基盤）

②DB固有Propertyへ入る前に、n8n／GitHub／Dashboard／Analyticsとの連携を前提にした共通プロパティ層を先に固める。**すべてのプロパティをすべてのDBに機械的に追加するわけではない。** DBの性質によって適用範囲を分け、無意味な項目（例：MentorにCultural Value Score）を持たせない。

### 適用スコープ

| Tier | 対象DB | フルセット適用か |
|---|---|---|
| **Content Core** | Article, Research, Experience Intelligence, Event Calendar, Law Update | ほぼ全プロパティ |
| **Source Layer** | Source Library, Source Monitor | 基本情報＋品質管理の一部（コンテンツ評価系は対象外） |
| **Distribution / Child** | Translation, SNS Queue | 基本情報＋AI管理＋（Translationのみ）コンテンツ分析を任意で |
| **System Layer** | Language Master, AI Agents, Prompt Library, Automation, Mentor | 基本情報＋AI管理の一部のみ |
| **Reporting** | Dashboard | 対象外（他DBのRollupのみで構成されるため独自のUniversal Propertyを持たない） |

### 1. 基本情報

| Property | 型 | 目的 | 適用 |
|---|---|---|---|
| **Record ID** | Formula | Notion内部のpage ID（API経由で常に取得可能）に加え、`ART-000042` のようなDB接頭辞＋連番を生成する人間可読ID。n8n／GitHub／Dashboard連携時はこれを実質的な主キーとして扱う | 全DB |
| **Title** | Title（Notion標準） | 各DBの一意な見出し。Article=Title、Research=Topic、Event Calendar=Event Nameのように表示名はDBごとに異なってよいが、役割は共通 | 全DB |
| **Status** | Select | レコードのライフサイクル状態。オプション内容はDBごとに異なってよいが、終端状態として必ず `Archived` を含める | Content Core／Source Layer |
| **Category** | Select | 主分類。役割はuniversalだが名称はドメインに合わせて据え置く（下記「命名の統一と例外」参照） | Content Core |
| **Tags** | Multi-select | 横断検索・n8nのフィルタ条件に使う自由入力タグ | 全DB |
| **Priority** | Select（High/Med/Low） | 対応優先度 | Content Core |
| **Owner** | Relation → Mentor | 人間側の責任者。AI側の担当は別途「AI Owner」で持つ | Content Core |
| **Created Date** | Notion標準 Created time | 作成日時 | 全DB |
| **Updated Date** | Date（手動更新） | Notion標準のLast edited timeとは別に持つ。閲覧・軽微編集では変わらず、**実質更新**（Constitution §11）でのみ更新することで、Translation側の再翻訳判定トリガーとして機能する | Content Core |
| **Published Date** | Date | 公開日時 | Content Core |
| **Archived Date** | Date | Statusが Archived になった日時 | Content Core／Source Layer |

### 2. 品質管理

| Property | 型 | 目的 | 適用 |
|---|---|---|---|
| **Trust Score** | Number（0–100） | Constitution §8 Trust Score Policyの実装。Source Reliability・Review Level・Freshness・Mentor Endorsementから算出 | Content Core／Source Library |
| **Source Count** | Rollup | 紐づくSource Libraryエントリ数 | Content Core |
| **Review Level** | Select（1／2／3） | Articleの既存 `Update Level` と同一の尺度をCore DB全体へ拡張したもの。Articleでは Update Level＝ポリシー入力、Review Level＝universal propertyとしての公開値で、実体は同じ値を指す | Content Core |
| **QA Status** | Select（Not Started／Passed／Failed／Needs Rework） | 第14章 Quality Checklistの結果 | Content Core |
| **Verification Status** | Select（Unverified／Verified／Needs Recheck） | Source Policyの再確認サイクルと連動する鮮度検証状態 | Content Core／Source Library |

### 3. AI管理

| Property | 型 | 目的 | 適用 |
|---|---|---|---|
| **AI Owner** | Relation → AI Agents | 担当したAI Agent | Content Core／Source Layer／Distribution |
| **AI Generated** | Checkbox | AIが生成に関与したか | 全DB |
| **Human Reviewed** | Checkbox | 人間のレビューを経たか | Content Core／Distribution |
| **Last AI Update** | Date | AIが最後に自動更新した日時 | Content Core／Source Layer／Distribution |
| **Prompt Version** | Rollup ← AI Owner.Linked Prompts | 生成時に使用したPrompt Libraryの版。品質のトレーサビリティを確保 | Content Core／Distribution |

### 4. 多言語

多言語系プロパティは **Articleにのみ** 適用する。Research・Event Calendar・Source Libraryなどは翻訳対象そのものではない内部作業データであり、翻訳が必要になった時点でArticleを経由するため。

| Property | 型 | 目的 |
|---|---|---|
| **Master Language** | Select（固定値 "ja"） | 翻訳の起点言語 |
| **Translation Status** | Rollup/Formula | 紐づく全Translationの集計状況（例：「12言語中8言語公開済み」）。個々の言語ごとの状態はTranslation DB側が正であり、これはその要約 |
| **Translation Progress** | Formula（%） | Published Translation件数 ÷ Language Master内のActive言語数 |

将来Experience Intelligenceの記述内容を利用者向けに直接多言語展開する場合は、その時点で同じ3プロパティを追加する。

### 5. コンテンツ分析

| Property | 型 | 目的 |
|---|---|---|
| **Popularity Score** | Number/Rollup | アプリ内閲覧・保存・SNSエンゲージメントから算出（将来Analytics連携） |
| **Cultural Value Score** | Number | Cultural Policy（第5章）に沿った文化的価値の評価 |
| **Visitor Suitability Score** | Number | 「今、外国籍の方に薦める価値があるか」の評価。Experience Intelligenceの核心指標 |
| **Recommendation Score** | Number（0–100、AI算出） | Trust Score・Cultural Value Score・Visitor Suitability Score・Popularity Score・Urgency・Audience適合度を合成した、AIによる総合推奨度。「編集部が次に着手すべきか」「利用者に薦めるべきか」を1つの数値に集約する |

Popularity／Cultural Value／Visitor Suitability Scoreの適用は **Article、Experience Intelligence、Event Calendar** の3つに限定する。Research（生データ）、Source Library（情報源そのもの）、Law Update（法律そのもの）には「人気」「文化的価値」という評価軸がなじまないため対象外とする。Translationには言語別のPopularity Scoreのみ任意で追加可能（同じ内容でも言語によって反応が異なりうるため）。

**Recommendation Scoreのみ、これらより広い範囲（Article, Research, Experience Intelligence, Event Calendar, Law Update）に適用する。** 未公開のResearchや、記事化前のLaw Updateであっても「これは優先して着手すべきか」をAIが数値で示せるようにするため。

### 6. Audience & Context（対象・文脈）

Article, Research, Experience Intelligence, Event Calendar, Law Update の5DB共通で使う、内容の「誰に・どこで・いつ・どれくらい急ぎか」を表す横断プロパティ。

| Property | 型 | 目的 |
|---|---|---|
| **Audience** | Multi-select | 対象読者・利用者層。下記の13区分で統一 |
| **Region** | Relation → Region Master（複数選択可） | 全国／地方／都道府県／市区町村／区／エリアまで対応する地域スコープ。詳細は①の「Region Master（詳細）」を参照 |
| **Season** | Multi-select（春／夏／秋／冬／通年） | 季節性。複数季節にまたがる内容は複数選択可、季節性がない内容は「通年」 |
| **Urgency** | Select（Critical／High／Medium／Low） | コンテンツ自体の時間的切迫度。編集部の作業優先度である`Priority`とは軸が異なる（下記参照） |

**Audienceの13区分**：観光客／在住外国人／留学生／技能実習生／特定技能／永住者／高度人材／外国籍社員／家族／子ども／企業担当者／自治体／日本人

> **既存プロパティとの整理**：ER Designで定義していたArticleの `Target Audience`（旅行者／在留外国人／留学生／技能実習・特定技能／移住希望者／企業／自治体／日本語学校）は、この新しい13区分の `Audience` に置き換える。「移住希望者」「日本語学校」は新リストに含まれていないが、Multi-selectはあとから選択肢を追加できるため、必要になった時点で追加する運用とする。

> **Urgency と Priority の違い**：`Priority`（基本情報）は編集部内の作業キューの並び順（人的リソースをどこに割くか）。`Urgency`（本節）はコンテンツそのものの時間的切迫度（読者にとって今すぐ必要か）。たとえば「施行3日前の法改正」はUrgency＝Criticalだが、担当者の手が空いていなければPriorityは別途調整される。**Urgency＝CriticalはConstitution §12 Emergency Update Rulesの発動条件のひとつとして扱う。**

> **Regionのみ適用範囲が異なる**：Audience／Season／Urgencyはこの5DB共通だが、`Region` はさらに **Source Library** にも追加する（自治体・観光協会等、地域に紐づく情報源を管理するため）。合計6DBがRegion Masterと接続する。

### 7. 運営

| Property | 型 | 目的 | 適用 |
|---|---|---|---|
| **Version** | Number | 実質更新（Constitution §11）のたびに+1 | Content Core |
| **Revision** | Number | 軽微な修正を含む全編集回数 | Content Core |
| **Confidentiality** | Select（Public／Internal／Confidential） | 公開範囲の分類 | 全DB |
| **Usage Scope** | Multi-select（Consumer App／Enterprise／Municipal Partnership／Internal Only） | Constitution §19 Future Expansion Policyのテナント分離を先取りする実装 | Content Core |
| **Related Constitution Version** | Text（例："v2.0.0"） | このレコードが最後にレビューされた時点で有効だった憲章バージョン。Audit Log（第18章）の裏付けとする | Content Core |

---

### この設計に伴う既存ドキュメントへの補正

Universal Propertiesを導入するにあたり、既存のER Design / Constitutionとの間に4点、命名・重複の整理が必要になった。

1. **Article「Master Status」→「Status」に改称。** 値・遷移（Draft → AI Draft → Human Review → Approved → Published → Archived）は変更なし。Universal Propertyとしての命名統一のため。
2. **Article「Update Level」はそのまま維持。** Universal Property「Review Level」は同じ1／2／3の尺度を他のCore DBへ拡張したもので、Articleにおいては Update Level と Review Level は同じ値を指すエイリアス関係にある（Update Level＝ポリシー入力、Review Level＝横断参照用の公開名）。
3. **Source Libraryの「Reliability（1〜5の数値）」は廃止し、Constitution §7 Source Policyの3段階「Tier（高／中／低）」に一本化する。** 新設の数値的な `Trust Score` は、Tierを含む複数要素から算出される計算結果として位置づけ、Tierと共存させる。これによりER Design側で生じていたReliability（数値）とConstitution側のTier（3段階）の不一致を解消する。
4. **Article「Target Audience」→ 新しい13区分の「Audience」に置き換える。**

また、Category的役割を持つプロパティ（Article.Category／Experience Intelligence.Intelligence Type／Source Library.Source Type／Event Calendar.Event Type）は名称を統一しない。ドメインごとの明確さを優先し、代わりにNotion上のプロパティ説明欄に `role:category` という自動化用タグを付与することで、n8n側が名前ではなく役割で主分類プロパティを検出できるようにする。

---

### 決定：Region実装方式

**案A（Region Master新設）を採用。** 詳細仕様は①の「[Region Master（詳細）](#region-master詳細)」を参照。全国約1,700の市区町村をフラットなSelectに持たせず、Country→Region→Prefecture→City→Ward→Area/Spotの階層をRelationで表現し、Knowledge Graphの地域軸として機能させる。

---

## ② Property一覧 — Phase A（Article / Research / Translation）

各DBについて、DB固有プロパティとUniversal Properties（適用スコープに従う）を1つの表に統合する。①Property一覧の表がType・必須項目を列として含むため、②③はその表を軸にした要約として扱う。

---

### 1. Article

#### ① Property一覧 ／ ② Property Type ／ ③ 必須項目

| Property | Type | 必須 | 由来 |
|---|---|---|---|
| Title | Title | 作成時必須 | DB固有 |
| Body | Text（Rich） | 作成時必須 | DB固有 |
| Slug | Formula → Text | 公開前必須 | DB固有（追加）※後述 |
| Category | Select | 作成時必須 | DB固有（role:category） |
| Status | Select | 作成時必須（初期値 Draft） | Universal（旧Master Status） |
| Record ID | Formula | 自動生成 | Universal |
| Tags | Multi-select | 任意 | Universal |
| Priority | Select（High/Med/Low） | 任意（初期値 Medium） | Universal |
| Owner | Relation → Mentor | 任意 | Universal |
| Created Date | Created time | 自動 | Universal |
| Updated Date | Date（手動更新） | 実質更新時のみ | Universal |
| Published Date | Date | 公開時必須 | Universal |
| Archived Date | Date | Archived時必須 | Universal |
| Trust Score | Formula（Number） | 自動算出 | Universal |
| Source Count | Formula（Number） | 自動算出 | Universal |
| Update Level（＝Review Level） | Formula（Number 1/2/3） | 自動算出 | DB固有＝Universal alias |
| QA Status | Select | 公開前必須 | Universal |
| Verification Status | Select | 公開前必須 | Universal |
| Last Verified Date | Date | Level2/3は必須 | DB固有（追加、Verification Statusの対） |
| AI Owner | Relation → AI Agents | 任意 | Universal |
| AI Generated | Checkbox | 自動 | Universal |
| Human Reviewed | Checkbox | Level2/3は公開前必須 | Universal |
| Last AI Update | Date | 自動 | Universal |
| Prompt Version | Rollup | 自動 | Universal |
| Source Research | Relation → Research | Category依存で必須 | DB固有 |
| Source Law Update | Relation → Law Update | Category依存で必須 | DB固有 |
| Source Event | Relation → Event Calendar | Category依存で必須 | DB固有 |
| Law Significance | Rollup ← Source Law Update | 自動 | DB固有 |
| Reviewed By | Relation → Mentor | Level2/3は必須 | DB固有 |
| Translations | Relation → Translation | 自動生成 | DB固有 |
| Languages Published | Rollup | 自動 | DB固有 |
| **Knowledge Links** | **Relation → Article（自己・多対多）** | **任意** | **DB固有（追加）** |
| Master Language | Select（固定 "ja"） | 自動 | Universal（Article限定） |
| Translation Status | Rollup/Formula | 自動 | Universal（Article限定） |
| Translation Progress | Formula（%） | 自動 | Universal（Article限定） |
| Popularity Score | Rollup/Number | 公開後自動 | Universal |
| Cultural Value Score | Number | 任意（AI提案） | Universal |
| Visitor Suitability Score | Number | 任意（AI提案） | Universal |
| Recommendation Score | Formula | 自動算出 | Universal |
| Audience | Multi-select（13区分） | 作成時必須 | Universal |
| Region | Relation → Region Master | 推奨 | Universal |
| Season | Multi-select | 任意（初期値 通年） | Universal |
| Urgency | Select | 作成時必須（初期値 Medium） | Universal |
| Version | Number | 自動+1 | Universal |
| Revision | Number | 自動+1 | Universal |
| Confidentiality | Select | 作成時必須（初期値 Public） | Universal |
| Usage Scope | Multi-select | 作成時必須（初期値 Consumer App） | Universal |
| Related Constitution Version | Text | 自動記録 | Universal |

計43プロパティ。

> **Knowledge Linksについて**：Region MasterやLanguage Masterが「軸（マスタデータ経由の間接的な関連）」だとすれば、Knowledge Linksは記事同士を直接つなぐ**フラットな関連網**。「ビザの記事」と「税金の記事」のように、CategoryもRegionも異なるが内容的に関連する記事同士を明示的につなぎ、将来のアプリ内「関連記事」表示・Knowledge Graph全体の記事間エッジとして機能する。Translations（親子関係）とは別軸であり、混同しない。

#### ④ Formula

| Property | 実装方針 |
|---|---|
| **Update Level** | `if(or(prop("Category")=="法律・制度", prop("Category")=="行政手続き", prop("Category")=="ビザ", prop("Category")=="税金", prop("Category")=="年金", prop("Category")=="保険", prop("Category")=="医療", prop("Category")=="教育制度", prop("Category")=="労働関係"), if(prop("Law Significance")=="Major", 3, 2), 1)` |
| **Recommendation Score** | `round(prop("Trust Score")*0.3 + prop("Cultural Value Score")*0.2 + prop("Visitor Suitability Score")*0.2 + prop("Popularity Score")*0.15 + if(prop("Urgency")=="Critical",100,if(prop("Urgency")=="High",70,if(prop("Urgency")=="Medium",40,10)))*0.15)` — 重みはv1の仮値。運用データが溜まり次第調整する |
| **Trust Score** | `round(prop("Source Count")*10 + prop("Update Level")*15 + if(prop("Verification Status")=="Verified",30,if(prop("Verification Status")=="Needs Recheck",10,0)))`（0–100にクリップ、実装時に`min()`で上限調整） |
| **Source Count** | `length(prop("Source Research")) + length(prop("Source Law Update")) + length(prop("Source Event"))` |
| **Record ID** | `"ART-" + format(id())` — 実装時にNotion側のゼロ埋め表現を検証 |
| **Slug** | 日本語タイトルの機械的スラッグ化はNotion Formula単体では困難（ローマ字変換が必要）。**Notion Formulaではなくn8n Automationで生成**し、結果をTextプロパティとして書き戻す方式に変更する（Formula欄はプレースホルダとして扱う） |
| **Translation Progress** | `round(prop("Languages Published") / max(1, [Language Masterの Active言語数のRollup]) * 100)` |

#### ⑤ Rollup

| Property | Relation元 | 集計内容 |
|---|---|---|
| Languages Published | Translations | Publish Status = 公開 の件数 |
| Law Significance | Source Law Update | Significance（Minor/Major） |
| Translation Status（要約） | Translations | Publish Status の unique値一覧 → Formulaで文字列化 |
| Popularity Score | Translations（言語別）＋SNS Queue | 各言語のエンゲージメントを合算（実装はRollup→Formula二段構成） |
| Prompt Version | AI Owner（AI Agents）経由 | AI AgentsがさらにPrompt Libraryをロールアップした値を再ロールアップ（2ホップ） |

#### ⑥ Relation

| Property | 相手DB | 方向 |
|---|---|---|
| Source Research | Research | 双方向（Researchの `Converted Article` が逆側） |
| Source Law Update | Law Update | 双方向 |
| Source Event | Event Calendar | 双方向 |
| Reviewed By / Owner | Mentor | 双方向 |
| Translations | Translation | 双方向（親子） |
| AI Owner | AI Agents | 双方向 |
| Region | Region Master | 双方向 |
| Knowledge Links | Article（自己） | 双方向・多対多 |

#### ⑦ View

- **編集ボード**：Statusでグループ化したBoard（Draft→AI Draft→Human Review→Approved→Published→Archived）
- **要レビュー**：Status=Human Review をUrgency降順でソートしたTable
- **Update Level別**：Update Levelでグループ化したBoard（レビュー担当の割り振りに使用）
- **地域別**：Regionでグループ化したTable
- **多言語カバレッジ**：Translation Progress昇順のTable（翻訳が遅れている記事を発見）
- **公開カレンダー**：Published DateのCalendar view
- **アーカイブ**：Status=Archivedのフィルタ済みTable

#### ⑧ Template

- **標準記事テンプレート**：Status=Draft、Master Language=ja、本文欄に第14章Quality ChecklistのTo-doを埋め込み済み
- **法改正記事テンプレート**：Category=法律・制度を事前設定、Source Law Updateのリレーション入力を促すプロンプト付き、第13章の免責事項ボイラープレートを本文冒頭に挿入済み
- **イベント記事テンプレート**：Category=イベント、Source Eventリレーション必須の注記、Season入力を促す
- **文化体験記事テンプレート**：Category=日本文化、Cultural Value Score入力欄とExperience Intelligenceへのリンク導線付き

#### ⑨ Automation対象

- Research.Status=Converted → Article新規作成（Source Researchを自動リレーション）
- Article.Update Date変化 → 全Translationの Needs Re-Translation再計算
- Article.Status→Published → SNS Queueへ自動登録
- Update Level 2/3かつ90日超過 → Verification Status/Last Verified Dateの再確認タスクを起票
- Update Level 2/3で Human Reviewed=false のまま Status を Published に変更しようとした場合 → Automationがブロックし編集長へ通知（Constitution §9 AI Behavior Rulesの技術的な担保）
- Article公開時 → Category／Region／Audienceが重なる既存Articleを検索し、Knowledge Links候補をAIが提案（人が採用/却下）

#### ⑩ AI利用方法

- **Writer Agent**：ResearchからBodyを起筆。Prompt Library「Article Draft – {Category}」を使用
- **QC Agent**：公開前に第14章Quality Checklistを自動実行し、QA Statusを設定
- **SEO Agent**：Title・Slug案を提示（人が採用/却下）
- **Linking Agent（AI Agentsの1役割として新設可）**：Knowledge Linksの候補を提案。最終採用は人（またはOwner）が行う
- **制約**：Update Level 2/3では、どのAI AgentもPublish Approvalに相当する操作（Statusを Published にする行為）を実行できない（Constitution §9）

---

### 2. Research

#### ① Property一覧 ／ ② Property Type ／ ③ 必須項目

| Property | Type | 必須 | 由来 |
|---|---|---|---|
| Topic | Title | 作成時必須 | DB固有 |
| Category | Select | 作成時必須（Articleの候補カテゴリ） | DB固有（role:category） |
| Summary | Text | Reviewing移行前に必須 | DB固有 |
| Raw Notes | Text | 任意 | DB固有 |
| **Evidence Level** | **Select（Official / Verified / Reported / Rumor / AI Suggested）** | **作成時必須（初期値 AI Suggested）** | **DB固有（追加）** |
| Status | Select（New→Reviewing→Converted/Rejected） | 自動（初期値New） | DB固有＝Universal |
| Record ID | Formula | 自動生成 | Universal |
| Tags | Multi-select | 任意 | Universal |
| Priority | Select | 任意 | Universal |
| Owner | Relation → Mentor | 任意 | Universal |
| Created / Updated / Archived Date | Date系 | 自動／Archived時必須 | Universal |
| Trust Score | Formula | 自動算出 | Universal |
| Source Count | Rollup | 自動 | Universal |
| Review Level | Select（1/2/3、手動または引継ぎ予測） | Reviewing移行前必須 | Universal |
| QA Status / Verification Status | Select | 任意 | Universal |
| AI Owner / AI Generated / Human Reviewed / Last AI Update / Prompt Version | 各種 | AI Generatedは自動 | Universal |
| Recommendation Score | Formula | 自動算出 | Universal |
| Audience / Region / Season / Urgency | 各種 | Audience・Urgencyは作成時必須 | Universal |
| Version / Revision / Confidentiality / Usage Scope / Related Constitution Version | 各種 | Confidentiality等は初期値あり | Universal |
| Converted Article | Relation → Article | Status=Converted時に必須 | DB固有 |
| Related Experience Signal | Relation → Experience Intelligence | 任意 | DB固有（双方向） |

計約25プロパティ（多言語・コンテンツ分析3スコアはResearchには適用しない）。

> **Evidence Levelについて**：Source Library.Tier（情報源そのものの一般的な信頼度）とは別軸で、**この特定の調査結果がどの程度確からしいか**を表す。同じTier=高のソースでも、まだ非公式な観測段階なら Reported、AIが複数のシグナルから推測しただけなら AI Suggested になりうる。Official／Verifiedは一次情報源での確認が前提。Evidence LevelがRumor／AI SuggestedのままStatus=Convertedへ進めることは、Update Level 2/3に該当するCategoryでは**Automationがブロックする**（Constitution §13 Legal & Medical Rulesの「疑わしきは公開しない」の技術的な担保）。

#### ④ Formula

| Property | 実装方針 |
|---|---|
| **Days Open** | `dateBetween(now(), prop("Created Date"), "days")` — 未着手Researchの滞留日数を可視化 |
| **Trust Score** | `round(if(prop("Evidence Level")=="Official",100,if(prop("Evidence Level")=="Verified",80,if(prop("Evidence Level")=="Reported",55,if(prop("Evidence Level")=="Rumor",25,10))))*0.7 + prop("Source Count")*10*0.3)` |
| **Recommendation Score** | Article同様の合成式だが、Popularity/Cultural Value/Visitor Suitabilityは存在しないため `round(prop("Trust Score")*0.5 + Urgencyの重み*0.3 + Source Countの重み*0.2)` |
| **Record ID** | `"RES-" + format(id())` |

#### ⑤ Rollup

| Property | Relation元 | 集計内容 |
|---|---|---|
| Source Count | Source Library | 関連ソース件数 |
| Prompt Version | AI Owner | Prompt Libraryの現行版 |

#### ⑥ Relation

| Property | 相手DB | 方向 |
|---|---|---|
| Source Library | Source Library | 双方向（多対多） |
| Converted Article | Article | 双方向（Article.Source Researchが逆側） |
| Related Experience Signal | Experience Intelligence | 双方向 |
| Owner | Mentor | 双方向 |
| AI Owner | AI Agents | 双方向 |
| Region | Region Master | 双方向 |

#### ⑦ View

- **未処理（New）**：Status=Newを Priority降順
- **カテゴリ別**：CategoryでグループBoard
- **Evidence Level別**：Evidence LevelでグループBoard（Rumor/AI Suggestedの滞留を監視）
- **滞留アラート**：Days Open > 30 のフィルタTable
- **地域別**：RegionグループTable
- **Converted / Rejected**：それぞれのフィルタTable

#### ⑧ Template

- **標準リサーチテンプレート**（初期値 Evidence Level=AI Suggested）
- **トレンド由来リサーチ**：Experience Intelligence（Trend）から生成される際の初期値プリセット（Evidence Level=Reported）
- **法改正監視リサーチ**：Source Monitorが法律系ソースの変化を検知した際に自動生成されるテンプレート（Category=法律・制度、Evidence Level=Verifiedをプリセット）

#### ⑨ Automation対象

- Source Monitorが変更検知 → Researchレコードを自動作成／更新
- Experience Intelligenceが「調査に値する」と判定 → Researchを自動作成し Related Experience Signal をリンク
- Category が Update Level 2/3相当かつ Evidence Level が Rumor／AI Suggested のまま Status を Converted に変更しようとした場合 → Automationがブロックし、Evidence Levelの引き上げ（一次情報源での確認）を要求
- Status→Converted → Article自動生成（Writer Agentへのタスク発行込み）
- Days Open > 30 かつ Status=New → Owner／編集長へリマインド通知

#### ⑩ AI利用方法

- **Research Agent**：Source Libraryの内容をSummary/Raw Notesへ要約、Category・Audience・Recommendation Score・**Evidence Level（初期値）**を提案
- **制約**：AIは自らEvidence LevelをOfficial／Verifiedに引き上げることはできない（一次情報源での人間の確認を経て初めて引き上げられる）。Trust ScoreがResearch単体で著しく低い（一次情報源なし）場合、AIはStatusをReviewingへ進める前に人間の確認を要求する

---

### 3. Translation

#### ① Property一覧 ／ ② Property Type ／ ③ 必須項目

| Property | Type | 必須 | 由来 |
|---|---|---|---|
| Parent Article | Relation → Article | 作成時必須 | DB固有 |
| Language | Relation → Language Master | 作成時必須 | DB固有 |
| Translated Title | Text | AI Translation Status=Done時必須 | DB固有 |
| Translated Body | Text | 同上 | DB固有 |
| Review Level（Rollup ← Parent Article.Update Level） | Rollup | 自動 | Universal（旧名Update Levelから改称） |
| AI Translation Status | Select（Not Started→Queued→In Progress→Done） | 自動遷移 | DB固有 |
| **Localization Status** | **Select（Not Started→Translated→Culturally Adapted→Needs Cultural Review）** | **Publish Approval付与前に Culturally Adapted 必須（全Review Level共通）** | **DB固有（追加）** |
| Human Review Status | Select（Not Required→Pending→In Review→Reviewed） | Review Level 2/3で必須 | DB固有 |
| Publish Approval | Select（Not Required→Pending→Approved/Rejected） | Review Level 2/3で必須 | DB固有 |
| Reviewer | Relation → Mentor | Review Level 2/3で必須 | DB固有 |
| Approved Date | Date | Publish Approval=Approved時必須 | DB固有 |
| Published Date | Date | 公開時必須 | DB固有（追加、Articleとの対称性） |
| Source Updated At | Rollup ← Parent Article.Updated Date | 自動 | DB固有 |
| Last Source Check | Date | Automation自動更新 | DB固有 |
| Needs Re-Translation | Formula（Yes/No） | 自動算出 | DB固有 |
| Change Summary | Text | Review Level 3で必須 | DB固有 |
| Publish Status | Select（App非公開/公開、SNS未投稿/投稿済み） | 自動遷移 | DB固有 |
| Record ID | Formula | 自動生成 | Universal |
| Tags | Multi-select | 任意 | Universal |
| Created Date | Created time | 自動 | Universal |
| Archived Date | Date | 任意 | Universal（Distribution拡張） |
| AI Owner | Relation → AI Agents | 任意 | Universal |
| AI Generated | Checkbox | 自動 | Universal |
| Human Reviewed | Checkbox | Review Level 2/3で必須 | Universal |
| Last AI Update | Date | 自動（旧AI Translated Atを統合） | Universal |
| Prompt Version | Rollup | 自動 | Universal |
| Popularity Score（言語別・任意） | Number/Rollup | 任意 | Universal（Translation限定で許可） |
| Confidentiality / Usage Scope | Select/Multi-select | 任意 | Universal（拡張） |

計約27プロパティ。Audience／Region／Season／Urgencyは**意図的に持たない**（親Articleの値をそのまま使う。言語ごとに矛盾したタグが付くのを防ぐため）。

> **Localization Statusについて**：AI Translation Status（AIが訳文を生成したか）とは別軸で、Constitution §6 Translation Policyが求める「直訳ではなく意味と文化的ニュアンスの翻訳」の**完成度**を追跡する。
> - `Translated`：直訳・機械翻訳的な訳文はできているが、慣用句や文化的言及への補足がまだ
> - `Culturally Adapted`：文化的背景の翻訳者注記・補足まで完了
> - `Needs Cultural Review`：文化的言及の扱いに疑義があり、Reviewerの追加確認が必要
>
> **Localization StatusがCulturally Adaptedに達するまで、Publish Approvalは付与できない。** これはReview Level 1（自動公開カテゴリ）にも適用される——「文化的ニュアンスを伝える」はARuの根幹（Mission／Core Values）であり、Update Levelの慎重さとは独立した最低ラインのため。

#### ④ Formula

| Property | 実装方針 |
|---|---|
| **Needs Re-Translation** | `if(prop("Source Updated At") > prop("Last Source Check"), true, false)` |
| **Record ID** | `"TRN-" + format(id())` |

#### ⑤ Rollup

| Property | Relation元 | 集計内容 |
|---|---|---|
| Review Level | Parent Article | Update Levelの値をそのまま反映 |
| Source Updated At | Parent Article | Updated Dateをそのまま反映 |
| Prompt Version | AI Owner | Prompt Libraryの現行版 |

#### ⑥ Relation

| Property | 相手DB | 方向 |
|---|---|---|
| Parent Article | Article | 双方向（親子） |
| Language | Language Master | 双方向 |
| Reviewer | Mentor | 双方向 |
| AI Owner | AI Agents | 双方向 |

#### ⑦ View

- **要再翻訳**：Needs Re-Translation=Yes のフィルタTable（最優先ワークフロー）
- **言語別ボード**：LanguageでグループBoard
- **レビュー待ち**：Human Review Status=Pending/In Review をReview Level降順
- **公開状況マトリクス**：Parent Article × Language のTable（多言語カバレッジを一望）
- **アーカイブ**

#### ⑧ Template

- **標準翻訳レコード**：AI Translation Status=Queuedで新規作成される既定フォーム
- **Level 3緊急翻訳**：Change Summary入力欄と優先通知チェックボックスを含むテンプレート

#### ⑨ Automation対象

- Parent Article.Updated Date変化 → 全言語のNeeds Re-Translation再評価、Last Source Check更新（Localization StatusもNot Startedへ差し戻し）
- Needs Re-Translation=Yes → Translator Agentが自動翻訳を実行しAI Translation Status=Doneへ、Localization Status=Translatedへ
- Localization Agent（Translator Agentと同一でも別役割でもよい）が文化的補足を追加 → Localization Status=Culturally Adaptedへ
- Localization Status=Culturally Adapted に達するまで、Review Level に関わらず Publish Approval は Not Required/Approved にならない（自動ブロック）
- Review Level 1 → Localization Status=Culturally Adapted到達後、Human Review Status/Publish Approvalを自動でNot Requiredにし、Publish Status=公開へ
- Review Level 2 → Reviewerへレビュー依頼通知（Constitution §10：48時間SLA）
- Review Level 3 → Change Summary生成＋編集長／専門メンターへ優先通知（Constitution §10：24時間SLA）

#### ⑩ AI利用方法

- **Translator Agent**：Translated Title/Bodyを生成し、AI Translation Status=Doneへ
- **Localization Agent**：文化的言及・慣用句への補足注記を追加し、Localization Status=Culturally Adaptedへ引き上げる。判断がつかない場合は Needs Cultural Review を選び人間へエスカレーションする（Constitution §6）
- **制約**：Review Level 2/3では、Publish ApprovalをAIが自ら Approved に変更することはできない（Constitution §9・§13）。Localization StatusをAIが自らCulturally Adaptedにできるのは、文化的言及が存在しない/軽微な場合に限り、判断に自信がなければ必ずNeeds Cultural Reviewを選ぶ（Constitution §9「確信度が低い場合は人間レビューを要求する」）

---

## ② Property一覧 — Phase B1（Experience Intelligence／Source Library／Source Monitor／Editorial Calendar）

### 0. 設計思想：Command Center

ARu Studioは管理ツールではなく、編集長が毎朝開く**司令室**である。Phase B1の4DBは、単体の台帳としてではなく、次の一本道として機能するように設計する。

```
Source Library（何を見張るか）
    ↓
Source Monitor（何が変わったか）
    ↓
Experience Intelligence（それは知識の不足か、好機か）
    ├─ Knowledge Gap（不足している知識）
    └─ Opportunity Intelligence（今だから価値が高いテーマ）
    ↓
Editorial Calendar（いつ・誰が・何を書くか）
    ↓
Article
```

**Knowledge GapとOpportunity Intelligenceは対になる2つのエンジン**として統合する。

| | Knowledge Gap | Opportunity Intelligence |
|---|---|---|
| 問いかけ | 「何が足りないか」 | 「今、何が価値が高いか」 |
| 性質 | 解消されるまで残り続ける（persistent） | 期限がある（expires） |
| トリガー | 記事の欠落・鮮度切れ・信頼度低下 | 季節性・トレンド・イベント接近・地域の勢い |
| Dashboard表示 | Today's Knowledge Gaps | Today's Opportunities |

両者とも `Intelligence Type` の値としてExperience Intelligenceに統合し、Editorial Calendarへ同じ経路（Source Signal Relation）で提案を送る。

---

### 4. Experience Intelligence

#### ① Property一覧 ／ ② Property Type ／ ③ 必須項目

**共通プロパティ（全Intelligence Type）**

| Property | Type | 必須 | 由来 |
|---|---|---|---|
| Title | Title | 作成時必須 | DB固有 |
| Intelligence Type | Select（Event/Culture/Trend/Local/Gap/Opportunity/User） | 作成時必須 | DB固有（role:category） |
| Description | Text | 作成時必須 | DB固有 |
| Status | Select（意味はTypeにより異なる、後述） | 自動（初期値New） | DB固有＝Universal |
| Related Article | Relation → Article | 任意 | DB固有 |
| Related Research | Relation → Research | 任意 | DB固有 |
| Source Signal（自己Relation） | Relation → Experience Intelligence | 任意 | DB固有 |
| Related Editorial Calendar Entry | Relation → Editorial Calendar | Actioned時必須 | DB固有 |
| Record ID | Formula | 自動生成 | Universal |
| Tags | Multi-select | 任意 | Universal |
| Priority | Select | 任意 | Universal |
| Owner | Relation → Mentor | 任意 | Universal |
| Created/Updated/Archived Date | Date系 | 自動 | Universal |
| Trust Score | Formula | 自動算出 | Universal |
| Source Count | Rollup | 自動 | Universal |
| Review Level | Select | 任意 | Universal |
| QA Status / Verification Status | Select | 任意 | Universal |
| AI Owner / AI Generated / Human Reviewed / Last AI Update / Prompt Version | 各種 | AI Generatedは自動 | Universal |
| Recommendation Score | Formula | Event/Culture/Local/Trend/Userのみ自動算出 | Universal |
| Audience / Region / Season / Urgency | 各種 | Type依存 | Universal |
| Version / Revision / Confidentiality / Usage Scope / Related Constitution Version | 各種 | Universal |

**Event／Culture／Local専用**

| Property | Type | 必須 |
|---|---|---|
| Popularity Score | Number/Rollup | 任意 |
| Cultural Value Score | Number | 任意 |
| Visitor Suitability Score | Number | 任意 |
| Related Event Calendar | Relation → Event Calendar | Event Typeのみ必須 |
| Related Source Library | Relation → Source Library | Local/Cultureは推奨 |

**Trend専用**

| Property | Type | 必須 |
|---|---|---|
| Platform | Select（Instagram/Threads/X/YouTube） | 作成時必須 |
| Trend Signal Strength | Number（0–100） | 自動算出 |
| Related SNS Queue | Relation → SNS Queue | 任意 |

**Gap専用**（前回確定済み、再掲）

| Property | Type | 必須 |
|---|---|---|
| Gap Type | Select（10種） | 作成時必須 |
| Gap Severity | Universal `Urgency`を流用 | 自動（Legalは常にCritical） |
| Metric / Evidence | Text | 作成時必須 |
| Affected Region | Relation → Region Master | Gap Type依存 |
| Affected Language | Relation → Language Master | Translation Gapのみ必須 |
| Affected Audience | Multi-select | Audience Gapのみ必須 |
| Affected Season | Multi-select | Seasonal Gapのみ必須 |
| Related Law Update | Relation → Law Update | Legal Gapのみ必須 |
| Suggested Action | Text（AI生成） | 作成時必須 |

**Opportunity専用（新設）**

| Property | Type | 必須 |
|---|---|---|
| **Opportunity Type** | Select（Seasonal Peak／Trending Now／Event Proximity／Regional Momentum／Audience Surge） | 作成時必須 |
| **Opportunity Window Start** | Date | 作成時必須 |
| **Opportunity Window End** | Date | 作成時必須（この日を過ぎると自動でStatus=Expired） |
| **Opportunity Score** | Formula（0–100） | 自動算出 |
| **Suggested Action** | Text（AI生成） | 作成時必須 |

**User専用**

| Property | Type | 必須 |
|---|---|---|
| Signal Volume | Number | 自動集計（検索件数・相談件数等の匿名集計値） |

計約45プロパティ（Type別の専用項目を含む延べ数）。

#### ④ Formula

| Property | 実装方針 |
|---|---|
| **Record ID** | `"EXI-" + format(id())` |
| **Recommendation Score**（Event/Culture/Local/Trend/User用） | `round(prop("Trust Score")*0.2 + prop("Cultural Value Score")*0.25 + prop("Visitor Suitability Score")*0.25 + prop("Popularity Score")*0.15 + Urgency重み*0.15)` |
| **Trend Signal Strength** | Automation側でSNS APIのエンゲージメント数を正規化して書き込む（Notion Formula単体では外部API値を取得できないため、n8nが計算しNumberへ書き戻す） |
| **Opportunity Score** | `round(prop("Trend Signal Strength")*0.35 + if(prop("Opportunity Type")=="Seasonal Peak", max(0, 100 - dateBetween(prop("Opportunity Window Start"), now(), "days")*5), 50)*0.35 + prop("Recommendation Score")*0.3)` — v1の仮重み。実データで調整する |
| **Days Until Opportunity Expires** | `dateBetween(prop("Opportunity Window End"), now(), "days")` |
| **Gap系Formula** | 前回確定分（Needs Re-Translation等はTranslation側で算出、GapレコードのMetricはAI Agentが算出しText/Numberへ書き込み） |

#### ⑤ Rollup

| Property | Relation元 | 集計内容 |
|---|---|---|
| Source Count | Related Source Library / Research | 関連ソース・リサーチ件数 |
| Prompt Version | AI Owner | Prompt Libraryの現行版 |
| Affected Region（表示用） | Related Signal | 関連するEvent/Culture/LocalのRegionを継承 |

#### ⑥ Relation

| Property | 相手DB | 方向 |
|---|---|---|
| Related Article | Article | 双方向 |
| Related Research | Research | 双方向 |
| Related Editorial Calendar Entry | Editorial Calendar | 双方向 |
| Related Event Calendar | Event Calendar | 双方向 |
| Related Source Library | Source Library | 双方向 |
| Related SNS Queue | SNS Queue | 双方向 |
| Related Law Update | Law Update | 双方向 |
| Source Signal | Experience Intelligence（自己） | 双方向 |
| Region | Region Master | 双方向 |
| Affected Language | Language Master | 双方向 |
| Owner / AI Owner | Mentor / AI Agents | 双方向 |
| Dashboard | Dashboard | Dashboard側からの一方向的Relation（Rollup起点） |

#### ⑦ View

- **Today's Briefing（最重要）**：Status=New を Intelligence Typeでグループ化し、Gap→Severity降順、Opportunity→Opportunity Score降順、その他→Recommendation Score降順でソート。**編集長が毎朝最初に開くView**
- **Knowledge Gapボード**：Intelligence Type=GapをGap Typeでグループ化。Legal Gapは常に最上段固定表示
- **Opportunityボード**：Intelligence Type=Opportunityを Opportunity Window End昇順（締切が近い順）
- **Trendウォッチ**：Intelligence Type=TrendをTrend Signal Strength降順
- **地域別**：RegionグループTable
- **Actioned/Resolved/Expired**：それぞれのアーカイブ的フィルタTable

#### ⑧ Template

- **Gap記録テンプレート**：Gap Type選択に応じてAffected系プロパティの入力欄が変わる（Notion側はConditional表示ができないため、使わない項目は空欄運用とし、テンプレート説明文で明記）
- **Opportunity記録テンプレート**：Opportunity Window Start/Endの入力必須化と、Suggested Action記入欄
- **Trendウォッチテンプレート**：Platform・Trend Signal Strengthの初期値プリセット

#### ⑨ Automation対象

- Gap Analysis Agentが毎日実行 → 10種のGapを検出しGapレコードを作成/更新
- Opportunity検出ジョブ（Gap Analysis Agentが兼務、または将来Opportunity Agentとして分離）が毎日実行 → Trend/Season/Event Calendarの接近をスキャンしOpportunityレコードを作成
- Opportunity Window Endを過ぎたレコード → Statusを自動でExpiredへ
- Status=Actioned → Editorial Calendarへ自動起票（Source Signalをリンク）
- Legal Gap検出 → 即時、編集長・専門メンターへ通知（Constitution §12）

#### ⑩ AI利用方法

- **Gap Analysis Agent**：Knowledge Gap Engine全体を実行（詳細はAI Agent Constitution §10）
- **Research Agent**：User Intelligenceのsignal Volumeを集計・要約
- **SNS Agent**：Trend Intelligenceの発見元になったSNS投稿を記録
- **制約**：AI利用方法・禁止事項はAI Agent Constitutionに従う。特にLegal Gapの重大度をAIが自己判断で引き下げることはできない

---

### 5. Source Library

#### ① Property一覧 ／ ② Property Type ／ ③ 必須項目

| Property | Type | 必須 | 由来 |
|---|---|---|---|
| Source Name | Title | 作成時必須 | DB固有 |
| URL | URL | 作成時必須 | DB固有 |
| Source Type | Select（政府/自治体/観光協会/ニュース/学術/SNS/コミュニティ/商店街/地域メディア） | 作成時必須（role:category） | DB固有 |
| Tier | Select（高/中/低） | 作成時必須 | DB固有（Constitution §7） |
| Trust Score | Formula | 自動算出 | Universal |
| Check Frequency | Select（Daily/Weekly/Monthly/Quarterly） | 作成時必須（初期値Weekly） | DB固有 |
| Last Checked | Rollup ← Source Monitor（最新Checked At） | 自動 | DB固有 |
| Region | Relation → Region Master | Local/Culture系ソースは推奨 | Universal（拡張） |
| Language | Relation → Language Master | 任意 | DB固有 |
| Status | Select（Active/Inactive/Under Review） | 自動（初期値Active） | Universal |
| Record ID | Formula | 自動生成 | Universal |
| Tags | Multi-select | 任意 | Universal |
| Owner | Relation → Mentor | 任意 | Universal |
| Created/Archived Date | Date系 | 自動 | Universal |
| AI Owner / AI Generated | 各種 | 任意 | Universal |
| Verification Status | Select | 任意 | Universal |
| Confidentiality | Select | 作成時必須 | Universal |

計約17プロパティ。

#### ④ Formula

| Property | 実装方針 |
|---|---|
| **Trust Score** | `round(if(prop("Tier")=="高",80,if(prop("Tier")=="中",50,20)) + if(dateBetween(now(), prop("Last Checked"), "days")<=30,20,0))` |
| **Record ID** | `"SRC-" + format(id())` |

#### ⑤ Rollup

| Property | Relation元 | 集計内容 |
|---|---|---|
| Last Checked | Source Monitor | 最新のChecked At |

#### ⑥ Relation

| Property | 相手DB | 方向 |
|---|---|---|
| Source Monitor | Source Monitor | 双方向（1対多） |
| Research | Research | 双方向（多対多） |
| Law Update | Law Update | 双方向 |
| Event Calendar | Event Calendar | 双方向 |
| Experience Intelligence | Experience Intelligence | 双方向 |
| Region | Region Master | 双方向 |
| Language | Language Master | 双方向 |
| Owner | Mentor | 双方向 |

#### ⑦ View

- **Tier別**：TierでグループBoard
- **要チェック**：Last Checked が Check Frequency の周期を超過したフィルタTable
- **地域別**：RegionグループTable
- **Inactive/Under Review**：フィルタTable

#### ⑧ Template

- **標準ソース登録**（Check Frequency=Weekly初期値）
- **法律・行政系ソース**（Tier=高、Check Frequency=Dailyをプリセット）

#### ⑨ Automation対象

- 新規Source登録 → 初回Source Monitorレコードを自動作成
- Last CheckedがCheck Frequencyの周期を超過 → Owner／編集長へリマインド

#### ⑩ AI利用方法

- **Research Agent**：新しい情報源候補を発見した際、Source Type／Tier（初期値は低め）を提案。Tierの引き上げは人間が行う

---

### 6. Source Monitor

#### ① Property一覧 ／ ② Property Type ／ ③ 必須項目

| Property | Type | 必須 | 由来 |
|---|---|---|---|
| Source | Relation → Source Library | 作成時必須 | DB固有 |
| Checked At | Date | 自動 | DB固有 |
| Check Method | Select（RSS/Webhook/Scraping/API/Manual） | 作成時必須 | DB固有 |
| Change Detected | Checkbox | 自動 | DB固有 |
| Diff Summary | Text（AI生成） | Change Detected=true時必須 | DB固有 |
| Severity | Universal `Urgency`を流用 | Change Detected=true時必須 | DB固有 |
| Triggered Research | Relation → Research | 任意 | DB固有 |
| Triggered Signal | Relation → Experience Intelligence | 任意（Gap/Opportunity起票時） | DB固有 |
| Status | Select（OK/Error/Changed/Needs Attention） | 自動 | Universal |
| Next Check Due | Formula | 自動算出 | DB固有 |
| Error Log | Text | Status=Error時必須 | DB固有 |
| Record ID | Formula | 自動生成 | Universal |
| AI Owner / AI Generated | 各種 | 任意 | Universal |

計約13プロパティ。

#### ④ Formula

| Property | 実装方針 |
|---|---|
| **Next Check Due** | `dateAdd(prop("Checked At"), if(prop("Source Check Frequency")=="Daily",1,if(prop("Source Check Frequency")=="Weekly",7,if(prop("Source Check Frequency")=="Monthly",30,90))), "days")`（`Source Check Frequency`はSource.Check FrequencyのRollup） |
| **Record ID** | `"MON-" + format(id())` |

#### ⑤ Rollup

| Property | Relation元 | 集計内容 |
|---|---|---|
| Source Check Frequency | Source | Check Frequencyの値をそのまま反映（Next Check Due計算用） |
| Source Tier | Source | Tierの値をそのまま反映（Severity判定の参考） |

#### ⑥ Relation

| Property | 相手DB | 方向 |
|---|---|---|
| Source | Source Library | 双方向 |
| Triggered Research | Research | 双方向 |
| Triggered Signal | Experience Intelligence | 双方向 |

#### ⑦ View

- **要対応（Changed/Needs Attention）**：Statusでフィルタ、Severity降順
- **エラー監視**：Status=Errorのフィルタ
- **Source別履歴**：Sourceでグループ化したTable（時系列）

#### ⑧ Template

- **標準チェックログ**（Automationが自動生成、手動作成は基本不要）

#### ⑨ Automation対象

- Next Check Due到来 → Check Methodに応じた自動チェックを実行し、新しいSource Monitorレコードを作成
- Change Detected=true かつ Source.Tier=高 かつ Source.Source Type=政府/自治体 → 自動でTriggered Researchを作成し、Category=法律・制度候補としてフラグ（Legal Gap検出の前段）
- Status=Error が3回連続 → Ownerへ通知（ソースが構造変更された可能性）

#### ⑩ AI利用方法

- **Research Agent**：Diff Summaryを生成し、変化の重大性からSeverityを提案（Legal相当の変化はUrgency=Critical寄りに倒す）

---

### 7. Editorial Calendar

#### ① Property一覧 ／ ② Property Type ／ ③ 必須項目

| Property | Type | 必須 | 由来 |
|---|---|---|---|
| Planned Topic | Title | 作成時必須 | DB固有 |
| Category | Select | 作成時必須（role:category） | DB固有 |
| Planned Date | Date | 作成時必須 | DB固有 |
| Status | Select（Idea→Planned→In Progress→Drafted→Published→Skipped/Cancelled） | 自動（初期値Idea） | Universal |
| Gap Type | Rollup ← Source Signal.Gap Type | 自動 | DB固有 |
| Opportunity Deadline | Rollup ← Source Signal.Opportunity Window End | 自動 | DB固有（追加） |
| Linked Article | Relation → Article | Status=Drafted以降必須 | DB固有 |
| Linked Research | Relation → Research | 任意 | DB固有 |
| Source Signal | Relation → Experience Intelligence | 推奨 | DB固有 |
| Assigned Owner | Relation → Mentor | 任意 | DB固有 |
| Assigned AI Agent | Relation → AI Agents | 任意 | DB固有 |
| Audience / Region / Season | Universal | Source Signalから引き継ぎ推奨 | Universal |
| Urgency | Rollup ← Source Signal.Urgency（Opportunity/Gap由来の場合） | 自動 | Universal |
| Recommendation Score | Rollup ← Source Signal.Recommendation Score/Opportunity Score | 自動 | Universal（拡張） |
| Record ID | Formula | 自動生成 | Universal |

計約18プロパティ。

#### ④ Formula

| Property | 実装方針 |
|---|---|
| **Days Until Planned** | `dateBetween(prop("Planned Date"), now(), "days")` |
| **Record ID** | `"CAL-" + format(id())` |

#### ⑤ Rollup

| Property | Relation元 | 集計内容 |
|---|---|---|
| Gap Type | Source Signal | Gap Typeを継承 |
| Opportunity Deadline | Source Signal | Opportunity Window Endを継承 |
| Urgency / Recommendation Score | Source Signal | それぞれの値を継承し、Editorial Priorities表示の並び替え軸にする |

#### ⑥ Relation

| Property | 相手DB | 方向 |
|---|---|---|
| Linked Article | Article | 双方向 |
| Linked Research | Research | 双方向 |
| Source Signal | Experience Intelligence | 双方向 |
| Assigned Owner | Mentor | 双方向 |
| Assigned AI Agent | AI Agents | 双方向 |
| Region | Region Master | 双方向 |

#### ⑦ View

- **今日の編集会議（最重要）**：Status≠Published/Cancelled を Urgency降順・Days Until Planned昇順でソート。**Today's Briefingと対になる、実行計画側のView**
- **カレンダー表示**：Planned DateのCalendar view
- **季節逃しアラート**：Opportunity Deadlineが7日以内かつStatus=Idea/Planned のフィルタTable
- **Gap Type別**：Gap Typeでグループ化
- **担当者別**：Assigned Ownerでグループ化

#### ⑧ Template

- **Gap由来テンプレート**：Source Signal必須、Gap Typeに応じた文言プリセット
- **Opportunity由来テンプレート**：Opportunity Deadline表示を強調し、締切超過前のリマインドを自動設定
- **自由起票テンプレート**：編集長が直接思いついた企画用（Source Signalなしでも作成可）

#### ⑨ Automation対象

- Experience Intelligence（Gap/Opportunity）がStatus=Actioned → 本DBへ自動起票
- Planned Dateの7日前でStatus=Idea/Planned → Owner／編集長へリマインド
- Opportunity Deadline経過 → Statusを自動でSkippedへ（機会を逃したことを可視化し、Knowledge Gap Engineの学習材料として残す）
- Linked Article.Status=Published → 本レコードのStatusを自動でPublishedへ

#### ⑩ AI利用方法

- **Gap Analysis Agent**：Actioned化と同時に、Planned Date・Assigned AI Agentの初期案を提示
- **制約**：Assigned Ownerの最終決定、Planned Dateの確定は人間が行う（AIは提案のみ）

---

### Dashboard連携プレビュー（Phase B1由来、正式設計はPhase B5）

ご指定の6セクションは、Phase B1の4DBだけで以下のようにデータ供給できる。

| セクション | データ源 | 集計方法 |
|---|---|---|
| **Today's Opportunities** | Experience Intelligence（Intelligence Type=Opportunity, Status=New/Acknowledged） | Opportunity Score降順 |
| **Today's Knowledge Gaps** | Experience Intelligence（Intelligence Type=Gap, Status=New） | Gap Severity降順、Legal Gapは常に最上段 |
| **Critical Updates** | Experience Intelligence（Gap Severity=Critical）＋ Article（Verification Status=Needs Recheck） | Urgency=Critical横断集計 |
| **Translation Queue** | Translation（Needs Re-Translation=Yes） | Review Level降順 |
| **Trending Topics** | Experience Intelligence（Intelligence Type=Trend） | Trend Signal Strength降順 |
| **Editorial Priorities** | Editorial Calendar（Status≠Published/Cancelled） | Urgency降順・Days Until Planned昇順 |

Dashboard自体のDB設計（Rollup定義・レイアウト）はPhase B5で確定するが、参照元のプロパティはすべて本Phase B1で確定済みのため、実装順序に問題は生じない。

---

*ARu HQ / Decode Japan — Notion Database Builder Spec v1 (Phase 1, Draft) — 2026-07-12*
