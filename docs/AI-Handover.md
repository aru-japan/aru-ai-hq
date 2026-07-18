<title>AI Handover Document</title>

# AI Handover Document

**この文書は人間の開発者向けではない。ChatGPT・Claude・Cursor・その他将来のAIが、この1ファイルだけを読んでこのプロジェクトの開発を継続できることを唯一の目的として書かれている。**

> この文書自体が古くなる可能性がある。「Latest Commit」「Current Phase」等のスナップショット情報は、必ず`git log`とNotionの実際の状態で裏を取ってから信じること。この文書は「地図」であり「現在地のGPS」ではない。

---

## ■ Project Overview

**ARu**は、外国籍の方が日本で安心して暮らし、旅行し、働けるようにサポートするAIプラットフォーム。コンセプトは「Decode Japan（日本を読み解く）」——「何をすべきか」だけでなく「なぜそうするのか」という文化的・制度的背景まで伝える。

このリポジトリ（`aru-ai-hq`）は、ARuを支える**編集部（ARu HQ）の運営基盤**——理念（Constitution）、設計（ER Design／Notion Builder Spec）、実装（Notion API連携スクリプト＋AI生成パイプライン）を1つにまとめたもの。ARuというアプリ本体のコードはこのリポジトリには含まれない。ここにあるのは「記事を作り、翻訳し、SNSへ出すまでの編集部そのもの」。

## ■ Mission

ARu Constitution（`docs/ARu-Constitution.md`）が定める最上位の目的：

> AIが調査・執筆・翻訳・SNSを担当し、人は最終確認だけを行う体制を作る。

ただし、これは「AIに任せて終わり」という意味ではない。**Update Level 2・3（法律・ビザ・税金・医療等）の内容は、AIがどれだけ高いスコアで評価しても、必ず人間が最終承認する。** この一線は、コード（`enforce_publish_gate.py`等）でも強制されている、単なる方針ではなく実装上の制約。

## ■ Architecture

編集部のコンテンツパイプラインは、以下の9段階（Notionデータベース＋Pythonスクリプトの組み合わせ）で構成される。

```
Research → Article → Article Review → Translation → Translation Review → SNS → SNS Review → Publish Gate
```

| 段階 | スクリプト | 入出力 |
|---|---|---|
| Duplicate Guard | `duplicate_guard.py` | 生成**前**にResearch.Topic→Article→Translation→SNSの存在を確認。既存なら生成せず「Already Exists」を記録（「1 Research Topic = 1 Article」を強制） |
| Research | `sync_source_monitor_to_research.py` | Source Monitor → Research |
| Article | `generate_article_pipeline.py article` | Research → Articles（実Claude API生成、**ARu公式テンプレート＝9セクション構成**で統一。`Verification Status`／`Last Verified Date`を必ず保存） |
| Article Review | `reviewer_agent.py` | Articles（5観点スコアリング：Accuracy/Evidence/Readability/Risk/Localization） |
| Translation | `generate_article_pipeline.py translation` | Articles → Translation（実Claude API生成、文化的補足を自己評価） |
| Translation Review | `translation_quality_reviewer.py` | Translation（5観点：Meaning Accuracy/Naturalness/Cultural Adaptation/Terminology/Hallucination Risk） |
| SNS | `generate_article_pipeline.py sns` | Articles → SNS Queue（Instagram/Threads/X、実Claude API生成） |
| SNS Review | `sns_quality_reviewer.py` | SNS Queue（5観点：Accuracy/Platform Fit/Engagement/Cultural Sensitivity/Risk） |
| Publish Gate | `enforce_publish_gate.py` | Articles（QA Status・Review Result・Human Reviewedを横断確認。Status=Published／Publishing Status=Published両方を監視） |
| Publishing | `publishing_center.py` | Articles（Publishing Status＝ARuアプリへの実掲載管理。人間が最終操作、AIは自動公開しない） |

**ゲートの核心ロジック**：Update Level（Articleのプロパティ、1〜3）によって挙動が分岐する。

- **Level 1**（イベント・観光・文化・生活情報等）：レビューPass＋Localization Status=Culturally Adaptedが揃えば、Translation.Publish Approvalは**AIが自動で`Not Required`へ**遷移させてよい（実証済み、Day 2）
- **Level 2・3**（法律・ビザ・税金・医療・重要な法改正等）：レビューが何点でも、Publish Approvalは**必ずPendingのまま**。人間（編集長Reiまたは専門家）の承認を経て初めてPublished

## ■ Current Database Structure（既存10DBのみ）

すべて実際にNotion上に作成済み。**新規データベースは追加しない**のが原則（後述）。

| Database | 役割 |
|---|---|
| Articles | 日本語マスター記事（唯一の公開DB） |
| Research | 調査・記事候補 |
| Translation | 記事の子DB。言語ごとの翻訳・レビュー・公開状況 |
| Source Library | 情報源のマスター台帳 |
| Editorial Calendar | 編集スケジュール・公開予定管理 |
| Experience Intelligence | Knowledge Gap Engine／Opportunity Intelligence |
| Source Monitor | 情報源の変化検知ログ |
| Law Update | 法改正の編集管理DB |
| Event Calendar | 祭り・イベント等の体験編集DB |
| SNS Queue | Instagram/Threads/X/Facebook/LinkedIn/TikTok投稿管理 |

**まだ存在しないDB（Deferred、削除ではなく保留）**：Language Master、Region Master、Mentor、AI Agents、Prompt Library、Automation。これらは実運用で必要性が確認できてから個別に追加する方針（`docs/Roadmap.md`参照）。**新しいAIがこれらを勝手に作らないこと。**

## ■ Current Automation（Phase B3.6〜B3.10、コードで実装済み）

すべて`notion-build/automation/`（一部`scripts/`）にあり、標準ライブラリのみで動作（pip installは不要）。

- **B3.6** `scripts/ai_gateway.py`：Claude API／OpenAI APIのどちらでも呼び出せる共通ゲートウェイ
- **B3.7/B3.11** `notion-build/automation/generate_article_pipeline.py`：`article`／`translation`／`sns`／`all`の4サブコマンド。Research→Article→Translation→SNSを実Claude APIで生成
- **B3.8** `reviewer_agent.py`：Article 5観点レビュー
- **B3.9** `translation_quality_reviewer.py`：Translation 5観点レビュー＋Publish Approvalゲート
- **B3.10** `sns_quality_reviewer.py`：SNS 5観点レビュー
- その他：`daily_briefing.py`（CLI版Dashboard）、`check_translation_gaps.py`、`sync_source_monitor_to_research.py`、`escalate_law_significance.py`、`sync_editorial_calendar_status.py`、`enforce_publish_gate.py`、`research_assistant.py`、`article_assistant.py`
- **一括生成** `notion-build/bulk_generate_articles.py`（旧`bulk_generate_20_articles.py`）：`TOPICS`リストを差し替えるだけで、Research→Article（9セクションテンプレート）→Review→Translation→Review→SNS×3→Reviewのフルパイプラインを日々再利用できる汎用スクリプト
- **Version 4準備** `article_freshness_monitor.py`：Update Levelごとのレビュー間隔（L1=90日／L2=30日／L3=14〜30日）を超過した記事、およびLaw Update/Source Monitor/Event Calendarで変化が検知された記事を`Freshness Status=Needs Update`にし、Dashboard最上部の「🔴 Update Needed」へ反映（新規DBなし、既存Articles DBへのプロパティ追加のみ）
- **Version 4準備** `coverage_analyzer.py`（＋`life_topics.py`／`backfill_life_topics.py`）：既存Category（Update Level判定用、変更なし）とは別に`Life Topics`（22トピックのMulti-select）を新設し、記事数・鮮度・Review待ちをトピック別に集計。AIが不足トピック・優先トピック・おすすめ新規テーマ（10件）を「外国籍の方の生活への影響度」の視点で提案し、Dashboard「📊 Coverage Analysis」＋専用Notionページ（計算済みサマリーをTable Blockとして毎回上書き生成）に反映
- **Version 4 Phase 2** `editorial_planner.py`：Coverage Analyzerのデータから★1〜5の優先編集プランを生成（★の算出はLife Topic Impact×記事数の決定論的ロジック、AIはReason／タイトル案／Expected Categoryの生成のみ担当）。`--generate-research`で選択したプラン項目のResearchレコードを自動作成（新規プロパティなし、Research DB既存の`Gap Engine`／`AI Suggested`選択肢を利用）。Dashboard「📝 Editorial Planner」＋専用Notionページに反映
- **Version 4 Phase 3** `publishing_center.py`：Articlesに`Publishing Status`等を追加し、Review Result／Translation Quality Result・Publish Approval／Freshness Status／必須項目からDraft⇄Ready to Publishを自動同期。**Publishedへは常に人間が変更し、AIは自動公開しない**。Freshness Monitorと双方向連携（Published→Needs Update、鮮度回復で自動復帰）。`enforce_publish_gate.py`もPublishing Status=Publishedを監視するよう拡張。Dashboard「🚀 Ready to Publish」「📚 Published Articles」「🛠 Needs Update」に反映
- **Version 4 Phase 4** `duplicate_guard.py`（＋`duplicate_prevention_report.py`）：**「1 Research Topic = 1 Article」**をコードで強制。生成**前**にResearch.Topic→Article→Translation→SNSの存在を順に確認し、既存なら生成せず「Already Exists」（どの段階まで存在したか付き）として記録する。`bulk_generate_articles.py`は処理ループを始める前にTOPICS全件を事前チェックし除外する設計（検知ではなく防止）。Dashboard「🛡 Duplicate Prevention」に本日の生成件数・スキップ件数・Already Exists一覧を反映
- **Version 4 Phase 5（Editor Experience）** `render_article_layout.py`：Articles.Body（1つのrich_textにARu公式9セクションが`**見出し**`形式で入っているだけ）を、Article**ページの実ブロック**として描画するレンダラー。Question/Basic Answer/More Details/Why Does Japan Do This?/ARu Tipの5つを本文フローに、残る4セクション（Practical Steps and Cautions/Latest Information/Related Questions/Mentor Support）は「その他の詳細」というtoggleブロックにまとめて折りたたむ。プロパティ・スキーマは一切変更しない、Bodyプロパティを唯一の原本としたまま表示だけを整形する完全追加レイヤー（既存スクリプトはどれもArticleページのブロック子要素を読み書きしていないことを全リポジトリgrepで確認済み）。`generate_article_pipeline.py`／`bulk_generate_articles.py`のArticle保存直後にフック済み（失敗してもArticleレコード自体の保存は妨げないnon-fatal設計）。既存Articles全38件（Archived除く）に一括バックフィル済み（0件失敗）
- **Version 4 Phase 5（Editor Experience）** `editor_home.py`／`ai_command_center.py`：編集長向けに「今日決めること」（Editor Home：Ready to Publish／Published／Needs Update／Publish Approval Pending／Article Review Waiting／Translation Review Waiting／SNS Draft Waiting／Today's Editorial Calendar／Today's Researchの9件数）と「AIが監視していること」（AI Command Center：Freshness内訳・Duplicate Prevention本日の活動・外部監視フィード3種・Coverage Analysis/Editorial Plannerへのポインタ）を分離した2つの専用Notionページ（ナビゲーションハブ、Dashboardの13 Linked Viewを再現するのではなくリンクで戻す設計）。フィルタは`docs/Dashboard-Setup-Guide.md`の設定一覧と完全に同一の条件を使い、数値が実際のDashboard表示とずれないようにしている
- **ARu Intelligence Phase 1** `source_watcher.py`：Source Library（既存DB）の公式情報源URLを`Check Frequency`に従って定期フェッチし、本文テキストのハッシュを前回値（新設プロパティ`Last Content Hash`のみ）と比較して**実際の変化検知**を行う。変化を検知した場合のみSource Monitorレコードを新規作成（`Change Detected=true`、`Impact Level`、AI Gateway生成の`Diff Summary`）。これまでこのパイプラインの下流（Research自動起票・Article強制フラグ・Publishing Center連携・Dashboard・AI Command Center）はすべて実装済みだったが、`Change Detected`を実際にtrueにする仕組み自体が存在しなかった（手動チェックボックスのみ）——Phase 1はその欠けていた1ピースだけを実装。政府・自治体系情報源の変化はSource Monitorへのフラグ立てのみで止め、Law Updateレコードは自動作成しない（人間が判断、Reiと確認済みの設計）。`article_freshness_monitor.py`の`find_source_monitor_signals()`に、Source Library.Related Research経由の2つ目の検知経路を追加（関数シグネチャは無変更）
- **ARu Intelligence Phase 2（Source Library Expansion）** `source_categories.py`／`bulk_import_sources.py`／`source_watcher.py`拡張／`ai_command_center.py`拡張：Source Libraryを1件から数百件規模へ拡張する準備。Category（22種）／Country／Region／City／Importance（Critical/High/Medium/Low、旧`Tier`を代替）／`Last Check Error`をSource Libraryへ追加（すべて既存DBへの追加のみ、新規DBなし——「Region Master」は既存のDeferred方針どおり作成せず、単純なSelect/rich_textで対応）。CSV一括登録`bulk_import_sources.py`を新規実装（本リポジトリ初のCSV読み込み機能。URL重複は自動スキップ、未知のSelect値は自動追加）。変化検知はSHA-256完全一致からSimHash方式の近似指紋＋ハミング距離比較へ変更し、広告・タイムスタンプ・訪問者数等のノイズを除去してから比較する誤検知削減ロジックを実装（実データで安定性・ノイズ耐性・実質変更検知の4パターンを確認）。Source Monitorへ`Update Classification`（11分類、AI判定）を追加。`ai_command_center.py`に「🌐 Source Intelligence」セクション、Dashboardに「🔴 Critical Source Updates」Linked Viewを追加。WebFetchで実在確認済みの9ソース（国税庁／厚生労働省／内閣府防災情報／気象庁／消防庁／日本年金機構／ハローワーク／国土交通省／JNTO）を投入し実データでテスト済み。人間承認ワークフロー（Source→Watcher→Source Monitor→Editor Review→Research→Article→Translation→SNS→Publish）は不変
- **ARu Intelligence Phase 3（Editorial Intelligence）** `research_prioritizer.py`／`today_opportunities.py`／`ai_command_center.py`再構成：「ARuを毎日使うプラットフォームにする」ことが目的（新機能追加ではなく既存システムの再利用・統合）。`research_prioritizer.py`はStatus=NewのResearchをFreshness／Foreign Resident Value／Tourism Value／Seasonal Relevance／Premium Potentialの5軸（各20点、計100点）で決定論的にスコアリング——すべて既存プロパティ（Category／Season／Usage Scope／Evidence Level／作成日時）から算出し、新規スキーマ・追加AI呼び出しは一切なし。`today_opportunities.py`はEvent Calendar（近日開催）／Source Monitor（本日のCritical/High変化）／Law Update（Confirmed）／Research（季節性の高い候補）の4つの既存システムを統合。`ai_command_center.py`を「編集長が毎日最初に見るページ」として再構成し、先頭5セクション（🎯 Today's Opportunities／🔴 Critical Updates／📊 Top Research Candidates／🚀 Publishing Queue／🕐 Recently Updated Articles）を追加、Phase 1/2の監視詳細セクションはその下に根拠として残した。実装中、Critical UpdatesがArchived済みの古いテスト記事（Freshness Statusがクリアされないまま残存）を誤って含めていたバグを発見・修正。`docs/Editorial-Workflow.md`を新規作成し、情報源監視から公開・鮮度管理までの編集ワークフロー全体を1つの文書にまとめた

詳細と実行方法は`docs/Automation-Scripts.md`。

## ■ Current Phase

**Roadmap Version 3.5（Pilot Operation）Day 2まで完了。** AI編集部を7日間実運用して検証する段階の2日目。

## ■ Latest Commit

`99f1557`（このHandover文書を書いた時点でのHEAD）。**必ず`git log --oneline -10`で実際の最新を確認すること。** このフィールドは経年劣化する。

## ■ Roadmap Current Position

（`docs/Roadmap.md`が正。ここは要約）

| Version | 状態 |
|---|---|
| 1 — Foundation | ✅ 完了 |
| 2 — AI Intelligence | ✅ 完了（Language Master/Region Master/MentorはDeferred） |
| 3 — AI Automation | ✅ 完了（AI Agents/Prompt Library/Automation DBはDeferred、実体はPythonスクリプト） |
| 3.5 — Pilot Operation | 🔶 進行中（Day 2／7完了） |
| 4 — Enterprise | ⏳ 未着手。Pilot完了後、かつ対外的な意思決定を要するため、実装だけでは進められない |
| 5 — Global | ⏳ 未着手 |

## ■ Completed Features

- ARu Constitution v2.0.0、AI Agent Constitution v1.1.0（統治文書一式）
- ER Design／Notion Database Builder Spec（全DB設計、Universal Properties）
- 実装済み10DB（すべて実データ・テストレコードあり）
- View/Template設定ガイド（Notion UI手動設定手順）
- Operating Manual（編集長向けSOP）
- AI Editorial Brain設計（6エージェント：Editor-in-Chief/Researcher/Writer/Reviewer/Translator/Social Manager、既存9ロールとのマッピング済み）
- AI Gateway（実Claude API接続確認済み。OpenAI経路は未検証）
- Research→Article→Translation→SNSの生成パイプライン（独立サブコマンド化済み、Phase B3.11）
- Article／Translation／SNSの3段階品質レビュー（すべて実データ・実APIでテスト済み）
- Publish Gate（Constitution §9/§13をコードで強制）
- Update Level 1の自動承認経路（Publish Approval→Not Required）を実データで実証
- 記事本文のARu公式テンプレート統一（9セクション）、`Verification Status`／`Last Verified Date`の記録（2026-07-14）
- Article Freshness Monitor（Version 4準備）：Update Levelごとのレビュー間隔管理＋Law Update/Source Monitor/Event Calendarとの連携による強制再レビューフラグ、Dashboard最上部「🔴 Update Needed」（2026-07-14）
- Coverage Analyzer（Version 4準備）：Life Topics（22トピック）によるカテゴリ分析＋AIによる不足分析・優先トピック・新規テーマ提案、Dashboard「📊 Coverage Analysis」＋専用ページ（2026-07-14）
- Editorial Planner（Version 4 Phase 2）：★1〜5の優先編集プラン自動生成＋`--generate-research`によるResearchレコード自動作成、Dashboard「📝 Editorial Planner」＋専用ページ（2026-07-14）
- Publishing Center（Version 4 Phase 3）：Publishing Statusによる公開管理（Draft/Ready to Publish/Published/Needs Update/Archived/Duplicate）、Freshness Monitorとの双方向連携、公開操作の自動記録（Published Date/By）、Dashboard「🚀📚🛠」3セクション（2026-07-14）
- Articles DB正規化：重複記事15グループ（記事30件）をResearch.Topic単位で検出し、判定基準に基づき各グループ1件を残して残りをArchive（Publishing Status=Duplicate）。削除はしていない（2026-07-14）
- Duplicate Prevention（Version 4 Phase 4）：「1 Research Topic = 1 Article」を生成**前**にコードで強制（`duplicate_guard.py`）。`bulk_generate_articles.py`は処理ループ開始前にTOPICS全件を事前チェックする設計に変更。Dashboard「🛡 Duplicate Prevention」＋専用ページ（2026-07-14）
- Dashboard 13セクション全Linked Database Viewを人手で設定完了（2026-07-16）。設定過程でSelect型プロパティ（`Priority`／`Urgency`）の「降順」がオプション定義順の逆——つまり意図と正反対の並びになる不具合を発見し、Articles・Research・Editorial Calendarの3DBでオプション定義順を並べ替えて解消。あわせてArticles.Priority／Urgencyが記事生成時に一度も継承されていなかった問題を修正し、`generate_article_pipeline.py`／`bulk_generate_articles.py`がResearchのPriority／Urgencyを自動継承する設計に変更、既存53記事もバックフィル済み
- Version 4 Phase 5（Editor Experience、2026-07-16）：Version 4のスキーマ・プロパティ・自動化を一切変更せず、表示とナビゲーションだけを編集長ファーストへ改善。①`render_article_layout.py`でArticleページ本文をARu公式9セクション（5つ本文フロー＋4つtoggle折りたたみ）として実ブロック描画（既存38記事に一括バックフィル済み、両生成パイプラインにフック済み）。②`editor_home.py`「今日決めること」9項目（合計92件、実データ確認済み）。③`ai_command_center.py`「AIが監視していること」（Freshness内訳2件、Duplicate Prevention本日2件生成、外部監視フィード3種、AI分析ページへのポインタ）。④Articleページのプロパティパネルを【本文】【公開情報】【関連情報】【AI Review】【System】へグループ化する手順を`docs/Article-Property-Panel-Guide.md`として文書化（Notion UI機能のためAPIから設定不可、View設定と同じ制約）。全既存自動化（Freshness Monitor／Publishing Center／Coverage Analyzer／Editorial Planner／Duplicate Prevention／Publish Gate）を再実行し、挙動に変化がないことを確認済み
- ARu Intelligence Phase 1（2026-07-16）：「記事を増やす」ではなく「既存コンテンツを常に最新・信頼できる状態に保つ」ことが目的。`source_watcher.py`を新規実装し、これまで手動チェックボックスでしかなかったSource Monitor.Change Detectedを、実際のURLフェッチ＋内容ハッシュ比較による本物の変化検知に置き換えた。下流（Research自動起票／Article強制フラグ／Publishing Center連携／Dashboard／AI Command Center）はすべて既存・既テストのまま、フラグに実データが流れるようになっただけ。新規スキーマはSource Libraryへの`Last Content Hash`（rich_text）1プロパティのみ。政府・自治体系情報源の変化はフラグ立てのみで、Law Updateの自動作成はしない（人間が判断、Constitutionの人間レビュー最優先原則に整合）。実データテストで、変化検知パス・AI生成Diff Summary・Dashboard/AI Command Centerへの反映（新規UIコードなし）まで確認済み。Reiの指示により、このセッションではLaw Update／Research／Article／Translation／SNS Queueへの新規レコード自動作成は一切実行していない
- ARu Intelligence Phase 2（Source Library Expansion、2026-07-17）：Source Libraryを1件から実運用に耐える規模へ拡張する準備。Category（22種）／Country／Region／City／Importance（Critical/High/Medium/Low）／`Last Check Error`を追加（新規DBなし）。`bulk_import_sources.py`でCSV一括登録を実現（本リポジトリ初のCSV機能）し、WebFetchで実在確認済みの9ソース（国税庁・厚生労働省・内閣府防災情報・気象庁・消防庁・日本年金機構・ハローワーク・国土交通省・JNTO）を実投入（9件成功・0件エラー）。変化検知をSHA-256完全一致からSimHash近似指紋＋ハミング距離比較へ変更し、広告・タイムスタンプ・訪問者数ノイズを実データで正しく無視しつつ実質的な変更は検知することを確認（安定性/ノイズ耐性/変更検知の3パターンいずれも想定どおり）。Source Monitorへ`Update Classification`（11分類、AI判定、実データ4件すべて正しく分類）を追加。`ai_command_center.py`「🌐 Source Intelligence」セクション、Dashboard「🔴 Critical Source Updates」Linked View（設定手順は`Dashboard-Setup-Guide.md`の14番目のセクションとして追記、実際のNotion UI設定はRei側の作業）を追加。人間承認ワークフローは無変更
- ARu Intelligence Phase 3（Editorial Intelligence、2026-07-18）：「ARuを毎日使うプラットフォームにする」ことが目的。新規スキーマ・追加AI呼び出しなしで、Status=NewのResearchを5軸（Freshness／Foreign Resident Value／Tourism Value／Seasonal Relevance／Premium Potential、各20点）で決定論的にスコアリングする`research_prioritizer.py`（実データ19件でテスト）、Event Calendar／Source Monitor／Law Update／Researchの4つの既存システムを統合する`today_opportunities.py`を新規実装。`ai_command_center.py`を「編集長が毎日最初に見るページ」として再構成し、🎯 Today's Opportunities／🔴 Critical Updates／📊 Top Research Candidates／🚀 Publishing Queue／🕐 Recently Updated Articlesの5セクションを追加（既存の監視詳細セクションは根拠情報として残置）。実装中、Archived記事のFreshness Statusクリア漏れによりCritical Updatesへ古いテスト記事が誤混入するバグを発見・修正（実データで3件→2件の正しい件数に修正確認）。`docs/Editorial-Workflow.md`を新規作成し編集ワークフロー全体を1文書化

## ■ Remaining Tasks

- **ARu Constitutionの改訂提案が3件承認待ち**（Pending Amendments、いずれも提案日2026-07-14、Level B、レビュー期間72時間→発効予定2026-07-17以降）：①ARu公式9セクションテンプレートとArticle Freshness Monitorの実態を§4・§11へ反映、②Publishing Centerの実装で明確になった「Level 1 ── 自動公開」表記の誤解を§15で解消（AIがARuアプリへ自動掲載することは元々一度もなく、運営方針自体は変更なし）、③「1 Research Topic = 1 Article」原則を§4へ追加（重複記事調査を受けてReiが明示的に指示）。**2026-07-17以降、編集長（Rei）の承認を得たら**、`docs/ARu-Constitution.md`の該当箇所を本文へ反映し、v2.0.0→v2.1.0（以降）へバージョンアップ、Revision Historyに記録し、Pending Amendments節から該当エントリを削除すること
- **Editorial Plannerが提案した19件のResearch（Status=New、Discovery Method=Gap Engine）がレビュー待ち**（2026-07-14、`editorial_planner.py --generate-research`で作成）。Dashboard「⑥ Today's Research」に表示される。Reiが内容を確認し、実際に記事化するものを選んで`generate_article_pipeline.py article`または`bulk_generate_articles.py`のTOPICSへ追加する
- Article.Status自体をAI Draft→Publishedへ自動昇格させるスクリプトが存在しない（Translation側のゲートのみ実証済み）。**Publishing Statusの導入により、少なくとも「ARuアプリに実際に掲載されているか」はStatusとは独立して追跡できるようになった**（`publishing_center.py`）
- **`QA Status`（Articles既存プロパティ）が全53記事で未設定**。`enforce_publish_gate.py`は必須としているが、Publishing CenterのReady to Publish判定には含めていない（要件になかったため）。誰がいつ設定する運用にするか、Ready to Publish条件に含めるべきかはReiの判断待ち
- **アーカイブした重複記事15件のTranslation・SNS Queueレコードは未整理のまま残っている**。親Articleが Archived/Duplicate のため公開経路には現れないが、レコード自体の削除・アーカイブは今回のスコープに含めていない（要判断）
- **Duplicate Preventionのログ（`notion-build/automation/logs/duplicate_prevention.jsonl`）はローカルファイルでGit管理外**。「本日の生成件数」等はスクリプトを実行した端末上の活動のみを反映する（Notion同期なし、既知の制約）
- 定期実行（cron/launchd）は未設定。すべて手動実行
- Critical Gap等の外部通知（Slack/メール）は未実装
- SNS実投稿（実際にプラットフォームへ投稿する部分）は未実装。Draft生成まで
- Pilot Operation Day 3〜7が残っている
- Deferred中の6DB（Language Master等）
- Audit Logの永続化（現状はGitコミット履歴とターミナル出力のみ）
- AI Gatewayのopenaiプロバイダ経路は未検証（Claudeのみ実績あり）

## ■ Known Limitations

- **Articleが`Status=Archived`になっても`Freshness Status`は自動でクリアされない。** `article_freshness_monitor.py`はArchived記事を対象外にしているだけで、Archive時点で既に`Needs Update`だった記事のフラグを消す処理が存在しない。2026-07-18、`ai_command_center.py`のCritical Updates集計でこれが原因の誤表示（Archived済みテスト記事の混入）を発見・修正済みだが、根本原因（Archive時のFreshness Statusクリア処理がない）自体は未修正。実害は限定的（Archived記事はDashboard/AI Command Centerの他の集計から既に除外されている）だが、新しいクエリを書く際は`Status`の除外条件を忘れないこと
- **NotionパブリックAPIはViewやTemplateを作成できない。** 手動設定が必要（`docs/View-Template-Guide.md`）
- **NotionパブリックAPIは「Linked view of database」ブロックを作成できない。** DashboardはPage＋説明文のみで、実際のフィルタ済みビューは手動で埋め込む必要がある
- **NotionパブリックAPIは既存Linked Viewの設定（Filter／Sort／表示プロパティ）を読み取ることもできない。** AIが「設計書と実際のView設定に差異がないか」を直接検証する手段はなく、確認は人間の目視（またはスクリーンショット共有）に頼る。AIが独立して検証できるのは、①設計書同士の整合性、②同じFilter/Sort条件でDBを直接クエリした際のデータの健全性、の2点まで
- **NotionパブリックAPIはページのプロパティパネルのグループ化・折りたたみを設定できない。** ViewやTemplateと同じ制約カテゴリ。Articleページのプロパティを【本文】【公開情報】【AI Review】【System】等へグループ化する作業（`docs/Article-Property-Panel-Guide.md`）は人間が手動で行う必要がある
- **`source_watcher.py`の実運用上の網羅範囲はSource Libraryへの実URL投入量に依存する。** 2026-07-17時点でSource Libraryの実データは10件（Phase 1テストレコード1件＋Phase 2シード9件）。Immigration／Tax／Health Insurance／Disaster／Weather／Emergency／Pension／Employment／Transportation／Tourismはカバー済みだが、Visa（外務省サイトが自動フェッチをブロック）／Student／Events／Festivals／Municipal Governments／Universities／Japanese Language Schools／Culture／Consumer Information／Housing／Banking／Trending Topicsは未着手。実際に数百件規模の監視網にするには、Reiまたは今後のフェーズでの継続的なソース登録が前提になる
- **SimHashによる誤検知削減は調整可能なヒューリスティックであり、解決済みの問題ではない。** 現在の閾値（`SIMHASH_CHANGE_THRESHOLD=2`、64bit中）は限られた実データでの検証に基づく初期値。ソース数が増えるにつれて実運用上のfalse positive/false negative発生率を見ながら再調整が必要になる可能性がある
- **JavaScriptで本文を描画するSPA型サイトは、stdlibのみのフェッチでは意味のあるテキストが取得できない可能性がある。** Phase 2でも未解決（Phase 1からの既知の制約を継続）
- **ページ全文のハッシュ比較による変化検知は粗い。** 広告や「最終更新日」表示など本質的でない変化でも誤検知（false positive）しうる。JavaScriptで本文を描画するSPA型サイトは、stdlibのみのフェッチでは意味のあるテキストが取得できない可能性がある。実運用でのfalse positive発生率を見てから、ソースごとのCSSセレクタ指定等の精緻化を検討する（Phase 2候補）
- **Select型プロパティのSortは値の重要度ではなくオプションの定義順に従う。** 「降順」はオプション定義順を逆にしたものであり、意味的な重要度の降順とは限らない（2026-07-16に発見、Priority／Urgencyで実際に逆転していた）。新しくSelect型プロパティを追加してSortに使う場合は、オプションの定義順を「重要度が低い→高い」の順にしておくこと（そうすれば「降順」が直感通り「重要度が高いものが先頭」になる）
- Notionのrich_textは1項目あたり2000文字制限（`rich_text_chunks()`で分割対応済み）
- Notion Formulaの構文は不安定な場合がある（`dateBetween()`は動くが、日付プロパティ同士の直接`>`比較が失敗した例がある）
- GitHubへのPushは、このBash実行環境では非対話認証ができず失敗する。人間が自身のターミナルで`git push`を実行する必要がある（過去、一度認証が通れば以降のPushは成功している）
- スケジューリングの仕組みがないため、すべてのスクリプトは手動実行が前提
- **Notionデータの外部バックアップが存在しない。** レコード（記事本文・翻訳・レビュー結果等）が誤って削除された場合、NotionのTrash／Version History（一般的に30日以内）が唯一の実質的な復旧手段。DBスキーマ自体は`notion-build/create_*.py`で再構築できるが、実データの復元手段は現状ない（詳細・緊急時の対応は[Recovery-Guide.md](./Recovery-Guide.md)）

## ■ Design Principles

新しいAIがこのプロジェクトに手を加える際、必ず守ること。

1. **Constitution First**：`docs/ARu-Constitution.md`が最上位の権威。コードの挙動とConstitutionが矛盾する場合、直すべきはコードであってConstitutionではない
2. **No New Database**：新規データベースの追加は、Reiに個別確認してからのみ行う。既存DB・既存プロパティの拡張、またはPythonスクリプトでの対応をまず検討する
3. **Human Review First**：Update Level 2・3のコンテンツは、AIのスコアがどれだけ高くても、AI単独でPublished／Publish Approval=Approvedにしてはならない。これは方針ではなくコードで強制されている制約
4. **Provider Agnostic**：AI呼び出しは`scripts/ai_gateway.py`経由で行い、Claude/OpenAIどちらか一方に決め打ちしない
5. **Quality First**：生成されたコンテンツは、Article／Translation／SNSそれぞれ5観点でスコアリングしてから次の工程へ進める。低スコアは黙って無視せず、Statusを進めない形でブロックする

## ■ Recovery Procedure（新しいAIが読む順番）

**2026-07-14より、この節の詳細版は[docs/START-HERE.md](./START-HERE.md)（10分で全体像）と[docs/Recovery-Guide.md](./Recovery-Guide.md)（10ステップの復旧手順＋緊急時シナリオ）に切り出した。** 重複を避けるため、ここでは要点のみ再掲する。

1. [`docs/START-HERE.md`](./START-HERE.md) — 最初に全体像をつかむ（10分）
2. この文書（`docs/AI-Handover.md`） — 開発継続のための本体文書
3. `docs/ARu-Constitution.md` — 何を優先するかの原則。ここに反する変更は絶対にしない。Pending Amendments節も確認する
4. `docs/Roadmap.md` → `docs/Automation-Scripts.md` → `docs/Version4-Status.md` — 現在地、実装カタログ、直近スナップショット。編集ワークフロー全体の1枚図が欲しい場合は`docs/Editorial-Workflow.md`
5. AIエージェントの権限・振る舞いを変更する場合は`docs/AI-Agent-Constitution.md` → `AI-Agent-Architecture.md` → `AI-Agent-Workflow.md` → `AI-Editorial-Brain.md`を参照
6. `notion-build/.env.example` — 必要な設定キーの一覧を確認する（**`notion-build/.env`自体は絶対に読み上げない・表示しない・コミットしない。中身は秘密情報**）
7. `git log --oneline -20` — この文書の「Latest Commit」が古くなっていないか確認する
8. Notion側の実データを確認する（`notion-build/automation/daily_briefing.py`を実行すると現状が一望できる）

**セッション・PC・APIキーのいずれかを失った場合は、上記の代わりに[docs/Recovery-Guide.md](./Recovery-Guide.md)のEmergency Recoveryを参照。**

---

*ARu HQ / Decode Japan — AI Handover Document v1.8 — 2026-07-18*
