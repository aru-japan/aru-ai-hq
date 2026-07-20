<title>全国情報収集の拡張 — 設計文書</title>

# 全国情報収集の拡張（イベント・トレンド・スポーツ体験・新店舗・食情報）
### 設計・監査文書（2026-07-20）

| | |
|---|---|
| **Status** | 設計・dry-run完了。Notion書き込み・新規プロパティ追加・自動化の本番実行は未実施 |
| **位置づけ** | [Mission-Control-Architecture.md](./Mission-Control-Architecture.md)・[Regional-Event-Discovery-Audit-2026-07-20.md](./Regional-Event-Discovery-Audit-2026-07-20.md)の延長線上にある設計文書 |
| **範囲** | イベント／トレンド／スポーツ体験／新店舗・日本初上陸／期間限定・ポップアップ／文化体験／収穫体験／食事制限対応情報の継続収集の設計と50件のdry-run |

---

## 1. 既存DB・プロパティで対応できる項目の監査

結論：**既存4DBの組み合わせで、要求された項目のほとんどを新規プロパティなしで表現できる。** 特にExperience Intelligenceは「トレンド」「機会の期限」を扱う設計が既にほぼこの用途のために存在していたと言えるほど適合度が高い。

### Experience Intelligence（44プロパティ）の再点検

| 既存プロパティ | 転用方法 |
|---|---|
| `Intelligence Type`（Event/Culture/Trend/Local/Gap/Opportunity/User） | トレンド→Trend、文化体験→Culture、新店舗→Local、期間限定機会→Opportunity として使用。**新しい選択肢は追加しない** |
| `Opportunity Window Start` / `Opportunity Window End` | 新店舗の開店日・期間限定の開始/終了として転用。Endを空欄にすれば「常設」を表現できる |
| `Days Until Opportunity Expires`（formula、自動計算） | 期限までの残り日数を自動表示。既存のまま使える |
| `Status`（New/Reviewing/Acknowledged/Actioned/Converted/Resolved/Rejected/**Expired**） | **「Expired」が既に存在**——期限切れの表現に新規値は不要 |
| `Platform`（Instagram/Threads/X/YouTube） | SNS発見元の記録に使用。ただし自治体公式サイト等SNS以外の発見元はカバーしない（後述の限界） |
| `Signal Volume`（number） | 複数Sourceでの言及件数の記録に使用 |
| `Trend Signal Strength`（number） | 「一時的な話題」か「継続傾向」かの強弱を数値で表現（継続傾向ほど高い値、という運用ルールで対応） |
| `Metric / Evidence`（rich_text） | 原文引用・公式発表の引用箇所に使用 |
| `Description`（rich_text） | 所在地・店舗種別・価格帯・食事制限対応の記載など、専用プロパティがない項目をここに構造化して記載 |
| `Source Confidence` / `Trust Score` | 確認状態（公式発表か推測か）の数値化に使用 |
| `Related Research` | Reiが深い記事候補に選んだ際の既存リレーション |
| `Related Signal` | 重複・関連候補の明示に使用（新規プロパティ不要） |
| `Last AI Update` | 最終確認日時 |

**専用プロパティがなく`Description`へ統合する項目**：地域（Regionプロパティ自体が存在しない）、所在地、発見元がSNS以外の場合の種別、価格帯、予約要否、食事制限対応の公式記載文言、初回発見日（Opportunity Window Startを流用しない場合）。

### Event Calendar（33プロパティ）の再点検

| 既存プロパティ | 転用方法 |
|---|---|
| `Repeat Schedule`（One-time/Annual/Monthly/Weekly/Irregular） | 継続開催のスポーツ体験・初心者教室（週次ランニング教室等）はここで表現。**イベント日が明確または定期開催のものはEvent Calendar優先** |
| `Status`（Planning/Confirmed/Promoting/Completed/**Cancelled**） | 中止・終了は既存値で表現可能 |
| `Type`（祭り/花火大会/フードフェス/蚤の市/マルシェ/文化イベント/自治体イベント/季節イベント/期間限定イベント） | 既存9値の範囲内で対応。スポーツ体験の具体的な型は不足するため`Description`相当は存在しないが、`Location`等へ記述で補う |
| `Accessibility`, `Family Friendly`, `Reservation Required`, `Rain Policy` | 既存のまま活用 |

### Source Monitor（28プロパティ）の再点検

| 既存プロパティ | 転用方法 |
|---|---|
| `Update Classification`（Law Change/Policy Update/Fee Change/Deadline Change/Event Update/Festival Schedule/Weather Warning/Transportation/Tourism Information/Emergency Notice/General News） | SNS・Web発見の分類にはやや法制度寄りの値が多いが、`Event Update`／`General News`で大半をカバー可能 |
| `Change Type`（New/Updated/Deleted/Policy Change/Emergency） | 新規発見＝New、既存情報の更新＝Updated として使用 |
| `Diff Summary` / `Change Summary` | 原文引用・変更内容の記録に使用 |
| `Status`（OK/Error/Changed/Needs Attention/Active/Paused/Check Required） | Source側の稼働状態管理にはそのまま使えるが、個別投稿の「確認状態」には転用しにくい（後述） |

### Source Library（既存確認済み24プロパティ相当）

`Source Type`に既に`SNS`という値が存在——SNSアカウントもSource Libraryの1レコードとして登録できる。`Category`、`Region`、`Tier`、`Verification Status`はそのまま活用。

### 監査結論・限界の正直な報告

1. **Region（地域）の専用プロパティがExperience Intelligenceに存在しない**——Descriptionへのテキスト記載で対応する
2. **Source Monitorの`Status`は「Sourceそのものの稼働状態」を表す設計であり、個別のSNS投稿1件ごとの確認状態には意味的にやや無理がある**——個別投稿はSource MonitorのDiff Summary欄に構造化テキストとして記録し、確認状態の管理はExperience Intelligence/Event Calendar側のStatusで行う、という役割分担にする
3. **料金・予約方法・画像URL・食事制限対応文言などに専用プロパティがない**——全てDescription/Metric-Evidence等の既存rich_textへ構造化して記載する。件数が増えた際にフィルタ・ソートがしづらくなる点は将来的な課題として記録する

---

## 2. 収集カテゴリと保存先の対応表

| カテゴリ | 保存先DB | 判定基準 |
|---|---|---|
| 地域の祭り・催し・体験教室（開催日が明確） | **Event Calendar** | 開催日／終了日が特定できるもの |
| 継続開催のスポーツ体験・初心者教室（週次ランニング教室等） | **Event Calendar** | `Repeat Schedule`で表現できる定期性があるもの |
| トレンド（SNSで話題の場所・食べ物等） | **Experience Intelligence**（`Intelligence Type=Trend`） | 特定の開催日がない、継続的な注目度の話題 |
| 新店舗・日本初上陸・リニューアル・期間限定店・ポップアップ | **Experience Intelligence**（`Intelligence Type=Local`または`Opportunity`） | 開店日はあるが「終了する催し」ではなく「存在する店」のため |
| 文化体験・収穫体験（常設プログラム） | **Experience Intelligence**（`Intelligence Type=Culture`） | 予約すればいつでも体験できる常設型 |
| 文化体験・収穫体験（特定日程の単発企画） | **Event Calendar** | 開催日が限定されるもの |
| ヴィーガン・ハラール・豚肉不使用等の食情報 | **Experience Intelligence**（`Intelligence Type=Local`） | 店舗の恒常的な属性情報として扱う |
| SNS・Webで発見した未整理の投稿・更新（一次スクリーニング前） | **Source Monitor** | Experience Intelligence/Event Calendarへ昇格する前の生の発見情報 |
| 継続監視する情報源そのもの（自治体・団体・SNSアカウント等） | **Source Library** | 発見元の登録台帳 |
| Reiが深い記事候補に選んだもの | **Research** | 既存のArticle Briefパイプラインへ接続 |

---

## 3. SNS・Web・公式SourceからNotionまでの収集フロー

```
① Sourceの登録（Source Library）
   自治体／国際交流団体／店舗公式／SNSアカウント（Source Type=SNS含む）等を登録
        │
        ▼
② 発見・監視
   ・Webページ：既存source_watcher.pyのフィンガープリント機構をそのまま使う
   ・SNS：API連携は今回設計せず、まずは定期的な手動/AI確認による発見を想定
        │
        ▼
③ 一次記録（Source Monitor）
   発見した投稿・更新を、原文・URL・発信者・投稿日・発見日を保持したまま記録
   Change Type=New、Status=Check Required 等、既存値で「未整理の発見」を表現
        │
        ▼
④ 分類・昇格判定（人間またはAI提案、最終判断はRei）
   開催日が明確 → Event Calendarへ
   トレンド・新店舗・食情報等 → Experience Intelligenceへ
   このとき、AIはARu掲載適性で除外しない（今回の確定方針を踏襲）
        │
        ▼
⑤ 確認状態の管理（Event Calendar.Status／Experience Intelligence.Status）
   候補発見＝Planning／New、公式確認済み＝Confirmed／Acknowledged、
   中止＝Cancelled、終了・期限切れ＝Completed／Expired
        │
        ▼
⑥ Reiによる深掘り判断
   価値ありと判断したものだけ、既存のRelated Researchリレーションを通じてResearchへ
   （Article Brief・Grounding Checkの既存パイプラインへ接続）
```

---

## 4. 重複判定・更新・終了・閉店検知の設計

### 重複判定

- 新規プロパティは追加せず、Experience Intelligenceの既存`Related Signal`リレーション（Experience Intelligence同士の関連付け）を使い、重複候補同士を明示的にリンクする
- 統合はせず、`Description`に「類似候補: 《タイトル》へのリンクあり、重複の可能性」と明記する運用ルールとする（前回のdry-runと同じ「重複統合しない」方針を踏襲）

### 更新検知

- Webページ：既存`source_watcher.py`のシンハッシュ差分検知をそのまま使用
- SNS：今回は自動更新検知の実装は行わず、定期的な再確認（人間またはAIによる手動チェック）を前提とする設計にとどめる（API連携は将来検討事項として記録）

### 終了・閉店検知

- Event Calendar：`Event Date`が過去日付になったPlanning/Confirmedレコードを検知し、`Status=Completed`へ。中止が確認されたものは`Status=Cancelled`
- Experience Intelligence：`Opportunity Window End`が過去日付になったものを`Status=Expired`へ（**既存のStatus値でそのまま表現可能**）
- いずれも`article_freshness_monitor.py`と同型の小規模スクリプトで実装可能（今回は設計のみ、実装はしない）
- **削除は行わない**——Reiの判断前にレコードを削除せず、状態を移すだけに留める。これは既存のArchived Dateプロパティ（Event Calendar/Experience Intelligenceとも既存）とも整合する

---

## 5. Dry-run（全国8地域、50件）

*別紙：[Nationwide-Intelligence-DryRun-2026-07-20.md](./Nationwide-Intelligence-DryRun-2026-07-20.md)*

---

## 6. Reiが確認するNotion画面のUI案

新規ページ・新規DBは作らず、既存の`ai_command_center.py`と同じ設計思想（marker-bounded自動生成セクション、既存プロパティの集計のみ）でDashboardに新セクションを追加する案。

### 案：「🔎 全国情報収集ダイジェスト」セクション（Dashboard内、新規手動Linked View不要）

- **① 要確認（New/Planning）件数** — Experience Intelligence・Event Calendarの新規候補を地域・カテゴリ別に件数表示（Mission Controlの0件表示ルールを踏襲：0件の地域も隠さず「情報パイプライン未稼働」として表示）
- **② 公式確認済み（Confirmed/Acknowledged）一覧** — 次に深掘りできる候補
- **③ 期限間近（Days Until Opportunity Expires ≤ 7等）** — Experience Intelligenceの既存formulaをそのまま活用した警告表示
- **④ 終了・期限切れ（Completed/Expired/Cancelled）** — 折りたたみ表示、削除はしない
- **⑤ 重複候補のペア一覧** — `Related Signal`でリンクされた組を表示し、Reiが統合/棄却を判断できるようにする

この設計は`editorial_planner.py`/`coverage_analyzer.py`と同じ「既存DBを集計してNotionページを再生成する」パターンの再利用であり、新規のNotion機能（Linked View等API制約のあるもの）には依存しない。

---

## 後続実装による更新（2026-07-20 追記、§6の旧UI案は削除せず以下に保持）

§6で提案した「🔎 全国情報収集ダイジェスト」というDashboard新セクション案は、**その名称・構成のままでは実装されていません。** 実際の後続実装は以下の通りで、§6は歴史的な設計案として残します。

- 実装名称：「ARu編集デスク｜今日の情報」（§6提案の「🔎 全国情報収集ダイジェスト」とは別名称・別構成）
- 実装ファイル：`notion-build/automation/editor_desk_digest.py`
- 実装コミット：`5e1b8d6`（初期実装、`git log`で実在確認済み）、最新修正コミット：`b3d7cb0`
- 現在実装済み（2026-07-20時点）：
  - 🎎 日本文化体験
  - 🥗 食の安心・お店情報
  - 未分類・詳細未確認（Status=New/Reviewing かつ Experience Genre・Dietary Accommodation Typeがともに空欄のレコードを実データ表示。タグは自動設定・推測分類しない）
  - 【テスト】接頭辞で始まる内部テストフィクスチャ2件は、Experience Intelligence内に保持したまま、Dashboard表示からのみ除外（削除・Status変更・プロパティ変更はしていない）
  - ライブ確認件数：文化体験2件／食の安心17件／未分類・詳細未確認14件／運用画面表示合計33件
- 準備中：
  - 今日の新着のクロスDB集計
  - 本日開催・近日開催
  - 変更・中止・期限切れ
  - Research連携・記事候補の整理（「深い記事候補」は自動判定していない。Related Research設定済みという意味の「Research連携済み」件数のみ表示）
  - Rei確認待ちのクロスDB集計

*ARu HQ / Decode Japan — Nationwide Intelligence Collection Design — 2026-07-20*
