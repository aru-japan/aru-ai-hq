# ARu AI HQ

ARu（外国籍の方が日本で安心して暮らし、旅行し、働けるようにサポートするAIプラットフォーム）の運営基盤リポジトリ。

## このリポジトリについて

ARu HQ（AI編集部）の運営思想・設計・実装を1つにまとめたもの。詳細は `docs/` を参照。

> **ChatGPT・Claude・Cursorなど、AIとしてこのリポジトリを引き継ぐ場合は、まず [AI Handover Document](docs/AI-Handover.md) を読むこと。**

## ドキュメント

| ドキュメント | 内容 |
|---|---|
| [AI Handover Document](docs/AI-Handover.md) | **将来のAI向け引き継ぎ文書。** このファイルだけで開発を継続できることを目的とする |
| [ARu Constitution](docs/ARu-Constitution.md) | 運営憲章。Mission/Vision/Core ValuesからGovernanceまで |
| [AI Agent Constitution](docs/AI-Agent-Constitution.md) | 各AIエージェントの責務・権限・禁止事項・エスカレーション条件 |
| [ER Design](docs/ER-Design.html) | データベースのER設計書（Relation/Rollup/Formula） |
| [Notion Builder Spec](docs/Notion-Builder-Spec.md) | Notion実装仕様（Database一覧、Universal Properties、Phase別設計） |
| [Roadmap](docs/Roadmap.md) | Version 1〜5の展開計画 |
| [Operating Manual](docs/Operating-Manual.md) | 編集長向け標準運用手順書（SOP） |
| [View & Template Guide](docs/View-Template-Guide.md) | Notion UI上でのView/Template手動設定手順 |
| [Dashboard Setup Guide](docs/Dashboard-Setup-Guide.md) | 編集長ホーム画面（Dashboard）の9セクションを、初めてのNotionユーザーでも30分で完成させる手順 |
| [AI Agent Architecture](docs/AI-Agent-Architecture.md) | AI Editorial Brain（6 Agent）の構造・利用DB・権限境界 |
| [AI Agent Workflow](docs/AI-Agent-Workflow.md) | 6 Agent間の処理手順・エスカレーション条件 |
| [AI Editorial Brain](docs/AI-Editorial-Brain.md) | Version 2.0の総括構想。AI編集部の全体像とガバナンス境界 |
| [Automation Scripts](docs/Automation-Scripts.md) | Version 3で実装した自動化スクリプト（Notion自動化＋AI Gateway＋Article/Translation/SNSの3段レビュー）の一覧と実行方法 |
| [Pilot Operation Guide](docs/Pilot-Operation-Guide.md) | Version 3.5：AI編集部を7日間実運用するための手順 |
| [Operation Checklist](docs/Operation-Checklist.md) | 7日間分の日次チェックリスト＋Operation Log記入欄 |

## 実装

- `notion-build/` — Notion APIを使ってARu Studioの各データベースを構築するPythonスクリプト一式。標準ライブラリのみで動作（`notion_api.py`が最小限のAPIクライアント）。
- `notion-build/automation/` — 既存10DBに対する自動化スクリプト（Translator/Researcher/Editor-in-Chiefの各AgentロジックをPythonで実装）。詳細は[Automation Scripts](docs/Automation-Scripts.md)。
- `scripts/ai_gateway.py` — Claude API／OpenAI APIのどちらでも呼び出せる共通AIゲートウェイ（標準ライブラリのみ）。詳細は[Automation Scripts](docs/Automation-Scripts.md)の「AI Gateway」節。

セットアップは `notion-build/.env.example` を `.env` にコピーし、`NOTION_TOKEN` と `ARU_STUDIO_PAGE_ID` を設定して実行する。AI Gatewayを使う場合は同じ`.env`に`CLAUDE_API_KEY`または`OPENAI_API_KEY`を追加する。

## 現在地

Roadmap Version 1・2・3は完了（一部Deferred）。Version 3.5（Pilot Operation：7日間実運用）Day 2まで完了。Update Level 1の自動公開経路（Publish Approval→Not Required）を実証済み。記事本文はARu公式テンプレート（9セクション構成）に統一し、`bulk_generate_articles.py`で日々の一括生成に対応（2026-07-14）。Version 4（Enterprise）はPilot完了後、別途方針確認のうえ着手する。詳細は [Roadmap](docs/Roadmap.md) を参照。
