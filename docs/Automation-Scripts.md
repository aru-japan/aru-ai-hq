<title>Automation Scripts v1.0</title>

# Automation Scripts
### ARu Studio — Roadmap Version 3 実装記録

| | |
|---|---|
| **Status** | Active — Notion自動化9スクリプト＋AI Gateway実装・実データ／実API（Claude）でテスト済み |
| **Date** | 2026-07-12 |
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

## 未実施事項（要判断）

- **スケジューリング**：cron／launchd等での定期実行はまだ設定していない。日次実行にするか、Rei自身が手動実行するかは別途判断が必要
- **通知**：Legal Gap・Criticalの検知結果をSlack/メール等へ通知する仕組みは未実装
- **Audit Log**：各スクリプトの実行結果は現状ターミナル出力のみで、永続的な記録先がない（Roadmap上Audit Log DBはDeferred）

---

*ARu HQ / Decode Japan — Automation Scripts v1.0 — 2026-07-12*
