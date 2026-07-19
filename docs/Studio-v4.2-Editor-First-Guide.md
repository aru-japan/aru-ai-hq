<title>Studio v4.2 Editor-First Guide</title>

# Studio v4.2 Editor-First Guide
### 編集長が毎朝どのように使うか — 5分で分かる運営フロー

| | |
|---|---|
| **Status** | Active |
| **対象** | ARu Studioを毎日運営するRei本人（および将来この役割を引き継ぐ人） |
| **位置づけ** | Dashboardの3ゾーン再設計（[Automation-Scripts.md](./Automation-Scripts.md)「ARu Studio v4.2 — 編集長ファースト3ゾーン再設計」節が実装の技術詳細）を、**使う側の視点だけ**でまとめたもの。技術的な背景を知る必要はなく、このページだけで毎朝の運営ができることを目指す |

---

## 1行で言うと

**Dashboardを開く → ✍️の記事をクリックして書き始める。それだけで1日が始められる。**

---

## 朝やること（60秒）

```bash
cd notion-build/automation
python3 source_watcher.py        # 情報源の変化を検知
python3 ai_command_center.py     # Dashboardを最新化
```

Notionで **Dashboard** を開く。上から3つのゾーンが並んでいる。

### ① ✍️ 今すぐ書く（最初に見る場所）

AIが「次に書くべき1本」を自動で1つだけ選んで表示する。タイトルは実際のNotionページへのリンクになっている。

- **クリックするだけで着手できる。** これが今日の第一候補
- 表示される記事は3種類のどれか
  - 「執筆中・◯◯」→ 昨日までの続きを書く（Articles）
  - 「Research候補 1位・スコア◯点」→ 新しい記事を書き始める（Research）
  - 「Story Bank・記事化待ち」→ ネタから直接書き起こす（Story Bank）
- 気に入らなければ「他の候補を見る（Research）→」から他の候補も見られる

**ここまでで実質2クリック**（Dashboardを開く＋タイトルをクリック）で記事の執筆画面にたどり着く。

### ② 📋 今日の判断（3つの数字だけ確認）

横に並んだ3つの数字を見るだけ。

| 数字 | 意味 | 0件でなければ |
|---|---|---|
| 🔴 Critical | 今すぐ人間の判断が要る案件 | 最優先で「詳細・AI監視」内の該当toggleを開く |
| 🚀 公開判断待ち | 公開してよいか判断待ちの記事数 | Ready to Publishの記事を確認し、公開判断を進める |
| 🔧 更新が必要 | 内容が古くなっている記事数 | 手が空いたときに確認する（緊急ではない） |

**全部0や少数なら、①の記事執筆にそのまま進んでよい。**

### ③ 🔍 詳細・AI監視（普段は開かなくてよい）

折りたたまれている。中には16個の小さなtoggleが入っており、①②の数字の根拠や、AIが裏側で監視している内容（Source Monitor、Law Update Pipeline、Production Stage内訳など）が項目ごとに分かれている。

**普段は開く必要はない。** ②で気になる数字があったときだけ、該当するtoggle（例：「🔴 Critical Updates（詳細）」）を1つだけ開けばよい。

---

## 1日の流れ（全体像）

```
Dashboardを開く
   ↓
✍️ 今すぐ書くをクリック → 執筆・レビュー
   ↓
📋 今日の判断の3数字を確認
   ↓
🔴 Criticalがあれば → 詳細toggleを開いて対応
🚀 公開判断待ちがあれば → Ready to Publishを確認し公開判断
   ↓
（手が空いたら）🔧 更新が必要 を確認
   ↓
新しい情報源・イベントを知ったら Source Library／Event Calendar へ登録
```

より詳しい編集判断のロジック（Update Levelごとの承認ルール等）は[Operating-Manual.md §1](./Operating-Manual.md#1-daily-editor-workflow毎日やること)を参照。

---

## よくある状況

**Q. ✍️ 今すぐ書く に「候補がありません」と出た**
Research・Story Bankどちらにも候補がない状態。Researchで新しいテーマを検討するか、Story Bankにアイデアを追加する（詳細は各DB先頭の説明文＝operator guideを参照）。

**Q. 同じ記事が何日も ✍️ に出続ける**
執筆中（Production Stage）のまま止まっている記事がある可能性。該当記事のProduction Stageを更新するか、優先度が低ければ一旦Headline Ready以前に戻す。

**Q. 3クリックで本当に足りるのか不安**
DashboardをNotionのサイドバーにお気に入り登録しておくと、「開く」の1クリック目がどこからでも一定になる（これは運用側の一回限りの設定で、スクリプトの対象外）。

**Q. Notionのボタン機能を使いたい**
公開APIではボタンブロックを作成できない（既知の制約、[Automation-Scripts.md](./Automation-Scripts.md)参照）。今のリンク方式でも「クリックすると開く」体験は同じだが、見た目のボタンが欲しい場合はNotion UI上で手動追加する（他のView設定と同じ一回限りの作業）。

---

## この画面で変わらないもの

- 11データベースのプロパティ・スキーマ・リレーションは一切変更されていない
- 既存の13個のLinked Views（Dashboard下部）はそのまま残っている
- AI用データベース（Source Monitor／Law Update／Experience Intelligence等）は裏側で今まで通り動いている——見える場所が「詳細・AI監視」に変わっただけ
- 公開操作（Publishing Status→Published）は今まで通り必ず人間が行う。AIは自動公開しない

---

*ARu HQ / Decode Japan — Studio v4.2 Editor-First Guide — 2026-07-19*
