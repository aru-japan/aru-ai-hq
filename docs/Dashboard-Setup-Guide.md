<title>Dashboard Setup Guide</title>

# Dashboard Setup Guide
### 編集長ホーム画面を、Notion初心者でも30分で完成させる

| | |
|---|---|
| **Status** | Active |
| **対象** | Notionをあまり使ったことがない方 |
| **所要時間の目安** | 合計約35〜40分（共通手順の理解に5分＋13セクション×2〜3分） |
| **前提** | NotionパブリックAPIは「他のデータベースを絞り込み表示する画面（Linked View）」を自動作成できないため、この作業だけは人の手で行う必要がある |

---

## この作業で何をするか

Dashboardページには、すでに見出しと説明文（Callout）がAPI経由で用意されている。それぞれの見出しの下に、**「Linked view of database」**という機能を使って、対応するデータベースの中身を絞り込み表示する画面を1つずつ埋め込んでいく。

やることは、**同じ6ステップを13回繰り返すだけ**。1回できれば、あとは数値を変えるだけの単純作業になる（「📊 Coverage Analysis」「📝 Editorial Planner」の2つはLinked Viewではなく専用Notionページへのリンクなので、この作業の対象外——本文中のリンクをクリックするだけで内容が見られる）。

---

## 共通手順（すべてのセクションで同じ）

### ステップ1：埋め込み場所にカーソルを置く

Dashboardページを開き、埋め込みたい見出し（例：「① Publish Approval Pending」）の**説明文（Callout）のすぐ下の空行**をクリックする。

### ステップ2：Linked Viewを呼び出す

キーボードで `/` を入力する。コマンド一覧が表示されるので、続けて `linked` と入力すると候補が絞り込まれる。

```
/linked
┌─────────────────────────────┐
│ 🔗 Linked view of database   │  ← これをクリック
│ 📄 Linked view of page        │
└─────────────────────────────┘
```

**「Linked view of database」**をクリックする。

### ステップ3：データベースを選ぶ

データベース選択画面が開く。検索欄に対象のデータベース名（例：`Translation`）を入力し、候補に出てきたデータベースをクリックする。

```
どのデータベースをリンクしますか？
┌─────────────────────────────┐
│ 🔍 Translation                │
├─────────────────────────────┤
│ 📊 Translation                │  ← これをクリック
└─────────────────────────────┘
```

これで、そのデータベースの中身を表示する表（View）がページに埋め込まれる。

### ステップ4：Filter（絞り込み）を設定する

埋め込まれた表の右上にある**「Filter」**ボタンをクリックする。

```
┌───────────────────────────────────────┐
│  [Filter ▾]  [Sort ▾]  [•••]           │
└───────────────────────────────────────┘
```

「+ Add filter」→ 対象のプロパティ名を選ぶ → 条件（Is／Is not／Contains等）を選ぶ → 値を選ぶ、の順に設定する。各セクションの具体的な設定値は、下の「9セクション設定一覧」を参照。

### ステップ5：Sort（並び順）を設定する

同じツールバーの**「Sort」**ボタンをクリックし、「+ Add sort」でプロパティと昇順(Ascending)／降順(Descending)を選ぶ。2段階の並び替え（例：優先度→日付）が必要な場合は、もう一度「+ Add sort」を押して2つ目の条件を追加する。

### ステップ6：表示するプロパティ（列）を絞る

ツールバー右端の**「•••」**（もっと見る）をクリックし、**「Properties」**を選ぶ。表示したいプロパティだけをオン（目のアイコン）にし、それ以外はオフにする。列が多すぎると見づらいため、下の一覧で指定した項目だけを表示することを推奨する。

これで1セクション完了。**残り12セクションも同じ6ステップを繰り返すだけ。**

---

## 13セクション設定一覧

| # | セクション | データベース | View種別 | Filter | Sort | 表示するプロパティ |
|---|---|---|---|---|---|---|
| 🔴 | Update Needed | Articles | Table | `Freshness Status` は `Needs Update` | `Freshness Urgency Score` 降順 | Title／Update Level／Days Since Verification／Freshness Urgency Score／Freshness Note／Freshness Checked Date |
| 🚀 | Ready to Publish | Articles | Table | `Publishing Status` は `Ready to Publish` | `Priority` 降順 → `Update Level` 降順 → `Last Verified Date` 昇順 | Title／Category／Life Topics／Update Level／Review Result／Last Verified Date（※Publish ApprovalはTranslation側のプロパティのためArticles Viewには列として出せない。関連Translationを開いて確認する） |
| 📚 | Published Articles | Articles | Table | `Publishing Status` は `Published` | なし | Title／Published Date／Published By／ARu App URL |
| 🛠 | Needs Update（公開済み） | Articles | Table | `Publishing Status` は `Needs Update` | `Freshness Urgency Score` 降順 → `Days Since Verification` 降順 | Title／Freshness Urgency Score／Days Since Verification／Update Level |
| ① | Publish Approval Pending | Translation | Table | `Publish Approval` は `Pending` | `Quality Overall Score` 降順 | Translation Name／Language／Publish Approval／Quality Overall Score／Parent Article |
| ② | Article Review Waiting | Articles | Table | `Status` は `AI Draft` または `Human Review` | `Urgency` 降順 → `Updated Date` 昇順 | Title／Status／Update Level／Urgency／Category |
| ③ | Translation Review Waiting | Translation | Table | `Quality Result` が空、または `Not Reviewed` | 作成日時 昇順 | Translation Name／Language／Quality Result／AI Translation Status |
| ④ | SNS Draft Waiting | SNS Queue | Table | `Status` は `Draft` **かつ** `Review Result` は `Pass` ではない | 作成日時 昇順 | Title／Platform／Review Result／Related Article |
| ⑤ | Today's Editorial Calendar | Editorial Calendar | Table | `Status` は `Idea`／`Planned`／`In Progress` のいずれか | `Urgency` 降順 → `Planned Date` 昇順 | Planned Topic／Status／Urgency／Planned Date／Category |
| ⑥ | Today's Research | Research | Table | `Status` は `New` | `Priority` 降順 → `Urgency` 降順 | Topic／Category／Evidence Level／Priority／Urgency／Discovery Method |
| ⑦ | Source Monitor Alerts | Source Monitor | Table | `Change Detected` にチェックが入っている | `Checked At` 降順 | Monitor Entry／Change Type／Impact Level／Checked At／Source |
| ⑧ | Recent Law Updates | Law Update | Table | フィルタなし（全件表示） | `Effective Date` 降順 | Law Name／Significance／Effective Date／Update Status／Jurisdiction |
| ⑨ | Recent Event Calendar | Event Calendar | Table | `Status` は `Cancelled` ではない | `Event Date` 昇順 | Event Name／Type／Event Date／Status／Location |

> **View種別について**：すべてTableを推奨する（設定項目がシンプルで、初めてでも迷わないため）。慣れてきたら④をPlatformでグループ化したBoard表示に変えるなど、好みに応じてアレンジしてよい。

---

## 完了チェックリスト

- [ ] ① Publish Approval Pending
- [ ] ② Article Review Waiting
- [ ] ③ Translation Review Waiting
- [ ] ④ SNS Draft Waiting
- [ ] ⑤ Today's Editorial Calendar
- [ ] ⑥ Today's Research
- [ ] ⑦ Source Monitor Alerts
- [ ] ⑧ Recent Law Updates
- [ ] ⑨ Recent Event Calendar

## よくあるつまずきポイント

- **フィルタの条件名が英語のまま出てくる**：Notionの仕様上、`Is`（である）／`Is not`（ではない）／`Contains`（含む）等はプロパティの型によって選べる条件が変わる。Select型は基本「Is」、Checkbox型は「チェック済み／未チェック」を選ぶ。
- **2段階のSortが1つしか表示されない**：「+ Add sort」を**もう一度**押すと2つ目の条件が追加できる（1つ目の条件で同じ値が並んだ場合の並び順として使われる）。
- **プロパティが多すぎて表が横に長い**：ステップ6の「Properties」で不要な列を非表示にすると解消する。

---

*ARu HQ / Decode Japan — Dashboard Setup Guide v1.0 — 2026-07-13*
