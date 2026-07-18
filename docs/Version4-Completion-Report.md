<title>ARu Studio Version4 Completion Report</title>

# ARu Studio Version4 Completion Report
### Version4の完了と、Version5への出発点の定義

| | |
|---|---|
| **Status** | Active（公式のVersion4クローズレポート） |
| **Date** | 2026-07-18 |
| **対象読者** | 将来の開発者・協働者・ステークホルダー全員 |
| **位置づけ** | Version4フェーズの正式なクロージングレポート。実装・スキーマ・Architecture文書のいずれも変更しない、文書作成のみのDocumentation Session成果物 |
| **⚠️ 命名についての重要な注記** | 本書が「Version4」と呼ぶものは、[Roadmap.md](./Roadmap.md)が定義する**「Version 4 — Enterprise」**（自治体連携・JNTO連携・企業向けダッシュボード・Mentorネットワーク本格拡大という対外的な事業判断を伴う本体、現状0/5・未着手）とは**異なる**。本書の「Version4」は、Roadmap.mdが「Version 4準備作業」と呼ぶ技術的土台（9/9完了）に加え、その後追加で行われたARu公式記事テンプレート再設計・3文書のArchitecture Phase・Article Template Framework（G3-A／G3-B）までを含む、**エンジニアリング上の一まとまりの区切り**を指す。Roadmap.mdの「Version 4 — Enterprise」本体は、本書の内容とは独立して、引き続き0/5・対外的な意思決定待ちのままである |

---

## 1. Executive Summary

Version4は、ARu Studioが「動くパイプライン」から「文書化された原則と、実証済みの拡張パターンを持つアーキテクチャ」へ移行したフェーズである。

**目指したこと**：Version 4（Enterprise）着手前に必要となる技術的土台（記事の鮮度管理、コンテンツギャップ分析、編集優先順位付け、公開管理、重複防止、編集長の体験改善、情報源監視の高度化）を固めること。

**成し遂げたこと**：上記9項目の技術的土台をすべて実データで完了させたのに加え、当初のスコープを超えて以下を達成した。

- ARu公式記事テンプレートを9セクションから8セクションへ再設計し、ブランド品質を標準化
- 3回のArchitecture Sessionを経て、技術・ユーザー体験・知識循環という3つの観点からARu Studioの原則を初めて文書化
- 単一のテンプレートしか扱えなかった仕組みを、複数テンプレートを安全に追加できる**Article Template Framework**へ発展させ、Eventテンプレートという実際の2つ目の実装で証明した

**なぜこれがARu Studioにとって大きな節目か**：これまでのARu Studioの成長は、機能を1つずつ実データで検証しながら積み上げる形で進んできた（実際、この規律自体がVersion4を通じて繰り返し有効性を証明した——6節で詳述）。Version4は、その積み上げの先に**初めて「なぜこう作るのか」を明文化した原則**を持ち込んだフェーズである。今後の拡張（新しいテンプレート、Mentor機能、Deep Guide等）は、都度ゼロから設計判断をやり直すのではなく、この原則と実証済みのパターンを土台にできる。

---

## 2. Major Achievements

### Architecture Phase

- **[Architecture-Specification-v1.0.md](./Architecture-Specification-v1.0.md)**：Knowledge Architecture（4つのKnowledge Domain）、Universal Properties、Category／Sub Category原則、Generation Rules、Architectural Constraints。Glossaryと17件のArchitecture Decision Logを含む
- **[User-Journey-Architecture-v1.0.md](./User-Journey-Architecture-v1.0.md)**：Mission、6段階のUser Journey、5段階のContent Ladder、Content Domains、Story Bank、Human Layer、Editorial Principles
- **[Knowledge-Lifecycle-Architecture-v1.0.md](./Knowledge-Lifecycle-Architecture-v1.0.md)**：Story／Knowledgeの2層のライフサイクル、User／Mentorフィードバックループ、Article／Deep Guideの進化、AI Learning Boundaries、Human Knowledge Integration、Long-term Content Maintenance

### Development

- **G3-A Template Framework**：`article_template.py`を単一テンプレート実装から`TEMPLATES`レジストリへリファクタリング。既存4スクリプトを無改修のまま、Standardテンプレートの振る舞いをバイトレベルで完全一致させたまま完了
- **G3-B Event Template**：レジストリへ`"event"`を第2エントリとして追加。`template_for_category()`によるCategory→テンプレートの一元的な振り分けを実装し、実データで「Standardへのフォールバックが起きない」ことを確認

### Documentation

- **AI-Handover.md**：Current Automation／Completed Featuresへの継続的な追記、Latest Commitフィールドの運用
- **Automation-Scripts.md**：v2.2→v2.3→v2.4と版を重ね、実データでのテスト結果を都度記録
- **Git workflow**：「`feat:`コミット→実コミットハッシュを埋めるフォローアップコミット」という2段階コミット規約の一貫した運用。Development／Documentation／Release Sessionという作業の型を[Studio-Operating-Manual.md](./Studio-Operating-Manual.md)として明文化
- **Rollback Criteria**：G3-Aで初めて正式に導入し、G3-Bではユーザー自身の追加指示（「Standard構成へのフォールバックが起きた場合は全面ロールバック」）によって拡張された、実装前に定義する客観的な失敗条件という規律

---

## 3. New Capabilities

Version4を経て、ARu Studioは以前にはできなかった以下のことができるようになった。

- **複数の記事テンプレート**：Standard（永続的な疑問への回答）とEvent（日時・場所を持つ体験）という、性質の異なる2つのテンプレートを同じ基盤で扱える
- **Category起点の自動テンプレート振り分け**：`template_for_category()`により、記事のCategoryさえ正しく設定されていれば、生成・レビュー・レンダリング・移行判定のすべてが自動的に正しいテンプレートを使う。人間が都度テンプレートを選ぶ必要がない
- **Event記事の生成**：日時・場所・費用・現金対応・英語対応等を前面に出したBefore You Go構成の記事を、実データで生成・検証済み
- **テンプレート対応のReviewer**：`reviewer_agent.py`が、記事がどのテンプレートに属するかを判定したうえで、そのテンプレート固有の必須セクションをチェックする
- **テンプレート対応のRenderer**：`render_article_layout.py`が、テンプレートごとに異なるセクション構成・折りたたみ方針で正しく描画する
- **拡張可能なアーキテクチャ**：新しいテンプレート（Law、Guide、Medical等）を追加するコストが、G3-A以前の「テンプレートを丸ごと再設計する」規模から、「レジストリへ1エントリを追加する」規模へ縮小した——これはまだ実証段階（Event 1件のみ）だが、Standard→Eventという実例が1つ存在することの意味は大きい

---

## 4. Architectural Outcomes

Version4を通じて確立された、技術文書だけでは表現できない原則を以下にまとめる。

- **User Journey**（Arrival→Daily Life→Discovery→Experience→Community→Support）：すべてのコンテンツ判断に「これは読者の滞在のどの時点に向けたものか」という軸を与える
- **Content Ladder**（QA Card→Article→Deep Guide→Mentor Chat→Mentor Session）：なぜ複数のテンプレート・複数の関与の深さが必要なのかに、初めて原則的な理由を与えた
- **Human Layer**：Version 2からDeferred状態のまま放置されていたMentor機能に、初めて「なぜ必要か」「どこで使われるか」という設計上の位置づけを与えた
- **Story Bank**：Researchを「記事化前の候補」としてだけでなく、Article・Premium Guide・SNS投稿・将来の更新までを生み出す1つのアイデアの旅として捉え直した
- **Knowledge Lifecycle**：「編集アイデアの旅（Story）」と「検証済み事実の維持（Knowledge）」を別の層として区別し、User Feedback LoopやMentor Feedback Loopが将来どこに接続されるべきかを示した

**これらが重要な理由**：これらの原則があることで、将来のどのDevelopment SessionやArchitecture Session（そしてどのAI——Claude・ChatGPT・その他）も、新しい設計判断をゼロから議論するのではなく、既存の原則と照らし合わせて評価できる。これは実際に、Architecture Decision Logが「却下された案（Event Calendarの汎用Content Hub化、物理的なDB統合等）」を記録していることで、同じ議論を将来繰り返さずに済むという形で既に機能している。

---

## 5. Project Health

- **Working tree status**：クリーン。ローカルの`main`は`origin/main`より6コミット先行（未push）
- **Regression status**：標準7スクリプト回帰テスト、`template_migration_report.py`、および実データでの生成・レビュー・レンダリングテストが、Version4内の全コミット時点で正常完走。G3-A・G3-Bともに、Standardテンプレートの振る舞いがバイトレベルで無変化であることを確認済み
- **Documentation status**：`AI-Handover.md`・`Automation-Scripts.md`は最新コミットまで反映済み。3本のArchitecture文書は相互参照済み
- **既知のドキュメント上のギャップ**：`Roadmap.md`が、ARu Intelligence Phase 1〜3・ARu公式記事テンプレート再設計・本書が扱うArchitecture Phase／Template Frameworkのいずれも反映していない。これは複数のセッションで繰り返し指摘されてきたが（`Version4-Status.md` 4節22項等）、未解消のまま残っている
- **Technical debt（既知、優先度順ではなく列挙）**：
  - Research／Law Update／Event Calendar間のリレーション名の不統一（`Converted Article`／`Affected Articles`／`Related Article`、`Audience`／`Impact Scope`）
  - Archived記事のFreshness Statusが自動でクリアされない（根本原因未修正）
  - G4（Event Calendarスキーマ拡張：`Cost`／`Cash Only`／`English Support`等）が未着手のまま保留
  - `QA Status`プロパティが全記事で未設定のまま
  - Source Libraryの実監視網が10件のみ（想定される規模には遠い）
- **未解決の論点**：[User-Journey-Architecture-v1.0.md](./User-Journey-Architecture-v1.0.md)と[Knowledge-Lifecycle-Architecture-v1.0.md](./Knowledge-Lifecycle-Architecture-v1.0.md)それぞれのOpen Questions節（QA Cardの用語衝突、Deep GuideとPremium Sectionの関係、Story BankとExperience Intelligenceの重複、Mentor DB着手判断、User Feedback LoopのARuアプリ依存等）は、いずれも未解決のまま次のセッションに引き継がれている

---

## 6. Lessons Learned

**有効だった判断**：

- **実装より先にArchitectureを固めたこと**：G3-Bのコード自体は、3本のArchitecture文書がテンプレートの名称・構成・優先順位に関する曖昧さを先に解消していたため、比較的速く・迷いなく実装できた
- **G3をG3-A／G3-Bへ分割したこと**：フレームワークのリスクと機能のリスクを分離した結果、G3-Aの完了条件を完全に独立して検証でき、後にG3-Bで問題が起きても原因の切り分けが容易になる設計になった
- **Exit CriteriaとRollback Criteriaを実装前に定義したこと**：「なんとなく終わった感じ」ではなく、客観的な停止条件を持てた
- **既存のUniversal Propertiesを再利用したこと**：新しいプロパティを都度追加するのではなく、既存の`Evidence Level`・`Trust Score`等を将来の機能（Human Knowledge Integration等）の受け皿として再利用する判断を重ねたことで、「新規データベースを作らない」原則が単なるスローガンではなく実際に機能する制約であることが繰り返し証明された

**繰り返すべきでないこと**：

- **新しい文書・概念の命名時に、既存の名称との衝突を確認し忘れるリスク**：「Version 5」（Roadmap.mdの既存定義と衝突）、「Knowledge Architecture」（Architecture-Specification-v1.0.md §3との衝突）はいずれも都度発見・是正できたが、これは仕組みによる防止ではなく、その都度の注意によるものだった。今後は新しい文書・概念を確定する前に、既存の文書タイトル・節タイトルを確認する習慣を明示的に持つべきである

**Architecture-firstが実装品質をどう改善したか**：G3-Bのコードが書かれる時点で、「Standard構成へのフォールバック」という失敗モードは、バグとして発見されたものではなく、あらかじめ名前がついた・想定された失敗モードとしてRollback Criterionに組み込まれていた。その結果、検証はこの失敗モードを狙って確認する形になり、「見た目問題なさそうだから大丈夫」という曖昧な確信ではなく、明確な合格を得ることができた。

---

## 7. Looking Ahead（Version5）

以下は方向性のみであり、実装の詳細は定義しない。

- **Editorial Intelligence**：Coverage Analyzer・Editorial PlannerとStory Bankの関係を深化させ、「AIがテーマを提案する」段階から「AIが編集会議そのものを支援する」段階へ
- **Story Bank evolution**：Story BankをExperience Intelligenceの拡張として実装するか独立した概念とするかを決定し、実際の日々の運用へ組み込む
- **Content maintenance**：Knowledge Lifecycle Architectureが指摘した長期的なメンテナンスの規模の限界に対応する、優先順位付けの仕組みを検討する
- **Premium strategy**：Deep Guide（Content Ladder Level 3）を、Articleに埋め込まれた1セクションではなく独立したコンテンツ種別として扱うかどうか、実際の読者需要をもとに検討する
- **Mentor knowledge integration**：Version 2から保留されているMentor DBに、User-Journey-Architectureが与えた位置づけをもとに初めて具体的な設計検討を行う
- **Continuous improvement**：G3-A／G3-Bで実証したTemplate Frameworkのパターンを、実際の需要が確認された段階でLaw・Guide・Medical等へ広げていく（先回りして speculative に作らない）

---

## 8. Final Assessment

**なぜVersion4は完了と言えるか**：計画された技術的土台（9項目）はすべて実データで完了し、今後の成長を安全かつ原則に沿って進めるために必要なアーキテクチャ（3文書）が、レビュー可能な形で文書化された。Template Frameworkは、Standard・Eventという2つの実装によって拡張パターンとして実証され、その全過程が実データに対する検証を伴っていた——推測や「動きそうだから良し」ではない。

**なぜARu Studioは今Version5に進む準備ができているか**：今後の作業（新しいテンプレート、Mentor機能、Deep Guide、フィードバックループ）は、(1) 拡張のための実証済みの技術パターン（Template Framework）、(2) 設計判断を照らし合わせるための文書化された哲学（3本のArchitecture文書）、(3) リスクを事前に発見してきた実績のある作業規律（Development／Documentation／Release Session、Exit／Rollback Criteria）という3つの土台の上に乗ることができる。

**最後にもう一度**：本書の「Version4完了」は、[Roadmap.md](./Roadmap.md)の「Version 4 — Enterprise」（自治体・JNTO連携等、対外的な意思決定を要する本体）の完了を意味しない。あちらは引き続き0/5・未着手のままである。本書が完了と述べるのは、それに先立つ技術的土台とアーキテクチャの整備が完了した、という意味に限定される。

---

*ARu HQ / Decode Japan — ARu Studio Version4 Completion Report — 2026-07-18*
