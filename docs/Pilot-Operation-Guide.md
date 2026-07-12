<title>Pilot Operation Guide v1.0</title>

# Pilot Operation Guide
### ARu Studio — Roadmap Version 3.5

| | |
|---|---|
| **Status** | Active |
| **Date** | 2026-07-12 |
| **目的** | AI編集部（AI Editorial Brain＋既存10DB＋Automation Scripts）を7日間実運用し、Version 4（Enterprise）着手前に「設計通りに動くか」を検証する |
| **関連文書** | [Roadmap](./Roadmap.md)／[AI Editorial Brain](./AI-Editorial-Brain.md)／[Automation Scripts](./Automation-Scripts.md)／[Operating Manual](./Operating-Manual.md)／[Operation Checklist](./Operation-Checklist.md) |

---

## 1. なぜPilot Operationが必要か

Version 1〜3で、10のデータベース・6つのAI Agentの設計・6本の自動化スクリプトが揃った。しかしこれらは、これまでテストレコード1〜2件で疎通確認をしただけであり、**実際の記事を7日間動かした経験がまだない**。Version 4（Enterprise）で企業・自治体に提供する前に、実運用で初めて見える不備（手順の抜け、スクリプトの想定外挙動、レビューの負荷等）を洗い出す。

新規データベースは追加しない。既存10DBとAutomation Scriptsをそのまま使う。

## 2. 体制

- 実行者：Rei（編集長）。AI Editorial Brainの6 Agentのうち、自動化されていない部分（Writer・Reviewer・Social Managerの一部）はRei自身が代行する
- 期間：7日間（連続稼働。土日を挟んでも構わないが、間を空けない）
- 記録先：[Operation Checklist](./Operation-Checklist.md)（新規DBを作らず、このMarkdownファイルに直接記入する）

## 3. 日次ルーティン（6項目）

| # | 項目 | やること | 使うツール |
|---|---|---|---|
| 1 | **Morning Brief** | その日の状況を一望する | `python3 automation/daily_briefing.py` の出力を確認。あわせてEditorial CalendarのDaily Viewを開く |
| 2 | **Research** | Source Monitorを確認し、必要ならResearchを起票 | `python3 automation/sync_source_monitor_to_research.py` を実行後、生成されたResearchレコードを人が確認・加筆 |
| 3 | **Article** | Researchから記事を1本以上起筆する | Article Templateを使用。Status=Draft→AI Draftまで進める |
| 4 | **Translation** | 再翻訳が必要な記事を検知し、翻訳を進める | `python3 automation/check_translation_gaps.py` を実行し、Needs Re-Translation=trueのレコードを翻訳する |
| 5 | **Review** | 文化／法律／情報精度／SEO／外国人目線の5観点でレビューし、公開ゲートを確認する | Constitution第14章Quality Checklistを実施後、`python3 automation/enforce_publish_gate.py` を実行してゲート違反がないか確認 |
| 6 | **SNS Draft** | 公開した記事のSNS投稿文を用意する | **現時点では手動。** 自動Draft生成スクリプトは未実装のため、SNS Queueへ直接Draftレコードを作成する |

## 4. Operation Logの書き方

[Operation Checklist](./Operation-Checklist.md)の各日の欄に、以下の観点で気づいたことを記録する。

- **うまく自動化できたこと**：スクリプトが想定通りに動いた／時間が節約できた箇所
- **手作業でカバーした箇所**：本来自動化したいが、今は人手で埋めている部分
- **詰まったこと・エラー**：スクリプトが失敗した、Notion側の制約にぶつかった等
- **AI Editorial Brainとの乖離**：[AI-Agent-Workflow.md](./AI-Agent-Workflow.md)に書いた手順と、実際にやったことが違った場合、その違い

7日分たまったログは、Version 4着手前の設計見直し（または新規DB追加の要否判断）の材料になる。

## 5. 完了条件

- 7日分すべてのOperation Checklistが記入されていること
- 最終日（Day 7）に振り返りを行い、「Version 4 Enterprise Ready」の判定チェックリスト（Operation Checklist末尾）を満たしているか確認すること
- Pilot中に見つかった重大な改善点（新規DBが必要、既存設計の変更が必要等）があれば、Version 4着手前に個別に方針確認すること

---

*ARu HQ / Decode Japan — Pilot Operation Guide v1.0 — 2026-07-12*
