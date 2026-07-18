<title>Studio v4.1 View Setup Guide</title>

# Studio v4.1 View Setup Guide
### ARu Studio Version 4.1 Editorial Intelligence — 24ビューを手動で設定する

| | |
|---|---|
| **Status** | Active |
| **対象** | Story Bank／Articles／Source Monitor／Law Updateを運用する編集担当者 |
| **前提** | NotionパブリックAPIはView（フィルタ・ソート済みの表示）を作成できないため、この作業は人の手で行う必要がある（[Story Bank View Setup Guide](./Story-Bank-View-Setup-Guide.md)・[Dashboard Setup Guide](./Dashboard-Setup-Guide.md)と同じ制約） |

---

## この作業で何をするか

各データベースを開き、上部の「+ Add a view」から、以下のビューを1つずつ作成する。各ビューは**Table**タイプのまま、Filter／Sortだけを設定すればよい。プロパティ名はすべて実際にNotion上へ追加済みのもの（`notion-build/add_v4_1_schema.py`・`add_v4_1_relations.py`実行済み）。

---

## Story Bank（7ビュー）

### 1. New QA
QA Questionが設定済みでまだレビューされていないカード。
- **Filter**：`QA Question` is not empty AND `Story Status` is `New`

### 2. High Priority
- **Filter**：`Priority` is `S` OR `Priority` is `A`

### 3. By Category
- **Sort**：`Content Category` 昇順（グループ化ビューにする場合は「Group by: Content Category」を使う）

### 4. Food Support
食事制限関連のQA・記事候補のみ。
- **Filter**：`Content Category` is `食事制限`
- **Sort**：`Dietary Restriction Type`でグループ化すると見やすい

### 5. Article Needed
- **Filter**：`Article Needed` is checked AND `Generated Article` is empty

### 6. Deep Guide Needed
- **Filter**：`Deep Article Needed` is checked AND `Generated Article` is empty
- 補足：AI Command Centerの「🆕 今日追加するQA・今日の記事・Deep Guide候補」セクションと同じ条件

### 7. Review Due
- **Filter**：`Next Review` is on or before today

---

## Articles（7ビュー）

### 1. Today's Articles
本日作成された記事。
- **Filter**：Created time is today（Notion組み込みの「Created time」を使用。Articlesにはカスタムの作成日プロパティがないため）

### 2. Headline Articles
- **Filter**：`Content Type` is `Headline`

### 3. Deep Guides
- **Filter**：`Content Type` is `Deep Guide`

### 4. Premium
- **Filter**：`Content Type` is `Premium`

### 5. Update Required
- **Filter**：`Current Validity` is `Review Due` OR `Current Validity` is `Outdated`
- 補足：既存の「Publishing Status = Needs Update」（時間経過によるFreshness起因）とは別軸。両方を見たい場合はDashboardの「🔴 Freshness 内訳」も参照

### 6. Review Due
- **Filter**：`Current Validity` is `Review Due`

### 7. Outdated
- **Filter**：`Current Validity` is `Outdated`

---

## Source Monitor（4ビュー）

### 1. Daily Check
- **Filter**：`Check Frequency` is `Daily`（Source Libraryからのrollupのため、Filterで直接指定できない場合はSource Library側でフィルタしてから確認する）

### 2. Weekly Check
- **Filter**：`Check Frequency` is `Weekly`

### 3. Change Detected
- **Filter**：`Change Detected` is checked

### 4. Errors
- **Filter**：`Status` is `Error`

---

## Law Update（6ビュー）

Update Statusの運用上の意味：`Monitoring`＝検知直後・未確認、`Confirmed`＝人間が実在/重要性を確認済み、`Reflecting to Article`＝影響記事を反映中、`Approval Required`＝人間の承認待ち、`Article Published`＝反映完了、`No Action Required`＝対応不要と判断、`Archived`＝終了。

### 1. New Changes
- **Filter**：`Update Status` is `Monitoring`

### 2. Urgent
- **Filter**：`Urgency` is `Critical` OR `Urgency` is `High`

### 3. Impact Analysis
- **Filter**：`Update Status` is `Confirmed`
- 補足：`law_update_pipeline.py`の`run_impact_analysis()`はこの状態のレコードを対象に、`Affected Category`が設定されていれば自動でAffected Stories/Affected Articlesを埋める

### 4. Updating
- **Filter**：`Update Status` is `Reflecting to Article`

### 5. Approval Required
- **Filter**：`Update Status` is `Approval Required`

### 6. Published
- **Filter**：`Update Status` is `Article Published`

---

*ARu HQ / Decode Japan — Studio v4.1 View Setup Guide — 2026-07-19*
