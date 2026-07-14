<title>Automation Scripts v1.4</title>

# Automation Scripts
### ARu Studio — Roadmap Version 3 実装記録 ＋ Version 4準備

| | |
|---|---|
| **Status** | Active — Notion自動化13スクリプト＋AI Gateway＋Article Freshness Monitor＋Coverage Analyzer＋Editorial Planner実装・実データ／実API（Claude）でテスト済み |
| **Date** | 2026-07-14 |
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
| `daily_briefing.py` | Editor-in-Chief | Dashboard（編集長ホーム画面）の9セクション相当をCLIに表示する、Linked View未設定時点でも使えるテキスト版ダッシュボード |
| `research_assistant.py` | Researcher | テーマを指定すると、Source Library／Law Update／既存Research／既存記事との重複をNotionから実データで検索し、Markdownのリサーチ資料を出力（Pilot Operation Day 1で使用） |
| `article_assistant.py` | Writer | テーマを指定すると、既存記事・Editorial Calendarとの重複確認、推奨Category/Update Level/Audienceを出力（Pilot Operation Day 1で使用） |
| `article_freshness_monitor.py` | Editor-in-Chief（Freshness Gate） | Update Levelごとのレビュー間隔超過、およびLaw Update/Source Monitor/Event Calendarの変化検知を基に、記事のFreshness Statusを日次更新しDashboard最上部の「🔴 Update Needed」に反映（Version 4準備、詳細後述） |
| `coverage_analyzer.py` | Editor-in-Chief（企画・編集会議） | 生活トピック別の記事数・鮮度・Review待ちを集計し、AIが不足トピック・優先トピック・おすすめ新規テーマ（10件）を提案。Dashboard「📊 Coverage Analysis」＋専用Notionページに反映（詳細後述） |
| `backfill_life_topics.py` | — | 既存記事にLife Topicsを一括付与する再実行可能なバックフィルスクリプト（Coverage Analyzerの前提データ作成用） |
| `editorial_planner.py` | Editor-in-Chief（編集会議・アサイン） | Coverage Analyzerの集計データから、★1〜5の優先度付き編集プラン（Reason・タイトル案・想定Update Level／Category）を生成し、`--generate-research`でResearchレコードを自動作成。Dashboard「📝 Editorial Planner」＋専用Notionページに反映（詳細後述） |

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

## 未実施事項（要判断）

- **スケジューリング**：cron／launchd等での定期実行はまだ設定していない。日次実行にするか、Rei自身が手動実行するかは別途判断が必要
- **通知**：Legal Gap・Criticalの検知結果をSlack/メール等へ通知する仕組みは未実装
- **Audit Log**：各スクリプトの実行結果は現状ターミナル出力のみで、永続的な記録先がない（Roadmap上Audit Log DBはDeferred）

---

*ARu HQ / Decode Japan — Automation Scripts v1.4 — 2026-07-14*
