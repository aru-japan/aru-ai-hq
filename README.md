# ARu AI HQ

ARu（外国籍の方が日本で安心して暮らし、旅行し、働けるようにサポートするAIプラットフォーム）の運営基盤リポジトリ。

## このリポジトリについて

ARu HQ（AI編集部）の運営思想・設計・実装を1つにまとめたもの。詳細は `docs/` を参照。

## ドキュメント

| ドキュメント | 内容 |
|---|---|
| [ARu Constitution](docs/ARu-Constitution.md) | 運営憲章。Mission/Vision/Core ValuesからGovernanceまで |
| [AI Agent Constitution](docs/AI-Agent-Constitution.md) | 各AIエージェントの責務・権限・禁止事項・エスカレーション条件 |
| [ER Design](docs/ER-Design.html) | データベースのER設計書（Relation/Rollup/Formula） |
| [Notion Builder Spec](docs/Notion-Builder-Spec.md) | Notion実装仕様（Database一覧、Universal Properties、Phase別設計） |
| [Roadmap](docs/Roadmap.md) | Version 1〜5の展開計画 |
| [Operating Manual](docs/Operating-Manual.md) | 編集長向け標準運用手順書（SOP） |
| [View & Template Guide](docs/View-Template-Guide.md) | Notion UI上でのView/Template手動設定手順 |

## 実装

`notion-build/` — Notion APIを使ってARu Studioの各データベースを構築するPythonスクリプト一式。標準ライブラリのみで動作（`notion_api.py`が最小限のAPIクライアント）。

セットアップは `notion-build/.env.example` を `.env` にコピーし、`NOTION_TOKEN` と `ARU_STUDIO_PAGE_ID` を設定して実行する。

## 現在地

Roadmap Version 2（AI Intelligence）進行中。詳細は [Roadmap](docs/Roadmap.md) を参照。
