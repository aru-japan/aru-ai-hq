<title>AI Agent Workflow v1.0</title>

# AI Agent Workflow
### ARu Studio — Roadmap Version 2.0 設計書

| | |
|---|---|
| **Status** | Draft — 設計のみ |
| **Date** | 2026-07-12 |
| **位置づけ** | [AI Agent Architecture v1.0](./AI-Agent-Architecture.md)で定義した6 Agentが、実際にどの順序で・どの条件で動くかを定める |

---

## 1. 日次サイクル（標準ワークフロー）

[ARu Studio Operating Manual](./Operating-Manual.md)の「朝やること」に対応する、Agent間の標準的な受け渡し。

| # | 実行者 | アクション | 完了条件 → 次の受け渡し |
|---|---|---|---|
| 1 | Researcher | Source Monitorを確認し、変化があればResearchを作成 | Research.Status=New → Editor-in-Chiefへ |
| 2 | Editor-in-Chief | Research／Experience Intelligence（Gap／Opportunity）を見てPriority／Urgencyを設定 | Priority確定 → Writerへ（Research.Status=Reviewing以降） |
| 3 | Writer | ResearchからArticle Draftを生成 | Articles.Status=AI Draft → Reviewerへ |
| 4 | Reviewer | 文化／法律／情報精度／SEO／外国人目線の5観点でレビュー | QA Status=Passed → Editor-in-Chiefへ／Failed → Writerへ差し戻し |
| 5 | Editor-in-Chief | Quality Gate通過を確認し、Update Levelで分岐 | 下記「Update Level分岐」参照 |
| 6 | Translator | Published後、対象言語のTranslationを生成 | Localization Status=Culturally Adapted → Social Managerへ |
| 7 | Social Manager | SNS Queueレコードを生成 | Status=Draft（人間の最終確認待ち） |

### Update Level分岐（ステップ5の詳細）

```
QA Status = Passed
        │
        ▼
   Update Level？
   ├─ 1 → Editor-in-ChiefがArticles.Statusを自動でPublishedへ
   ├─ 2 → Editor-in-Chiefがレビュー結果を要約し、Reviewer（Mentor）へ提示 → 人間が承認して初めてPublished
   └─ 3 → Editor-in-ChiefがChange Summaryを含めて編集長(Rei)へ緊急性を明示 → 人間が承認して初めてPublished
```

---

## 2. 法改正対応ワークフロー

[ARu Studio Operating Manual §7](./Operating-Manual.md)を、6 Agent体制向けに具体化したもの。

1. **Researcher**：Source Monitor（Source Type=政府/自治体、Tier=高）の変化を検知し、Law Updateレコードを作成（Update Status=Monitoring）
2. **Researcher**：一次情報源で内容を確認できたらUpdate Status=Confirmed、Significanceを設定（Minor/Major）
3. **Editor-in-Chief**：Significance=MajorのLaw Updateを検知したら、関連するAffected Articlesの Urgency を Critical に引き上げる
4. **Writer**：Affected Articlesの内容を、Law Update.Impact Summary／Action Requiredに基づいて更新
5. **Reviewer**：「法律」観点を最優先でレビュー。Update Status=Reflecting to Article
6. **Editor-in-Chief**：Significance=Majorの場合、**Update Level 3の人間承認フローへ必ず送る**（第4章「エスカレーション」参照）
7. 承認後、Update Status=Article Published、Affected Translationも同様に更新（Translatorが担当）

---

## 3. 緊急更新ワークフロー

ARu Constitution §12 Emergency Update Rulesに対応する。

1. どのAgentも、Source Monitor.Change Type=EmergencyまたはImpact Level=Criticalを検知した時点で、**Editor-in-Chiefへ即時エスカレーション**する
2. Editor-in-Chiefは、対象Articlesおよび紐づく全TranslationのStatusを Human Review 相当へ戻す（日本語・全言語同時）
3. 編集長（Rei）または該当分野の専門家が6時間以内に確認する（現時点ではMentor DB未実装のため、都度人手で確認先を手配）
4. 対応内容は現時点では手動記録（Audit Log DBはPhase B5で実装予定）

---

## 4. Agent間のハンドオフ・エスカレーション条件

| 発生条件 | 送り元 | 送り先 | 理由 |
|---|---|---|---|
| Research.Evidence Level = Rumor/AI Suggested のまま Update Level 2/3相当に着手しようとした | Researcher | Editor-in-Chief（→人間） | 一次情報源での確認が必要 |
| Articles.QA Status = Failed | Reviewer | Writer | 修正差し戻し |
| Articles.QA Status = Failed が3回連続 | Reviewer | 人間（編集長） | Agent間のループを止める |
| Translation.Localization Status = Needs Cultural Review | Translator | 人間（該当言語のレビュー担当） | 文化的判断は人間が最終判断 |
| Update Level 2 | Editor-in-Chief | 人間（担当レビュー） | 48時間SLA（ARu Constitution §10） |
| Update Level 3 | Editor-in-Chief | 人間（編集長 or 専門家） | 24時間SLA（ARu Constitution §10） |
| SNS Queueの投稿にUpdate Level 2/3のコンテンツが含まれる | Social Manager | 人間 | Publish Approval確定前は投稿不可 |

---

## 5. 現時点の実行主体について

本ワークフローは**設計であり、まだ自動実行されない**。現時点（Roadmap Version 2）では、各ステップは人間（Rei）がNotion上で手動、またはClaude Codeとの対話を通じて代行する。Version 3（AI Automation）でn8n・Automation DBが実装されて初めて、このワークフローが実際に自律実行される。

---

*ARu HQ / Decode Japan — AI Agent Workflow v1.0 — 2026-07-12*
