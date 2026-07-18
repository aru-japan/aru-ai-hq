<title>ARu Intelligence Operating Manual v4</title>

# ARu Intelligence Operating Manual
### 標準運用手順書（SOP）— ARu Intelligence Version 4（Phase 1〜3実装後）

| | |
|---|---|
| **Status** | Active |
| **Date** | 2026-07-18 |
| **対象読者** | ARuの編集業務を担当する誰でも（編集長Rei本人、新しく加わる編集者、将来この役割を引き継ぐ人） |
| **位置づけ** | [ARu Constitution](./ARu-Constitution.md)が定める「何を優先するか」を、日々の具体的な操作手順に落とし込んだもの。矛盾する場合はConstitutionが優先する。個々のスクリプトの実装詳細は[Automation Scripts](./Automation-Scripts.md)、パイプライン全体の1枚図は[Editorial Workflow](./Editorial-Workflow.md)を参照 |
| **前提** | このマニュアルだけでARuの日次・週次・月次運用ができることを目標に書かれている。旧v1.0（2026-07-12、Phase B1 MVP時代）は完全に置き換え——記載されていた「将来自動化される予定」の項目は、Source Watcher／Editorial Planner／Research Prioritizer／Publishing Center／AI Command Centerとしてすべて実装済み |

---

## 1. Daily Editor Workflow（毎日やること）

**1日の作業は必ずAI Command Centerから始める。** これが編集長の毎日のホーム画面。

### 朝：AI Command Centerを開く

```bash
cd notion-build/automation
python3 source_watcher.py        # 情報源の変化を検知（最初に実行）
python3 ai_command_center.py     # 上記の結果を含めて最新化
```

Notionで「AI Command Center」ページを開き、上から順に確認する：

1. **🎯 Today's Opportunities** — 直近2週間のイベント、本日検知した重要な情報源変化、最近Confirmedされた法改正、季節性の高いResearch候補。今日動くべきことがここに並ぶ
2. **🔴 Critical Updates** — 外部シグナルで要更新フラグが立った記事、本日のCritical情報源変化、重要度MajorでArticle未反映の法改正。**ここに何かあれば他の作業より先に確認する**
3. **📊 Top Research Candidates** — Status=NewのResearchを5軸スコアでランキングした上位5件。今日どのResearchから手を付けるかの参考にする
4. **🚀 Publishing Queue** — Ready to Publishの記事一覧。公開判断が必要なものがここに並ぶ
5. **🕐 Recently Updated Articles** — 直近更新された記事。何が最近動いたかの把握用

その下（Freshness内訳／Duplicate Prevention／外部監視フィード／Source Intelligence／AI分析ページへのリンク）は、上記サマリーの根拠を掘り下げたいときに見る詳細セクション。

### 昼：Editor Homeと個別作業

```bash
python3 editor_home.py
```

「今日、人間が決めること」9項目（Ready to Publish／Published／Needs Update／Publish Approval Pending／Article Review Waiting／Translation Review Waiting／SNS Draft Waiting／Today's Editorial Calendar／Today's Research）を確認し、実際の記事レビュー・翻訳レビュー・SNS確認・Research判断を進める。個別の記事一覧を操作する場合はDashboardの該当Linked Viewを開く（詳細は[Dashboard Setup Guide](./Dashboard-Setup-Guide.md)の14セクション表）。

### 夕方：公開判断と後片付け

1. Publishing Queue（🚀 Ready to Publish）の記事を確認し、実際にARuアプリへ掲載したものは`Publishing Status`を手動で`Published`にする（**AIは自動公開しない。この操作は必ず人間が行う**）
2. 新しく見つけた情報源があれば、Source Libraryに登録する（§4参照）
3. 新しいイベント（祭り・花火大会・季節イベント等）を知ったら、Event Calendarに登録する（§5参照）
4. Criticalとして扱った案件があれば経緯を一言メモしておく（Audit Log DBは未実装のため、現状は手動メモ）

---

## 2. Weekly Maintenance（週次メンテナンス）

```bash
python3 coverage_analyzer.py     # 生活トピック別の記事数・不足分析
python3 editorial_planner.py     # 次に書くべき新規テーマの提案（★1〜5）
```

1. Coverage Analysis（📊）・Editorial Planner（📝）の専用ページを開き、不足トピック・優先テーマを確認する
2. Editorial Plannerが提案したテーマのうち、実際にResearch化するものを選ぶ場合は `python3 editorial_planner.py --generate-research` を実行する
3. Source Libraryの`Last Check Error`が付いているソースがないか確認する（§4のトラブルシューティング参照）
4. Research Prioritizerの上位候補（AI Command Centerの📊セクション）に長期間動きのないものがないか確認する
5. `docs/ARu-Constitution.md`のPending Amendments節に、レビュー待ちの改訂案（Level B：72時間以上経過）がないか確認する

## 3. Monthly Maintenance（月次メンテナンス）

1. Articles全体の`Trust Score`／`Verification Status`を俯瞰し、更新優先度の高い記事を洗い出す
2. Source Libraryの`Importance`／`Check Frequency`が実態と合っているか見直す（新しく重要になった情報源はCriticalへ、更新頻度が下がった情報源はチェック間隔を延ばす）
3. Category／Region別の記事・ソース分布を確認し、著しく手薄な領域がないか確認する（現状Visa・Student・Festivals等は情報源が未整備——[Automation Scripts](./Automation-Scripts.md)の「未着手のカテゴリ」参照）
4. `source_watcher.py`のSimHash閾値（`SIMHASH_CHANGE_THRESHOLD`）が実運用で機能しているか——誤検知が多すぎないか、逆に見逃しがないかを振り返り、必要なら調整する
5. ARu Constitution・AI Agent Constitutionの内容が実態と乖離していないか確認する。乖離があればLevel A/B/Cを判定し改訂プロセスに乗せる（Constitution §20）
6. 月間の公開記事数・カテゴリ別カバレッジ・Source Watcherが検知した変化件数を振り返る

---

## 4. Source Library Management（情報源の管理）

Source Libraryは監視対象の公式情報源を保持する既存DB（Phase 2で拡張）。

### プロパティ一覧

| プロパティ | 型 | 内容 |
|---|---|---|
| `Source Name` | title | 情報源の名称 |
| `URL` | url | フェッチ対象の実URL |
| `Source Type` | select | 政府／自治体／観光協会／ニュース／学術／SNS／コミュニティ／商店街／地域メディア |
| `Category` | select | 22種（Immigration／Visa／Student／Employment／Tax／Pension／Health Insurance／Disaster／Transportation／Tourism／Events／Festivals／Municipal Governments／Universities／Japanese Language Schools／Weather／Culture／Consumer Information／Housing／Banking／Emergency／Trending Topics） |
| `Country` / `Region` / `City` | select / select / rich_text | Japan／9地方区分＋全国・海外／自由入力 |
| `Importance` | select | **Critical／High／Medium／Low —— 監視優先度の正式なフィールド。旧`Tier`より優先して使う** |
| `Check Frequency` | select | Daily／Weekly／Monthly／Quarterly |
| `Status` | select | Active（監視対象）／Inactive／Under Review |
| `Last Checked` / `Last Content Hash` / `Last Check Error` | date / rich_text / rich_text | `source_watcher.py`が自動更新。手動で触らない |

### ソースを1件追加する

Notion上でSource Libraryに新規ページを作成し、最低限`Source Name`・`URL`・`Status=Active`・`Importance`・`Check Frequency`を設定する。次回`source_watcher.py`実行時に自動的にベースライン確立（1回目は「変化なし」判定、誤検知しない設計）される。

### 一括で追加する（数十〜数百件）

```bash
python3 bulk_import_sources.py --csv path/to/your.csv
```

CSVの列：`Source Name,URL,Source Type,Category,Country,Region,City,Importance,Check Frequency`（`Source Name`と`URL`は必須、他は省略可・省略時は既定値を適用）。テンプレートは`notion-build/automation/data/source_library_import_template.csv`、実在確認済みの実データ例は`source_library_seed.csv`を参照。**同じURLは自動でスキップされる（重複作成されない）**。CSV内の新しいCategory/Country/Region/Importance値は自動でSelectの選択肢に追加される。

### ソースを止める

`Status`を`Inactive`にする（**削除しない**）。`source_watcher.py`は`Status=Active`のみを対象にする。

---

## 5. Event Calendar Management（イベントカレンダーの管理）

Event Calendar（既存DB）は祭り・花火大会・季節イベント等を管理し、`today_opportunities.py`経由でAI Command Centerの「🎯 Today's Opportunities」に直近14日以内のものが自動表示される。

### 主なプロパティ

| プロパティ | 内容 |
|---|---|
| `Event Name` | イベント名 |
| `Type` | 祭り／花火大会／フードフェス／蚤の市／マルシェ／文化イベント／自治体イベント／季節イベント／期間限定イベント |
| `Event Date` | 開催日（Today's Opportunitiesの近日判定に使われる） |
| `Status` | Planning／Confirmed／Promoting／Completed／Cancelled（**Cancelled・CompletedはToday's Opportunitiesの対象外**） |
| `Location` | 開催場所 |
| `Best Season` / `Season` | 春／夏／秋／冬／通年 |
| `Recommended Audience` | 観光客／在住外国人／留学生等 |

### 運用のコツ

現状Event Calendarに実データがほとんどないため、Today's Opportunitiesの表示が空になりがち。**実際に知っているイベント（地域の祭り、観光キャンペーン等）を積極的に登録すると、翌日以降のTodays Opportunitiesにすぐ反映される。** Status=Cancelledにした場合も削除せず記録として残す。

---

## 6. Source Watcher Workflow（情報源監視の仕組み）

```bash
python3 source_watcher.py
```

### 何をしているか

1. Source Libraryから`Status=Active`かつ`Check Frequency`の間隔が経過した（チェック期限が来た）ソースを、`Importance`の高い順（Critical→Low）に抽出（1回の実行あたり最大50件）
2. 各URLをフェッチ（stdlib `urllib`のみ、robots.txt確認あり、15秒タイムアウト）
3. 本文テキストからSimHash指紋（64bit）を計算し、前回値とのハミング距離を比較
4. **ハミング距離が2ビット以下なら「変化なし」**（広告・タイムスタンプ・訪問者数等のノイズは無視される設計）。それを超えたら「変化あり」と判定し、Source Monitorレコードを新規作成（`Impact Level`はそのソースの`Importance`から、`Diff Summary`と`Update Classification`はAIが生成）
5. 初回チェック（保存済み指紋なし）では誤って「変化あり」と出さない（ベースライン確立のみ）

### 変化を検知したら（編集者の判断）

- Source Monitorに新しいレコードができ、Dashboardの「⑦ Source Monitor Alerts」「🔴 Critical Source Updates」（Importance=Criticalのみ）に表示される
- **`source_watcher.py`自体はLaw Update／Research／Article／Translation／SNS Queueへは一切書き込まない。** 政府・自治体系の変化はフラグが立つだけで、Law Updateレコードを作るかどうかは必ず人間が判断する
- 一般的な変化は、別途`sync_source_monitor_to_research.py`を実行するとResearchドラフトが自動作成される（Status=New、Discovery Method=Source Monitor）。これも編集者が任意のタイミングで実行する

### 誤検知に気づいたら

閾値（`source_watcher.py`内の`SIMHASH_CHANGE_THRESHOLD`、現在2）は実データに基づく初期値。特定のソースで誤検知が頻発する場合、月次メンテナンス（§3）で調整を検討する。

---

## 7. AI Command Center Workflow（AI Command Centerの使い方）

```bash
python3 ai_command_center.py
```

日次運用（§1）で毎朝実行する前提。5つの主要セクション＋詳細セクションの意味は以下のとおり：

| セクション | 何を見るか | 出典 |
|---|---|---|
| 🎯 Today's Opportunities | 今日動くべき機会（イベント・情報源変化・法改正・季節性Research） | `today_opportunities.py` |
| 🔴 Critical Updates | 最優先で確認すべき変化の合算 | Freshness＋Source Monitor＋Law Update |
| 📊 Top Research Candidates | 優先順位の高いResearch上位5件 | `research_prioritizer.py` |
| 🚀 Publishing Queue | 公開判断待ちの記事 | Publishing Status=Ready to Publish |
| 🕐 Recently Updated Articles | 直近更新された記事 | Articles.Updated Date |
| 🔴 Freshness内訳 | 更新が必要な記事の内訳（外部シグナル／時間経過） | Article Freshness Monitor |
| 🛡 Duplicate Prevention | 本日の生成・重複スキップ件数 | Duplicate Guard |
| 📡 外部監視フィード | Source Monitor／Law Update／Event Calendarの件数 | 各DB |
| 🌐 Source Intelligence | 監視対象ソース数・本日の変化・エラー中のソース | Source Library／Monitor |
| 🧭 AI分析ページへのリンク | Coverage Analysis／Editorial Plannerへの導線 | ポインタのみ |

**Editor Homeとの違い**：Editor Homeは「今日、人間が決めること」9項目に特化した軽量版。AI Command Centerはそれに加えてAIが検知・提案した内容までを含む、より広い「編集長の毎日のホーム画面」。基本的にはAI Command Centerを開けば1日の作業が始められる。

---

## 8. Publishing Workflow（公開フロー）

```
Research → Article（Update Level判定・9セクションテンプレート・Priority/Urgency自動継承）
  → Article Review（5観点スコアリング）
  → Translation → Translation Review（5観点）
  → SNS×3 → SNS Review（5観点）
  → Publish Gate（enforce_publish_gate.py） → Publishing Center（publishing_center.py）
  → Dashboard「🚀 Ready to Publish」 → 編集長が手動でPublished判定
```

### 生成コマンド

```bash
python3 generate_article_pipeline.py article --keyword "..."      # 単発
python3 bulk_generate_articles.py                                  # TOPICSリストを一括生成
```

生成**前**に`duplicate_guard.py`が「1 Research Topic = 1 Article」を強制する。同じテーマの記事を複数作りたくなったら、**新規作成ではなく既存Articleの更新**が正しい運用。

### Update Levelによるゲート

- **Level 1**（イベント・観光・文化・生活情報等）：AIレビューPass＋文化的補足完了で、Translation.Publish Approvalが自動で`Not Required`になってよい
- **Level 2・3**（法律・ビザ・税金・医療・重要な法改正等）：AIスコアが何点でも、**Publish Approvalは必ずPendingのまま**。人間の承認を経て初めて先へ進める

### Publishing Statusのライフサイクル

`Draft`→`Ready to Publish`→（人間が）`Published`。公開済み記事が鮮度切れになると自動で`Needs Update`へ、鮮度回復で自動的に元へ戻る。`Archived`／`Duplicate`は削除ではなく退避——**削除は一切行わない**。

**AIは公開そのものを実行しない。** `Published`への変更は常に人間が行う（ARuアプリへの実投稿APIが存在しないため）。

---

## 9. Troubleshooting Guide（トラブルシューティング）

| 症状 | 原因・対処 |
|---|---|
| `ConnectionResetError: [Errno 54]`／`URLError`が出て途中で止まる | AI Gateway呼び出し中の一時的なネットワーク瞬断。**同じコマンドをもう一度実行すれば通常成功する**（このセッション中も複数回発生し、すべて再実行で解消した既知のパターン） |
| スクリプトが何分経っても終わらない（CPU使用率がほぼ0%） | ネットワーク呼び出しがハングしている可能性。`ps aux`でプロセスを確認し、CPU時間がほぼ増えていなければ`kill`して再実行する |
| `source_watcher.py`で特定のソースが毎回`ERROR`になる | Source Libraryの`Last Check Error`列を確認する。`HTTP 403`等はrobots.txtブロックまたはBot対策の可能性——そのソースは自動フェッチに向いていない（例：外務省サイトはWebFetch/urllibからの自動アクセスを拒否する） |
| Dashboardのセクションが空・古いまま | Notion公開APIはLinked Viewの設定を読み書きできないため、フィルタ変更や新規View追加は[Dashboard Setup Guide](./Dashboard-Setup-Guide.md)の手順で手動設定する必要がある |
| Archivedにした記事がCritical Updates等に出続ける | 既知の制約：Archive時に`Freshness Status`が自動クリアされない。新しいクエリを書く際は`Status`が`Archived`でないことを必ず条件に含める（詳細は[AI-Handover.md](./AI-Handover.md)のKnown Limitations） |
| 重複記事を作ってしまった／作りそうになった | `duplicate_guard.py`が生成前に自動ブロックするはずだが、心当たりがあれば`duplicate_prevention_report.py`を実行して本日の生成・スキップ状況を確認する |
| `.env`の値が読めない・スクリプトが`KeyError`で落ちる | `notion-build/.env.example`と見比べ、必要な`_DB_ID`／`_PAGE_ID`が揃っているか確認する。**`.env`の中身は絶対に表示・コミットしない** |
| Notionのスキーマを変更したのに反映されない | 各スクリプトの`ensure_schema()`は起動のたびに実行される（べき等）。それでも反映されない場合はNotion側のプロパティ名の完全一致（大文字小文字・全角半角含む）を確認する |

---

## 10. Backup and Recovery（バックアップと復旧）

**詳細な手順は[Recovery-Guide.md](./Recovery-Guide.md)（10ステップ＋緊急時シナリオ）を参照。ここでは要点のみ。**

- **コードのバックアップ**：GitHub（`git push`）が唯一の実質的なバックアップ。ローカルの変更は必ずコミット・プッシュする習慣を保つ
- **Notionデータのバックアップ**：**外部バックアップは存在しない。** Notion自体のTrash／Version History（一般的に30日以内）が唯一の実質的な復旧手段。誤って重要なレコードを削除した場合は、Notionの操作履歴から復元を試みる
- **DBスキーマの再構築**：`notion-build/create_*.py`で再現可能（ただし実データは戻らない）
- **`.env`のバックアップ**：`.env`自体はGit管理外（`.gitignore`済み）。APIキー・トークンをローテーションした場合は、手元で安全に控えておく（このマニュアル・チャット・コミットには絶対に書かない）
- **セッション・PC・APIキーを失った場合**：[Recovery-Guide.md](./Recovery-Guide.md)のEmergency Recoveryへ。読む順番は[START-HERE.md](./START-HERE.md)→本マニュアル→[AI-Handover.md](./AI-Handover.md)

---

## 11. First Week Checklist（運用開始 最初の1週間）

- [ ] **Day 1**：Dashboardの14番目のセクション「🔴 Critical Source Updates」Linked Viewが実際に設定済みか確認する（Notion公開APIでは設定状況を読み取れないため、目視確認が必要）
- [ ] **Day 1**：Source Libraryの全レコードに`Category`／`Importance`が設定されているか確認する（未設定のレコードがあれば手動で埋める）
- [ ] **Day 1〜3**：毎朝`source_watcher.py`→`ai_command_center.py`を実行し、Today's OpportunitiesとCritical Updatesを確認する習慣をつける
- [ ] **Day 2〜4**：実際に知っている近日イベント（祭り・花火大会・季節イベント等）をEvent Calendarへ最低数件登録する（Today's Opportunitiesが実データで機能し始める）
- [ ] **Day 3〜5**：Source Libraryに未着手カテゴリ（Visa／Student／Festivals／Municipal Governments等）の情報源を数件追加する
- [ ] **End of week**：1週間の実運用を踏まえ、定期実行（cron／launchd）を導入するか判断する
- [ ] **End of week**：`Update Classification`が実際の変化検知で正しく機能しているか、初回の実例を確認する

---

## 12. Production Best Practices（運用上の原則）

1. **削除しない、Archiveする。** 記事・情報源・重複レコードのいずれも、削除ではなくStatus変更で退避する
2. **AIに公開・法的判断をさせない。** `Published`判定、Law Updateレコードの作成はいずれも人間が行う（Constitutionの人間レビュー最優先原則）
3. **秘密情報を絶対にコミット・表示しない。** コミット前に必ず`git diff --cached | grep -iE "sk-ant|sk-proj|_API_KEY=.+|NOTION_TOKEN=.+"`で確認する（差分なし＝grep終了コード1が正常）
4. **新しいクエリはArchivedを除外する。** 既知の制約（§9参照）に対する標準対策
5. **コード変更後は回帰テストを実行する。** 最低限`article_freshness_monitor.py`／`publishing_center.py`／`enforce_publish_gate.py`／`coverage_analyzer.py`／`editorial_planner.py`／`duplicate_prevention_report.py`／`source_watcher.py`を実データに対して再実行し、既存の挙動が変わっていないことを確認する
6. **Source Libraryを急拡大させすぎない。** 政府・公共サイトへの配慮として、`source_watcher.py`は1回の実行あたり最大50件・リクエスト間1.5秒の間隔を守る設計。CSV一括登録も段階的に行う
7. **新規データベースを勝手に作らない。** 既存DBの拡張・新規プロパティで対応できないか必ず先に検討する（Region Master等、意図的にDeferredのままにしているDBがある）
8. **ドキュメントを実態に合わせ続ける。** 新しいスクリプト・セクションを追加したら、[Automation Scripts](./Automation-Scripts.md)・本マニュアル・[Editorial Workflow](./Editorial-Workflow.md)のいずれかを同じセッション内で更新する（本マニュアルのv1.0が6日間放置され実態と乖離した反省を踏まえる）
9. **常に正直に報告する。** テスト件数・実データの偏り・未検証の項目は、都合よく見せず実態どおり記録する

---

*ARu HQ / Decode Japan — ARu Intelligence Operating Manual v4.0 — 2026-07-18*
