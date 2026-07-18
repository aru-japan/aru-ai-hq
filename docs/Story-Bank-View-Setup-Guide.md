<title>Story Bank View Setup Guide</title>

# Story Bank View Setup Guide
### Story Bankの7ビューを手動で設定する

| | |
|---|---|
| **Status** | Active |
| **対象** | Story Bankデータベースを実際に運用する編集担当者 |
| **前提** | NotionパブリックAPIはView（フィルタ・ソート済みの表示）を作成できないため、この作業は人の手で行う必要がある（[Dashboard Setup Guide](./Dashboard-Setup-Guide.md)と同じ制約） |

---

## この作業で何をするか

Story Bankデータベースを開き、上部の「+ Add a view」（または既存ビューの隣の＋）から、以下7つのビューを1つずつ作成する。各ビューは**Table**タイプのまま、Filter／Sortだけを設定すればよい。

---

## 1. Story Backlog

まだ生産に入っていないStory全体を一覧する、基本のビュー。

- **Filter**：`Story Status` is `New` OR `Story Status` is `Approved`
- **Sort**：`Priority` 降順（S→A→B→C。Priorityのオプション定義順を`C, B, A, S`にしてあるため、降順ソートで正しくSが先頭に来る）

## 2. High Priority

- **Filter**：`Priority` is `S` OR `Priority` is `A`

## 3. Summer

- **Filter**：`Season` contains `夏`

## 4. Autumn

- **Filter**：`Season` contains `秋`

## 5. Evergreen

- **Filter**：`Evergreen` is checked

## 6. Premium Candidates

- **Filter**：`Premium Candidate` is checked

## 7. Ready for Production

- **Filter**：`Story Status` is `Approved`
- 補足：Story Statusの選択肢に「Ready for Production」という値は作っていない。「Approved」＝「次工程（QA Card／Article生成）に進めてよい」という意味で運用する想定。もし将来「Approved」と「Ready for Production」を別の状態として分けたい場合は、Story Statusの選択肢追加をDevelopment Sessionで検討する

---

## 補足：Summer／Autumn以外の季節ビューが必要になったら

同じ手順で`Season` contains `春`／`Season` contains `冬`のビューを追加すればよい（今回の依頼にはなかったため作成していない）。

---

*ARu HQ / Decode Japan — Story Bank View Setup Guide — 2026-07-18*
