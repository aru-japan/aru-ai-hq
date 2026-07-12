<title>Automation Scripts v1.0</title>

# Automation Scripts
### ARu Studio — Roadmap Version 3 実装記録

| | |
|---|---|
| **Status** | Active — 6スクリプト実装・実データでテスト済み |
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
| `daily_briefing.py` | — | Dashboardの8セクション相当をCLIに表示する、Linked View未設定時点でも使えるテキスト版ダッシュボード |
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
| daily_briefing.py | 8セクションすべてが実データ（Gap／Opportunity／Event等）を正しく表示 |
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

**現状の制約（正直な報告）**：CLAUDE_API_KEY・OPENAI_API_KEYはまだ`.env`に未設定のため、実際のAPI呼び出しはまだ検証できていない。エラーハンドリング（キー未設定時に分かりやすいエラーメッセージで終了すること）は確認済み：

```
$ python3 scripts/ai_gateway.py --input "..."
ERROR: Neither CLAUDE_API_KEY nor OPENAI_API_KEY is set in notion-build/.env. Add one of them to use the AI Gateway.
```

いずれかのキーが設定され次第、200文字要約の実動作を確認する。

## 未実施事項（要判断）

- **スケジューリング**：cron／launchd等での定期実行はまだ設定していない。日次実行にするか、Rei自身が手動実行するかは別途判断が必要
- **通知**：Legal Gap・Criticalの検知結果をSlack/メール等へ通知する仕組みは未実装
- **Audit Log**：各スクリプトの実行結果は現状ターミナル出力のみで、永続的な記録先がない（Roadmap上Audit Log DBはDeferred）

---

*ARu HQ / Decode Japan — Automation Scripts v1.0 — 2026-07-12*
