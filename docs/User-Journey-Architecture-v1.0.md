<title>ARu User Journey & Content Architecture v1.0</title>

# ARu User Journey & Content Architecture
### v1.0 — 編集哲学とユーザージャーニーの定義

| | |
|---|---|
| **Status** | Active（Vision／Specification。実装は一切含まない） |
| **Date** | 2026-07-18 |
| **対象読者** | ARuの編集・プロダクト・実装に関わるすべてのAI・人間 |
| **位置づけ** | 本書は「ARuというサービスがユーザーにとって何であるべきか（Why／What）」を定義する。[Architecture-Specification-v1.0.md](./Architecture-Specification-v1.0.md)が「どう構築されているか（技術的なKnowledge Architecture）」を定義するのに対し、本書はその**上位**に位置する——今後のテンプレート設計（Event Template、Law Template、Experience Template等）は、本書が定義するユーザー体験に奉仕する形で設計されるべきである |
| **本セッションの制約** | Architecture Session 02。コード実装・Pythonファイル変更・Notionスキーマ変更・コミットのいずれも行っていない。本書は新規ドキュメントの作成のみ |

> 本書のほぼ全体はVision（到達点の定義）であり、現時点で実装されているものではない。すでに存在する要素（Constitution Mission、Category分類、Deferred状態のMentor DB等）とは明示的に接続し、既存資産の上に vision を積み上げていることを示す。存在しないものを存在するかのようには書かない。

---

## Chapter 1 — Mission

### ARuの目的は「質問に答えること」ではない

[ARu Constitution](./ARu-Constitution.md)が定めるMission——「AIが調査・執筆・翻訳・SNSを担当し、人は最終確認だけを行う体制を作る」——は運営体制の定義であり、**ユーザーにとってARuが何をしてくれる存在なのか**を定義するものではなかった。本章はそのギャップを埋める。

ARuの目的は、外国籍の方・訪日者が以下を実現できるよう支援することである。

- **日本で安全に暮らす**（live safely）
- **新しい体験を発見する**（discover new experiences）
- **日本文化を楽しむ**（enjoy Japanese culture）
- **地域コミュニティとつながる**（connect with local communities）
- **不安を減らす**（reduce anxiety）
- **どこに助けを求めればよいかを知る**（know where to ask for help）

これは「答え」の提供では終わらない。**質問に答えることはARuの入口であって、目的地ではない。**

### 目指すべき感情

ユーザーがARuに対して抱くべき感情は、1つの言葉に集約される。

> **「何から始めればいいか分からないけど、ARuがあれば大丈夫」**
> ("I don't know where to start, but ARu will guide me.")

この感情は、単発の正確な回答の積み重ねだけでは生まれない。Chapter 2〜7で定義するユーザージャーニー・コンテンツラダー・Human Layerが揃って初めて成立する、**ARu全体の設計目標**である。

---

## Chapter 2 — User Journey

ユーザーがARuと関わり続ける全体の流れを、6つの段階として定義する。

```
Arrival（到着期）
   ↓
Daily Life（日常生活）
   ↓
Discovery（発見）
   ↓
Experience（体験）
   ↓
Community（つながり）
   ↓
Support（支援）
```

**この流れは一方通行ではない。** Arrival後もDaily LifeとSupportの間を行き来し続け、Discovery→Experience→Communityは滞在期間を通じて何度も繰り返される循環である。[Studio-Operating-Manual.md §9](./Studio-Operating-Manual.md#editorial-philosophy)のEditorial Philosophyが「Deliverされた知識がDiscoverの入力へ再び戻る」循環を定義しているのと同じ構造が、ユーザー体験の側にも存在する。

### 各段階の目的

| 段階 | 目的 | 典型的な状況 |
|---|---|---|
| **Arrival** | 来日直後の「何をすればいいか分からない」不安を最小化する | 在留カード、住民登録、口座開設、携帯契約——高リスクで一度きりの手続きが集中する時期 |
| **Daily Life** | 継続する生活のための実務知識を提供し続ける | 税金、保険、更新手続き、住居、交通——滞在中ずっと発生し続ける事柄 |
| **Discovery** | 日本という国自体への好奇心に応える | 文化的背景、なぜこうなのか、まだ知らない日本 |
| **Experience** | 発見したことを実際の行動に変える | 祭り・花火・季節イベントへ実際に足を運ぶ |
| **Community** | 一人ではないと感じられる場をつなぐ | 言語交流、地域コミュニティ、ボランティア |
| **Support** | 一人で抱えきれない状況に、信頼できる人がいると保証する | 複雑な法的問題、健康不安、個別事情の相談 |

Arrival・Daily Lifeは主に「不安を減らす」（Chapter 1）を担い、Discovery・Experience・Communityは「発見・文化・つながり」を担い、Supportは「助けを求める先を知る」を担う。6段階すべてが揃って初めて、Chapter 1のMission全体をカバーする。

---

## Chapter 3 — Content Ladder

ユーザーが必要とする関与の深さは一様ではない。5段階のContent Ladderを定義する。

| Level | 名称 | 役割 |
|---|---|---|
| **1** | QA Card | 即座の短い答え |
| **2** | Article | トピックを説明する |
| **3** | Deep Guide（Premium） | 詳細なローカル知識・実例・コツ・モデルコース・穴場情報 |
| **4** | Mentor Chat | 個人的な安心感、簡単な相談 |
| **5** | Mentor Session | 個別対応、専門的な支援 |

### 各レベルの目的

- **Level 1 QA Card**：「今すぐ知りたい1つの答え」に最短距離で応える。読むのに数秒〜十数秒で完結する
- **Level 2 Article**：QA Cardだけでは足りない背景・理由・文脈を説明する。ARu公式テンプレート（8セクション）が担う領域はここ
- **Level 3 Deep Guide（Premium）**：読むだけでなく「実際に行動する」ことを後押しする。具体的な場所、タイミング、費用、モデルコース、あまり知られていない情報
- **Level 4 Mentor Chat**：コンテンツでは解消しきれない「これで合っているか不安」という感情に、人（またはそれに近い存在）が応答する
- **Level 5 Mentor Session**：個別の状況が複雑で、専門的な判断が必要な場合に、実際の専門家が対応する

### レベル間の自然な移動

```
QA Card（即答）
   ↓ 「もっと知りたい」
Article（理解を深める）
   ↓ 「実際にやってみたい」
Deep Guide（行動に移す）
   ↓ 「これで本当に合っているか不安」
Mentor Chat（安心感を得る）
   ↓ 「自分の状況は特殊で、個別の判断が必要」
Mentor Session（専門的な解決）
```

Level 1〜3はAIが生成するコンテンツの「深さ」の軸であり、Level 4〜5は「人の関与」の軸である。ユーザーは必ずしもLevel 1から順に上がる必要はなく、状況によってどのレベルからでも入ってこられる（例：SNSで見た祭り情報からいきなりDeep Guideへ、またはいきなりMentor Chatへ）。

### 既存アーキテクチャとの接続・要調整点

- **Level 2 Article**は、[Architecture-Specification-v1.0.md](./Architecture-Specification-v1.0.md)で定義したArticle Template Framework（G3-A、実装済み）がそのまま該当する
- **Level 3 Deep Guide**は、現行のStandardテンプレートに含まれる「Premium Section」（Articleの1セクション）を、独立した1つのコンテンツ単位へ引き上げたものに相当する。今日のPremium Sectionが「種」であり、需要のあるトピックがLevel 3へ育つ、という関係性になり得る——これは実装判断であり本書では決定しない
- **Level 1 QA Card**という名称は、[Studio-Operating-Manual.md §9](./Studio-Operating-Manual.md#9-editorial-content-lifecycle)のEditorial Content Lifecycle ④「QA Card」（🧭執筆前の品質チェックポイントとして定義）とは**意味が異なる**。あちらは「執筆前のゲート」、本書のLevel 1は「独立した完成コンテンツ」である。**この用語の意味の食い違いは、次のArchitecture Sessionで明示的に解消すべき既知の論点として記録する**
- **Level 4／5 Mentor Chat・Mentor Session**は、Chapter 6で詳述する

---

## Chapter 4 — Content Domains

ARuが扱う主要な生活・体験領域を定義する。

| Domain | 役割 |
|---|---|
| Daily Life | 日々の暮らしの実務全般（ゴミ出し、買い物、公共料金等） |
| Government | 行政手続き（住民登録、各種証明書、届出） |
| Medical | 医療機関へのアクセス、健康保険制度、症状別の対応 |
| Transportation | 公共交通機関の使い方、ICカード、乗り換え |
| Housing | 賃貸契約、引っ越し、近隣トラブル |
| Japanese Language | 言語学習、日本語交流、敬語・コミュニケーション |
| Food | 食文化、飲食店の利用、食material の入手 |
| Culture | 慣習・マナー・宗教・歴史的背景 |
| Festivals | 祭り、伝統行事 |
| Fireworks | 花火大会（Festivalsの中でも象徴性が高く独立して扱う価値がある） |
| Events | 一過性の催事・展示・マルシェ等 |
| Community | 地域コミュニティ、国際交流協会等とのつながり |
| Volunteering | ボランティア活動への参加 |
| Experiences | 体験型のアクティビティ（伝統工芸体験等） |
| Travel | 旅行・観光情報 |
| Seasonal Information | 季節ごとの話題・注意事項 |
| Work | 就労・転職・労務関連 |
| Education | 教育制度、就学、進学 |
| Emergency | 災害・急病等の緊急対応 |
| Finance | 税金、銀行、保険、年金 |
| Driving | 運転免許、交通ルール |
| （Etc.） | 上記に収まらない新規領域は、新規Categoryではなくまず既存領域のSub Categoryとして検討する（下記参照） |

### 既存のCategory分類との接続（重要）

現行のResearch DBは既に7つのCategory（法律・制度／イベント／日本文化／旅行情報／生活情報／ニュース／トレンド）を持ち、[Architecture-Specification-v1.0.md §6](./Architecture-Specification-v1.0.md)は「トップレベルCategoryを増やし続けるのではなく、Sub Categoryの階層で対応する」方針を既に定めている。本章の21ドメインは、まさにそのSub Categoryの実体候補になる。

| 既存Category | 対応する本章のDomain（Sub Category候補） |
|---|---|
| 法律・制度 | Government, Work（労務）, Finance（税務）, Driving, Emergency（法制度面） |
| 生活情報 | Daily Life, Medical, Transportation, Housing, Education |
| 日本文化 | Japanese Language, Culture, Food |
| イベント | Festivals, Fireworks, Events, Community, Volunteering |
| 旅行情報 | Travel, Experiences, Seasonal Information |
| ニュース／トレンド | （季節性の高いDomain横断の速報が該当） |

新しいドメインが必要になった場合も、**まずこの表のどこかに収まらないかを確認してから**、真に既存7分類のいずれにも属さない場合のみ新規Categoryの追加を検討する（Design Principle：Category拡張よりSub Category優先）。

---

## Chapter 5 — Story Bank

### Story BankはArticleではない

Story Bankは、**まだ記事化されていない編集アイデアの図書館**である。1つの「Story」はまだ1つの記事ではなく、複数の成果物を生み出す種である。

```
Story（アイデア）
   ↓
Research（裏取り・検討）
   ↓
Article（記事化）
   ↓
Premium Guide（Deep Guideへの深化）
   ↓
Instagram（SNS展開）
   ↓
Threads（SNS展開）
   ↓
Future updates（継続的な更新）
```

### Storyのライフサイクル

| フェーズ | 内容 |
|---|---|
| Idea | 編集者・AIが「これは良いStoryになる」と直感した段階。まだ裏取りされていない |
| Validated | Researchとして裏取り・優先順位付けされ、記事化の是非が判断される段階 |
| Written | Article（Level 2）として文章化される |
| Deepened | 需要が確認された場合、Deep Guide（Level 3）へ深化する |
| Distributed | Instagram・Threads等、SNSへ展開される |
| Sustained | 公開後も定期的に見直され、鮮度を保つ（Editorial Content Lifecycle ⑫ Periodic Updateと同じ仕組みに接続する） |

### 既存アーキテクチャとの接続・要調整点

Story Bankという概念は、既存の**Experience Intelligence**（Knowledge Domain、Gap／Opportunity／Trend／Event／Culture／Local／Userという信号を検出する層）と**強く重なる**。Experience Intelligenceが機械的・AI主導の信号検出であるのに対し、Story Bankは編集者の直感・企画力を起点とした、より人間主導のアイデア管理という位置づけになり得るが、**両者が別々の実体を持つべきか、Experience Intelligenceの一部（例えばIntelligence Type="Story"の追加）として扱うべきかは未決定**。「新規データベースを作らない」原則に照らせば後者が有力だが、これは実装判断であり、次のArchitecture Sessionまたは実際のDevelopment Session着手前に明示的に決定すべき論点として記録する。

同様に、Story一つが Research→Article→Premium Guide→SNS×2 という複数成果物を生むという構造は、[Architecture-Specification-v1.0.md §7](./Architecture-Specification-v1.0.md)で定義した**ハブ＆スポーク型生成モデル**（単一の検証済みKnowledge Domainレコードから複数成果物が並行生成される）と本質的に同じ思想である。Storyという概念は、これまでEvent限定で検討していたハブ＆スポークモデルを、**全コンテンツ領域に一般化した際の「ハブ」そのもの**と理解するのが最も整合的である。

---

## Chapter 6 — Human Layer

### AIが最初に答え、人が最後に寄り添う

Content Ladder（Chapter 3）を編集哲学として言い換えると、以下の順序になる。

1. **AIがまず答える**（QA Card／Article）
2. **Articleが理解を深める**
3. **Deep Guideが行動を後押しする**
4. **Mentor Chatが安心感を与える**
5. **Mentor Sessionが個人の状況を解決する**

Level 4・5はAIコンテンツでは代替できない領域である。**「これで合っているか、誰かに確認してほしい」という感情は、どれだけ正確な記事でも解消しない。** ここに応えられるかどうかが、ARuと「よくできたFAQサイト」を分ける決定的な違いになる。

### 既存アーキテクチャとの接続（重要な発見）

Mentor機能は、実は本書で初めて登場する概念ではない。[Roadmap.md](./Roadmap.md)・[AI-Handover.md](./AI-Handover.md)は、Version 2の段階で既に**Mentorを「Deferred（実装保留）」データベースの1つ**として明記しており、理由は「現状、専門家レビューは都度手配（[Operating-Manual.md](./Operating-Manual.md) §7参照）」となっている。

つまり、Mentor機能に対する**必要性はすでに認識されていたが、それをユーザー体験のどこに位置づけるべきかという設計が本書以前には存在しなかった**。本章は、その空白を埋めるものである。Mentor DBをいつ実装するかは別途判断が必要だが、「なぜ必要か」「どこで使われるか」（Level 4／5、Content Ladderの最終段階）は本書によって初めて明確になった。

### なぜこれがARuの競争優位性か

- 一般的な検索エンジン・生成AIチャットは「答える」ことはできても、「その答えが自分の状況に本当に当てはまるか」を保証できない
- ARuのMentor Chat／Mentor Sessionは、AIが生成した理解の土台（QA Card／Article／Deep Guide）の上に、**実在する・検証された人間**が乗ることで、外国籍の方が最も必要としている「誰かが自分の状況を分かってくれている」という感覚を提供できる
- これはコンテンツだけでは模倣できない。競合がAIで同水準の記事を量産できたとしても、**信頼できるMentorのネットワークとそこへの導線**は容易に複製できない

---

## Chapter 7 — Editorial Principles

### すべての記事が答えるべき3つの問い

1. **なぜこれが重要なのか？**（Why does this matter?）
2. **なぜ外国籍の方がこれを知るべきなのか？**（Why should foreigners know this?）
3. **次に何をすべきか？**（What action should they take next?）

これらはARu公式テンプレートの既存セクション（Cultural Background＝1・2に対応、ARu Tip＝3に対応）と整合しているが、本章はこれを**すべての記事が満たすべき編集チェック項目**として明文化する。

### 記事は最終目的地ではない

すべての記事は、以下6つの行動のいずれかへユーザーを導かなければならない。

- 別の記事を読む（Read another article）
- イベントを見つける（Discover an event）
- 体験してみる（Try an experience）
- コミュニティに参加する（Join a community）
- Mentorに相談する（Ask a mentor）
- Mentor Sessionを予約する（Book a mentor session）

**記事は目的地ではなく、次のステップへの通過点である。** この原則は、Chapter 2のUser Journey（段階間の移動）とChapter 3のContent Ladder（レベル間の移動）を、記事という最小単位のレベルで実現するものである。

### 既存アーキテクチャとの接続・要調整点

現行のArticles DBには、記事間の関連性を表す`Knowledge Links`（Related Articles）リレーションが既に存在する。本章の原則を実現するには、この関連性の対象を**記事間だけでなく、Event Calendar・Community・（将来的な）Mentorドメインへも広げる**必要がある——これは新しいリレーションの追加を意味し、実装判断としてDevelopment Session側での検討が必要になる。

同様に、`reviewer_agent.py`の決定論的チェック（現在はARu Tipの有無を機械的に検証している）に、**「次のステップへの導線が最低1つ含まれているか」**という同種のチェックを将来追加する余地がある。これも本書では決定せず、次の実装セッションへの示唆として記録するに留める。

---

## Open Questions for Future Sessions（本書が意図的に未決定のまま残した論点）

| # | 論点 | 関連章 |
|---|---|---|
| 1 | Level 1「QA Card」と、Editorial Content Lifecycle ④「QA Card」（執筆前ゲート）の用語衝突をどう解消するか | Chapter 3 |
| 2 | Level 3「Deep Guide」は、既存のPremium Sectionが成長したものとして実装するか、独立した新しいコンテンツ単位として実装するか | Chapter 3 |
| 3 | Story Bankは独立した新しい概念として実装するか、既存のExperience Intelligence（Intelligence Type拡張）として実装するか | Chapter 5 |
| 4 | Mentor DB（Deferred）の実装着手の是非・タイミング | Chapter 6 |
| 5 | `Knowledge Links`をArticle間だけでなくEvent／Community／Mentorドメインへ拡張するリレーション設計 | Chapter 7 |
| 6 | `reviewer_agent.py`への「次のステップ導線チェック」追加の要否 | Chapter 7 |

これらはすべて、本書のVisionを実際のG3-B以降のテンプレート設計・実装へ落とし込む際に、改めてArchitecture SessionまたはDevelopment Sessionで決定すべき事項である。

---

*ARu HQ / Decode Japan — ARu User Journey & Content Architecture v1.0 — 2026-07-18*
