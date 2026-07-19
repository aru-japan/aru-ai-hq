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

## ■ Current Database Structure（既存11DB）

すべて実際にNotion上に作成済み。**新規データベースは追加しない**のが原則（後述）——Story Bankは、Rei自身の明示的な指示（Implementation Session、2026-07-18）にもとづく、この原則の正式な例外である。

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
| **Story Bank**（2026-07-18新設） | 編集アイデアの起点となるDB。Story Bank→QA Card→Article→Deep Guide→Instagram→Threadsというパイプラインの最上流。詳細は本文書■ Current Automationおよび[Automation Scripts](./Automation-Scripts.md)参照 |

**ARu Studio v4.1（2026-07-19）でプロパティ数が変わったDB**：Story Bank（15→28）、Articles（66→74）、Source Monitor（18→25）、Law Update（31→41）。すべて既存プロパティ・既存リレーションの再利用を優先し、新規追加は最小限——詳細な再利用表は[Automation Scripts](./Automation-Scripts.md)「ARu Studio v4.1 Editorial Intelligence」節参照。

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
- **ARu公式記事テンプレート再設計** `article_template.py`（新規、単一の情報源）／`render_article_layout.py`・`generate_article_pipeline.py`・`reviewer_agent.py`（更新）／`template_migration_report.py`（新規）：ブランド品質の標準化。旧9セクションテンプレートを、新しい8セクション公式構成（Basic Answer／More Details／Cultural Background／ARu Tip［必須］／Things to Know／FAQ／Premium Section／Sources）へ置き換えた。Title・Related Articles・Last Updatedは既存プロパティ（記事タイトル・`Knowledge Links`・`Last Verified Date`）から扱い、Bodyには含めない。`reviewer_agent.py`は既存の5観点スコアリングに加え、決定論的なセクション有無チェック（`Review Suggestions`に付記）とAIによるPremium価値・重複・fact/interpretation/recommendation区別の評価を追加（新規レビュープロパティなし）。`template_migration_report.py`は全記事をスキャンし新規プロパティ`Template Status`（Up to Date／Update Needed）を設定、Publishing Status・Priority・Urgencyで優先順位付けした移行レポートを生成——既存記事は自動的に書き換えない。実装中、AIが箇条書き内で使うインライン太字（例：「**浴衣を着てみましょう**：...」）を誤ってセクション境界と認識し、本文が途中で途切れる潜在バグ（旧テンプレートにも存在）を発見・修正。実データ全38記事をスキャンした結果、全件がUpdate Needed（新テンプレート導入前の生成のため想定どおり）。指定テスト記事の改訂版を生成したが、Rei承認まで本番記事は上書きしていない

- **Article Template Framework（G3-A、Standardのみ、2026-07-18）** `article_template.py`を単一テンプレート実装から`TEMPLATES`レジストリ（現状`"standard"`のみ登録）へリファクタリング。`get_template(name="standard")`で参照し、`parse_body_sections()`／`validate_sections()`は`template=`引数（既定`"standard"`）を追加。既存4スクリプト（`generate_article_pipeline.py`／`reviewer_agent.py`／`render_article_layout.py`／`template_migration_report.py`）はimport文・呼び出し方を一切変更せず、モジュールレベル定数（`SECTION_ORDER`等）がレジストリのビューになったことで動作を維持——リスク最小化のためあえて4スクリプト側は無改修とした。実データで検証：①`parse_body_sections`／`validate_sections`が固定テスト入力5パターン（正常系／箇条書き内インライン太字／ARu Tip欠落／空文字列／表記ゆれ見出し）でリファクタ前後バイトレベルで完全一致、②新規テストResearch/Articleを生成し8/8セクション検出（ARu Tip含む、検証後Archived／Rejectedへ退避）、③既存記事1件に対する`render_article_layout.py`実行・`reviewer_agent.py`実行（実Claude API呼び出し）がいずれも正常動作、④`template_migration_report.py`を全39記事に対して再実行し分類結果に変化なし（Update Needed 39/39、パターン不変）、⑤標準7スクリプト回帰テスト（`article_freshness_monitor.py`等）すべて正常完走。**目的はG3-B（Eventテンプレート）以降を、Standardテンプレートの安定動作を壊すリスクなしで低コストに追加できるようにすること。この時点でEventテンプレートは未実装、レジストリには`"standard"`のみ登録。**
- **Article Template Framework（G3-B、Eventテンプレート追加、2026-07-18）** `article_template.py`の`TEMPLATES`レジストリへ`"event"`を第2エントリとして追加（Before You Go／What to Expect／Cultural Background／Who This Is For／ARu Tip／Cautions & Accessibility／Premium Section／Sources、必須＝Before You Go・ARu Tip）。新規`template_for_category(category)`がCategory→テンプレート名の対応を一元化（Category=`イベント`→`"event"`、それ以外→`"standard"`）。Option 1（G4のEvent Calendarスキーマ拡張を待たない）で実装：費用・現金対応・英語対応など既存プロパティで確認できない項目は、Premium Section／Sourcesと同じ「捏造せず個別に未確認と明記する」方針をBefore You Go内でも踏襲。既存4スクリプト（`generate_article_pipeline.py`／`reviewer_agent.py`／`render_article_layout.py`／`template_migration_report.py`）はいずれもCategoryから`template_for_category()`でテンプレートを解決してから`parse_body_sections()`／`validate_sections()`等へ`template=`を渡す形に更新（G3-Aとは異なりこの4スクリプトも変更対象）。実データで検証：①Standardテンプレートの`TEMPLATES["standard"]`エントリがG3-A時点とバイトレベルで完全一致（無変更を確認）、②新規テストResearch（Category=イベント）から実際にArticleを生成し**Before You Go**から本文が始まる（Basic Answerへのフォールバックなし）8/8セクション検出を確認、③同記事に対する`render_article_layout.py`（`[event]`表示）・`reviewer_agent.py`（実Claude API、`【テンプレート準拠：event】全8セクション確認済み`）がいずれも正常動作、④`template_migration_report.py`実行で当該記事のみ`Up to Date`（他39件のStandard記事は`Update Needed`のまま不変）、⑤標準7スクリプト回帰テストすべて正常完走。テスト記事・テストResearchは検証後Archived／Rejectedへ退避。**Reiが追加指示したRollback Criterion（Event記事が必須セクションを欠くか、誤ってStandard構成にフォールバックした場合は全面ロールバック）を満たすことを実データで確認済み。**

- **Story Bank Database v1.0（2026-07-18、新規DB）** `notion-build/create_story_bank.py`：Story Bank→QA Card→Article→Deep Guide→Instagram→Threadsというパイプラインの最上流となる新規データベース。プロパティ：Title／Category（Research既存の7分類を再利用）／Subcategory（現状「花火大会」のみ、今後有機的に追加）／Season／Region（Source Libraryと同じ地方区分）／Priority（S/A/B/C、オプション定義順をC→Sの低→高にして降順ソートでSが先頭に来るようにした——2026-07-16のPriority/Urgency降順バグと同じ教訓を先取り適用）／Target User／Evergreen／Premium Candidate／Event Month／Source Status／Story Status。リレーションは実在するDBのみに設定（`Generated Article`→Articles、`Related SNS Posts`→SNS Queue、いずれも双方向relationとして実データで確認済み）。QA Card・Deep Guideへのリレーションは、両者ともまだ保存モデルが未決定のため意図的に追加していない。View（Story Backlog／High Priority／Summer／Autumn／Evergreen／Premium Candidates／Ready for Production）はNotion公開APIの制約により作成できず、[Story-Bank-View-Setup-Guide.md](./Story-Bank-View-Setup-Guide.md)として手動設定手順を文書化した。**[Knowledge-Lifecycle-Architecture-v1.0.md](./Knowledge-Lifecycle-Architecture-v1.0.md)のOpen Question #3（Story BankをExperience Intelligence拡張ではなく独立DBとして実装するか）は、本実装によって「独立DB」で確定した。**
- **Story Bank Batch #001インポート（2026-07-18）** `notion-build/automation/bulk_import_story_bank.py`（新規）：ChatGPT側が選定した「National Fireworks Top 50」の最初の20件をCSV（`notion-build/automation/data/story_bank_batch_001.csv`）からインポート。**Claude Codeはコンテンツを推測・生成・補完しない**——ChatGPTが企画・選定し、Claude Codeはインポート・実装のみを担当するという役割分担（2026-07-18確定）にもとづく。CSVの英語ラベル（Category="Event"、Region="Tokyo"等）は、既存の日本語Select語彙（イベント、関東等）へ正規化してから書き込む設計とし、新しい英語オプションを並存させない。インポート前に既存タイトルとの重複確認を実施（実データ0件重複）。実行結果：**20件中20件インポート、重複0件**。2件の判断が必要な警告を検出：①「関門海峡花火大会」のRegionが元データで`Fukuoka/Yamaguchi`（2地方にまたがる）だったため、Region単一選択の制約上`九州・沖縄`へ判断で割り当て、②「熱海海上花火大会」のEvent Monthが元データで`Multiple`（具体的な月の指定なし）だったため、推測せずEvent Month未設定のままにした
- **Story Bankバッチ運用ルールの正式化（2026-07-18）** Batch #001実施時に生じた2件の警告（Region複数県またがり／Event Month=Multiple）を、恒久的なスキーマ・運用ルールへ格上げ。`notion-build/add_story_bank_notes_and_region_rules.py`（新規、一回限りのスキーマ移行スクリプト）でStory Bankに3つの変更を適用済み：①`Region`→`Primary Region`へリネーム、②新規`Notes`（rich_text）追加、③Event Monthの選択肢に`Multiple`を追加（実データで反映確認済み、13オプション：1月〜12月＋Multiple）。`bulk_import_story_bank.py`を全面改修——Regionが複数県にまたがる場合は先頭県を`Primary Region`に設定しNotesへ残り（例：関門海峡花火大会なら`Fukuoka`→`九州・沖縄`をPrimary Region、`Also spans: Yamaguchi`をNotesへ）、Event Month=`Multiple`は未設定にせず選択肢`Multiple`をそのまま設定するよう変更（今後は空欄放置なし）。CSV運用ルールも正式化：保存場所は`notion-build/automation/data/`、命名は`StoryBank_Batch###_Category.csv`、インポート成功後は`notion-build/automation/data/imported/`へ移動（削除せず履歴として保管）——`story_bank_batch_001.csv`も本ルールに合わせ`imported/`へ移動済み。毎回のインポート報告は**重複チェック／インポート件数／Story Bank総件数／エラー／保留事項**の5項目のみに固定。ChatGPTからCSVを受け取り次第、Claude Codeが確認なしで自動インポートする運用に移行（Rei承認済み）
- **ARu Studio v4.1 Editorial Intelligence（2026-07-19）** Story Bankを「QAカードの起点」として運用、Law Updateを更新キューとして運用、Source MonitorからLaw Update・影響記事の抽出までを既存資産の再利用で実現。Rei方針「重複プロパティは作らず既存拡張を優先」にもとづき、実装前にAPIで4DBの実スキーマを取得し、要求項目の多くを既存プロパティ・既存リレーションで代替（例：Target Persona→既存13値Audience taxonomy再利用、Update Status→既存Statusへの選択肢追加）。段階的実装（Schema→Relations→Automation→Templates→Dashboard→Docs）、各段階で実データ検証済み。新規：Story Bank(15→28)/Articles(66→74)/Source Monitor(18→25)/Law Update(31→41)のプロパティ追加、7本の新規リレーション（重複0件確認済み）、`notion-build/automation/law_update_pipeline.py`（Human-in-the-loop、AIはPublishedを一切設定しない）、`article_template.py`へ5テンプレート追加（headline/deep_guide/premium/update_notice/food_restriction）＋QA Card/Existing Article Revisionガイド、`ai_command_center.py`へ5新規セクション。詳細・既知のギャップ（Previous Rule自動保存なし、SNS Queue連携未実装、Content Type起点の新規生成CLI未対応等）は`docs/Automation-Scripts.md`「ARu Studio v4.1 Editorial Intelligence」節、View設定は[Studio-v4.1-View-Setup-Guide.md](./Studio-v4.1-View-Setup-Guide.md)参照
- **編集運営フローの精緻化（2026-07-19）** v4.1を単なる変更検知から編集運営フローへ拡張（Rei追加指示）。①`law_update_pipeline.py`にPriority自動算出（Urgency＋影響範囲、既存Priorityプロパティ再利用）とImpact Summary（既存rich_text）へのQA/記事(Content Type別)/SNS件数の構造化記録を追加、②`notion-build/automation/review_scheduler.py`（新規）でUpdate Frequencyに基づくNext Review自動算出と定期レビュー期限抽出を実装（Event-Basedは年が特定できないため対象外、意図的）、③`ai_command_center.py`の先頭を「🆕 今日追加するQA」「🔴 更新が必要な記事」「🚀 公開待ちコンテンツ」の3セクションへ再構成（既存の個別セクションを重複なく統合、他は詳細として維持）。実データ検証済み（既存Story Bank本番レコード1件を一時的に使用した検証は完了後に元の未設定状態へ復元済み）。標準7スクリプト回帰テスト全通過。詳細は`docs/Automation-Scripts.md`「編集運営フローの精緻化」節参照
- **Production Stage（Story Bank・Articles両方の新規プロパティ、2026-07-19）** `notion-build/add_production_stage.py`：Reiが提示した制作パイプライン（Today's QA→Headline Ready→Basic Writing→Deep Writing→Translation→SNS→Ready→Published）を、Story Bank（32プロパティ）とArticles（77プロパティ）の両方へ独立したSelectとして追加——「Statusは編集・承認状態、Production Stageは制作フロー」という役割分離のRei明示指示にもとづく。Story Bankは起点Storyの全体位置づけ、Articlesは個別記事自体の位置づけを別々に追跡（1つのStoryから複数Content Typeの記事が並行して異なる段階にありうるため）。スキーマのみでバックフィルなし（Story Bank 21件・Articles 59件とも未設定のまま、捏造禁止ルール）。`ai_command_center.py`に「📋 Production Stage内訳」（パイプライン順の件数表示）を追加、カンバン（Board View）自体はAPI制約により[Studio-v4.1-View-Setup-Guide.md](./Studio-v4.1-View-Setup-Guide.md)で手動設定。自動進行の自動化は未実装（要判断）

詳細と実行方法は`docs/Automation-Scripts.md`。

## ■ Current Phase

**Roadmap Version 3.5（Pilot Operation）Day 2まで完了。** AI編集部を7日間実運用して検証する段階の2日目（Business Roadmap側の進行、v4.1とは独立）。

**Studio側：ARu Studio v4.1「Editorial Intelligence」を2026-07-19付でReleased（正式リリース）とした。** [Studio-v4.1-Release-Notes.md](./Studio-v4.1-Release-Notes.md)・Gitタグ`studio-v4.1.0`参照。**Rei決定により、v4.1をもって新機能開発を一時停止し、実運用フェーズへ移行する。** Version 4.2は実運用から得られる知見にもとづいて設計する方針——次にAIセッションを開始する際は、明示的な実装依頼がない限り新機能を提案・実装しないこと。

## ■ Latest Commit

`b3c7ae8`（このHandover文書を書いた時点でのHEAD）。**必ず`git log --oneline -10`で実際の最新を確認すること。** このフィールドは経年劣化する。

**Dashboard「作業開始画面」化（2026-07-19、方向性のみ確認・未実装）**：Reiより、Dashboardを「案内板」から「編集長が一日中仕事をする作業開始画面」へ発展させる方向性が明示された（詳細は[Automation-Scripts.md](./Automation-Scripts.md)「Zone 2の使いやすさ改善」節の「今後の方向性」参照）。次にこの領域へ着手する際は、具体的な構成案（DB・プロパティ単位でAPI実装可能な範囲とRei手動設定が必要な範囲を明示）を提示し承認を得てから実装すること。

**Version 4.2着手（2026-07-19、Rei明示の実装依頼）**：上記「新機能開発を一時停止」の方針どおり、Rei本人からの明示的な依頼を受けて着手。①「運営者向けガイド」（11データベース＋Dashboardの先頭に役割・使うタイミング・次に進むDB・AI／人の担当・具体例・次の作業を表示）②「編集長ファースト3ゾーン再設計」（Dashboardを✍️今すぐ書く／📋今日の判断／🔍詳細・AI監視の3ゾーンへ再構成、「3クリック以内で記事を書き始められる」ことを必須要件として実装）。詳細は[Automation-Scripts.md](./Automation-Scripts.md)の該当節参照。新機能開発の一時停止方針そのものは継続中——本件のような明示的な依頼がない限り、新規実装を提案・着手しないこと。

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
- ARu公式記事テンプレート再設計（2026-07-18）：ブランド品質の標準化として、記事本文の構成を旧9セクションから新8セクション（Basic Answer／More Details／Cultural Background／ARu Tip［必須］／Things to Know／FAQ／Premium Section／Sources）へ刷新。`article_template.py`を単一の情報源として新設し、生成（`generate_article_pipeline.py`）・レビュー（`reviewer_agent.py`）・レンダリング（`render_article_layout.py`）の3スクリプトが共通で参照する設計に統合（従来の重複定義を解消）。`reviewer_agent.py`に決定論的なテンプレート準拠チェックとAIによる追加評価（Premium価値・重複・fact/interpretation/recommendation区別）を追加、`template_migration_report.py`を新規実装し新規プロパティ`Template Status`で全記事の準拠状況を可視化（既存記事は自動的に書き換えない）。実データテストで、AIが箇条書き内のインライン太字を誤ってセクション境界と認識し本文が途切れる潜在バグ（旧テンプレートから存在）を発見・修正。全38記事がUpdate Needed（想定どおり、コード不具合ではない）。指定テスト記事「日本のカフェ文化が変わった理由」の改訂版を実データから生成、既存の実質的内容を保持しつつ8セクションへ再編成——**Rei承認まで本番記事は上書きしていない**

- Article Template Framework（G3-A、2026-07-18）：`article_template.py`を単一実装から`TEMPLATES`レジストリへリファクタリング（Standardテンプレートのみ登録、Event等の将来テンプレートを低コストで追加できる土台）。既存4スクリプトは無改修のまま動作を維持し、実データ（既存記事の再レンダリング・再レビュー、新規テスト記事の生成、全39記事の`template_migration_report.py`再実行、標準7スクリプト回帰テスト）で振る舞いの同一性を確認済み（詳細は本文書■ Current Automation、[Automation Scripts](./Automation-Scripts.md)参照）。次段階（Eventテンプレートの追加、G3-B）は別セッションで着手予定——**次のArchitecture Sessionでは実装より先にARu User Journey Specificationを定義する方針（Rei決定）**
- **Architecture Phase完了（`2ff1064`、2026-07-18）**：3回のArchitecture Sessionの成果として、[Architecture-Specification-v1.0.md](./Architecture-Specification-v1.0.md)（Knowledge Architecture／Universal Properties／Category・Sub Category／Generation Rules等の技術仕様、Glossary・Architecture Decision Log付き）、[User-Journey-Architecture-v1.0.md](./User-Journey-Architecture-v1.0.md)（Mission／User Journey／Content Ladder／Content Domains／Story Bank／Human Layer／Editorial Principles）、[Knowledge-Lifecycle-Architecture-v1.0.md](./Knowledge-Lifecycle-Architecture-v1.0.md)（Story／Knowledge Lifecycle、User・Mentorフィードバックループ、Article／Deep Guide進化、AI Learning Boundaries、Human Knowledge Integration、Long-term Content Maintenance）の3文書を追加。G3-B着手前に編集哲学・ユーザー体験・知識循環を実装より先に定義する方針（Rei決定）にもとづくもので、コード・スキーマの変更は含まない
- Article Template Framework（G3-B、2026-07-18）：`TEMPLATES`レジストリへ`"event"`を追加し、`template_for_category()`によるCategory→テンプレートの一元的な振り分けを実装。Standardテンプレートの既存動作は無変更（バイトレベルで確認）。既存4スクリプトすべてをCategoryベースでテンプレートを解決する形に更新。実データで、Category=イベントのテスト記事が正しくEventテンプレート（Before You Goから開始、8/8セクション）で生成され、Standardへフォールバックしないことを確認——Reiが追加したRollback Criterionを満たす（詳細は本文書■ Current Automation、[Automation Scripts](./Automation-Scripts.md)参照）。G4（Event Calendarスキーマ拡張）は依存させず、未確認情報は個別に「未確認」と明記する既存の捏造防止方針で対応
- **Version4 Completion Report作成（`c4b473d`、2026-07-18）**：Version4準備作業・Architecture Phase・G3-A／G3-Bを対象とした公式クロージングレポート[Version4-Completion-Report.md](./Version4-Completion-Report.md)を作成。`Roadmap.md`の「Version 4 — Enterprise」（対外的な事業判断を要する本体、引き続き0/5）とは異なるスコープであることを明記済み
- **Story Bank Database v1.0（2026-07-18、新規DB）**：Rei明示的承認によりNo New Database原則の例外として実装。詳細は本文書■ Current Automation・[Story-Bank-View-Setup-Guide.md](./Story-Bank-View-Setup-Guide.md)を参照
- **Story Bank Batch #001（2026-07-18）**：ChatGPT選定の花火大会20件を`bulk_import_story_bank.py`でインポート（20/20成功、重複0件）。詳細は本文書■ Current Automation参照
- **ARu Studio v4.1 Editorial Intelligence（2026-07-19）**：Story Bank(15→28)/Articles(66→74)/Source Monitor(18→25)/Law Update(31→41)へのプロパティ追加、7本の新規リレーション、Law Update Pipeline（Human-in-the-loop）、5テンプレート追加、Dashboard5セクション追加。詳細は本文書■ Current Automation・[Automation Scripts](./Automation-Scripts.md)・[Studio-v4.1-View-Setup-Guide.md](./Studio-v4.1-View-Setup-Guide.md)参照
- **ARu Studio v4.1 正式リリース（Released、2026-07-19）**：編集運営フローの精緻化（Priority自動算出／Impact Summary構造化／review_scheduler.py／Dashboard再構成）とProduction Stage（Story Bank・Articles両方）を経て、[Studio-v4.1-Release-Notes.md](./Studio-v4.1-Release-Notes.md)として正式クローズ。Gitタグ`studio-v4.1.0`（Business Roadmapのタグ`v1.1.0`〜`v3.5.0`と混同しないよう、あえて`v4.1.0`ではなく`studio-`接頭辞とした）。**Rei決定により、v4.1をもって新機能開発を一時停止し実運用フェーズへ移行。Version 4.2は実運用の知見にもとづいて設計する方針**
- **AI Command Center・Dashboardの統一（2026-07-19、リリース後のRei追加指示）**：v4.1正式リリース後、既存Dashboardの構成がVersion4.0時代のままでv4.1の運営フローと不一致という指摘を受け対応（新機能追加ではなく既存画面の整合性修正のため、新機能開発一時停止方針とは矛盾しない）。AI Command Centerの先頭7セクションをRei指定の優先順（🆕今日追加するQA／✍今日作る記事(Production Stage別)／🔴更新が必要な記事／🚀公開待ちコンテンツ／📋Production Stage内訳／📡Source Monitor Alerts／⚖Recent Law Updates）に再構成し、実際のNotionページのブロック順をAPIで取得して確認済み。手動Dashboard（13 Linked View）は[Dashboard-Setup-Guide.md](./Dashboard-Setup-Guide.md)へ同じ優先順の推奨並び順を追加（実際の並べ替えはRei手動作業）。Coverage Analysis／Duplicate Prevention／Today's Research等の分析系はいずれも削除せず下部へ維持。詳細は[Automation-Scripts.md](./Automation-Scripts.md)「AI Command Center・Dashboardの統一」節参照
- **ホーム画面の統一：DashboardをAI Command Centerの正式ホームへ（2026-07-19、追加指示）**：DashboardページとAI Command Centerページの重複を解消するため、Dashboardを唯一のホーム画面に統一。Rei確認済みの方針：①既存13 Linked Viewは削除せず残す（実運用数週間後に整理）、②`ai_command_center.py`（ファイル名は同じ、書き込み先のみDashboardへ変更）が7項目セクションをDashboardページへ書き込む、③旧AI Command Centerページは更新停止のみでバックアップとして保持。NotionパブリックAPIは「先頭挿入」ができないため、開始・終了2つのcalloutを目印として自動生成セクションの範囲を特定し、その間だけを安全に差し替える方式を実装（既存13 Linked Viewには一切触れない）。実装中、ページが137ブロックとなり100件のページネーション境界を超えたことで目印を見失うバグを発見・修正（`_fetch_all_children()`でページネーション対応）。実データで2回連続実行しブロック数が変化しない（重複なし）ことを確認済み。Reiが自動生成セクション全体をDashboard上部へ移動済み（マーカー追跡設計が実運用で正しく機能することを確認）。詳細は[Automation-Scripts.md](./Automation-Scripts.md)「ホーム画面の統一」節参照
- **運営ガイドの折りたたみ化（2026-07-19、追加指示）**：見出し・最終更新時刻・7項目構成の説明文を、毎日確認する必要がないためページ先頭から折りたたみ（toggle）ブロック「📖 運営ガイド」へ移設し、自動生成セクション末尾（終了マーカー直前）へ配置。ホーム画面を開いて最初に見えるのが「🆕 今日追加するQA」になるよう修正。実データで確認済み（block 0が🆕見出しになったことをAPIで確認）。詳細は[Automation-Scripts.md](./Automation-Scripts.md)「運営ガイドの折りたたみ化」節参照
- **ARu Studio v4.2「編集長ファースト3ゾーン再設計」＋運営者向けガイド（2026-07-19、別セッションで実施）**：Dashboardを①✍️今すぐ書く（AIが次の1本を自動提案・実リンク）②📋今日の判断（🔴Critical／🚀公開判断待ち／🔧更新が必要の3数字）③🔍詳細・AI監視（16個のtoggleへ集約）の3ゾーンへ再構成。各DBのdescription欄へ運営者向けガイドを追加。スキーマ・プロパティ変更なし。詳細は[Studio-v4.2-Editor-First-Guide.md](./Studio-v4.2-Editor-First-Guide.md)、技術詳細は[Automation-Scripts.md](./Automation-Scripts.md)参照
- **Research → Article Brief（v4.2、2026-07-19）**：「データベースを見る編集部」から「記事を書く編集部」への転換。実装前にNotion画面レベルのモックアップと8段階ワークフローのストーリーシミュレーションで承認を得てから実装。Research 32→35プロパティ：`Raw Notes`を`Editor's Notes`へリネーム（AI専用の`Summary`と役割分離、既存の未使用フィールドを転用し新規プロパティは追加せず）、新規リレーション3本（`Related Law Updates`／`Related QA`↔Story Bank／`Related Articles`——既存`Converted Article`とは別軸）。Freshness／Why now?／Source Confidenceはいずれも既存プロパティ（`Last AI Update`／`Evidence Level`／`Verification Status`等）の表示方法のみで新規スキーマなし。実データで76件のResearch・対象4DBとも件数変化なし、重複リレーションなし、標準回帰テスト全通過。編集運用ルールは[Operating-Manual.md](./Operating-Manual.md)§13、技術詳細は[Automation-Scripts.md](./Automation-Scripts.md)「Research → Article Brief」節参照。**Article Brief自体のページレイアウト（トグル・Callout・埋め込みView）は未実装、次回セッションの対象**

## ■ Remaining Tasks

- **Studio v4.3の方向性候補（2026-07-19、まだ設計・実装は未着手）**：Article Brief初回実運用（外国人の社会保険、25分）で、Reiより「構造としては正しいが、編集者として大きな変化を体感できたとまでは言えなかった」というフィードバック。ネガティブな評価ではなく、次のテーマ選定の材料として記録——**候補テーマは「構造改善」ではなく「編集者がすぐに違いを感じられるUI/UX改善」**（具体例：SNSドラフトの見やすさ改善）。詳細は[Operating-Manual.md](./Operating-Manual.md)§13運用ログ参照。命名はBusiness Roadmapとは独立の「Studio v4.3」を想定（既存のBusiness Roadmap vs Studio vXの命名規則どおり）
- **Article Briefのページレイアウト自体が未実装**（2026-07-19）：Research→Article Briefのスキーマ・リレーションは完了したが、モックアップで示した画面構成（トグル・Callout・埋め込みDatabase View・「記事を書く」ボタン）自体はまだNotion上に反映していない。次回実装対象
- **既存13 Linked Viewの整理は保留中**（2026-07-19、Rei方針）：実運用を数週間進めた後、不要なセクション（Today's Opportunities的な旧構成等）を整理する。[Dashboard-Setup-Guide.md](./Dashboard-Setup-Guide.md)「ARu Studio v4.1 推奨並び順」に新規2種類（今日追加するQA＝Story Bank、今日作る記事＝Articles Production Stage別）の設定内容を記載済みだが、実際の追加・並べ替えは急がず後回しでよい方針
- **旧AI Command Centerページの最終的な扱いが未決定**（2026-07-19）：削除・Archiveせず、更新のみ停止してバックアップ兼リファレンスとして保持中。実運用を進めながら将来判断する
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
- **Law Update PipelineのD（変更前後の全文保存）が未実装**：`source_watcher.py`はSimHash指紋のみ保存し生の全文を残さないため、`Previous Rule`は自動では埋まらない（`New Rule`はDiff/Change Summaryから自動転記される）
- **Law Update PipelineのG（SNS Queue連携）が未実装**：SNS Queueに「要更新」を表すプロパティが無い（今回のリクエストのプロパティ一覧に含まれていなかったため追加していない）。Translationの`Needs Re-Translation`フラグ立ては実装済み
- **Content Type起点の新規記事生成がまだできない**：`generate_article_pipeline.py`のCLIは`--content-type`引数を持たない。Headline/Deep Guide/Premium/Update Noticeテンプレートは、記事作成後にContent Typeを人間が設定すれば以降のreviewer/render/migration reportで正しく解決される
- **Food Restriction Supportテンプレートは未到達**：Story Bank→Article自動生成パイプライン自体がまだ存在しない（本セッションのスコープ外）。テンプレート自体はレジストリに登録済みで、そのパイプラインができた時にそのまま使える
- **Story Bank Batch #001は「National Fireworks Top 50」の一部（20件）のみ**：全50件のうち残り30件は未投入。ChatGPT側からBatch #002以降が`notion-build/automation/data/StoryBank_Batch###_Category.csv`として提供され次第、`bulk_import_story_bank.py`で確認なしに自動インポートする運用（2026-07-18確定）
- **Story Bank 20件はSource Status=Unverified・Story Status=Newのまま**：Rei／ChatGPT側での事実確認・優先順位レビュー待ち。QA Card・Articleの生成はまだ行っていない（指示どおり）
- **Knowledge-Lifecycle-Architecture-v1.0.md Open Question #3の文書側反映が未了**：「Story Bankは独立DB」で運用上は確定済み（AI-Handover.md記載済み）だが、Architecture文書自体への反映はRei指示により次回のArchitectureメンテナンスセッションへ意図的に持ち越し中

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

*ARu HQ / Decode Japan — AI Handover Document v1.9 — 2026-07-18*
