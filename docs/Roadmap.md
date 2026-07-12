<title>ARu Studio Roadmap v1</title>

# ARu Studio Roadmap
### Version 1

| | |
|---|---|
| **Status** | Active |
| **Date** | 2026-07-12 |
| **位置づけ** | ARu Constitution §19 Future Expansion Policyを、実際のバージョン計画に落とし込んだもの |

---

## Version 1 — Foundation（完成）

**目的**：編集部が実際に動ける最小構成を作る。

- ARu Constitution v2.0.0（運営憲章）
- AI Agent Constitution v1.1.0（AI各役割の責務・権限・禁止事項）
- ER Design ／ Notion Database Builder Spec（全17DB設計、Universal Properties確定）
- **実装済み5DB**：Articles／Research／Translation／Source Library／Editorial Calendar
- View（Daily／Weekly／Review／Archive）／Article・Research・Translation Template
- ARu Studio Operating Manual（日次・週次・月次・緊急対応・法改正対応の手順）

この時点では、Gap検出・翻訳の再検知・情報源の変化監視などはすべて**Rei自身の手動運用**で回っている。

---

## Version 2 — AI Intelligence（次に着手）

**目的**：ARuが「今何が起きているか」「何が足りないか」を自ら認識できるようにする。

- **Experience Intelligence**（Knowledge Gap Engine／Opportunity Intelligence）
- Source Monitor（情報源の変化を自動検知）
- Law Update／Event Calendar／SNS Queue
- Language Master／Region Master（Knowledge Graphの言語軸・地域軸）
- Mentor（専門メンター台帳）
- Dashboard（Today's Opportunities／Knowledge Gaps／Critical Updates等の集約）

このバージョンの終わりには、「知る」ことは自動化されるが、「実行」はまだ人とAIの手作業が中心。

---

## Version 3 — AI Automation

**目的**：n8n・GitHub Actions・Claude Code／各種AI APIを接続し、「知る」から「実行する」までを自動化する。

- AI Agents／Prompt Library／Automation DBの本稼働（9つのAI Agentが実際にタスクを実行）
- n8n：Source変化検知→Research起票→Article下書き→Translation自動生成の一連を自動化
- Needs Re-Translationの自動検知・自動再翻訳トリガー
- SNS自動投稿（Update Level 2/3のPublish Approvalゲートを維持したまま）
- Audit Logの自動記録（Constitution §18）

このバージョンで、Mission「AIが調査・執筆・翻訳・SNSを担当し、人は最終確認だけを行う」体制が技術的に完成する。

---

## Version 4 — Enterprise

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

**Version 1は完了。Version 2（Experience Intelligence：Knowledge Gap Engine + Opportunity Intelligence）に着手する。**

---

*ARu HQ / Decode Japan — ARu Studio Roadmap v1 — 2026-07-12*
