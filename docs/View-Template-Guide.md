<title>ARu Studio — View & Template 設定ガイド</title>

# ARu Studio — View & Template 設定ガイド
### Phase B1 MVP（5DB）向け・Notion UI手動設定手順

| | |
|---|---|
| **Status** | Active |
| **Date** | 2026-07-12 |
| **対象** | Articles／Research／Translation／Source Library／Editorial Calendar（実装済み5DB） |
| **前提** | View・TemplateはNotionパブリックAPIでは作成できないため、本ガイドの手順に沿ってNotion UI上で手動設定する |

---

## 0. Viewを作る共通手順（毎回同じ操作）

1. 対象データベースを開く（フルページ推奨）
2. 画面上部のビュータブ列にある **「+」** をクリック
3. 表示形式を選ぶ（本ガイドの指定に従う：Table／Board／Calendar）
4. ビュー名を入力（例：「Daily View」）
5. ビュー右上の **「Filter」** をクリックし、指定の条件を追加
6. **「Sort」** をクリックし、指定の並び順を追加
7. Board表示の場合は **「Group by」** でグループ化する列を指定
8. 設定は自動保存される

以下、DBごとに4つのView（Daily／Weekly／Review／Archive）の設定内容を示す。

---

## 1. Articles

編集長が「今日、何を承認・執筆すべきか」を見る場所。

| View | 表示形式 | Filter | Sort / Group |
|---|---|---|---|
| **Daily View** | Table | Status is any of `AI Draft`, `Human Review` | Sort: Urgency（降順）→ Updated Date（昇順） |
| **Weekly View** | Calendar | なし（全件、Published Dateを表示軸に） | Calendar軸: Published Date |
| **Review View** | Board | Status = `Human Review` | Group by: Update Level |
| **Archive View** | Table | Status = `Archived` | Sort: Archived Date（降順） |

---

## 2. Research

「今日、何を採用・調査すべきか」を見る場所。

| View | 表示形式 | Filter | Sort / Group |
|---|---|---|---|
| **Daily View** | Table | Status = `New` | Sort: Priority（降順）→ Urgency（降順） |
| **Weekly View** | Board | Status is not `Converted`, is not `Rejected` | Group by: Discovery Method |
| **Review View** | Table | Status = `Reviewing` | Sort: Evidence Level（`AI Suggested`/`Rumor`が上に来るよう手動並び順設定）→ Trust Score（昇順） |
| **Archive View** | Table | Status is any of `Converted`, `Rejected` | Sort: 最終更新（降順） |

> Evidence Levelのソートは、NotionのSelectプロパティで選択肢の並び順を「Official→Verified→Reported→Rumor→AI Suggested」の逆順（AI Suggestedが先頭）に設定しておくと、Sort機能で自然に危険度の高いものが上に来る。

---

## 3. Translation

「今日、どの言語のどの翻訳を進めるべきか」を見る場所。

| View | 表示形式 | Filter | Sort / Group |
|---|---|---|---|
| **Daily View** | Table | Needs Re-Translation = チェック済み、または AI Translation Status = `Queued` | Sort: Review Level（降順） |
| **Weekly View** | Board | なし | Group by: Language |
| **Review View** | Table | Human Review Status is any of `Pending`, `In Review` | Sort: Review Level（降順） |
| **Archive View** | Table | Publish Status = `Published` | Sort: Published Date（降順） |

---

## 4. Source Library

「今日、何を確認・追加すべきか」を見る場所。

| View | 表示形式 | Filter | Sort / Group |
|---|---|---|---|
| **Daily View** | Table | Status = `Active` | Sort: Last Checked（昇順＝未確認が長いものが上） |
| **Weekly View** | Board | Status = `Active` | Group by: Source Type |
| **Review View** | Table | Verification Status is any of `Unverified`, `Needs Recheck` | Sort: Tier（降順） |
| **Archive View** | Table | Status = `Inactive` | Sort: Source Name（昇順） |

---

## 5. Editorial Calendar

**編集部運営の司令塔。編集長が毎朝最初に開くべきDB。**

| View | 表示形式 | Filter | Sort / Group |
|---|---|---|---|
| **Daily View** | Table | Status is any of `Idea`, `Planned`, `In Progress` | Sort: Urgency（降順）→ Planned Date（昇順） |
| **Weekly View** | Calendar | なし | Calendar軸: Planned Date |
| **Review View** | Table | Status = `Drafted` | Sort: Success KPI（降順） |
| **Archive View** | Table | Status is any of `Published`, `Skipped`, `Cancelled` | Sort: Planned Date（降順） |

---

## 6. Templateの作り方（共通手順）

1. 対象データベースを開く
2. 右上の **「New」ボタン横の小さな ∨（下矢印）** をクリック
3. **「New template」** を選択
4. 開いたテンプレート編集画面で、各プロパティに既定値を設定する（下記参照）
5. 必要であればページ本文にチェックリスト等を追加する（`/to-do` でTo-doブロックを挿入）
6. 右上の「...」からテンプレート名を設定して保存
7. 複数テンプレートがある場合、よく使うものを「Set as default」にできる

---

## 7. Article Template

**既定プロパティ**

| Property | 既定値 |
|---|---|
| Status | Draft |
| Master Language | ja |
| Priority | Medium |
| Urgency | Medium |
| Confidentiality | Public |
| Usage Scope | Consumer App |
| Article Owner | Rei |
| AI Generated | 未チェック |
| Human Reviewed | 未チェック |

**本文に挿入するチェックリスト**（ARu Constitution 第14章 Quality Checklistをそのまま反映）

```
/to-do 出典（Source Library）が明記されている
/to-do Categoryと Audience が設定されている
/to-do 「何をすべきか」だけでなく「なぜ」が書かれている
/to-do マナーと法律が混同されずに区別されている
/to-do 法律・医療系の場合、免責事項が入っている
/to-do Update Level 2/3の場合、有資格メンターのレビューが完了している
/to-do 一般化・ステレオタイプ表現がない
/to-do リンク・日付・固有名詞が最新かつ正確である
```

> **応用**：法改正記事用に複製し、Category=法律・制度、Urgency=High をプリセットした「法改正記事テンプレート」を追加で作ると、Constitution §13の免責事項を本文冒頭に埋め込んだ専用テンプレートになる。

---

## 8. Research Template

**既定プロパティ**

| Property | 既定値 |
|---|---|
| Status | New |
| Evidence Level | AI Suggested |
| Priority | Medium |
| Discovery Method | Manual |
| Confidentiality | Public |
| AI Generated | 未チェック |

---

## 9. Translation Template

**既定プロパティ**

| Property | 既定値 |
|---|---|
| AI Translation Status | Queued |
| Localization Status | Not Started |
| Human Review Status | Not Required |
| Publish Approval | Not Required |
| Publish Status | Not Published |
| Confidentiality | Public |

---

## 10. Dashboard：Linked View埋め込み手順（v2、編集長ホーム画面）

DashboardページはAPIで雛形（見出し9つ＋説明のCallout）まで自動生成済み。各見出しの下に「Linked view of database」を埋め込むのはNotion UI上での手動作業になる。

**配置の考え方**：上から「①〜④ 今すぐ判断が必要なもの（承認・レビュー待ち）」→「⑤〜⑥ 今日の予定」→「⑦〜⑨ 外部シグナル・モニタリング」の順。編集長が毎朝上から順に見ていけば、優先度の高いものから対応できるように並べてある。

**共通手順**

1. Dashboardページを開き、埋め込みたい見出しの直下にカーソルを置く
2. `/linked` と入力し、**「Linked view of database」** を選択
3. 埋め込みたいデータベース（例：Translation）を選ぶ
4. 表示形式をTableまたはBoardに変更
5. 右上の「Filter」「Sort」で、下表の条件を設定する
6. 見やすいようにプロパティの表示列を絞る（Notionの「Properties」設定で非表示にできる）

**9セクションの設定内容**

| # | セクション | データベース | Filter | Sort |
|---|---|---|---|---|
| ① | Publish Approval Pending | Translation | Publish Approval=Pending | Quality Overall Score 降順 |
| ② | Article Review Waiting | Articles | Status is AI Draft or Human Review | Urgency 降順 → Updated Date 昇順 |
| ③ | Translation Review Waiting | Translation | Quality Result is empty または Not Reviewed | 作成日 昇順 |
| ④ | SNS Draft Waiting | SNS Queue | Status=Draft かつ Review Result ≠ Pass | 作成日 昇順 |
| ⑤ | Today's Editorial Calendar | Editorial Calendar | Status is Idea/Planned/In Progress | Urgency 降順 → Planned Date 昇順 |
| ⑥ | Today's Research | Research | Status=New | Priority 降順 → Urgency 降順 |
| ⑦ | Source Monitor Alerts | Source Monitor | Change Detected=true | Checked At 降順 |
| ⑧ | Recent Law Updates | Law Update | なし（全件） | Effective Date 降順 |
| ⑨ | Recent Event Calendar | Event Calendar | Status ≠ Cancelled | Event Date 昇順 |

> **旧バージョンからの変更**：以前の8セクション構成（Today's Opportunities／Knowledge Gaps／Critical Updates等、Experience Intelligence中心）から、**Publish Approval Pending／Article・Translation・SNSのReview待ち／Today's Research／Recent Law Updates**を軸にした9セクション構成へ全面刷新した。Experience Intelligence（Gap/Opportunity）は現時点でDashboardの主要動線からは外れているが、DB自体は健在で、必要であれば追加セクションとして復活させられる。

---

*ARu HQ / Decode Japan — View & Template Setup Guide v1 — 2026-07-12*
