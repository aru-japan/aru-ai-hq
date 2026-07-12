<title>AI Agent Architecture v1.0</title>

# AI Agent Architecture
### ARu Studio — Roadmap Version 2.0 設計書

| | |
|---|---|
| **Status** | Draft — 設計のみ。Notion／Pythonへの実装はまだ行っていない |
| **Date** | 2026-07-12 |
| **位置づけ** | [AI Agent Constitution v1.1.0](./AI-Agent-Constitution.md)が定める9つのAIロール（責務・権限・禁止事項）を土台に、実際に10DB体制で動く**6つの運用エージェント（AI Editorial Brain）**として再編成したもの |
| **対象DB** | Articles／Research／Translation／Source Library／Editorial Calendar／Experience Intelligence／Source Monitor／Law Update／Event Calendar／SNS Queue（実装済み10DB。新規DB追加なし） |

---

## 1. なぜ9ロールを6エージェントに再編成するのか

[AI Agent Constitution v1.1.0](./AI-Agent-Constitution.md)は、Research／Writer／Translator／Localization／SEO／SNS／QC／Linking／Gap Analysisという **9つの粒度の細かいロール** を定義した。これは「何をしてはいけないか」を厳密に定めるための単位として適切だが、実際の日々の編集業務は、もっと大きな塊（「今日何を書くか決める」「書く」「翻訳する」等）で動く。

そこで、AI Editorial Brainでは、9ロールの**責務・権限・禁止事項はそのまま維持**しつつ、実務上の窓口として**6つのAgent**にまとめ直す。

**マッピング表**

| AI Editorial Brainの6 Agent | 対応するAI Agent Constitutionのロール | 備考 |
|---|---|---|
| ① Editor-in-Chief | （新設）＋ QC Agentの一部＋Gap Analysis Agentの一部＋Linking Agent | 人間の編集長（Rei）の代理ではない。詳細は第4章「ガバナンス境界」 |
| ② Researcher | Research Agent ＋ Gap Analysis Agentの検知機能の一部 | Source Monitor監視・Law Update反映・Event収集まで担当範囲を明示的に拡張 |
| ③ Writer | Writer Agent | 変更なし |
| ④ Reviewer | QC Agent ＋ SEO Agent ＋（新設：法律・外国人目線の観点） | 5つの審査観点（文化／法律／情報精度／SEO／外国人目線）を持つ複合レビュアーとして再定義 |
| ⑤ Translator | Translator Agent ＋ Localization Agent | 翻訳と文化的補足を1つのAgentに統合 |
| ⑥ Social Manager | SNS Agent | Editorial Calendarとの連携を明示的に追加 |

**引き継がれない機能はない。** 9ロールの禁止事項・エスカレーション条件は、対応する6 Agentのいずれかが責任を持って引き継ぐ。

---

## 2. 6つのAgent

### ① Editor-in-Chief

| 項目 | 内容 |
|---|---|
| **責務** | Priority決定（Articles／Research／Editorial CalendarのPriority・Urgencyを調整）、公開判断のゲート運用、Quality Gate（QA Status確認） |
| **利用DB** | Experience Intelligence／Editorial Calendar／Articles／SNS Queue |
| **主な入力** | Experience IntelligenceのGap／Opportunity（Status=New）、Editorial CalendarのDaily View |
| **主な出力** | Editorial Calendar・ArticlesのPriority／Urgency更新、QA Status確認、Editorial CalendarのStatus進行 |
| **権限境界** | 第4章を参照。**Update Level 2/3のPublish Approvalを単独で確定させることはできない** |

### ② Researcher

| 項目 | 内容 |
|---|---|
| **責務** | Source Monitorの監視、Research作成、Law Updateの内容確認・反映、Event情報の収集 |
| **利用DB** | Source Monitor／Research／Source Library／Law Update／Event Calendar |
| **主な入力** | Source Monitorの`Change Detected`／`Change Type`／`Impact Level` |
| **主な出力** | Researchレコードの新規作成（Evidence Level・Discovery Method設定）、Law Update.Update Statusの更新、Event Calendarの新規登録 |
| **権限境界** | Evidence LevelをOfficial／Verifiedへ自ら引き上げることはできない（AI Agent Constitution §2） |

### ③ Writer

| 項目 | 内容 |
|---|---|
| **責務** | ResearchからArticle Draftを生成する |
| **利用DB** | Research／Articles |
| **主な入力** | Research（Status=Converted）のSummary／Raw Notes |
| **主な出力** | Articles.Body（Status=AI Draft） |
| **権限境界** | StatusをHuman Review以降へ自ら進めることはできない（AI Agent Constitution §3） |

### ④ Reviewer

| 項目 | 内容 |
|---|---|
| **責務** | 5つの観点でレビューする：**文化**（Cultural Policy適合）、**法律**（Law Update整合性）、**情報精度**（出典・Trust Score）、**SEO**（Title/Slug最適化）、**外国人目線**（Audienceにとっての分かりやすさ・過不足） |
| **利用DB** | Articles／Experience Intelligence／Law Update |
| **主な入力** | Articles（Status=AI Draft）、関連するLaw Update.Impact Summary、Experience IntelligenceのTrust Score |
| **主な出力** | Articles.QA Status、レビューコメント（本文またはNotes相当） |
| **権限境界** | QA Status＝Failedの記事を、他のAgentが独断でPublishedへ進めることを止める側（AI Agent Constitution §8） |

### ⑤ Translator

| 項目 | 内容 |
|---|---|
| **責務** | 11言語（en/zh-CN/zh-TW/ko/vi/id/es/tl/ne/pt/th）への翻訳、Localization（文化的補足） |
| **利用DB** | Translation／Articles |
| **主な入力** | Articles（Status=Published、またはUpdated Date変化）、Translation.Needs Re-Translation |
| **主な出力** | Translation.Translated Title/Body、AI Translation Status、Localization Status |
| **権限境界** | Localization Status＝Culturally Adaptedに確信が持てない場合はNeeds Cultural Reviewを選ぶ（AI Agent Constitution §4/§5） |

### ⑥ Social Manager

| 項目 | 内容 |
|---|---|
| **責務** | SNS Queueレコードの生成（Caption／Hashtags／CTA）、投稿スケジュールの提案 |
| **利用DB** | SNS Queue／Editorial Calendar／Articles |
| **主な入力** | Articles（Status=Published）、Editorial Calendar.Content Goal／Campaign |
| **主な出力** | SNS Queue.Caption／Hashtags／CTA／Scheduled Date（Status=Draft） |
| **権限境界** | Update Level 2/3由来のコンテンツは、Publish Approval確定前にStatusをScheduled／Postedにできない（AI Agent Constitution §7） |

---

## 3. データフロー（テキスト図）

```
Source Monitor ──→ Researcher ──→ Research ──→ Writer ──→ Articles(AI Draft)
                                                              │
                            ┌─────────────────────────────────┘
                            ▼
                        Reviewer（5観点レビュー）
                            │
                    QA Status = Passed?
                     │              │
                    Yes             No → Writerへ差し戻し
                     ▼
              Editor-in-Chief（Quality Gate・公開判断）
                     │
        Update Level 1？───Yes──→ 自動でArticles.Status = Published
                     │No
                     ▼
        人間（Rei）の承認待ち → Published
                     │
                     ▼
              Translator（11言語・Localization）
                     │
                     ▼
              Social Manager（SNS Queue生成）
```

Experience Intelligence（Gap／Opportunity）とEditorial Calendarは、Editor-in-Chiefを通じてこのフロー全体に「次に何をすべきか」を供給する（Command Center機能）。

---

## 4. ガバナンス境界（最重要）

**Editor-in-Chief Agentは、人間の編集長（Rei）の代理ではない。** ARu Constitution §9・§10・§13、AI Agent Constitution全体の禁止事項は、Editor-in-Chiefにもそのまま適用される。

- **Update Level 1**：Editor-in-ChiefがQuality Gateを通過したと判断すれば、自動的にArticles.Statusを Published へ進めてよい（人間レビュー不要、既存ルール通り）。
- **Update Level 2・3**：Editor-in-Chiefの「公開判断」は、**公開の可否を人間（Rei、または該当分野の専門Mentor）に提示するための準備（Priority付け・Quality Gate通過確認・レビュー結果の要約）に限られる。** 実際にPublish Approval＝ApprovedにしてStatusをPublishedへ進める操作は、人間が行う。

この境界は、AI Agent ConstitutionにおけるLevel C相当の変更（AI Behavior Rulesの根幹）に触れる可能性があるため、本設計書の内容を正式にAI Agent Constitutionへ反映する場合は、[ARu Constitution §20 Governance](./ARu-Constitution.md)の改訂プロセスを経ることを推奨する。

---

## 5. 未実装事項（Phase B4/B5、Roadmap Version 3）

- **AI Agents DB**：6 Agent（または9ロール）を実際のNotionレコードとして登録する（現時点ではドキュメント上の定義のみ）
- **Prompt Library**：各Agentが使うプロンプトの版管理（現時点では存在しない）
- **Automation**：n8n等による実際の自動実行（現時点ではAgentの動作はすべて概念設計であり、実行主体は人間またはClaude Codeの手動操作）

---

*ARu HQ / Decode Japan — AI Agent Architecture v1.0 — 2026-07-12*
