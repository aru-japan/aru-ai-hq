<title>Article Property Panel Guide</title>

# Article Property Panel Guide
### 編集長がArticleページを開いた瞬間に、本文と公開情報だけを見られる状態にする

| | |
|---|---|
| **Status** | Active |
| **対象** | Notionをあまり使ったことがない方 |
| **所要時間の目安** | 1記事あたり約3〜5分（テンプレート化すれば以降はコピーで一瞬） |
| **前提** | NotionパブリックAPIは「プロパティパネルのグループ化・折りたたみ」を自動設定できないため（Linked Database Viewと同じ制約）、この作業だけは人の手で行う必要がある |

---

## この作業で何をするか

Version 4 Phase 5（Editor Experience）の一部。**データベースのスキーマ（プロパティの追加・削除・名前変更）は一切変更しない** —— 変更するのは、Articleページを開いたときにどのプロパティがどの順番・どのグループで見えるか、という「見た目」だけ。

Articleのプロパティを4つのグループに分け、上位2グループ（本文寄り／公開情報）は常に開いた状態、下位2グループ（AI Review／System）は折りたたんだ状態にする。

---

## 共通手順（1記事につき1回）

### ステップ1：Articleページを開く

対象のArticleページを開き、プロパティパネル（タイトル直下の一覧）を表示する。

### ステップ2：グループを作る

プロパティ名の上で右クリック（またはプロパティ名の右の「•••」）→ **「Group」**（または「Add to group」）を選ぶ。同じグループに入れたいプロパティを続けて選択していく。

```
Priority          •••
┌─────────────────────┐
│ Edit property         │
│ Group              ←  │  これをクリック
│ Hide in view           │
└─────────────────────┘
```

> Notionのバージョンによりメニュー名が「Group」ではなく「Add to section」等になっている場合がある。見当たらない場合は、プロパティを1つドラッグして別のプロパティの上に重ねると自動的にグループ化されることもある。

### ステップ3：グループ名を付ける

作成したグループの見出し部分をクリックし、下の「グループ設定一覧」にある名前（【本文】【公開情報】【AI Review】【System】）を入力する。

### ステップ4：グループを折りたたむ

グループ見出し横の「▾」（折りたたみ矢印）をクリックして、【AI Review】と【System】を閉じた状態にする。【本文】と【公開情報】は開いたままにする。

### ステップ5：テンプレート化して使い回す（推奨）

1記事で設定できたら、そのページの「•••」→「Duplicate」または既存の「New article」テンプレートに同じグループ設定を反映させておくと、以後生成される記事にも自動的に同じ並びが適用される（テンプレート機能自体もAPIからは触れないため、これも手動設定）。

---

## グループ設定一覧

実際にArticles DBへ書き込んでいるプロパティ名を、各自動化スクリプトのコードから確認した実名で記載（`docs/Article-Property-Panel-Guide.md` 作成時点）。

| グループ | 状態 | プロパティ |
|---|---|---|
| 【本文】 | 常に展開 | Title／Body／Category／Audience／Season／Life Topics／Tags |
| 【公開情報】 | 常に展開 | Publishing Status／Priority／Urgency／Review Result／Status／Last Verified Date／Published Date／Update Level |
| 【関連情報】 | 常に展開（任意で折りたたみ可） | Source Research／Knowledge Links／Source Law Update／Article Owner（Translation・SNS Queue・Experience Intelligence側からの逆リレーションはNotionが自動命名するため、実際の表示名は各自の画面で確認） |
| 【AI Review】 | 折りたたみ | Review Accuracy Score／Review Evidence Score／Review Readability Score／Review Risk Score／Review Localization Score／Review Suggestions／Review Date |
| 【System】 | 折りたたみ | Record ID／Version／Revision／AI Generated／Human Reviewed／Archived Date／Freshness Status／Days Since Verification／Freshness Urgency Score／Freshness Checked Date／Freshness Note／QA Status／Verification Status／Related Constitution Version／Slug／Master Language／Confidentiality／Usage Scope／Last AI Update／Updated Date／Published By／ARu App URL／Previous Publishing Status／Publishing Status Updated Date |

> 上記はコードで確認できた実在プロパティのみを掲載。Trust Score／Cultural Value Score／Visitor Suitability Score／Popularity Score／Recommendation Scoreはスキーマ上は存在するが、現時点でどの自動化スクリプトも書き込んでいない（未使用）。使うことになった場合は【AI Review】グループに追加する。

---

## 完了チェックリスト（1記事につき）

- [ ] 【本文】グループを作成し、展開状態にした
- [ ] 【公開情報】グループを作成し、展開状態にした
- [ ] 【関連情報】グループを作成した
- [ ] 【AI Review】グループを作成し、折りたたんだ
- [ ] 【System】グループを作成し、折りたたんだ
- [ ] ページを開いた瞬間に本文と公開情報だけが見える状態になっている

---

## よくあるつまずきポイント

- **「Group」メニューが見当たらない**：Notionのバージョン差によりメニュー名・場所が変わることがある。プロパティを別のプロパティの直下にドラッグ&ドロップすると自動でグループ化される場合もある。
- **1記事ずつ設定するのが大変**：新規記事テンプレート（Notionの「New article」テンプレート）側に同じグループ構成を一度反映させておけば、以後の新規作成分は自動的に同じ見た目になる。既存記事は手動で1件ずつ設定する必要がある。
- **リレーションの逆プロパティ名が分からない**：Translation／SNS Queue／Experience Intelligence／ResearchからArticlesへの逆リレーションは、Notionがリンク元データベース名などから自動生成するため、コード上では確定できない。実際のArticleページを開いて確認すること。
- **グループ化してもDashboardのLinked Viewには影響しない**：Linked Viewが表示する列（Properties）は各Viewごとに個別設定されており、Articleページ単体のプロパティパネル表示とは独立している。本ガイドの作業はDashboardの表示に一切影響しない。

---

*ARu HQ / Decode Japan — Article Property Panel Guide v1.0 — 2026-07-16*
