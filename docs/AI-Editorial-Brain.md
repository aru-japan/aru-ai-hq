<title>AI Editorial Brain v1.0</title>

# AI Editorial Brain
### ARu Studio — Roadmap Version 2.0 総括設計書

| | |
|---|---|
| **Status** | Draft — 設計のみ。Version 2.0の中核構想 |
| **Date** | 2026-07-12 |
| **関連文書** | [AI Agent Architecture](./AI-Agent-Architecture.md)（構造）／[AI Agent Workflow](./AI-Agent-Workflow.md)（手順）／[AI Agent Constitution](./AI-Agent-Constitution.md)（根拠となる権限規定） |

---

## 1. これは何か

AI Editorial Brainは、「ARu AI編集部」を実際に機能させるための頭脳部分である。ARu Constitutionが掲げるMission——

> AIが調査・執筆・翻訳・SNSを担当し、人は最終確認だけを行う

——を、6つのAgent（Editor-in-Chief／Researcher／Writer／Reviewer／Translator／Social Manager）として具体化したものであり、実装済みの10データベース（Articles〜SNS Queue）の上で動作する設計である。

新しいデータベースは追加しない。既存の10DBに対して、それぞれのAgentが定まった役割で読み書きする。

## 2. 6つのAgentが1つの頭脳として機能する

| Agent | 役割を一言で言うと |
|---|---|
| Editor-in-Chief | 何を優先し、何を公開してよいかを判断するゲート |
| Researcher | 世の中の変化（情報源・法改正・イベント）を拾い上げる感覚器 |
| Writer | 拾い上げた情報を記事という形に変換する |
| Reviewer | 5つの観点（文化・法律・情報精度・SEO・外国人目線）で品質を保証する |
| Translator | 日本語という単一言語の壁を越えさせる |
| Social Manager | 完成した記事を、世界に向けて発信する |

詳細な責務・利用DB・入出力は[AI Agent Architecture](./AI-Agent-Architecture.md)を、実際の処理順序は[AI Agent Workflow](./AI-Agent-Workflow.md)を参照。

## 3. 最も重要な原則：Editor-in-Chiefは人間の代わりではない

AI Editorial Brainの設計において、唯一絶対に譲れない一線がこれである。

- **Update Level 1**（イベント・観光・文化・季節記事等）：AI Editorial Brainだけで、調査から公開・翻訳・SNS配信まで完結してよい。
- **Update Level 2・3**（法律・ビザ・税金・医療・重要な法改正等）：AI Editorial Brainは、調査・執筆・レビュー・翻訳・配信の**準備**まではすべて行うが、**最終的にPublishedにする権限は人間（編集長Rei、または該当分野の専門家）にある。**

この一線は、ARu Constitution §9（AI Behavior Rules）・§13（Legal & Medical Rules）、AI Agent Constitution全体の禁止事項からそのまま継承したものであり、AI Editorial Brainの導入によって緩めるものではない。「AIが編集部として機能する」ことと、「AIが最終責任を持つ」ことは別である。

## 4. 現在地と、まだ動いていないもの

AI Editorial Brainは**現時点では設計のみ**であり、自律的には動いていない。

| 要素 | 現状 |
|---|---|
| 6 Agentの責務定義 | ✅ 完了（本ドキュメント群） |
| 10DBとの対応関係 | ✅ 完了 |
| Agent間のワークフロー | ✅ 完了 |
| AI Agents DBへの正式登録 | ⏳ 未着手（Phase B4/B5） |
| Prompt Libraryによるプロンプト管理 | ⏳ 未着手 |
| n8n等による自動実行 | ⏳ 未着手（Roadmap Version 3） |

それまでの間、[ARu Studio Operating Manual](./Operating-Manual.md)に定めた手順を、Rei自身がこの6 Agentの「代役」として手動で実行する。AI Editorial Brainは、その手動作業を将来自動化するときの設計図としてすでに機能している。

## 5. Version 3への橋渡し

Roadmap Version 3（AI Automation）に進む際、本ドキュメント群がそのまま実装仕様になる：

- AI Agent ArchitectureのAgent定義 → AI Agents DBのレコード
- AI Agent WorkflowのステップとSLA → Automation DBのワークフロー定義・n8nのトリガー条件
- 各Agentの入出力プロパティ → n8nノードが読み書きするNotionプロパティ

設計と実装の間に断絶がないよう、Version 3で実装する際は、本ドキュメントを変更履歴とともに更新し、実装との乖離を作らないこと。

---

*ARu HQ / Decode Japan — AI Editorial Brain v1.0 — 2026-07-12*
