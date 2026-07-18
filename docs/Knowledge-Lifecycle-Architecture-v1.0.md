<title>ARu Knowledge Lifecycle Architecture v1.0</title>

# ARu Knowledge Lifecycle Architecture
### v1.0 — 知識の循環と時間経過にともなう変化の定義

| | |
|---|---|
| **Status** | Active（Vision／Specification。実装は一切含まない） |
| **Date** | 2026-07-18 |
| **対象読者** | ARuの編集・プロダクト・実装に関わるすべてのAI・人間 |
| **位置づけ** | 本書は「ARuの知識がどう循環し、時間とともにどう変化するか」を定義する、Architecture Session 03（最終）の成果物。[User-Journey-Architecture-v1.0.md](./User-Journey-Architecture-v1.0.md)（Why／ユーザー体験）→ 本書（知識の循環という時間軸）→ [Architecture-Specification-v1.0.md](./Architecture-Specification-v1.0.md)（How／技術構造）という3部作の中間に位置する |
| **命名についての注記** | 当初「ARu Knowledge Architecture」という名称で作成したが、[Architecture-Specification-v1.0.md §3](./Architecture-Specification-v1.0.md)の「Knowledge Architecture」（4つのKnowledge Domainの**静的な構造**を定義）と同名になり将来的な混同を招くと判断し、「**Knowledge Lifecycle Architecture**」へ改題した（2026-07-18、内容の変更は伴わない）。本書が扱うのは知識の**動的な流れ**（循環・進化・フィードバック）であり、静的な構造定義ではない |
| **本セッションの制約** | Architecture Session 03。コード実装・Pythonファイル変更・Notionスキーマ変更・コミットのいずれも行っていない |

> 本書のほぼ全体はVision（到達点の定義）である。既存の実装（Freshness Monitor、Editorial Content Lifecycle等）とは明示的に接続し、どこまでが現実で、どこからが構想かを区別する。

---

## 知識の循環系（全体像）

本書が扱う9つのテーマは、実は1つの循環の異なる断面である。

```
                    ┌─────────────────────────────────────┐
                    │                                       │
                    ▼                                       │
   [Story Lifecycle] → [Knowledge Lifecycle] → [公開されたContent]
                    ▲                                       │
                    │                                       ▼
        [Human Knowledge Integration]          [Article Evolution]
                    ▲                           [Deep Guide Evolution]
                    │                                       │
        [Mentor Feedback Loop] ←──────────────┐            │
                    ▲                          │            ▼
        [User Feedback Loop] ←─────────────────┴── [Long-term Content Maintenance]
                    │
        （すべての流れを貫く制約）
        [AI Learning Boundaries]
```

Story（アイデア）が生まれ、Knowledge（検証済みの事実）へと磨かれ、公開されたContentが時間とともに進化し（Article Evolution／Deep Guide Evolution）、その利用実態（User Feedback）と人の関与（Mentor Feedback、Human Knowledge Integration）が次のStoryを生む——これが1周である。この循環全体を通じて、AIがどこまで自律的に動いてよいか（AI Learning Boundaries）という制約が常にかかる。Long-term Content Maintenanceは、この循環を止めずに回し続けるための運用面の裏付けである。

---

## 1. Story Lifecycle

Storyのライフサイクル自体（Idea→Validated→Written→Deepened→Distributed→Sustained）は[User-Journey-Architecture-v1.0.md Chapter 5](./User-Journey-Architecture-v1.0.md)で定義済みであり、本書では再定義しない。ここでは、そのライフサイクルが本書の他の8テーマとどう接続するかだけを示す。

| Storyのフェーズ | 接続する既存Knowledge Domain／概念 |
|---|---|
| Idea | Human Knowledge Integration（8節）／User Feedback Loop（3節）が種を供給する |
| Validated | Research（Knowledge Domain）。[Architecture-Specification-v1.0.md §3](./Architecture-Specification-v1.0.md) |
| Written | Article（Content Ladder Level 2） |
| Deepened | Deep Guide（Content Ladder Level 3）。進化の詳細は6節 |
| Distributed | SNS Queue、将来的なPush Notification |
| Sustained | Article Evolution（5節）／Long-term Content Maintenance（9節）が引き継ぐ |

**Storyは「終わらない」。** Sustainedフェーズは終着点ではなく、Article Evolution・User Feedback Loop・Mentor Feedback Loopを通じて次のIdeaへ再び接続する（上記循環図を参照）。

---

## 2. Knowledge Lifecycle

### StoryとKnowledgeは別の層である

Story Lifecycleが「1つの編集アイデアの旅」であるのに対し、Knowledge Lifecycleは「1つの検証済みの事実が、公開されてから陳腐化し更新されるまでの旅」である。両者は密接に関係するが同一ではない——**Storyは棄却されて終わることがあるが（Research.Status=Rejected）、一度公開されたKnowledgeは、たとえ元のStoryへの関心が失われても、独立して鮮度管理され続ける。**

Knowledge Lifecycleの実体は、既に[Studio-Operating-Manual.md §9 Editorial Content Lifecycle](./Studio-Operating-Manual.md#9-editorial-content-lifecycle)が定義する13段階（①Source Discovery〜⑬Archive）そのものである。本書はこれを再定義せず、以下の対応関係だけを明確にする。

| 層 | 主な関心事 | 該当する既存定義 |
|---|---|---|
| Story層 | このアイデアは記事化する価値があるか | User-Journey-Architecture-v1.0.md Chapter 5 |
| Knowledge層 | この事実は今も正しいか、最新か | Editorial Content Lifecycle ①〜⑬（特に⑫Periodic Update、⑬Archive） |

Storyが「Written」フェーズに達した時点で、Knowledge Lifecycleが引き継ぐ。以降、そのKnowledgeは元のStoryとは独立して、Article Evolution（5節）・Deep Guide Evolution（6節）のルールに従って生き続ける。

---

## 3. User Feedback Loop

### これはLane 0「User Needs」と同一の概念である

以前のアーキテクチャ議論で、Source Discoveryを4レーン（Official／Events & Seasonal／User Needs／Trending & Lifestyle）に拡張する構想があり、Lane 0「User Needs」は「実運用の知見を踏まえて再検討する」方針で**意図的に保留**された。本節で定義するUser Feedback Loopは、**そのLane 0と同じものである**——新しい概念として扱わず、Lane 0の定義を「知識循環」という視点から言い換えたものと位置づける。

### 想定される流れ（🧭 全体が未実装。ARuアプリ側の計測機能に依存）

```
ユーザーがARuアプリでコンテンツを閲覧・検索
   ↓（未実装：アプリ側の計測・ログ機能が前提）
利用実態のシグナル（よく読まれる／答えが見つからず離脱／検索してもヒットしない）
   ↓
research_prioritizer.pyのFreshness／Foreign Resident Value等の既存スコアリング軸に
　「実需要」という新しい軸を追加する候補になる
   ↓
Coverage Analyzer／Editorial Plannerの優先順位づけに反映
   ↓
新しいStoryの着想（1節）へ
```

**このリポジトリはARuアプリ本体を含まないため、ユーザーの行動データそのものを取得する手段がない。** これは[User-Journey-Architecture-v1.0.md](./User-Journey-Architecture-v1.0.md)のOpen Questionsでも触れていない、本書で新たに明示する制約である。実装が可能になるのは、ARuアプリ側が何らかの形で利用実態データをこのリポジトリ側へ提供できるようになってから、という前提を明記する。

---

## 4. Mentor Feedback Loop

Mentor Chat／Mentor Session（Content Ladder Level 4／5、[User-Journey-Architecture-v1.0.md Chapter 6](./User-Journey-Architecture-v1.0.md)）は、単なる「その場限りの相談対応」で終わらせるべきではない。Mentorとのやり取りは、2つの独立したフィードバック経路を持つべきである。

### 経路A：新しいStoryの種になる

複数のユーザーが同じ論点についてMentorに相談している場合、それは「既存コンテンツでは解消できていない需要」を意味する。この気づきは、1節のStory Lifecycle「Idea」フェーズへの入力になる。

### 経路B：既存コンテンツの鮮度シグナルになる

Mentorは実在の専門家・実務者であり、実際の最新の現場対応を知っている。もしMentorが「この記事に書かれている手順はもう古い」と気づいた場合、それは`article_freshness_monitor.py`が現在参照している信号（Law Update／Source Monitor／Event Calendarの変化）とは**別の、人間発の鮮度シグナル**である。

**既存の`article_freshness_monitor.py`の`find_source_monitor_signals()`は、この種の人間発シグナルを受け取る経路を持っていない。** これは、9節Long-term Content Maintenanceとあわせて、将来のDevelopment Session候補として明示的に記録する（🧭未実装）。

---

## 5. Article Evolution

公開されたArticle（Level 2）は、2つの異なる軸で進化し得る。

### 軸A：鮮度を保つ（既存、実装済み）

`article_freshness_monitor.py`が担う、Update Levelごとのレビュー間隔・外部シグナルによる強制再レビュー——これは2節Knowledge Lifecycleの⑫Periodic Updateとして既に実装・運用されている。

### 軸B：深さへ進化する（🧭未実装、本書で新たに定義）

Articleの中の「Premium Section」に需要が集中する場合（実データで裏付けるなら、将来的なUser Feedback Loopやアクセス実態から判断することになる）、そのArticleはDeep Guide（Level 3）へ**昇格**し得る。これは「古くなったから直す」進化ではなく、「価値が確認されたから深める」進化であり、Knowledge Lifecycleの中でも独自の分岐として扱う必要がある。

両方の軸を1つの表にまとめる。

| 進化の種類 | トリガー | 既存実装との関係 |
|---|---|---|
| 鮮度維持 | Update Level経過期間、Law Update／Source Monitor／Event Calendar変化、Mentor Feedback（4節） | `article_freshness_monitor.py`（既存部分は実装済み、Mentor経路は未実装） |
| 深さへの昇格 | 需要の集中（User Feedback Loop、3節） | 未実装。Premium SectionからDeep Guideへの昇格ロジックそのものが存在しない |

---

## 6. Deep Guide Evolution

Deep Guide（Level 3）は、Article（Level 2）と同じ進化の仕組みをそのまま適用すべきではない。理由は2つある。

1. **陳腐化の速度が違う。** Deep Guideが含む「具体的な費用・予約方法・穴場情報」は、Articleの「文化的背景」よりもはるかに速く古くなる。Update Levelベースの一律のレビュー間隔（L1=90日等）をDeep Guideにそのまま適用すると、実態より遅れて陳腐化に気づくことになる——**Deep GuideはArticleより短いレビュー間隔を持つべき**というのが本書の提案（具体的な日数は実装判断）
2. **Deep Guideは新しいStoryの発見源になり得る。** Deep Guideを実際に使うユーザーは「実際にそこへ行く・それをする」段階に最も近い読者であり、そこで得られたMentor Feedback（4節）・User Feedback（3節）の密度は他のどのコンテンツ種別よりも高くなると想定される。**Deep Guideは知識循環図（冒頭）における最も濃いフィードバックのハブになる**、という位置づけを本書で明示する

---

## 7. AI Learning Boundaries

知識循環にフィードバックループ（3節・4節）が加わることで、新たな懸念が生まれる——**AIが、フィードバックを踏まえて自分自身の判断基準を無断で書き換えてしまうリスク**である。本節はこの懸念に対する境界線を、既存のConstitution原則の再確認とあわせて明文化する。

### 既存原則の再確認（✅ 既存、Constitutionでコード上も強制）

- Update Level 2・3のコンテンツは、AIのスコアに関わらず人間の最終承認が必須
- AIは公開（Published）そのものを実行しない
- 情報源を捏造しない。確認できない場合は「未確認」と明記する

### 本書が新たに明示する境界（フィードバックループ特有の論点）

| AIが自律的に行ってよいこと | AIが自律的に行ってはならないこと |
|---|---|
| シグナルの検出（Source Watcher等） | Storyを「価値がない」と判断し、記録を残さず破棄すること |
| 決定論的なスコアリング（`research_prioritizer.py`のような既存の重み付けロジックの**適用**） | フィードバックを踏まえて、スコアリングの**重み付けロジック自体を自己変更**すること——これは必ずDevelopment Sessionでの人間レビューを経る |
| 下書きの生成、要約、分類の提案 | Mentorの人間としての判断を、AIが後から上書き・再解釈すること |
| Article／Deep Guideの鮮度アラートを立てること | ユーザー・Mentorからのフィードバックのみを根拠に、記事を自動的に書き換えて再公開すること（人間レビューを経ずに） |

**この表の右列が、AI Learning Boundariesの核心である。** フィードバックループは「人間がより良い判断をするための材料」を増やすものであり、「AIがより自律的になる」ための手段ではない。

---

## 8. Human Knowledge Integration

Mentor・編集者が持つ知識がARuに取り込まれる経路は、AI出力を人間がレビューする経路（既存、Human Review First）とは**逆方向**であり、これまで明示的に設計されていなかった。

### 想定される経路（🧭未実装）

```
人間（Mentor／編集者）の知識・経験
   ↓
一般化可能か判断（個別事情なのか、多くの人に当てはまる知見なのか）
   ↓
一般化可能な場合 → Research候補として起票（Discovery Method="Human Insight"等、新しい識別子が必要）
   ↓
Evidence Level="Official"または"Verified"として、通常のKnowledge Lifecycleに合流
```

既存のResearch／Law Updateには、既に`Evidence Level`（Official／Verified／Reported／Rumor／AI Suggested）という選択肢がある。人間発の知見はここに自然に接続できる——**新しい選択肢を追加する必要すらなく、既存のプロパティで表現できる**という点は、実装コストの観点で重要な発見である。

一般化できない場合（本当に個別の事情）は、Research候補にはせず、Mentor Sessionの記録としてのみ残す（Content Ladder Level 5の範囲内で完結させる）。

---

## 9. Long-term Content Maintenance

知識循環を止めずに回し続けるための、運用上の裏付けを整理する。

### 既存の仕組み（✅ 実装済み）

- `article_freshness_monitor.py`：Update Levelごとのレビュー間隔管理
- `template_migration_report.py`：テンプレート準拠状況の可視化
- Dormant→Needs Update→Published（🧭設計合意済み、未実装。反復イベント向け）

### 本書が追加する視点：規模の限界（正直な指摘）

現在の記事数（約39件）であれば、Reiが個別にFreshness Statusを確認する運用は成立する。しかし本書のVisionが実現し、Content Domainsが広がり、Deep Guide・Mentor Feedbackが積み上がれば、**「何から手をつけるべきか」を人間が都度判断する現在のやり方は規模的に破綻する。**

対応として、以下を将来のDevelopment Session候補として明示する（🧭未実装）。

- 既存の`Priority`／`Urgency`／`Trust Score`（Universal Properties、[Architecture-Specification-v1.0.md §5](./Architecture-Specification-v1.0.md)）を用いた、**メンテナンス待ちコンテンツの優先順位付けスクリプト**（`research_prioritizer.py`と同種の決定論的ロジックを、鮮度管理側にも適用する）
- Mentor Feedback（4節）・User Feedback（3節）が実装された場合、その信号を上記の優先順位付けに統合する経路

現時点でこの優先順位付けの仕組みは存在しない。Freshness Monitorが検知したNeeds Updateの記事は、現状すべて同列に扱われている。

---

## Open Questions for Future Sessions

| # | 論点 | 関連節 |
|---|---|---|
| 1 | Article→Deep Guideへの「昇格」ロジックをどう判定するか（現状は需要データがなく判定不能） | 5節 |
| 2 | Deep Guideの適切なレビュー間隔（Update Levelベースの間隔より短くすべきという方向性のみ合意） | 6節 |
| 3 | Mentor Feedbackを`article_freshness_monitor.py`へ統合する具体的なデータ構造 | 4節・9節 |
| 4 | Human Knowledge Integrationの「一般化可能か」を誰が・どう判断するか（人間の裁量に委ねるのか、基準を明文化するのか） | 8節 |
| 5 | メンテナンス優先順位付けスクリプトの設計（`research_prioritizer.py`と同じ思想を転用できるか） | 9節 |
| 6 | User Feedback Loop実現のためにARuアプリ側へ何を依頼する必要があるか | 3節 |

これらはすべて、G3-B以降の実装、またはさらに別のArchitecture Sessionで扱うべき事項として記録する。

---

*ARu HQ / Decode Japan — ARu Knowledge Lifecycle Architecture v1.0 — 2026-07-18*
