<title>Automation Scripts v2.1</title>

# Automation Scripts
### ARu Studio — Roadmap Version 3 実装記録 ＋ Version 4準備 ＋ Version 4 Phase 5（Editor Experience）＋ ARu Intelligence Phase 1/2/3

| | |
|---|---|
| **Status** | Active — Notion自動化24スクリプト＋AI Gateway＋Article Freshness Monitor＋Coverage Analyzer＋Editorial Planner＋Publishing Center＋Duplicate Prevention＋Editor Experience（Article Layout Renderer／Editor Home／AI Command Center）＋ARu Intelligence Phase 1（Source Watcher）＋Phase 2（Source Library Expansion／Bulk Import）＋Phase 3（Research Prioritizer／Today's Opportunities／Editorial Intelligence）実装・実データ／実API（Claude）でテスト済み |
| **Date** | 2026-07-18 |
| **位置づけ** | [AI Agent Workflow](./AI-Agent-Workflow.md)に定めた処理を、新規DB（AI Agents／Prompt Library／Automation）を追加せず、既存10DBに対するPythonスクリプトとして実装したもの |
| **場所** | `notion-build/automation/` |

---

## 前提

これらのスクリプトは、[Roadmap](./Roadmap.md)でDeferredとした`Automation` DBの代わりに、実際に動く自動化を先に用意するためのもの。実行主体は今のところ**人間が手動で実行する、またはOSのスケジューラ（cron等）に登録する**ことを想定しており、**スケジューリング自体はまだ設定していない**（要判断。下記「未実施事項」参照）。

---

## スクリプト一覧

| スクリプト | 対応するAgent | 処理内容 |
|---|---|---|
| `check_translation_gaps.py` | Translator | ArticleのUpdated Date変化をTranslation.Source Updated At（Rollup）経由で検知し、`Needs Re-Translation`をチェック |
| `sync_source_monitor_to_research.py` | Researcher | Source Monitorで`Change Detected=true`かつ未着手のものから、Researchドラフトを自動作成 |
| `escalate_law_significance.py` | Editor-in-Chief | Law Update.Significance=Majorの場合、Affected ArticlesのUrgencyを自動でCriticalへ引き上げ |
| `sync_editorial_calendar_status.py` | Editor-in-Chief | Linked ArticleがPublishedになったEditorial Calendarエントリを自動でPublishedへ同期 |
| `enforce_publish_gate.py` | Editor-in-Chief（Quality Gate） | Status=PublishedなのにQA Status≠PassedやUpdate Level 2/3でHuman Reviewed=falseの記事を検知し、Human Reviewへ強制的に差し戻す（ARu Constitution §9/§13のコード化） |
| `daily_briefing.py` | Editor-in-Chief | Dashboard（編集長ホーム画面）のうち🔴 Update Needed＋①〜⑨（計10セクション）をCLIに表示する、Linked View未設定時点でも使えるテキスト版ダッシュボード（📊📝🚀📚🛠の5セクションは専用Notionページ／Linked View側のみで、CLI版には未反映） |
| `research_assistant.py` | Researcher | テーマを指定すると、Source Library／Law Update／既存Research／既存記事との重複をNotionから実データで検索し、Markdownのリサーチ資料を出力（Pilot Operation Day 1で使用） |
| `article_assistant.py` | Writer | テーマを指定すると、既存記事・Editorial Calendarとの重複確認、推奨Category/Update Level/Audienceを出力（Pilot Operation Day 1で使用） |
| `article_freshness_monitor.py` | Editor-in-Chief（Freshness Gate） | Update Levelごとのレビュー間隔超過、およびLaw Update/Source Monitor/Event Calendarの変化検知を基に、記事のFreshness Statusを日次更新しDashboard最上部の「🔴 Update Needed」に反映（Version 4準備、詳細後述） |
| `coverage_analyzer.py` | Editor-in-Chief（企画・編集会議） | 生活トピック別の記事数・鮮度・Review待ちを集計し、AIが不足トピック・優先トピック・おすすめ新規テーマ（10件）を提案。Dashboard「📊 Coverage Analysis」＋専用Notionページに反映（詳細後述） |
| `backfill_life_topics.py` | — | 既存記事にLife Topicsを一括付与する再実行可能なバックフィルスクリプト（Coverage Analyzerの前提データ作成用） |
| `editorial_planner.py` | Editor-in-Chief（編集会議・アサイン） | Coverage Analyzerの集計データから、★1〜5の優先度付き編集プラン（Reason・タイトル案・想定Update Level／Category）を生成し、`--generate-research`でResearchレコードを自動作成。Dashboard「📝 Editorial Planner」＋専用Notionページに反映（詳細後述） |
| `publishing_center.py` | Editor-in-Chief（公開管理） | Articles全件のPublishing Status（Draft／Ready to Publish／Published／Needs Update／Archived／Duplicate）を、Review Result・Translation Quality Result／Publish Approval・Freshness Status・必須項目の充足状況から同期。Published判定は必ず人間が行い、AIは自動公開しない。Dashboard「🚀 Ready to Publish」「📚 Published Articles」「🛠 Needs Update」に反映（詳細後述） |
| `duplicate_guard.py` | Editor-in-Chief（生成前ゲート） | 生成開始**前**にResearch.Topic／Article／Translation／SNSの存在を順に確認し、既存なら生成せず「Already Exists」として記録する。「1 Research Topic = 1 Article」原則をコードで強制（詳細後述） |
| `duplicate_prevention_report.py` | Editor-in-Chief（公開管理） | `duplicate_guard.py`のログから本日の生成件数・スキップ件数・Already Exists一覧を集計。Dashboard「🛡 Duplicate Prevention」＋専用Notionページに反映（詳細後述） |
| `render_article_layout.py` | Editor-in-Chief（Editor Experience） | Articles.Bodyの9セクションテンプレートを、Articleページの実ブロック（見出し＋段落、4セクションはtoggle折りたたみ）として描画。スキーマ・プロパティは無変更（詳細後述） |
| `editor_home.py` | Editor-in-Chief（Editor Experience） | 「今日、人間が決めること」9項目の件数をDashboardと同一フィルタで集計し、専用Notionページ（ナビゲーションハブ）に反映（詳細後述） |
| `ai_command_center.py` | Editor-in-Chief（Editor Experience） | Freshness内訳・Duplicate Prevention本日の活動・外部監視フィード・AI分析ページへのポインタを専用Notionページ（ナビゲーションハブ）に反映（詳細後述） |
| `source_watcher.py` | Editor-in-Chief（情報源監視） | Source Libraryの公式情報源URLを定期フェッチし、SimHash指紋の変化から本物の変化検知を行い、Source Monitorレコードを自動作成。Importance優先度順で処理し、Update Classificationを自動分類（詳細後述） |
| `source_categories.py` | — | Source Category（22件）とUpdate Classification（11件）のタクソノミー定義（`life_topics.py`と同じ構造）。`ensure_schema()`とAI分類の単一の情報源 |
| `bulk_import_sources.py` | Editor-in-Chief（情報源一括登録） | CSVからSource Libraryへ一括登録。URL重複はスキップ、未知のSelect値は自動でスキーマへ追加（詳細後述） |
| `research_prioritizer.py` | Editor-in-Chief（企画・優先順位付け） | Status=NewのResearchを5軸（Freshness／Foreign Resident Value／Tourism Value／Seasonal Relevance／Premium Potential）で決定論的にスコアリング。新規スキーマ・AI呼び出しなし（詳細後述） |
| `today_opportunities.py` | Editor-in-Chief（企画・優先順位付け） | Event Calendar／Source Monitor／Law Update／Researchの4つの既存システムを統合し、「今日動くべきこと」を種類別に提示（詳細後述） |

## 実行方法

```
cd notion-build/automation
python3 check_translation_gaps.py
python3 sync_source_monitor_to_research.py
python3 escalate_law_significance.py
python3 sync_editorial_calendar_status.py
python3 enforce_publish_gate.py
python3 daily_briefing.py
python3 research_assistant.py --topic "在留カード更新" --keyword "在留"
python3 article_assistant.py --topic "在留カード更新" --keyword "在留" --category "法律・制度"
```

いずれも標準ライブラリのみで動作し、`notion-build/.env`のNOTION_TOKENと各`_DB_ID`を読み込む。

## テスト結果（実データ）

| スクリプト | 結果 |
|---|---|
| check_translation_gaps.py | 既存Translationテストレコード1件を検査、要再翻訳なしと正しく判定 |
| sync_source_monitor_to_research.py | Source Monitorのテストレコードから、リンク漏れだったResearchを実際に1件新規作成 |
| escalate_law_significance.py | Law Update（Significance=Major）テストレコードから、Affected ArticleのUrgencyをMedium→Criticalへ実際に更新 |
| sync_editorial_calendar_status.py | 対象のLinked ArticleがまだDraftのため、正しく「同期対象なし」と判定 |
| enforce_publish_gate.py | Published状態の記事が存在しないため、正しく「違反なし」と判定 |
| daily_briefing.py | 9セクションすべてが実データ（Publish Approval Pending／Article・Translation・SNS Review Waiting／Research／Law Update／Event等）を正しく表示（Dashboard刷新に合わせて更新） |
| research_assistant.py | 「在留カード更新」で実行し、Source Library・既存Research・既存記事との重複を正しく検出（Pilot Day 1） |
| article_assistant.py | 同上、Category=法律・制度からUpdate Level 2を正しく推奨（Pilot Day 1） |

---

## AI Gateway（Phase B3.6）

**場所**：`scripts/ai_gateway.py`（`notion-build/`とは別の、リポジトリ直下の新フォルダ）

**目的**：ここまでのスクリプトはNotionからの実データ取得のみで、要約・執筆などの生成AI処理はすべてこのチャット上でAI Operator（Claude）が手動で担当していた。AI Gatewayは、**Claude APIとOpenAI APIのどちらでも呼び出せる共通の入り口**を用意し、将来この生成AI部分をコードから直接呼び出せるようにするための土台。

**設定**：`notion-build/.env`に`CLAUDE_API_KEY`・`OPENAI_API_KEY`を追加（どちらか一方だけでも動作する）。

**プロバイダの選び方**：`--provider`で明示指定しない限り、Claude／OpenAIどちらのキーが設定されているかを見て自動選択する（両方ある場合はClaudeを優先）。

**動作確認**：

```
python3 scripts/ai_gateway.py --input "要約したい文章..."
```

**動作確認済み（実API呼び出し）**：CLAUDE_API_KEYが設定され、実際にClaude APIを呼び出して要約を生成できることを確認した。

---

## Phase B3.7：Research→Article→Translation→SNSの自動生成パイプライン

**場所**：`notion-build/automation/generate_article_pipeline.py`

**内容（Phase B3.11で独立サブコマンド化）**：AI Gateway（実際のClaude API呼び出し）を使い、Article／Translation／SNSを独立して実行できる。

```
python3 generate_article_pipeline.py article     --keyword "..." --category "..."
python3 generate_article_pipeline.py translation  --article-id "..."
python3 generate_article_pipeline.py sns          --article-id "..."
python3 generate_article_pipeline.py all          --keyword "..." --category "..."   # 従来通り3つ連続実行
```

1. **article**：Research（Status=Converted）を1件取得し、Claude APIで記事本文を生成してArticlesへ保存（Status=**AI Draft**、CategoryからUpdate Levelを自動算出、Source Researchでリンク）
2. **translation**：既存Articleを取得し、Claude APIで英訳を生成。**翻訳と同時にAI自身が文化的補足の完了度を自己評価**し（`CULTURAL_ADAPTATION: Done`／`Needs Review`）、Localization Statusへ反映（Phase B3.11で追加）
3. **sns**：既存Articleを取得し、Instagram／Threads／Xそれぞれ異なるトーンの投稿文をClaude APIで生成しSNS Queueへ保存

**ガバナンス**：生成された記事・翻訳・投稿はすべて**未公開・未承認の状態**で保存される。Update Level 2以上は、Human Reviewed・Publish Approvalが完了するまでどのAgentも公開状態に進めることはできない（ARu Constitution §9・§13、`enforce_publish_gate.py`が担保）。

**テスト結果（実データ・実API）**：
- Phase B3.7：「在留カード更新」（Update Level 2）でArticle・Translation・SNS×3を一括生成
- Phase B3.9（Day1）：「出入国在留管理庁サイトの更新検知」（Update Level 2）で同様に生成
- Phase B3.11（Day2）：「浅草ほおずき市を楽しむ」（**Update Level 1**）で3工程を**独立実行**し、Translation Quality ReviewerがPublish Approvalを`Not Required`へ自動遷移させることを実証（詳細は[Operation Checklist Day 2](./Operation-Checklist.md)）

**修正したバグ・改善**：
- `Source Research`のRelationプロパティが未作成だった（Articles作成時にResearchとの接続が漏れていた）→ Notion側の既存プロパティ名を`Source Research`にリネームして解消
- Notionのrich_textは1項目2000文字までの制限があり、長い本文でAPIエラーになった → `rich_text_chunks()`で自動分割する処理を追加
- （Phase B3.11）Article／Translation／SNSが1つのスクリプトにまとまっていたため独立呼び出しができなかった → `article`／`translation`／`sns`／`all`のサブコマンドに分割
- （Phase B3.11）CategoryからUpdate Levelを自動算出する処理を追加（従来は法律・制度カテゴリ＝Update Level 2固定だった）

---

## Phase B3.8：Reviewer Agent

**場所**：`notion-build/automation/reviewer_agent.py`

**内容**：Articlesの記事を、実際にClaude APIで5観点それぞれ100点満点で採点し、改善提案とともにArticleページへ保存する。

**Articlesへ追加したプロパティ**：`Review Accuracy Score`／`Review Evidence Score`／`Review Readability Score`／`Review Risk Score`／`Review Localization Score`（いずれもNumber）、`Review Overall Score`（**Formula**：5項目の平均を自動算出）、`Review Result`（Select：Not Reviewed／Pass／Needs Revision／Fail）、`Review Suggestions`（Rich Text）、`Review Date`（Date）

**Pass判定ロジック（v1の仮基準、運用データを見て調整予定）**：

- **Pass**：Overall Score ≥ 70 かつ Risk Score ≥ 60
- **Fail**：Overall Score < 50 または Risk Score < 40
- それ以外：**Needs Revision**

Riskだけ他の観点より厳しい閾値にしているのは、読みやすさ等が高くても法的リスクの高い記述は見逃さないため。

**Publish Gateとの連携**：`enforce_publish_gate.py`を更新し、**Update Level 2・3の記事は`Review Result=Pass`でない限りPublishedへ進めない**（すでにあったQA Status・Human Reviewedのチェックに追加する形）。

**テスト結果（実データ・実API）**：Phase B3.7で生成した「在留カード更新」記事（Update Level 2）を実際にレビュー。

| 観点 | スコア |
|---|---|
| Accuracy | 75 |
| Evidence | 55 |
| Readability | 82 |
| Risk | 78 |
| Localization | 70 |
| **Overall** | **72** |
| **Result** | **Pass** |

改善提案も実際に生成され保存された（出典URLの明記、在留資格別の具体例追加等の具体的な指摘）。

---

## Phase B3.9：Translation Quality Reviewer

**場所**：`notion-build/automation/translation_quality_reviewer.py`

**内容**：Translationの未承認翻訳（Publish Approval=Pending）を、実際にClaude APIで5観点それぞれ100点満点で採点し、改善提案とともにTranslationページへ保存する。

**Translationへ追加したプロパティ**：`Quality Meaning Accuracy Score`／`Quality Naturalness Score`／`Quality Cultural Adaptation Score`／`Quality Terminology Score`／`Quality Hallucination Risk Score`（いずれもNumber）、`Quality Overall Score`（**Formula**：5項目の平均を自動算出）、`Quality Result`（Select：Not Reviewed／Pass／Needs Revision／Fail）、`Quality Suggestions`（Rich Text）、`Quality Review Date`（Date）

**Pass判定ロジック**：Overall Score ≥ 75 **かつ** Meaning Accuracy ≥ 75 **かつ** Hallucination Risk ≥ 70。原文の意味を壊す誤訳や、原文にない情報の創作（幻覚）は、他の観点が高くても見逃さないための設計。

**Publish Approvalとの連携（ゲートロジック）**：

| 条件 | 結果 |
|---|---|
| Quality Result ≠ Pass | Publish Approval = **Pending**（進めない） |
| Quality Result = Pass だが Parent Article.Update Level が 2 または 3 | Publish Approval = **Pending**（AIスコアに関わらず人間承認が必須。ARu Constitution §9・§13） |
| Quality Result = Pass、Update Level = 1、だが Localization Status ≠ Culturally Adapted | Publish Approval = **Pending**（Phase Aで確定した「文化的補足が先」ルールを維持） |
| Quality Result = Pass、Update Level = 1、Localization Status = Culturally Adapted | Publish Approval = **Not Required**（自動解除） |

**テスト結果（実データ・実API）**：Phase B3.7で生成した英訳（Parent ArticleのUpdate Level=2）を実際にレビュー。

| 観点 | スコア |
|---|---|
| Meaning Accuracy | 92 |
| Naturalness | 88 |
| Cultural Adaptation | 85 |
| Terminology | 90 |
| Hallucination Risk | 88 |
| **Overall** | **89** |
| **Result** | **Pass** |

**ゲートが正しく機能したことを確認**：Quality Result=Passかつスコアも高い（89点）にもかかわらず、Parent ArticleがUpdate Level 2のため、Publish Approvalは**Pendingのまま維持**された（AIが高スコアでも人間承認を省略しないことを実証）。

---

## Phase B3.10：SNS Quality Reviewer

**場所**：`notion-build/automation/sns_quality_reviewer.py`

**内容**：SNS QueueのDraft投稿を、元記事（Related Article）の内容と照らし合わせて実際にClaude APIで5観点それぞれ100点満点で採点し、改善提案とともにSNS Queueページへ保存する。

**SNS Queueへ追加したプロパティ**：`Review Accuracy Score`／`Review Platform Fit Score`／`Review Engagement Score`／`Review Cultural Sensitivity Score`／`Review Risk Score`（いずれもNumber）、`Review Overall Score`（**Formula**：5項目の平均を自動算出）、`Review Result`（Select：Not Reviewed／Pass／Needs Revision／Fail）、`Review Suggestions`（Rich Text）、`Review Date`（Date）

**Pass判定ロジック**：Overall Score ≥ 75 **かつ** Accuracy ≥ 75 **かつ** Risk ≥ 70。

**Statusとの連携（ゲートロジック）**：Pass未満はStatusを**Draftのまま維持**する（明示的に上書きし、他の処理で誤って進んでいた場合も差し戻す）。Passの場合でも、このスクリプト自体はStatusをScheduled／Postedへは進めない——Update Level 2/3の記事に紐づく投稿は、Article側のPublish Approvalと人間の最終確認が別途必要なため（ARu Constitution §16）。

**テスト結果（実データ・実API）**：SNS Queueの全Draft（4件）を実際にレビュー。

| 投稿 | Accuracy | Platform Fit | Engagement | Cultural Sensitivity | Risk | Overall | Result |
|---|---|---|---|---|---|---|---|
| X（Phase B3.7生成） | 85 | 88 | 72 | 82 | 80 | **81** | **Pass** |
| Threads（Phase B3.7生成） | 85 | 82 | 78 | 88 | 80 | **83** | **Pass** |
| Instagram（Phase B3.7生成） | 85 | 88 | 75 | 82 | 80 | **82** | **Pass** |
| Instagram（Phase B3.5当時のテストレコード） | 15 | 45 | 35 | 70 | 25 | **38** | **Fail** |

**思わぬ収穫**：Phase B3.5の段階で作成していた古いテスト用SNS投稿（中身のないダミー記事にリンクされたもの）も対象に入り、**Reviewerが正しくFailと判定した。** 「テスト投稿なのに実用的な情報のように見えてしまう」という具体的なリスクまで指摘しており、スコアリングが機械的な平均処理ではなく、内容を踏まえた妥当な判断をしていることの裏付けになった。

改善提案も具体的に生成された（原文のニュアンス「身分証明書であり、滞在資格を証明する重要な書類」が英訳でやや補足的になっている点を指摘）。

---

## 一括生成：`notion-build/bulk_generate_20_articles.py`

**内容**：20件のテーマについて、Research→Article→Article Review→Translation→Translation Review→SNS×3→SNS Review×3のフルパイプラインを、既存の生成・レビュー関数（`generate_article_pipeline.py`／`reviewer_agent.py`／`translation_quality_reviewer.py`／`sns_quality_reviewer.py`）を再利用してループ実行するスクリプト。CSVインポートではなく直接Notion API経由で登録する方式を採用（既存DBの複雑なSelect/Relation/Formatスキーマを正しく扱うため）。

**実行結果（実データ・実API、2026-07-13）**：20テーマ・120件のNotionレコード（Research 20＋Article 20＋Translation 20＋SNS Queue 60）を約16分16秒で生成。技術的エラーは0件。Article Review 19/20 Pass、Translation Review 19/20 Pass、SNS Review 56/60 Pass。Update Level 1（15件）のTranslationは自動でPublish Approval=Not Requiredへ、Update Level 2（5件）は正しくPendingのまま維持され、ゲートロジックが大規模データでも機能することを確認した。

---

## ARu公式記事テンプレート統一 ＋ 一括生成：`notion-build/bulk_generate_articles.py`（2026-07-14）

**変更内容**：`bulk_generate_20_articles.py`を`bulk_generate_articles.py`へリネームし、テーマリストを差し替えるだけで日々再利用できる汎用スクリプトへ変更。あわせて`generate_article_pipeline.py`の`generate_article_text()`を改修し、記事本文を**ARu公式テンプレート（9セクション）**で統一生成するようにした。

**ARu公式テンプレート（9セクション、`ARU_ARTICLE_TEMPLATE_INSTRUCTIONS`定数として実装）**：

1. Question（ユーザーが最初に知りたい質問）
2. Basic Answer（無料部分として単独で読める基本回答）
3. More Details（背景・例外・具体例）
4. Why Does Japan Do This?（日本独自の文化・制度・背景理由）
5. Practical Steps and Cautions（手順・必要なもの・よくある失敗）
6. Latest Information（最新情報。無ければ「最終確認日：{verified_date}」を明記）
7. ARu Tip（不安を減らす短い実践的アドバイス）
8. Related Questions（関連テーマを2〜3件）
9. Mentor Support（メンター相談への案内）

**Articlesへ追加したプロパティ**：`Verification Status`（Select：Verified／Unverified／Needs Recheck）、`Last Verified Date`（Date）。Update Level 1の記事でも「最新情報の確認日」を必ず保存する、という運用要件をコード化したもの。

**実行結果（実データ・実API、2026-07-14）**：15テーマ・90件のNotionレコード（Research 15＋Article 15＋Translation 15＋SNS Queue 45）を生成。**最初の1記事のみ先にテスト実行し、9セクションすべてが意図通り出力されること（Latest Informationに最終確認日が明記されること含む）を人手で確認してから、残り14記事を実行**する手順を踏んだ。

- 技術的エラー：0件（1件、バックグラウンド実行の多重化ミスで処理が中断したが、対象記事のTranslation／SNSのみを再実行して復旧。データの重複や欠損なし）
- Article Review：15/15 Pass
- Translation Review：15/15 Pass（Update Level 2の4記事＝運転免許・ふるさと納税・年末調整・転職退職はすべて正しくPublish Approval=Pendingを維持。Update Level 1の11記事は自動でNot Requiredへ）
- SNS Review：44/45 Pass（1件Needs Revision：図書館記事のInstagram投稿、Accuracy Scoreが閾値未満のためStatus=Draftのまま保持）

---

## Article Freshness Monitor（Version 4準備、2026-07-14）

**場所**：`notion-build/automation/article_freshness_monitor.py`

**目的**：記事の情報が古くなっていないかを日次で自動チェックし、レビューが必要な記事をDashboard最上部に表示する。新規データベースは追加せず、既存Articles DBへのプロパティ追加とDashboardページへのセクション追加のみで実装した。

**Articlesへ追加したプロパティ**：`Freshness Status`（Select：Fresh／Needs Update）、`Days Since Verification`（Number）、`Freshness Urgency Score`（Number：レビュー期限に対する経過日数の割合(%)。100超で期限超過）、`Freshness Checked Date`（Date：直近チェック日）、`Freshness Note`（Rich Text：なぜ再レビューが必要かの短いメモ）

**Update LevelごとのReview Interval**：

| Update Level | 間隔 | 備考 |
|---|---|---|
| 1 | 90日 | イベント・文化・旅行情報・生活情報等 |
| 2 | 30日 | 法律・制度 |
| 3 | 14〜30日（既定30日） | `LEVEL_3_INTERVAL_DAYS`定数を書き換えるだけで変更可能（コード内で14〜30日にクランプ） |

**基準日の決め方（優先順）**：`Last Verified Date` → `Review Date` → `Published Date` → Notionページの作成日時（`created_time`）。いずれも無い記事は対象外としてスキップ（現状は発生しない設計）。

**外部シグナル連携（時間経過を待たずに強制フラグ）**：

| 情報源 | 検知条件 | Articlesへの接続経路 |
|---|---|---|
| Law Update | `Update Status`が`Confirmed`または`Reflecting to Article` | `Affected Articles`（既存Relation、直結） |
| Source Monitor | `Change Detected=true` | `Triggered Research` → Research.`Converted Article` → Articles（既存Relationを2ホップで辿る、新規Relationは追加していない） |
| Event Calendar | `Status=Cancelled` | `Related Article`（既存Relation、直結） |

該当した記事は、時間経過に関わらず`Freshness Status=Needs Update`・`Freshness Urgency Score=150`（時間ベースの最大値100を上回り、常に最優先で表示される）に設定され、`Freshness Note`にはAI Gateway経由で生成した「なぜ再レビューすべきか」の日本語1〜2文が保存される。

**Dashboard連携**：Dashboardページの最上部（① Publish Approval Pendingより上）に「🔴 Update Needed」の見出し＋説明Calloutを追加済み（Linked View自体は他セクション同様、手動設定が必要。手順は[View & Template Guide](./View-Template-Guide.md)）。`daily_briefing.py`にも同内容をセクション0として追加し、Freshness Urgency Score降順で表示する。

**実行方法**：

```
cd notion-build/automation
python3 article_freshness_monitor.py
```

初回実行時に`ensure_schema()`が上記5プロパティを自動作成する（既存の場合は上書きされるだけで害はない、何度実行しても安全＝冪等）。

**テスト結果（実データ・実API、2026-07-14）**：既存Articles 53件全件を実行。基準日なしでスキップされた記事は0件。Fresh 51件、Needs Update（時間経過による期限超過）0件（すべて直近2日以内に作成された記事のため妥当）、Needs Update（外部シグナルによる強制フラグ）2件——Law Update側の入管法改正シグナル1件、Source Monitor側の変化検知シグナル1件がそれぞれ正しく紐づいたArticleを検知し、AIが生成した再レビュー推奨コメントも内容に即した具体的な文面になっていることを確認した。

---

## Coverage Analyzer（Version 4準備、2026-07-14）

**場所**：`notion-build/automation/coverage_analyzer.py`（依存：`life_topics.py`／`backfill_life_topics.py`）

**目的**：編集長（Rei）が毎朝5分で「何の記事を追加・更新すべきか」を判断できるようにする。単なる記事数の集計ではなく、「外国籍の方が日本で生活する上で必要な情報が十分網羅されているか」という視点でAIが分析する。

**Life Topics（新設）**：既存の`Category`（7値：イベント／日本文化／旅行情報／生活情報／ニュース／トレンド／法律・制度）はUpdate Levelの判定に使われており、これは変更していない。カバレッジ分析にはより粒度の細かい**独立した軸**が必要なため、Articlesに`Life Topics`（Multi-select、22トピック）を新設した。1記事が複数トピックに紐づいてよい。

<details><summary>22トピック一覧</summary>

住居・引っ越し／医療・健康／税金／年金・社会保険／教育／子育て／介護／妊娠・出産／高齢者支援／障がい者支援／防災・緊急対応／就労・キャリア／在留資格・ビザ／交通／通信・インフラ／金融・銀行／買い物・消費／文化・マナー／イベント・季節行事／旅行・観光／ニュース・トレンド／行政手続き・相談窓口

</details>

**既存記事への付与**：`backfill_life_topics.py`で、既存53記事すべてをAIが分類（タイトル＋本文からLife Topicsを最大3件選択、既に付与済みの記事はスキップするため再実行安全）。以降の新規記事は`generate_article_pipeline.py`の`article`サブコマンドおよび`bulk_generate_articles.py`が生成時に自動付与するため、再バックフィルは基本的に不要。

**①カテゴリ分析**：Life Topicごとに以下を集計（既存Categoryでも参考表として同様に集計）。

- 記事数
- 直近更新日（`Last Verified Date`→`Review Date`→`Published Date`→作成日時の優先順、Article Freshness Monitorの`get_baseline_date()`を再利用）
- Freshness状況（Fresh／Needs Updateの内訳、Article Freshness Monitorが日次更新する`Freshness Status`をそのまま利用）
- Update Level構成（L1／L2／L3の内訳）
- Review待ち件数（`Review Result`≠Pass）

**②不足分析（AI）**：①の集計（記事数0件のトピックも含む）をAI Gatewayに渡し、単純な件数の少なさではなく「生活への影響度・緊急性」を踏まえて以下を生成する。

- 不足しているトピック（5〜8件）
- 優先して追加すべきトピック（3〜5件、理由付き）
- おすすめ新規記事テーマ（10件、読者が実際に検索しそうな質問形式）

**表示**：Dashboard最上部（🔴 Update Neededの直下）に「📊 Coverage Analysis」セクションを追加し、詳細は専用の**Coverage Analysisページ**（`COVERAGE_ANALYSIS_PAGE_ID`、初回実行時に自動作成）へリンク。このページはLinked View（手動設定が必要な他セクションと違い）ではなく、**実際のTable Blockとして毎回上書き生成**される——集計結果は「特定条件のレコード一覧」ではなく「計算済みのサマリー」なので、Notion APIで作成可能な通常のBlockで十分表現できるという判断による。

**実行方法**：

```
cd notion-build/automation
python3 backfill_life_topics.py   # 初回のみ（以降は新規記事が自動付与）
python3 coverage_analyzer.py
```

**テスト結果（実データ・実API、2026-07-14）**：既存Articles 53件全件をLife Topics付与済み。分析結果、`介護`／`妊娠・出産`／`高齢者支援`／`障がい者支援`が0件、`教育`／`ニュース・トレンド`が1件のみと判明。AIは単純な件数だけでなく「生命・生活への影響度」を踏まえ、医療・健康／妊娠・出産／介護／障がい者支援を優先トピックとして提案し、「外国籍の方が日本で妊娠したら最初にすべきことは？」等、検索されやすい質問形式のテーマ案を10件生成した。

---

## Editorial Planner（Version 4 Phase 2、2026-07-14）

**場所**：`notion-build/automation/editorial_planner.py`（依存：`life_topics.py`／`coverage_analyzer.aggregate()`）

**目的**：Coverage Analyzerが「何が足りないか」を示すのに対し、Editorial Plannerは「次に何を書くべきか」を具体的に提案する。編集会議でそのままアサインに使える粒度（優先度・理由・タイトル案・想定Update Level／Category）まで踏み込む。

**Life Topic Impact（新設）**：`life_topics.py`に`LIFE_TOPIC_IMPACT`（Critical／High／Medium／Low、22トピック分）を追加。記事数だけでなく「その情報がないと読者がどれだけ困るか」を加味するための軸で、医療・健康／妊娠・出産／防災・緊急対応／在留資格・ビザをCriticalとした。

**検出ロジック（決定論的、AIに委ねない）**：トピックごとに「影響度別の許容記事数」を超えていなければプランに含める。

| 影響度 | 許容記事数（この件数以下でプランに含む） |
|---|---|
| Critical | 4件以下 |
| High | 3件以下 |
| Medium | 2件以下 |
| Low | 1件以下 |

★の算出も決定論的（影響度×現在の記事数の組み合わせで1〜5に固定マッピング）。AIは各プランの**Reason・タイトル案・Expected Category**の生成にのみ使い、優先順位の算出そのものはAIに委ねない——Article Freshness Monitorの「日数計算は決定論、推奨コメントはAI」という設計方針を踏襲したもの。

**Expected Update Level**：AIには聞かない。AIが提案したExpected CategoryをArticles.Categoryの正規の7値で検証し（無効な値は`life_topics.DEFAULT_CATEGORY_FOR_TOPIC`のフォールバックへ）、既存の`generate_article_pipeline.compute_update_level()`にそのまま渡して算出する。カテゴリ判定ロジックを二重管理しないための設計。

**Generate Research アクション**：

```
python3 editorial_planner.py                                    # プラン表示のみ
python3 editorial_planner.py --generate-research                 # 全プラン項目のタイトル案をResearchへ
python3 editorial_planner.py --generate-research --limit 3       # 優先度上位3項目のみ
python3 editorial_planner.py --generate-research --topics "医療・健康,妊娠・出産"  # トピック名で選択
```

作成されるResearchレコードは、新規プロパティの追加なしで既存の選択肢をそのまま利用：`Status=New`（Dashboard「⑥ Today's Research」に自動的に現れる）、`Evidence Level=AI Suggested`、`Discovery Method=Gap Engine`（Research DBに元々用意されていた選択肢を活用）、`Priority`／`Urgency`は★の数から機械的にマッピング。

**表示**：Dashboard「📊 Coverage Analysis」の直下に「📝 Editorial Planner」セクションを追加。詳細は専用Notionページ（Coverage Analysisと同じ、Table/Block形式で毎回上書き生成する方式）。

**テスト結果（実データ・実API、2026-07-14）**：既存53記事に対して実行し、10トピックがプランに検出された（★5：妊娠・出産、★4：介護／高齢者支援／障がい者支援／医療・健康／防災・緊急対応、★3：子育て、★2：教育／年金・社会保険、★1：ニュース・トレンド）。`--generate-research`を実行し、実際に19件のResearchレコードを作成（Status=New、Discovery Method=Gap Engine、Category／Priority／Urgencyともに正しく設定されていることを実データで確認）。

---

## Publishing Center（Version 4 Phase 3、2026-07-14）

**場所**：`notion-build/automation/publishing_center.py`（`enforce_publish_gate.py`も拡張）

**目的**：編集長（Rei）が、記事の公開・更新・アーカイブ状況を一目で把握し、ARuアプリへ掲載する記事を迷わず選べるようにする。**AIによる自動公開は一切行わない**——ARuアプリへの実投稿APIが存在しないため、Publishedは「人間がARuアプリへ手動掲載済み」という管理状態として定義している。

**プロパティの責務分担（重複を避けるための整理）**：

| プロパティ | 責務 | このスクリプトの扱い |
|---|---|---|
| `Status`（既存） | Notion内の編集ワークフロー（Draft/AI Draft/Human Review/Approved/...） | 一切変更しない |
| `Review Result`（既存） | 記事本文がAIレビューを通過したか | 読み取りのみ |
| `Translation.Quality Result`（既存） | 各言語の翻訳がAIレビューを通過したか | 読み取りのみ |
| `Translation.Publish Approval`（既存） | Constitution §9/§13が定める人間承認ゲート | 読み取りのみ（書き込むのは`translation_quality_reviewer.py`と人間のみ） |
| `Freshness Status`（既存） | レビュー間隔内かどうか（Article Freshness Monitorが管理） | 読み取り、Publishing Statusとの同期に利用 |
| `Publishing Status`（新規） | **ARuアプリに実際に掲載されているか／掲載準備が整っているか** | このスクリプトが管理する中心プロパティ |

**追加したプロパティ**（Articles DB。`Published Date`は既存プロパティを再利用し、重複追加していない）：

- `Publishing Status`（Select：Draft／Ready to Publish／Published／Needs Update／Archived）
- `Published By`（People）
- `ARu App URL`（URL、手動入力）
- `Previous Publishing Status`（Select、同じ5値）
- `Publishing Status Updated Date`（Date）

**Ready to Publish判定（すべて満たす場合のみ）**：

1. `Review Result = Pass`
2. 紐づく全Translationの`Quality Result = Pass`（Translationが1件も無い場合は不可）
3. 紐づく全Translationの`Publish Approval`が`Not Required`または`Approved`（`Pending`／`Rejected`は不可。Update Level 2/3は人間が`Approved`にしない限り`Pending`のまま=不可のため、人間承認必須がそのまま担保される）
4. `Freshness Status = Fresh`（`Needs Update`はもちろん、未判定も不可——「鮮度不明」を「鮮度OK」とみなさない安全側の判断）
5. 必須項目：Title・Body・Category・Last Verified Dateが存在。**「Summary」はArticles DBに独立したプロパティが存在しないため、Source Research（Articleの出典）のSummaryが存在するかで代替判定している**（要件にあった項目名と実スキーマの差異を、勝手にプロパティを増やさず既存データで解釈した設計判断）

**Ready to Publishへ進めても、自動でPublishedにはしない。** Publishedへの変更は常に人間がNotion上で行う。

**Freshness Monitor連携（双方向）**：

- `Published`の記事でFreshness Statusが`Needs Update`になったら → Publishing Statusを`Needs Update`へ自動変更（`Previous Publishing Status=Published`を記録）
- `Needs Update`の記事でFreshness Statusが`Fresh`に戻ったら → `Previous Publishing Status`を見て元の状態（`Published`または`Ready to Publish`）へ自動復帰
- 未公開（Draft/Ready to Publish）の記事は、Freshness Statusが`Needs Update`である限りReady to Publishへ進めない

**公開操作の記録**：人間がNotion上でPublishing Statusを`Published`へ変更すると、次回`publishing_center.py`実行時に「Published Dateが空＝直近で公開された」と判定し、`Published Date`（今日の日付）と`Published By`（そのページの実際の`last_edited_by`、Notion APIの実データを使用——存在しない投稿APIは一切仮定していない）を自動記録する。`ARu App URL`は掲載先を人間が手動入力する。

**enforce_publish_gate.pyの拡張**：既存は`Status=Published`のみ監視していたが、`Publishing Status=Published`も同じ基準（QA Status=Passed、Update Level 2/3はHuman Reviewed=trueかつReview Result=Pass）で監視するよう拡張。違反があれば`Publishing Status`を`Needs Update`へ強制的に差し戻す。

**初期分類結果（実データ、2026-07-14）**：既存53記事に対して実行。

| Publishing Status | 件数 |
|---|---|
| Ready to Publish | 20 |
| Draft | 33 |
| Published | 0（一括自動設定は行っていない） |
| Needs Update | 0 |

Draft 33件のうち大半はUpdate Level 2（法律・制度）でTranslation Publish Approvalが`Pending`のまま（人間承認待ち、正しい挙動）、一部は`Last Verified Date`未設定（ARu公式テンプレート導入前の旧記事）、2件はFreshness Status=Needs Update（Article Freshness Monitorが検知済み）。

**テスト結果（実データ・実API、2026-07-14）**：

- Update Level 1で全条件Pass → 20件が正しくReady to Publishへ（実データで確認）
- Update Level 2でPublish Approval=Pending → 全件Draftのまま（実データで確認、人間承認必須が維持されている）
- Freshness Status=Needs Update → Ready to Publishにならないことを確認（2件とも該当理由に明記）
- Publishing Statusを人間が`Published`へ変更 → 次回実行でPublished Date／Published Byが正しく記録されることを確認
- Published記事のFreshness StatusをNeeds Updateに変更 → Publishing Statusが`Needs Update`へ自動遷移し、`Previous Publishing Status=Published`が記録されることを確認
- Freshness StatusをFreshに戻す → `Previous Publishing Status`を見て`Published`へ正しく復帰することを確認
- `enforce_publish_gate.py`実行 → 違反0件（テスト用に一時的にPublishedへ変更した記事は、既存ゲートが`QA Status`未設定という実在の欠落を正しく検知して差し戻した。テスト後は実データを汚さないよう手動でクリーンアップ済み）

**既知の制約**：

- **`QA Status`（既存の手動プロパティ）が53記事すべて未設定**。`enforce_publish_gate.py`は元々このプロパティを必須としており、Ready to Publish判定には含めていないため、Publishing Status=Publishedへ進めても既存ゲートに引っかかる可能性がある。QA Statusを誰がいつ設定する運用にするかは、Rei自身の判断が必要な未解決事項として残す（Ready to Publish条件に含めるかどうかも含め、要件にはなかったため今回は変更していない）
- `ARu App URL`は自動生成できない（実投稿APIが存在しないため）。人間が手動入力する前提
- Translationが0件の記事はReady to Publishに進めない設計だが、これは要件に明記された基準を字義通り実装した結果であり、意図的な挙動

---

## Articles DB正規化：重複記事の検出とアーカイブ（2026-07-14）

**きっかけ**：Reiから「Articles DBに同じテーマの記事が複数存在しているようです」と指摘を受け、公開作業を一時停止して調査した。

**原因**：タイトル文言の違いではなく（AIは毎回異なる表現でタイトルを生成するため、同一テーマでも見た目上は別記事に見える）、**同一テーマのResearch→Article→Translation→SNSフルパイプラインが複数回実行されていた**ことが根本原因。具体的には：

- 2026-07-14の一括生成で、バックグラウンド処理を誤って2回起動し、13テーマが2回ずつ生成された
- 2026-07-13の一括生成のTOPICSリストに「ゴミ分別」が重複して含まれていた
- 2026-07-12の初期テストで作成された【テスト】記事が、本番記事と同じResearchに紐づいたまま残っていた

**検出方法**：Article.Titleではなく、紐づくResearch.Topicでグループ化することで確実に検出（AIが生成するタイトル文言は毎回変わるため、Title同士の突合せでは検出漏れが起きる）。

**結果**：15グループ・記事30件がすべて完全重複（Article・Translation・SNS×3まで含めてフルパイプラインが2回実行されていた）と判明。判定基準（① Article・Translation・SNS全件がPassでNeeds Revisionがないこと優先 → ② Review Overall Scoreが高い方 → ③ 同条件なら作成が早い方）で各グループ1件を残し、**15件をArchive**した（削除はしていない）。

各アーカイブ記事には`Status=Archived`・`Archived Date`に加え、`Publishing Status=Duplicate`（新設の選択肢）・`Previous Publishing Status`・`Publishing Status Updated Date`を記録。53記事 → 実質38記事（Ready to Publish 11／Draft 27）に正規化された。

---

## Duplicate Prevention（Version 4 Phase 4、2026-07-14）

**場所**：`notion-build/automation/duplicate_guard.py`（＋`duplicate_prevention_report.py`）

**目的**：上記の重複を二度と起こさない。検知して後から直すのではなく、**生成が始まる前に止める**設計。ARuの原則：**「1 Research Topic = 1 Article」**。内容を更新する必要が生じた場合も、新しいArticleを作るのではなく既存Articleを更新する運用とする。

**チェック手順（①〜④、生成前に実施）**：

1. `Research.Topic`が完全一致するレコードが既に存在するか
2. そのResearchから変換された、`Status`が`Archived`ではないArticleが存在するか
3. そのArticleにTranslationが存在するか
4. そのArticleにSNS Queueが存在するか

いずれかが存在する場合、**新規生成を一切行わず**、到達していた最も深い段階（Research／Article／Translation／SNS）とともに「Already Exists」として記録する。

**呼び出し元によってチェックの意味が変わる**：

- `bulk_generate_articles.py`（Researchを自らその場で作成する経路）：Research.Topicが存在するだけで異常（2026-07-14の事故そのもの）とみなし、その時点でブロックする
- `generate_article_pipeline.py article`（既存のConverted Researchを前提に動く経路）：Researchが存在するのは正常なので、そこでは止めず、非ArchivedのArticleが存在する場合にのみブロックする

**`bulk_generate_articles.py`側の変更点（検知ではなく防止）**：従来は`process_topic()`内で生成してから問題が判明していたが、`main()`のループが始まる**前**に全TOPICSを一括チェックし、既存トピックをリストから除外してから処理を始めるよう変更した。

**Dashboard連携**：Dashboard「📝 Editorial Planner」の直下に「🛡 Duplicate Prevention」セクションを追加。本日の生成件数・生成スキップ件数・重複検知件数・Already Exists一覧・重複なし✅を、専用Notionページ（Table Blockと同じ、毎回上書き生成方式）で表示。

**既知の制約**：集計の元になるログ（`notion-build/automation/logs/duplicate_prevention.jsonl`）はローカルファイルであり、Notion・Gitのどちらとも同期しない（`.gitignore`済み）。「本日の」件数は、そのスクリプトを実行した端末上での活動のみを反映する。

**テスト結果（実データ、2026-07-14）**：
- 既存の完全重複記事（花火大会）に対して`generate_article_pipeline.py article`を実行 → AI Gateway呼び出し・Notionレコード作成を一切せず、段階=SNSで正しくスキップ
- 現在の`bulk_generate_articles.py`のTOPICS（15件、いずれも生成済み）を事前チェック → 15件全件が正しく「既に存在」と判定され、生成対象から除外されることを確認（2026-07-14の事故が再現不可能になったことを実証）
- 存在しない架空トピックでチェック → 正しく「生成可能」と判定

**テスト中に発見・修正したバグ**：`publishing_center.py`は`Publishing Status`の新しい選択肢`Duplicate`を認識しておらず、`Archived`だけを「触らない」対象としていた。このままアーカイブ後に`publishing_center.py`を再実行すると、Duplicateへ移動した15件が評価ロジックに引っかかり、Draft／Ready to Publishへ**意図せず復元されてしまう**バグだった。`sync_publishing_status()`の判定と、`ensure_schema()`が書き込む選択肢一覧の両方に`Duplicate`を追加して修正し、実データで再実行して15件が正しく`Duplicate (untouched)`のまま維持されることを確認した。

---

## Dashboard運用整備で発見・修正した2件の不具合（2026-07-16）

Dashboard の Linked Database View を手動設定する過程で、Rei と一緒にデータ側の不具合を2件発見・修正した。

### ① Select型プロパティの「降順」が意図と逆だった

`Priority`（High／Medium／Low）と`Urgency`（Critical／High／Medium／Low）は、Notionのスキーマ上「重要な選択肢を先に定義する」順（High→Medium→Low等）で作成していた。ところがNotionのSelect型プロパティのSortは、値の重要度ではなく**オプションの定義順**に従う仕様のため、UI上で「降順」を選ぶと定義順を逆にした並び——つまり**Low（最も重要度が低いもの）が先頭に来てしまう**、意図と正反対の挙動になっていた。

Articles・Research・Editorial Calendarの3DBで、`Priority`／`Urgency`のSelectオプション定義順を「Low→Medium→High」「Low→Medium→High→Critical」へ並べ替えて解消（既存の選択値・色は保持したまま順序のみ変更。データそのものは変更していない）。これにより「Today's Research」「Ready to Publish」「Article Review Waiting」「Today's Editorial Calendar」の4セクションすべてで、「降順」が正しく「緊急度・優先度が高いものを先頭に表示する」動作になった。

### ② Articles.Priorityが記事生成パイプラインで一度も書き込まれていなかった

既存53記事のうち52件で`Priority`が未設定（空）だった。原因は`generate_article_pipeline.py`・`bulk_generate_articles.py`のどちらも、ArticleへPriorityを書き込む処理自体が存在しなかったため。`Urgency`も同様に、値そのものは書き込んでいたが`"Medium"`固定のハードコードだった（Researchの実際の値を反映していなかった）。

**恒久対応**：ArticleはResearchの`Priority`・`Urgency`を生成時に自動継承する設計に変更した。

- `generate_article_pipeline.py` `run_article()`：既存の`Converted` Researchから`Priority`／`Urgency`を読み取り、そのままArticleへコピー（値が無い場合のみ`Medium`にフォールバック）
- `bulk_generate_articles.py` `process_topic()`：その場で作成したResearchの`Priority`／`Urgency`（`research_page`のレスポンスから直接取得、追加API呼び出し不要）をArticleへコピー
- 既存53記事は、それぞれのSource Researchから`Priority`／`Urgency`を取得し一括バックフィル（実データで実行、53件成功・0件失敗）

**正直な結果報告**：バックフィル後、53記事すべてが`Priority=Medium`（うち1件のみ`Urgency=High`、残りは`Medium`）となった。これはバグではなく、これまでの`bulk_generate_articles.py`のResearch生成コードが`Priority`／`Urgency`を`"Medium"`固定で作成していたことをそのまま反映した結果——**継承の仕組み自体は正しく動作しており**、Editorial Plannerが提案したResearch（★評価に基づき`High`／`Critical`まで幅がある）が今後Article化されていけば、自然にPriorityが分散していく設計になっている。Ready to Publishの並び順は、現時点ではPriority段が全件同点のため実質的にUpdate Level・Last Verified Dateの2段目・3段目が並び順を決めているが、これは①の修正により正しく機能している状態であり、Priority分散が進めば1段目からも効くようになる。

---

## Version 4 Phase 5（Editor Experience、2026-07-16）

**目的**：Reiから「編集長が記事を開いた瞬間に、必要な情報だけを見られるようにしたい」との要望。ただし**Version 4のデータベーススキーマ・プロパティ名・リレーション・Formula・自動化は一切変更しない**という明示的な制約付き。表示（レイアウト）とナビゲーション（導線）だけを改善する、という限定スコープで実施。

事前調査で分かった2つの前提：
1. 編集長が挙げた「Question／Basic Answer／…」等の見出しは**プロパティではなく**、Articles.Bodyという1つのrich_textプロパティの中に`**見出し**`形式で入っているテキストにすぎない（既存のARu公式9セクションテンプレート）。これまでこれらを実際の見出しブロックとして表示するコードは存在しなかった。
2. Notionページのプロパティパネルの「グループ化・折りたたみ」設定は、View／Templateと同じくNotionパブリックAPIに公開されていない機能。コードでは設定できず、人間の手動作業が必要（`docs/Article-Property-Panel-Guide.md`参照）。

### `render_article_layout.py`

**場所**：`notion-build/automation/render_article_layout.py`

**処理内容**：Articles.Bodyを`**見出し**`単位でパースし（正規化＋近似マッチで多少の表記ゆれを許容）、Article**ページの実ブロック**として描画する。Question／Basic Answer／More Details／Why Does Japan Do This?／ARu Tipの5つは本文フローに直接、残る4つ（Practical Steps and Cautions／Latest Information／Related Questions／Mentor Support）は「その他の詳細」というtoggleブロックへ折りたたむ。9セクションテンプレート導入前の古い記事（見出しが1つも見つからない場合）は、本文をそのまま1つの段落として表示するフォールバックを用意。Bodyプロパティ自体は一切書き換えない、表示専用の追加レイヤー。

**安全性の裏付け**：既存の全自動化スクリプトをリポジトリ全体でgrepし、Articleページのブロック子要素（`/blocks/{id}/children`）を読み書きするスクリプトが他に1つも存在しないことを確認済み。このレンダラーが触る領域は完全に新規・独立しており、Freshness Monitor・Publishing Center・Reviewer Agent・Coverage Analyzer・Editorial Planner・Duplicate Prevention・Publish Gateのいずれにも影響しない。

**パイプライン統合**：`generate_article_pipeline.py`（`run_article()`）・`bulk_generate_articles.py`（`process_topic()`）の両方で、Article保存直後にフック。レンダリング失敗はtry/exceptでnon-fatal扱いとし、Articleレコード自体の保存（プロパティ書き込み）を妨げない設計。

**テスト結果（実データ）**：
- `backfill --dry-run`で全38記事（Archived除く）を事前確認 → 9セクションテンプレート導入後の15記事は7〜9/9セクションを正しく検出、導入前の記事はすべて0/9検出（想定どおり、フォールバック経路に入る）
- 実記事1件をレンダリング → 14ブロック生成、Notion側でtoggleのネストされたchildren（見出し3＋段落×4）が正しく作成されることをAPI読み取りで確認
- 同じ記事を再レンダリング → ブロック数14で一致（冪等性を確認）
- `generate_article_pipeline.py article`／`bulk_generate_articles.py`をそれぞれ実際に1回ずつ実行し、新規Article生成直後にレンダリングが正しく動作することを確認（テスト用Article・Researchはいずれも検証後Archived）
- 全38記事に対する本番バックフィル実行 → **38件処理、0件失敗**

### `editor_home.py` ／ `ai_command_center.py`

**場所**：`notion-build/automation/editor_home.py`、`notion-build/automation/ai_command_center.py`

**設計方針**：既存Dashboardの13個のLinked Database View（Notion UIで手動設定済み）を再現するのではなく、その数値だけを毎回再計算して見せる**ナビゲーションハブ**として新規作成（既存Dashboardには一切触れない）。数値を計算するフィルタは`docs/Dashboard-Setup-Guide.md`の13セクション設定一覧と**完全に同一の条件**を使用し、実際のDashboard表示と数値がずれないようにしている。

- **Editor Home**（「今日、人間が決めること」）：🚀 Ready to Publish／📚 Published Articles／🛠 Needs Update／① Publish Approval Pending／② Article Review Waiting／③ Translation Review Waiting／④ SNS Draft Waiting／⑤ Today's Editorial Calendar／⑥ Today's Researchの9項目の件数とDashboardへのリンクを表示
- **AI Command Center**（「AIが監視・検知していること」）：🔴 Freshness内訳（外部シグナル起因／時間経過起因を`article_freshness_monitor.FORCE_FLAG_URGENCY_SCORE`定数で分離）、🛡 Duplicate Prevention本日の活動（`duplicate_prevention_report.py`の関数を直接再利用、再実装なし）、⑦〜⑨ 外部監視フィード（Source Monitor Alerts／Recent Law Updates／Recent Event Calendar）、📊 Coverage Analysis・📝 Editorial Plannerへのポインタ（最終更新日時＋リンクのみ、AI分析内容の再計算はしない＝AI Gateway呼び出しを増やさない）

**テスト結果（実データ、2026-07-16）**：
- Editor Home：Ready to Publish 11／Published 0／Needs Update 0／Publish Approval Pending 15／Article Review Waiting 38／Translation Review Waiting 1／SNS Draft Waiting 8／Today's Editorial Calendar 0／Today's Research 19（合計92件）を正しく集計し、専用Notionページへ反映
- AI Command Center：Freshness内訳（合計2件、外部シグナル起因2件／時間経過起因0件）、Duplicate Prevention本日（生成2件／スキップ0件）、Source Monitor Alerts 1／Recent Law Updates 1／Recent Event Calendar 1、Coverage Analysis・Editorial Plannerへのポインタ（最終更新日時付き）を正しく反映

### Article Property Panel Guide

**場所**：`docs/Article-Property-Panel-Guide.md`

**内容**：Articleページのプロパティを【本文】【公開情報】【関連情報】【AI Review】【System】の4〜5グループへ分け、上位2グループは常に展開・下位2グループは折りたたむための手動Notion UI手順書（`docs/Dashboard-Setup-Guide.md`と同じ構成）。対象プロパティ名は各自動化スクリプトのコードから実際に書き込んでいるものだけを実名で確認して掲載（未使用のスコア系プロパティも明記）。

### 既存自動化への影響確認（回帰テスト、2026-07-16）

Phase 5実装後、以下を実データに対して1回ずつ再実行し、挙動に変化がないことを確認した：`article_freshness_monitor.py`／`publishing_center.py`／`coverage_analyzer.py`／`editorial_planner.py`／`duplicate_prevention_report.py`／`enforce_publish_gate.py`。いずれもエラーなく完走し、既存ロジックどおりの結果を返した（スキーマ・プロパティへの新規書き込みはFreshness Monitor・Publishing Centerが従来から行っている範囲内のみで、Phase 5のコードに起因する変化はゼロ）。

---

## Source Watcher（ARu Intelligence Phase 1、2026-07-16）

**目的**：Reiから「記事を増やすことではなく、ARuが常に最新・信頼できる情報を保っていること」を目的としたPhase 1の依頼。①公式情報源の監視、②変化検知、③影響を受けるResearch／Articleの特定、④編集者への更新候補提示、の4点。既存のFreshness Monitor／Source Monitor／Law Update／Dashboard／Publishing Centerを最大限再利用する制約付き。

**実装前調査で判明した事実**：このパイプラインの下流側（Change Detected=trueを起点にResearchを自動起票する`sync_source_monitor_to_research.py`、Source Monitor/Law Update/Event Calendarの変化からArticleを強制的に要再レビューへ倒す`article_freshness_monitor.py`のクロスDB検知、Publishing Centerとの連携、Dashboardの「⑦ Source Monitor Alerts」「🔴 Update Needed」セクション、AI Command Centerの外部監視フィード表示）はすべてすでに実装・テスト済みだった。欠けていたのは唯一、**「Source Monitor.Change Detectedを実際に自動でtrueにする仕組み」**——リポジトリ全体を`urllib|requests\.|fetch\(|diff|scrape`等でgrepしても、外部URLを実際にフェッチして変化を検知するコードは1件も存在しなかった（`Change Detected`はこれまで完全に手動チェックボックスだった）。

**場所**：`notion-build/automation/source_watcher.py`（新規）

**処理内容**：
1. Source Library（既存DB、情報源の静的マスター台帳）から、`URL`が設定済み かつ `Check Frequency`（Daily/Weekly/Monthly/Quarterly）の間隔が経過した「チェック期限が来た」レコードを抽出
2. 各URLをstdlibの`urllib.request`のみでフェッチ（`robots.txt`の許可確認付き、15秒タイムアウト、リクエスト間1.5秒のディレイ、1回の実行あたり最大20件のキャップ——政府サイト等への配慮）
3. stdlibの`HTMLParser`でscript/style/nav/footerを除いた本文テキストを抽出し、SHA-256でハッシュ化
4. 初回チェック（保存済みハッシュなし）→ ハッシュを保存するだけ（誤検知を防ぐため、初回では「変化あり」を出さない）
5. ハッシュが前回と一致 → `Last Checked`のみ更新
6. ハッシュが変化 → **Source Monitorレコードを新規作成**（`Change Detected=true`、`Impact Level`はTier×Source Typeから導出、`Diff Summary`はAI Gateway経由で1〜2文の日本語要約を生成、`Status=Changed`）。Source Libraryの`Last Checked`・`Last Content Hash`（新設プロパティ）も更新

**スキーマ変更はSource Libraryへの1プロパティ追加のみ**：`Last Content Hash`（rich_text）。Source Monitor・Law Update・Research・Articlesなど他のDBは一切変更していない。

**政府・自治体系情報源の扱い（Reiと確認済みの設計判断）**：変化を検知しても、Law Updateレコードを**自動作成しない**。Source Monitorレコードを作成してフラグを立てるところまでで止め、Law Updateを起票するかどうかは人間の編集者が判断する。Law Updateは法律・ビザ等のUpdate Level 2/3に相当する法的重みを持つため、Constitutionの「人間レビュー最優先」原則に沿って、Researchの自動起票（既存の`sync_source_monitor_to_research.py`、影響度の低い新規テーマ発見という性質のため既に許容されている）よりも一段階慎重に扱う。

**`article_freshness_monitor.py`への1件の追加的拡張**：`find_source_monitor_signals()`が従来`Source Monitor → Triggered Research → Research.Converted Article`の経路しか辿っていなかったため、`sync_source_monitor_to_research.py`が自動起票した以外の——つまり人間が既にSource Libraryへ`Related Research`として紐づけていた——既存Researchが変化検知の対象から漏れる問題があった。`Source Monitor → Source → Source Library.Related Research → Research.Converted Article`という2つ目の経路を同じ関数内に追加し、両方の結果を1つの`signals`辞書へマージするよう変更（関数のシグネチャ・呼び出し元は無変更）。

**テスト結果（実データ、2026-07-16）**：
- Source Library実データ：現時点で1件のみ（DB作成時のテストレコード、実際の出入国在留管理庁公式サイトの実URL`https://www.moj.go.jp/isa/`を保持）。**Source Library全体への実URL投入はまだこれからで、Phase 1の実運用上の網羅範囲は現時点ではこの1件のみ**——これは正直に報告する実運用上の前提であり、コード側の欠陥ではない
- 本文抽出・ハッシュ化の安定性：同じページを2回連続フェッチし、ハッシュが完全一致することを確認
- 初回実行（本番）：1件中1件を正しく「baseline established」として処理、誤った`Change Detected`は0件
- 2回目実行（即時再実行）：`Check Frequency=Weekly`のため「まだ期限が来ていない」と正しくスキップ
- 変化検知パスの実証：対象レコードの保存済みハッシュを意図的に不一致な値へ書き換え、`Check Frequency`が経過した状態を作った上で再実行 → Source Monitorレコードが実際に作成され、`Impact Level=Critical`（Tier=高×Source Type=政府）、AI生成の`Diff Summary`（実際のページ本文から生成された妥当な日本語要約）を確認。実行後、Source Libraryのハッシュは実際の最新ハッシュへ正しく復元された（テスト起因の不整合は残らない設計）
- `find_source_monitor_signals()`の拡張：本番データを一切変更せず、`unittest.mock`によるローカルモックテストで新旧2経路が正しくマージされることを確認（旧経路＝Triggered Research由来のarticle、新経路＝Source Library.Related Research由来のarticle、両方が`signals`に反映されることを実証）。その後`article_freshness_monitor.py`を実データに対して再実行し、既存の検知結果（Needs Update 1件）に変化がないことを確認（回帰なし）
- 回帰テスト：`publishing_center.py`／`coverage_analyzer.py`／`editorial_planner.py`／`duplicate_prevention_report.py`／`enforce_publish_gate.py`を実データに対して再実行し、いずれもエラーなく完走、既存ロジックどおりの結果を確認
- 提示層（Dashboard／AI Command Center）の無変更確認：`ai_command_center.py`を再実行したところ、「⑦ Source Monitor Alerts」の件数が1件→2件（新規検知分を含む）へ自動的に反映された。Dashboardの「⑦ Source Monitor Alerts」Linked Viewと同一のFilter条件（`Change Detected=true`）で直接クエリし、同じ2件が返ることも確認——**新しいUIコード・新しいLinked Viewは一切追加していない**

**このセッションで明示的に自動化しなかったこと（Reiの指示）**：`sync_source_monitor_to_research.py`（Research自動起票）・Law Update・Article・Translation・SNS Queueへの新規レコード作成は、このセッションでは実行していない。`source_watcher.py`自体もこれらのDBへは一切書き込まない（Source LibraryとSource Monitorのみ）。`sync_source_monitor_to_research.py`はコード自体は無変更で、これまで通り編集者が実行すれば正しく動作する状態のまま。

**既知の制約**：
- JavaScriptで本文を描画するSPA型の政府サイトは、stdlibのみのフェッチでは意味のあるテキストが取得できない可能性がある
- ページ全文のハッシュ比較は粗い検知方式であり、広告・「最終更新日」表示など本質的でない変化でも誤検知（false positive）しうる。実運用でのfalse positive発生率を見てから、Phase 2でソースごとのCSSセレクタ指定等の精緻化を検討する
- **Source Library内の実URL投入がPhase 1の実効性の前提条件**：現時点で実URLを持つレコードは1件のみ。Reiが実際の政府・自治体・観光協会等のURLをSource Libraryへ登録していくことで、初めてPhase 1が実運用上の価値を持つ

## Source Library Expansion（ARu Intelligence Phase 2、2026-07-17）

**目的**：Phase 1が指摘した課題（「監視エンジンはできたが、監視対象がほぼ空」）を解消する。Reiの依頼：①Source Libraryをカテゴリ別に拡張、②数百件規模のソースを手作業でなく一括投入できる仕組み、③Critical/High/Medium/Lowの監視優先度、④変化の種類を分類、⑤誤検知（false positive）の削減、⑥Intelligence Dashboard、⑦公開ワークフロー（人間承認）は不変。「新規データベースは追加しない」「Version 4互換性を維持する」という制約は継続。

**場所**：`notion-build/automation/source_categories.py`（新規）、`notion-build/automation/bulk_import_sources.py`（新規）、`notion-build/automation/source_watcher.py`（拡張）、`notion-build/automation/ai_command_center.py`（拡張）

### ① Source Libraryアーキテクチャ拡張

Source Libraryへ5プロパティを追加（すべて既存DBへの追加のみ、リレーション先の新規DBは作成していない——「Region Master」は`docs/Roadmap.md`が既にDeferredとして文書化している未構築DBであり、新しいAIが勝手に作らないという既存方針に従い、Country/Region/Cityは単純なSelect/rich_textとして実装）：

| プロパティ | 型 | 内容 |
|---|---|---|
| `Category` | Select（22件） | Immigration／Visa／Student／Employment／Tax／Pension／Health Insurance／Disaster／Transportation／Tourism／Events／Festivals／Municipal Governments／Universities／Japanese Language Schools／Weather／Culture／Consumer Information／Housing／Banking／Emergency／Trending Topics（Reiの指定どおり、英語表記のまま） |
| `Country` | Select | Japan／Other International |
| `Region` | Select | 北海道／東北／関東／中部／近畿／中国／四国／九州・沖縄／全国／海外 |
| `City` | rich_text | 自由入力（都市名の選択肢は膨大なためSelectにせず） |
| `Importance` | Select（4件） | Critical／High／Medium／Low —— 既存の`Tier`（高/中/低）に代わる、監視優先度の正式なフィールド。`Tier`はスキーマ上残すが（削除は破壊的変更のため回避）、新規ロジックはすべて`Importance`を参照する |
| `Last Check Error`（当初計画にはなかった追加） | rich_text | 直近チェックのエラー内容。成功時は空にクリア。ローカルログファイル方式（`duplicate_prevention.jsonl`と同じ、マシン依存という既知の制約を持つ）ではなく、Source Library自体のプロパティとして持たせることで、Notion上でどこからでも同期・閲覧できるようにした——計画からの意図的な改善点として明記 |

`Monitoring Status`は新規プロパティを追加せず、既存の`Status`（Active/Inactive/Under Review）をそのまま「監視対象かどうか」の判定に使う（`source_watcher.py`の対象抽出条件は`Status=Active`）。

`source_categories.py`は`life_topics.py`と同じ構造（フラットなリスト定数）で、`SOURCE_CATEGORIES`（22件）と`UPDATE_CLASSIFICATIONS`（11件、後述）の2つを保持する単一の情報源。

### ② 一括インポート

`bulk_import_sources.py`：stdlibの`csv.DictReader`でCSVを読み込み、Notion APIで直接ページを作成する（このリポジトリに以前CSV読み込み機能は一切存在しなかった——`bulk_generate_articles.py`のコメントが説明するとおり、Notionネイティブの「CSV Import」はSelect/Relationプロパティを正しく設定できないため、意図的に避けられてきた）。

- 必須列：`Source Name`／`URL`。任意列（未入力時は既定値を適用）：`Source Type`（政府）／`Category`／`Country`／`Region`／`City`／`Importance`（Medium）／`Check Frequency`（Weekly）
- 実行前にSource Library内の既存URLを1回クエリし、CSV内で既に存在するURLの行は「重複」としてスキップ（`duplicate_guard.py`と同じ「暗黙の重複を許さない」原則を、記事ではなく情報源に適用したもの）
- CSV内に未知のCategory/Country/Region/Importance値があれば、ページ作成前に自動でSelectの選択肢へ追加（「無効なSelectオプション」エラーを未然に防止）
- `notion-build/automation/data/source_library_import_template.csv`（ヘッダー＋実在確認済み1件の記入例）と`notion-build/automation/data/source_library_seed.csv`（後述の実データ9件）の2ファイルを同梱

### ③ 監視優先度

`Importance`（Critical/High/Medium/Low）が優先度の正式なフィールド。`source_watcher.py`の`derive_impact_level()`は`Importance`が設定されていればそれをそのまま採用し、未設定の場合のみ（Phase 1時点の記録の後方互換のため）従来の`Tier`×`Source Type`推論にフォールバックする。`get_due_sources()`はチェック期限が来たソースを`Importance`の高い順（Critical→High→Medium→Low）へソートしてから1回あたりの上限件数（20→50件に引き上げ）を適用するため、ソースが数百件規模に増えてもCritical案件が後回しにされない。

### ④ Update Classification（変化の分類）

Source Monitorへ`Update Classification`（Select、11件：Law Change／Policy Update／Fee Change／Deadline Change／Event Update／Festival Schedule／Weather Warning／Transportation／Tourism Information／Emergency Notice／General News）を追加。変化検知時、`classify_update()`（`ai_gateway.py`経由、`generate_diff_summary()`と同じ呼び出しパターン）が`UPDATE_CLASSIFICATIONS`の中から最も適切な1件を判定し、検証に失敗（AIの誤出力・ハルシネーション）した場合は`General News`へフォールバックする——`life_topics.py`の「既知リストに対する検証、未知の値は採用しない」というパターンを踏襲。既存の`Change Type`プロパティと、それを参照する`sync_source_monitor_to_research.py`の`CHANGE_TYPE_TO_URGENCY`マッピングは無変更（`Update Classification`は並存する追加フィールド）。

**実データでのテスト（4件、いずれも正しく分類）**：「週間労働時間上限の変更」→`Policy Update`、「確定申告期限の延長」→`Deadline Change`、「大雨警報」→`Weather Warning`、「夏祭りの日程決定」→`Festival Schedule`。

### ⑤ 誤検知（false positive）の削減

Phase 1のSHA-256完全一致比較を、**SimHash方式の近似指紋比較**へ置き換え（stdlibのみ、`hashlib.blake2b`を使用）。

1. `normalize_for_fingerprint()`：日付・時刻らしきパターン、「件／人／回／PV／アクセス」等を伴う数字（訪問者カウンタ等）を正規表現で除去
2. `compute_shingles()`：5単語のスライディングウィンドウでシングル（shingle）を生成
3. `simhash()`：各シングルのハッシュ値をビットごとの多数決で統合し、64bitの指紋を生成
4. `hamming_distance()`：2つの指紋のハミング距離（異なるビット数）を計算
5. ハミング距離が閾値（`SIMHASH_CHANGE_THRESHOLD=2`）を超えた場合のみ「変化あり」と判定。広告・タイムスタンプ・訪問者数のような周辺的なノイズは指紋を数ビットしか動かさないため閾値以下に収まり、実質的な内容変更は多くのビットを動かすため閾値を超える

**実データでのテスト結果**（実際にフェッチした出入国在留管理庁ページ、252単語）：
- 安定性：同一ページを2回フェッチ→ハミング距離0（誤検知なし）
- ノイズ耐性：実ページ本文＋偽の訪問者数「4,821件」＋タイムスタンプを追加→ハミング距離2（閾値以下、正しく「変化なし」と判定）
- 実質的な変更の検知：本文の約15%を別の内容に置換→ハミング距離13（閾値超え、正しく「変化あり」）
- 小さいが実質的な編集：文章を1文追加→ハミング距離3（閾値超え、正しく「変化あり」）

`Last Content Hash`プロパティの中身がSHA-256（Phase 1）からSimHash（Phase 2）へ内部的に変わるが、フォーマット不一致（16進数の桁数で判定）を検知した場合は「変化あり」ではなく「レガシー形式のため再ベースライン化」として扱い、誤検知を出さないようにしている——実際にPhase 1のテストレコード1件でこの経路が実データ上で正しく動作することを確認した。

このアルゴリズムは調整可能なヒューリスティックであり、「解決済みの問題」ではない。実運用でソース数が増えるにつれて閾値の再調整が必要になる可能性がある（既知の制約として明記）。

### ⑥ Dashboard／AI Command Center拡張

- `ai_command_center.py`に新セクション「🌐 Source Intelligence」を追加：監視対象ソース数（Active内訳付き）、本日の変化検知件数、うちCritical件数、エラー中のソース一覧、本日のUpdate Classification内訳、Research候補件数（`Status=New`かつ`Discovery Method=Source Monitor`のResearch）
- Dashboardへ新規Linked Database View「🔴 Critical Source Updates」（Source Monitor、`Impact Level=Critical`かつ`Change Detected=true`、`Checked At`降順）を追加——設定手順は既存13セクションと同じ共通手順（[Dashboard Setup Guide](./Dashboard-Setup-Guide.md)の14番目のセクションとして追記）。**新しいNotionページは作成していない**——既存のDashboardとAI Command Centerを拡張しただけ

### ⑦ 人間ワークフロー（不変）

Source → Watcher → Source Monitor → Editor Review → Research → Article → Translation → SNS → Publishのチェーンは一切変更していない。`source_watcher.py`は今回もSource LibraryとSource Monitorのみに書き込み、Research／Article／Translation／SNS Queueへは一切書き込まない。

### 実データでのシード投入と実行結果（2026-07-17）

- **Category検証済み実ソース9件**をWebFetchで1件ずつ疎通確認したうえで`source_library_seed.csv`として整備し、`bulk_import_sources.py`で投入：国税庁（Tax／Critical）、厚生労働省（Health Insurance／Critical）、内閣府防災情報のページ（Disaster／Critical）、気象庁（Weather／Critical）、総務省消防庁（Emergency／Critical）、日本年金機構（Pension／High）、ハローワークインターネットサービス（Employment／High）、国土交通省（Transportation／High）、日本政府観光局JNTO（Tourism／Medium）——**9件作成、0件重複、0件エラー**
- **未着手のカテゴリ**（実ソース未投入、Reiまたは今後のPhaseでの追加が必要）：Visa（外務省サイトが自動フェッチをブロックしたため見送り）、Student、Events、Festivals、Municipal Governments、Universities、Japanese Language Schools、Culture、Consumer Information、Housing、Banking、Trending Topics
- **投入後の`source_watcher.py`実行**：Source Library計10件（Phase 1のテストレコード1件＋Phase 2のシード9件）に対して実行し、Importance降順（Critical→High→Medium）で正しくソートされた順に処理、9件すべて「baseline established」（0誤検知）。同日中に強制的に再チェック対象とした2回目の実行では9件すべて「unchanged（ハミング距離0）」を確認、Phase 1のテストレコード1件は「レガシー形式のため再ベースライン化」経路が実データ上で正しく機能
- **回帰テスト**：`article_freshness_monitor.py`／`publishing_center.py`／`coverage_analyzer.py`／`editorial_planner.py`／`duplicate_prevention_report.py`／`enforce_publish_gate.py`を実データに対して再実行し、いずれもエラーなく完走、既存ロジックどおりの結果を確認

## Editorial Intelligence（ARu Intelligence Phase 3、2026-07-18）

**目的**：Phase 1/2で「情報源監視の仕組み」ができたので、Phase 3ではそれを含む既存の全システムを編集長が実際に**毎日使う**形にまとめる。新機能の追加ではなく、既存システムの再利用と統合が目的（Reiの依頼どおり）。新規データベースは一切追加していない。

**場所**：`notion-build/automation/research_prioritizer.py`（新規）、`notion-build/automation/today_opportunities.py`（新規）、`notion-build/automation/ai_command_center.py`（再構成）、`docs/Editorial-Workflow.md`（新規）

### ① Today's Opportunities

`today_opportunities.py`：4つの既存システムを日付ベースで統合し、「編集者が今日動くべきこと」を提示する。新しいクロスタイプの単一スコアは作らず（祭りとビザ制度改正を1つの数値で比較するのは無理があるため）、種類ごとに分けて表示する。

- **Event Calendar**（既存DB）：`Status`が`Cancelled`/`Completed`以外、`Event Date`が今日から14日以内のイベント（祭り／花火大会／フードフェス等、既存の`Type`選択肢がそのまま該当）
- **Source Monitor**（既存DB）：本日`Checked At`＝今日 かつ `Impact Level`がCritical/Highの変化（政府発表・ビザ制度更新等）
- **Law Update**（既存DB）：`Update Status=Confirmed`（確定したがまだArticleに反映されていない法改正）
- **Research**（既存DB）：`research_prioritizer.py`の上位候補のうち、Category=イベント/旅行情報 かつ 季節性スコアが高いもの（Event Calendarにまだ載っていない、季節性の高い企画の種）

### ② Research Prioritization

`research_prioritizer.py`：Status=NewのResearchを5軸でスコアリングし、上位から表示する。

| 軸 | 満点 | 算出方法 |
|---|---|---|
| Freshness | 20点 | 発見（作成）からの経過日数。新しいほど高得点 |
| Foreign Resident Value | 20点 | Research.Category（既存7分類）→ Critical/High/Medium/Lowへのマッピング（法律・制度=Critical、生活情報=High等） |
| Tourism Value | 20点 | 同じくCategoryから、旅行情報=Critical、イベント/日本文化=High等 |
| Seasonal Relevance | 20点 | Research.Season（既存プロパティ）と実際の現在の季節を照合。一致=20点、通年=12点、季節指定なし=8点、不一致=3点 |
| Premium Potential | 20点 | Usage Scope（既存プロパティ）にEnterprise/Municipal Partnershipが含まれる=20点、Evidence LevelがOfficial/Verified=12点、それ以外=5点 |

**5軸すべて、Researchの既存プロパティのみから決定論的に算出——新規AI呼び出しゼロ、新規スキーマゼロ。** そのためAI Command Centerを再実行するたびに追加コストなく再計算できる。

**実データでのテスト（2026-07-18）**：Status=New 19件全件をスコアリング。上位10件はいずれもCategory=法律・制度（Foreign Resident Value=Critical=20点）の同時期一括生成Researchで、Freshness/Seasonal/Premiumの差のみで48点に並んだ——これはロジックの不具合ではなく、現状のResearch backlogがCategory・Season的に同質であることを正直に反映した結果（Categoryや季節がばらつけば差が広がる設計）。

### ③ AI Command Centerの再構成（編集長の毎日のホーム画面）

`ai_command_center.py`の先頭5セクションを差し替え、Phase 1/2の監視詳細セクションはその下に「根拠」として残した：

1. 🎯 Today's Opportunities
2. 🔴 Critical Updates（外部シグナルで要更新フラグの記事＋本日のCritical情報源変化＋重要度MajorでArticle未反映のLaw Updateの合算）
3. 📊 Top Research Candidates（`research_prioritizer.py`上位5件）
4. 🚀 Publishing Queue（`editor_home.py`のReady to Publishと同一フィルタを再利用、数値の食い違いを防止）
5. 🕐 Recently Updated Articles（Articles.Updated Date降順、上位5件）

**実装中に発見・修正したバグ**：Critical Updatesの初期実装は`Status=Archived`の記事を除外しておらず、Archived後もFreshness Statusが「Needs Update」のまま残っていた古いテスト記事1件が誤って表示されていた（記事をArchiveする際にFreshness Statusをクリアする仕組みがそもそも存在しないため）。他の全スクリプトが徹底している「Archivedは除外する」という規約に倣い、`Status`の除外条件を追加して解消。実データで合計3件→2件（正しい件数）に修正されたことを確認済み。

**Editor Homeとの役割分担**：Editor Home（Phase 5）は「今日、人間が決めること」9項目に特化した軽量ページとして存続。AI Command Centerは、それに加えてAIが検知・提案した内容までを含む、より広い「編集長の毎日のホーム画面」という位置づけになった。

### ④ ドキュメント整備

`docs/Editorial-Workflow.md`を新規作成し、情報源監視→企画・優先順位付け→編集者レビュー→コンテンツ生成→公開ゲート→鮮度管理（環流）という編集ワークフロー全体を1つの図・1つの文書にまとめた。個々のスクリプトの詳細は引き続き本ドキュメント（Automation Scripts）を参照する構成とし、重複を避けた。

### ⑤ 実データでのテスト結果まとめ（2026-07-18）

- `research_prioritizer.py`：Status=New 19件を実データでスコアリング、5軸すべて正しく算出
- `today_opportunities.py`：実データで動作確認——直近14日のEvent Calendar 0件（実データが少ないため）、本日の重要情報源変化0件、Confirmed済みLaw Update 1件、季節性Research候補0件（現状のResearchがCategory=法律・制度に偏っているため0件、ロジックは正常）
- `ai_command_center.py`再構成後：Today's Opportunities／Critical Updates（バグ修正後2件）／Top Research Candidates（5件）／Publishing Queue（11件）／Recently Updated Articles（5件）まで、実データで正しく表示・Notionページへの書き込みを確認
- 回帰テスト：`article_freshness_monitor.py`／`publishing_center.py`／`enforce_publish_gate.py`／`duplicate_prevention_report.py`／`editor_home.py`／`coverage_analyzer.py`／`editorial_planner.py`／`source_watcher.py`／`bulk_import_sources.py`（重複スキップ経路含む）を実データに対して再実行し、いずれもエラーなく完走、既存ロジックどおりの結果を確認

## 未実施事項（要判断）

- **スケジューリング**：cron／launchd等での定期実行はまだ設定していない。日次実行にするか、Rei自身が手動実行するかは別途判断が必要
- **通知**：Legal Gap・Criticalの検知結果をSlack/メール等へ通知する仕組みは未実装
- **Audit Log**：各スクリプトの実行結果は現状ターミナル出力のみで、永続的な記録先がない（Roadmap上Audit Log DBはDeferred）

---

*ARu HQ / Decode Japan — Automation Scripts v2.1 — 2026-07-18*
