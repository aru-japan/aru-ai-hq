<title>ARu Studio Roadmap v2</title>

# ARu Studio Roadmap
### Version 2

| | |
|---|---|
| **Status** | Active |
| **Date** | 2026-07-12 |
| **位置づけ** | ARu Constitution §19 Future Expansion Policyを、実際のバージョン計画に落とし込んだもの |

---

## 実装順序の最適化について（重要）

Version 2・3で新規に必要となる6DB（Language Master／Region Master／Mentor／AI Agents／Prompt Library／Automation）は、**目標から削除しない。実装順序のみを変更し、`Deferred（実装保留）`として扱う。**

方針：まず**新規DBを追加せず、既存10DB（Articles／Research／Translation／Source Library／Editorial Calendar／Experience Intelligence／Source Monitor／Law Update／Event Calendar／SNS Queue）を最大限活用したPython自動化**を完成させる。実運用でDeferred項目の必要性が実際に確認できた段階で、個別に再評価・実装する。

---

## Version 1 — Foundation（完成）

**目的**：編集部が実際に動ける最小構成を作る。

- ARu Constitution v2.0.0（運営憲章）
- AI Agent Constitution v1.1.0（AI各役割の責務・権限・禁止事項）
- ER Design ／ Notion Database Builder Spec（全17DB設計、Universal Properties確定）
- **実装済み5DB**：Articles／Research／Translation／Source Library／Editorial Calendar
- View（Daily／Weekly／Review／Archive）／Article・Research・Translation Template
- ARu Studio Operating Manual（日次・週次・月次・緊急対応・法改正対応の手順）

---

## Version 2 — AI Intelligence（完了。一部Deferred）

**目的**：ARuが「今何が起きているか」「何が足りないか」を自ら認識できるようにする。

**実装済み**

- **Experience Intelligence**（Knowledge Gap Engine／Opportunity Intelligence）
- Source Monitor（情報源の変化を検知するDB構造）
- Law Update／Event Calendar／SNS Queue
- Dashboard（ホーム画面ページ＋View手動設定ガイド）
- AI Editorial Brain設計（AI-Agent-Architecture／AI-Agent-Workflow／AI-Editorial-Brain）

**Deferred（実装保留）**

| DB | 理由 | 再評価のきっかけ |
|---|---|---|
| Language Master | 現状11言語をSelectで運用中、実害なし | 20言語以上への拡張時、または表記ゆれが実運用で問題化した時 |
| Region Master | 現状Locationを自由テキストで運用中 | 地域別ダッシュボード・自治体連携が実際に必要になった時 |
| Mentor | 現状、専門家レビューは都度手配（Operating Manual§7参照） | メンターの人数が増え、個別手配が非効率になった時 |

---

## Version 3 — AI Automation（完了：実装順序を変更）

**目的**：既存10DBを最大限活用し、Python自動化スクリプトで「知る」から「実行する」までを実現する。n8n専用のAutomation DBやAI Agents DBが無くても、実際に動く自動化を先に作る。

**実装方針の変更**

| 当初計画 | 変更後 |
|---|---|
| AI Agents／Prompt Library／Automation DBの本稼働 | **Deferred**。実体はPythonスクリプト（`notion-build/automation/`）として実装し、DB化は実運用で必要性が確認できてから |
| n8nによる自動化 | まずPythonスクリプトで同等のロジックを実装（将来n8nへ移植可能な設計） |
| Needs Re-Translationの自動検知 | Pythonスクリプトで実装済み（`check_translation_gaps.py`） |
| SNS自動投稿 | Draft自動生成まで実装済み（`generate_article_pipeline.py`、Phase B3.7）。実投稿は引き続き人間が最終確認 |
| Reviewer Agentの実装 | 実装済み（`reviewer_agent.py`、Phase B3.8）。5観点スコアリング＋Update Level 2/3のPublish Gate連携 |
| Audit Logの自動記録 | DB化はDeferred。当面はGitコミット履歴とスクリプトの実行ログで代替 |

**実装済み（[Automation Scripts](./Automation-Scripts.md)参照）**

- `check_translation_gaps.py`（Translator）
- `sync_source_monitor_to_research.py`（Researcher）
- `escalate_law_significance.py`（Editor-in-Chief）
- `sync_editorial_calendar_status.py`（Editor-in-Chief）
- `enforce_publish_gate.py`（Editor-in-Chief／Quality Gate、Constitution §9・§13のコード化）
- `daily_briefing.py`（Dashboard 8セクションのCLI版）

すべて実データに対してテスト済み。Mission「AIが調査・執筆・翻訳・SNSを担当し、人は最終確認だけを行う」の**技術的な骨格**を、新規DBなしで実現した。

**未実施**：定期実行のスケジューリング（cron等）、Legal Gap等の外部通知、SNS Queue自動Draft生成。

---

## Version 3.5 — Pilot Operation

**目的**：AI編集部（AI Editorial Brain＋既存10DB＋Automation Scripts）を、実際に**7日間運用**して検証する。設計・自動化が揃っただけでは「動く」とは言えない。実運用を経て初めてVersion 4（Enterprise）への準備が整ったと判断する。

**新規DBは追加しない。** 既存10DB・Automation Scripts・[AI Editorial Brain](./AI-Editorial-Brain.md)の設計をそのまま使う。

**日次で実施する6項目**（詳細は[Pilot Operation Guide](./Pilot-Operation-Guide.md)）

1. Morning Brief（`daily_briefing.py` ＋ Editorial Calendar Daily View）
2. Research（Source Monitor監視・`sync_source_monitor_to_research.py`）
3. Article（Writer相当の起筆）
4. Translation（`check_translation_gaps.py`による検知＋翻訳実施）
5. Review（5観点レビュー＋`enforce_publish_gate.py`によるゲート確認）
6. SNS Draft（現時点は手動。自動Draft生成スクリプトは未実装）

**Operation Log**：日々の気づき・改善点は、新規DBではなく[Operation Checklist](./Operation-Checklist.md)内に直接記録する（7日分のテンプレートを用意）。

**完了条件**：7日間分のOperation Checklistが記入され、最終日に振り返り（何が自動化できたか、何が依然手作業か、Version 4着手前に直すべき設計上の不備は何か）が行われること。

---

## Version 4 — Enterprise

**前提条件：Version 3.5 Pilot Operation（7日間の実運用）が完了していること。** 設計上動くはずのものが、実際の運用でも動くと確認できるまで、企業・自治体向けへは拡張しない。

**目的**：個人利用者向けサービスから、企業・自治体・日本語学校向けプラットフォームへ拡張する。

- Usage Scope（Enterprise／Municipal Partnership）を実運用で使い始める。Universal Propertiesの段階ですでに全Content Core DBに用意済み
- 自治体・観光協会・企業とのデータ連携（Source Libraryの「地域固有の魅力」情報源が公式パートナー契約に発展）
- JNTO／Visit Japanとの連携（Region Masterに既に用意済みのURL項目を実際のAPI連携へ）
- 企業向けダッシュボード（外国籍社員の受け入れ状況、生活支援コンテンツの利用状況等）
- Mentorネットワークの本格拡大（行政書士・医療関係者・企業担当者との正式契約）

このバージョンの技術的土台は、Version 1の段階で意図的に先回りして設計済み（Confidentiality／Usage Scopeの早期導入）。

---

## Version 5 — Global

**目的**：日本という単一国の枠を越え、ARuのモデル自体を輸出可能にする。

- Region Masterの「Country」階層を実際に複数国で使い始める
- 対応言語をLanguage Masterの拡張性を活かして20言語以上へ
- Timezoneフィールド（Version 1から予約済み）を実際の海外展開で使用開始
- 「Decode Japan」のフレームワークを、他国向け「Decode X」として再利用できる形に一般化
- ARu Constitution／AI Agent Constitutionの理念部分（Mission／Core Values）を、国をまたいでも通用する形に再検証（Level C改訂として扱う）

---

## 現在地

**Version 1・2・3は完了（一部Deferred）。Version 3.5（Pilot Operation：7日間の実運用）に着手する。Version 4（Enterprise）はPilot Operation完了後、かつ対外的な意思決定・契約行為を伴うため、着手前に別途方針確認が必要。**

---

*ARu HQ / Decode Japan — ARu Studio Roadmap v2 — 2026-07-12*
