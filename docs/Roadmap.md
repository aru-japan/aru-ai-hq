<title>ARu Studio Roadmap v2</title>

# ARu Studio Roadmap
### Version 2

| | |
|---|---|
| **Status** | Active |
| **Date** | 2026-07-12 |
| **位置づけ** | ARu Constitution §19 Future Expansion Policyを、実際のバージョン計画に落とし込んだもの |
| **関連文書** | [AI Handover Document](./AI-Handover.md)（将来のAI向け引き継ぎ文書。本Roadmapの要約も含む） |

---

## 実装順序の最適化について（重要）

Version 2・3で新規に必要となる6DB（Language Master／Region Master／Mentor／AI Agents／Prompt Library／Automation）は、**目標から削除しない。実装順序のみを変更し、`Deferred（実装保留）`として扱う。**

方針：まず**新規DBを追加せず、既存10DB（Articles／Research／Translation／Source Library／Editorial Calendar／Experience Intelligence／Source Monitor／Law Update／Event Calendar／SNS Queue）を最大限活用したPython自動化**を完成させる。実運用でDeferred項目の必要性が実際に確認できた段階で、個別に再評価・実装する。

---

## Version 1 — Foundation（完成）

**目的**：編集部が実際に動ける最小構成を作る。

- ARu Constitution v2.0.0（運営憲章）
- AI Agent Constitution v1.1.0（AI各役割の責務・権限・禁止事項）
- ER Design ／ Notion Database Builder Spec（全17DB設計、Universal Properties確定）
- **実装済み5DB**：Articles／Research／Translation／Source Library／Editorial Calendar
- View（Daily／Weekly／Review／Archive）／Article・Research・Translation Template
- ARu Studio Operating Manual（日次・週次・月次・緊急対応・法改正対応の手順）

---

## Version 2 — AI Intelligence（完了。一部Deferred）

**目的**：ARuが「今何が起きているか」「何が足りないか」を自ら認識できるようにする。

**実装済み**

- **Experience Intelligence**（Knowledge Gap Engine／Opportunity Intelligence）
- Source Monitor（情報源の変化を検知するDB構造）
- Law Update／Event Calendar／SNS Queue
- Dashboard（ホーム画面ページ＋View手動設定ガイド）
- AI Editorial Brain設計（AI-Agent-Architecture／AI-Agent-Workflow／AI-Editorial-Brain）

**Deferred（実装保留）**

| DB | 理由 | 再評価のきっかけ |
|---|---|---|
| Language Master | 現状11言語をSelectで運用中、実害なし | 20言語以上への拡張時、または表記ゆれが実運用で問題化した時 |
| Region Master | 現状Locationを自由テキストで運用中 | 地域別ダッシュボード・自治体連携が実際に必要になった時 |
| Mentor | 現状、専門家レビューは都度手配（Operating Manual§7参照） | メンターの人数が増え、個別手配が非効率になった時 |

---

## Version 3 — AI Automation（完了：実装順序を変更）

**目的**：既存10DBを最大限活用し、Python自動化スクリプトで「知る」から「実行する」までを実現する。n8n専用のAutomation DBやAI Agents DBが無くても、実際に動く自動化を先に作る。

**実装方針の変更**

| 当初計画 | 変更後 |
|---|---|
| AI Agents／Prompt Library／Automation DBの本稼働 | **Deferred**。実体はPythonスクリプト（`notion-build/automation/`）として実装し、DB化は実運用で必要性が確認できてから |
| n8nによる自動化 | まずPythonスクリプトで同等のロジックを実装（将来n8nへ移植可能な設計） |
| Needs Re-Translationの自動検知 | Pythonスクリプトで実装済み（`check_translation_gaps.py`） |
| SNS自動投稿 | Draft自動生成まで実装済み（`generate_article_pipeline.py`、Phase B3.7）。実投稿は引き続き人間が最終確認 |
| Reviewer Agentの実装 | 実装済み（`reviewer_agent.py`、Phase B3.8）。5観点スコアリング＋Update Level 2/3のPublish Gate連携 |
| Translation Quality Reviewerの実装 | 実装済み（`translation_quality_reviewer.py`、Phase B3.9）。翻訳品質5観点スコアリング＋Publish Approvalゲート連携 |
| SNS Quality Reviewerの実装 | 実装済み（`sns_quality_reviewer.py`、Phase B3.10）。SNS投稿5観点スコアリング＋Statusゲート連携 |
| Audit Logの自動記録 | DB化はDeferred。当面はGitコミット履歴とスクリプトの実行ログで代替 |

**実装済み（[Automation Scripts](./Automation-Scripts.md)参照）**

- `check_translation_gaps.py`（Translator）
- `sync_source_monitor_to_research.py`（Researcher）
- `escalate_law_significance.py`（Editor-in-Chief）
- `sync_editorial_calendar_status.py`（Editor-in-Chief）
- `enforce_publish_gate.py`（Editor-in-Chief／Quality Gate、Constitution §9・§13のコード化）
- `daily_briefing.py`（Dashboardの🔴＋①〜⑨・計10セクション相当のCLI版。編集長ホーム画面刷新に合わせて更新）

すべて実データに対してテスト済み。Mission「AIが調査・執筆・翻訳・SNSを担当し、人は最終確認だけを行う」の**技術的な骨格**を、新規DBなしで実現した。

**未実施**：定期実行のスケジューリング（cron等）、Legal Gap等の外部通知、SNS Queue自動Draft生成。

---

## Version 3.5 — Pilot Operation

**目的**：AI編集部（AI Editorial Brain＋既存10DB＋Automation Scripts）を、実際に**7日間運用**して検証する。設計・自動化が揃っただけでは「動く」とは言えない。実運用を経て初めてVersion 4（Enterprise）への準備が整ったと判断する。

**新規DBは追加しない。** 既存10DB・Automation Scripts・[AI Editorial Brain](./AI-Editorial-Brain.md)の設計をそのまま使う。

**日次で実施する9工程**（Phase B3.6〜B3.10の実装により、当初計画の6項目からフル自動生成＋3段レビューへ拡張。詳細は[Pilot Operation Guide](./Pilot-Operation-Guide.md)・[Automation Scripts](./Automation-Scripts.md)）

1. Morning Brief（`daily_briefing.py`）
2. Research（`sync_source_monitor_to_research.py`。採否判断のみ人間）
3. Article Draft（`generate_article_pipeline.py article`、実Claude API、Phase B3.11で独立サブコマンド化）
4. Article Review（`reviewer_agent.py`、5観点スコアリング）
5. Translation（`generate_article_pipeline.py translation`、Phase B3.11で独立サブコマンド化・文化的補足の自己評価を追加）
6. Translation Review（`translation_quality_reviewer.py`、5観点スコアリング）
7. SNS Draft（`generate_article_pipeline.py sns`、Instagram/Threads/X、Phase B3.11で独立サブコマンド化）
8. SNS Review（`sns_quality_reviewer.py`、5観点スコアリング）
9. Publish Gate Check（`enforce_publish_gate.py`）

**Operation Log**：日々の気づき・改善点は、新規DBではなく[Operation Checklist](./Operation-Checklist.md)内に直接記録する（7日分のテンプレートを用意）。

**Day 1実施済み（2026-07-13）**：フル9工程を実データ・実APIで実行し、全工程成功。詳細は[Operation Checklist](./Operation-Checklist.md)を参照。

**Day 2実施済み（2026-07-13）**：Day 1の改善点2点に対応。①`generate_article_pipeline.py`をarticle/translation/sns/allの独立サブコマンドへリファクタリング、②Update Level 1の記事で実行し、**Translation Quality ReviewerがPublish Approvalを自動的に`Not Required`へ遷移させることを実証**。詳細は[Operation Checklist](./Operation-Checklist.md)を参照。

**完了条件**：7日間分のOperation Checklistが記入され、最終日に振り返り（何が自動化できたか、何が依然手作業か、Version 4着手前に直すべき設計上の不備は何か）が行われること。

---

## Version 4 — Enterprise

**前提条件：Version 3.5 Pilot Operation（7日間の実運用）が完了していること。** 設計上動くはずのものが、実際の運用でも動くと確認できるまで、企業・自治体向けへは拡張しない。

**Version 4準備作業（Pilot Operation期間中に先行実施、Version 4着手そのものではない）**：

- **Article Freshness Monitor**（`notion-build/automation/article_freshness_monitor.py`、2026-07-14）：既存Articles DBに`Freshness Status`／`Days Since Verification`／`Freshness Urgency Score`／`Freshness Checked Date`／`Freshness Note`を追加し、Update Levelごとの review interval（Level 1=90日／Level 2=30日／Level 3=14〜30日で設定可能）を超過した記事を自動検知。Law Update／Source Monitor／Event Calendarで関連する変化が検知された記事は、時間経過に関わらずAIの推奨コメント付きで強制的に再レビュー対象へ。Dashboardの最上部に「🔴 Update Needed」セクションとして追加済み。新規DBは追加していない（既存Articles DBの拡張のみ）。詳細は[Automation Scripts](./Automation-Scripts.md)を参照。エンタープライズ向け機能（企業向けダッシュボード等）そのものではなく、コンテンツ鮮度という運用の土台を先に固めるための実装。
- **Coverage Analyzer**（`notion-build/automation/coverage_analyzer.py`、2026-07-14）：既存Category（Update Level判定用、変更なし）とは別に`Life Topics`（22トピックのMulti-select）を新設し、生活トピック別の記事数・鮮度・Review待ちを集計。AIが「外国籍の方の生活への影響度」の視点で不足トピック・優先トピックとおすすめ新規テーマ（10件）を提案。Dashboard「📊 Coverage Analysis」＋専用Notionページに反映。新規DBは追加していない。
- **Editorial Planner**（`notion-build/automation/editorial_planner.py`、Version 4 Phase 2、2026-07-14）：Coverage Analyzerのデータから、Life Topic Impact（Critical／High／Medium／Low）と現在の記事数を組み合わせた決定論的ロジックで★1〜5の優先編集プランを生成（AIはReason・タイトル案・Expected Categoryの生成のみ担当し、優先順位そのものはAIに委ねない）。`--generate-research`で選択したプラン項目のResearchレコードを自動作成（Research DB既存の`Gap Engine`／`AI Suggested`選択肢を利用、新規プロパティなし）。Dashboard「📊 Coverage Analysis」の直下に「📝 Editorial Planner」セクションを追加。「不足を見つける」だけでなく「次に何を書くべきかを具体的に提案する」段階へ進んだもの。
- **Publishing Center**（`notion-build/automation/publishing_center.py`、Version 4 Phase 3、2026-07-14）：既存Articles DBに`Publishing Status`（Draft／Ready to Publish／Published／Needs Update／Archived／Duplicate）等を追加し、ARuアプリへの掲載状況を一元管理。Review Result・Translation Quality Result／Publish Approval・Freshness Status・必須項目の充足状況からDraft⇄Ready to Publishを自動同期するが、**Publishedへは常に人間が変更し、AIによる自動公開は行わない**（ARuアプリへの実投稿APIが存在しないため、Publishedは「人間が手動掲載済み」の管理状態として定義）。Article Freshness Monitorと双方向連携し、公開済み記事が要更新になれば自動でNeeds Updateへ、鮮度回復時は元の状態へ自動復帰する。`enforce_publish_gate.py`もPublishing Status=Publishedを監視するよう拡張。Dashboardに「🚀 Ready to Publish」「📚 Published Articles」「🛠 Needs Update」の3セクションを追加。既存53記事のうち20件がReady to Publish、33件がDraftと初期分類された（Publishedへの一括自動設定はしていない）。
- **Articles DB正規化＋Duplicate Prevention**（`notion-build/automation/duplicate_guard.py`、Version 4 Phase 4、2026-07-14）：Publishing Center導入直後、Reiから「同じテーマの記事が複数存在する」と指摘を受け調査した結果、2026-07-13〜14の一括生成でResearch→Article→Translation→SNSのフルパイプラインが同一テーマに対し複数回実行されていたことが判明（15グループ・記事30件、うち14グループは重複実行、1グループは【テスト】記事の残存）。判定基準に基づき各グループ1件を残して14件をArchive／Duplicateへ移動（削除はしていない）。再発防止として、ARuの原則**「1 Research Topic = 1 Article」**をコードで強制する`duplicate_guard.py`を実装：生成**前**にResearch.Topic→Article→Translation→SNSの存在を確認し、既存なら生成せず「Already Exists」として記録する。`bulk_generate_articles.py`は処理ループ開始前にTOPICS全件を事前チェックし除外する設計（検知ではなく防止）に変更。Dashboardに「🛡 Duplicate Prevention」セクションを追加し、本日の生成件数・スキップ件数・Already Exists一覧を可視化。内容を更新する場合も新規Article作成ではなく既存Articleの更新を運用原則とする。
- **Editor Experience**（Version 4 Phase 5、2026-07-16。**「Version 5」ではない** —— 本Roadmapが既に定義しているVersion 5「Global」との名称衝突を避けるためPhase 5として実施）：Version 4のスキーマ・プロパティ・自動化を一切変更せず、編集長が記事を開いた瞬間に必要な情報だけを見られるようにする表示・ナビゲーション改善。`render_article_layout.py`がArticles.Bodyの9セクションテンプレートをArticleページの実ブロックとして描画（既存38記事に一括バックフィル済み、両生成パイプラインにフック済み）。「今日、人間が決めること」を集約する`editor_home.py`と、「AIが監視・検知していること」を集約する`ai_command_center.py`の2つのナビゲーションハブページを新設（既存Dashboardの13 Linked Viewは再現せずリンクで戻す設計）。Articleページのプロパティパネルを【本文】【公開情報】【AI Review】【System】等へグループ化する手動手順を`docs/Article-Property-Panel-Guide.md`として文書化。既存自動化6スクリプトの回帰テストでDashboard互換性100%・自動化継続動作を確認済み。
- **ARu Intelligence — Phase 1**（`notion-build/automation/source_watcher.py`、2026-07-16〜17。**Version 4 Phase番号の続きではなく別トラック** —— 目的が「編集長の作業体験の改善」ではなく「コンテンツの鮮度・信頼性の担保」であるため、Reiの依頼どおり独立した名称で管理する）：記事を増やすことではなく、既存コンテンツが常に最新・信頼できる状態を保つことが目的。Source Library（既存DB）の公式情報源URLを定期フェッチし、内容ハッシュ比較で実際の変化を検知——これまでSource Monitor.Change Detectedは完全に手動チェックボックスで、外部URLを実際にフェッチするコードは1つも存在しなかった。変化を検知した場合のみSource Monitorレコードを新規作成し、Research／Article強制フラグ／Publishing Center／Dashboard／AI Command Centerという既存の下流パイプライン（すべて実装・テスト済みだったが実データを受け取ったことがなかった）へ流し込む。新規スキーマはSource Libraryへの`Last Content Hash`プロパティ1つのみ。政府・自治体系情報源の変化はフラグ立てのみに留め、Law Updateの自動作成はしない（人間が判断、Constitutionの人間レビュー最優先原則に整合）。Reiの明示的な指示により、このPhase 1実装セッションではLaw Update／Research／Article／Translation／SNS Queueへの新規レコード自動作成は一切実行していない——検知と報告のみを行い、コンテンツ化の判断は人間の編集者に委ねる設計。
- **ARu Intelligence — Phase 2（Source Library Expansion）**（2026-07-17、Phase 1と同じ独立トラック）：「監視エンジンはできたが監視対象がほぼ空」というPhase 1の課題を解消。Source LibraryへCategory（22種）／Country／Region／City／Importance（Critical/High/Medium/Low）を追加（新規DBは作成せず、既存のDeferred方針どおりRegion Masterは作らない）。CSV一括登録ツール`bulk_import_sources.py`を新設し、WebFetchで実在確認済みの9ソース（税務・健康保険・防災・気象・消防・年金・雇用・国交・観光の各政府機関）を実投入。変化検知をSHA-256完全一致からSimHash近似指紋＋ハミング距離比較へ変更し、広告・タイムスタンプ・訪問者数等のノイズを無視する誤検知削減ロジックを実装（実データで確認済み、閾値は今後調整の余地あり）。Source Monitorへ`Update Classification`（11分類、AI判定）を追加。`ai_command_center.py`・Dashboardへそれぞれ新セクション／新Linked Viewを追加（新規ページは作成せず既存ハブの拡張のみ）。人間承認ワークフロー（Source→Watcher→Source Monitor→Editor Review→Research→Article→Translation→SNS→Publish）は不変。
- **ARu Intelligence — Phase 3（Editorial Intelligence）**（2026-07-18、Phase 1/2と同じ独立トラック）：「ARuを毎日使うプラットフォームにする」ことが目的——新機能追加ではなく、既存システムの再利用と統合。`research_prioritizer.py`がStatus=NewのResearchをFreshness／Foreign Resident Value／Tourism Value／Seasonal Relevance／Premium Potentialの5軸（各20点、計100点）で決定論的にスコアリング（新規スキーマ・追加AI呼び出しなし、既存プロパティのみから算出）。`today_opportunities.py`がEvent Calendar／Source Monitor／Law Update／Researchという4つの既存システムを統合し「今日動くべきこと」を提示。`ai_command_center.py`を「編集長が毎日最初に見るページ」として再構成し、🎯 Today's Opportunities／🔴 Critical Updates／📊 Top Research Candidates／🚀 Publishing Queue／🕐 Recently Updated Articlesの5セクションを追加（既存の監視詳細は根拠情報として下部に残置、新規ページは作成せず既存ハブの拡張のみ）。`docs/Editorial-Workflow.md`を新規作成し、情報源監視から公開・鮮度管理までの編集ワークフロー全体を1文書化。新規データベースは作成していない。

**目的**：個人利用者向けサービスから、企業・自治体・日本語学校向けプラットフォームへ拡張する。

- Usage Scope（Enterprise／Municipal Partnership）を実運用で使い始める。Universal Propertiesの段階ですでに全Content Core DBに用意済み
- 自治体・観光協会・企業とのデータ連携（Source Libraryの「地域固有の魅力」情報源が公式パートナー契約に発展）
- JNTO／Visit Japanとの連携（Region Masterに既に用意済みのURL項目を実際のAPI連携へ）
- 企業向けダッシュボード（外国籍社員の受け入れ状況、生活支援コンテンツの利用状況等）
- Mentorネットワークの本格拡大（行政書士・医療関係者・企業担当者との正式契約）

このバージョンの技術的土台は、Version 1の段階で意図的に先回りして設計済み（Confidentiality／Usage Scopeの早期導入）。

---

## Version 5 — Global

**目的**：日本という単一国の枠を越え、ARuのモデル自体を輸出可能にする。

- Region Masterの「Country」階層を実際に複数国で使い始める
- 対応言語をLanguage Masterの拡張性を活かして20言語以上へ
- Timezoneフィールド（Version 1から予約済み）を実際の海外展開で使用開始
- 「Decode Japan」のフレームワークを、他国向け「Decode X」として再利用できる形に一般化
- ARu Constitution／AI Agent Constitutionの理念部分（Mission／Core Values）を、国をまたいでも通用する形に再検証（Level C改訂として扱う）

---

## 現在地

**Version 1・2・3は完了（一部Deferred）。Version 3.5（Pilot Operation：7日間の実運用）に着手する。Version 4（Enterprise）はPilot Operation完了後、かつ対外的な意思決定・契約行為を伴うため、着手前に別途方針確認が必要。**

**注記（2026-07-19、v4.1正式リリースにより更新）**：上記のBusiness Roadmap進行とは別に、Studio側のエンジニアリング・マイルストーンとして「ARu Studio v4」に続き「**ARu Studio v4.1 Editorial Intelligence」が2026-07-19付でReleased（正式リリース）**となった（[Studio-v4.1-Release-Notes.md](./Studio-v4.1-Release-Notes.md)、Gitタグ`studio-v4.1.0`）。両者は独立したカウンタであり、Studio vXの完了はBusiness Roadmapの本Versionを進めるものではない——[Version4-Completion-Report.md](./Version4-Completion-Report.md)で確立した命名規則にもとづく。**Rei決定：v4.1をもってStudio側の新機能開発を一時停止し、実運用フェーズへ移行する。Version 4.2は実運用から得られる知見にもとづいて設計する方針であり、着手時期は未定。** なお本Roadmap自体はARu Intelligence Phase 1-3・記事テンプレート再設計・Architecture Phaseを含め複数フェーズ分の更新が反映されておらず、既知のドキュメントギャップとして残っている（別セッションでのDocumentation Session対応が必要）。

---

*ARu HQ / Decode Japan — ARu Studio Roadmap v2 — 2026-07-12*
