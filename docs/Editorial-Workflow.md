<title>Editorial Workflow</title>

# Editorial Workflow
### ARu HQ — 発見から公開までの完全な流れ（ARu Intelligence Phase 3）

| | |
|---|---|
| **Status** | Active |
| **Date** | 2026-07-18 |
| **位置づけ** | これまで`docs/AI-Handover.md`のArchitecture節・各Automation Scriptsのセクションに分散していた「編集ワークフロー」の全体像を、1つの文書に統合したもの。個々のスクリプトの実装詳細は[Automation Scripts](./Automation-Scripts.md)を参照 |

---

## 全体像（1枚図）

```
① 情報源監視                          ② 企画・優先順位付け
Source Library ──▶ source_watcher.py ──▶ Source Monitor
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
       sync_source_monitor_to_    article_freshness_monitor.py   （編集者が手動判断）
       research.py（Research起票）  （既存記事へのフラグ立て）      Law Update起票

Research（Status=New） ──▶ research_prioritizer.py（優先順位スコアリング）
Coverage Analyzer（不足分析） ──▶ editorial_planner.py（新規テーマ提案・★評価）
                    │
                    ▼
③ 編集者レビュー（人間が必ず判断）
AI Command Center（🎯 Today's Opportunities／🔴 Critical Updates／
                    📊 Top Research Candidates／🚀 Publishing Queue／
                    🕐 Recently Updated Articles）
                    │
                    ▼
④ コンテンツ生成パイプライン
Research → Article（Update Level判定・9セクションテンプレート）
  → Article Review → Translation → Translation Review → SNS×3 → SNS Review
                    │
                    ▼
⑤ 公開ゲート（人間承認、Update Level 2/3は例外なし）
Publish Gate（enforce_publish_gate.py） → Publishing Center
  → Dashboard「🚀 Ready to Publish」→ 編集長が手動でPublished判定
                    │
                    ▼
⑥ 公開後の鮮度管理（①へ環流）
article_freshness_monitor.py が公開済み記事を継続監視 → Needs Update検知
  → Publishing Center が自動でPublishing Status=Needs Updateへ
```

**この全体を貫く一線**：AIはどの段階でも**公開そのものを実行しない**。ARuアプリへの実際の掲載（Publishing Status=Published）は常に人間の操作であり、実投稿APIも存在しない。Update Level 2・3（法律・ビザ・税金・医療等）は、AIレビューが何点でも人間の承認を経るまでPublish Approval=Pendingのまま。この制約はConstitution §9/§13としてコードで強制されている。

---

## ① 情報源監視（ARu Intelligence Phase 1/2）

| 段階 | スクリプト | 内容 |
|---|---|---|
| ソース管理 | （手動 + `bulk_import_sources.py`） | Source Library（既存DB）に、Category（22種）／Country／Region／City／Importance（Critical/High/Medium/Low）付きで公式情報源を登録。CSV一括登録に対応 |
| 変化検知 | `source_watcher.py` | `Check Frequency`に従いURLを定期フェッチ、SimHash近似指紋＋ハミング距離比較で本物の変化のみ検知（広告・タイムスタンプ・訪問者数等のノイズは無視）。変化があればSource Monitorレコードを作成し、AIが`Diff Summary`と`Update Classification`（11分類）を生成 |
| 下流への伝播 | `sync_source_monitor_to_research.py` | Change Detected=trueだが未着手の変化から、Researchドラフトを自動作成（`Discovery Method=Source Monitor`） |
| 記事への反映 | `article_freshness_monitor.py` | Source Monitor／Law Update／Event Calendarの変化を、関連するArticleへ`Freshness Status=Needs Update`として強制反映（`Source Library.Related Research`経由の関連付けも含む） |

**政府・自治体系情報源の変化は、Law Updateの自動作成をしない。** 人間の編集者が、Source Monitorのフラグを見て必要と判断した場合にのみLaw Updateレコードを作成する（Constitutionの人間レビュー最優先原則）。

---

## ② 企画・優先順位付け（Coverage Analyzer / Editorial Planner / Research Prioritizer）

| スクリプト | 答える問い | ロジック |
|---|---|---|
| `coverage_analyzer.py` | 生活トピック別に見て、記事は十分に揃っているか？ | Life Topics（22トピック）別の記事数・鮮度・Review待ちを集計し、AIが「生活への影響度」の視点で不足トピックを判定 |
| `editorial_planner.py` | 次に何を新しく書くべきか？ | Coverage Analyzerのデータ×Life Topic Impact tierの決定論的ロジックで★1〜5の優先プランを生成。`--generate-research`で選んだプランをResearchレコードとして自動作成 |
| `research_prioritizer.py`（Phase 3新規） | **既にあるResearch（Status=New）の中で、どれから手を付けるべきか？** | Freshness／Foreign Resident Value／Tourism Value／Seasonal Relevance／Premium Potentialの5軸、各0〜20点（計100点満点）で採点。すべてResearchの既存プロパティ（Category／Season／Usage Scope／Evidence Level／作成日時）から決定論的に算出——追加のAI呼び出し・追加スキーマは一切なし |

**Editorial Plannerが「何もないところに新しいテーマを提案する」のに対し、Research Prioritizerは「もう手元にあるResearchの順番を決める」役割**。両者は補完関係にあり、どちらか一方に統合すると意味が曖昧になるため別スクリプトのまま維持している。

---

## ③ 編集者レビュー（AI Command Center = 編集長の毎日のホーム画面）

`ai_command_center.py`（Phase 3で「編集長が毎日最初に見るページ」として再構成）が表示する5セクション：

| # | セクション | 出典 |
|---|---|---|
| 🎯 | Today's Opportunities | `today_opportunities.py`（Event Calendar近日開催分＋本日のCritical/High情報源変化＋直近ConfirmedのLaw Update＋季節性の高いResearch候補、4つの既存システムを統合） |
| 🔴 | Critical Updates | 外部シグナルで要更新フラグの記事＋本日のCritical情報源変化＋重要度MajorでArticle未反映のLaw Update |
| 📊 | Top Research Candidates | `research_prioritizer.py`の上位5件 |
| 🚀 | Publishing Queue | Articles.Publishing Status=Ready to Publish（`editor_home.py`と同一フィルタ、数値の食い違いを防ぐ） |
| 🕐 | Recently Updated Articles | Articles.Updated Date降順、上位5件 |

このページより下には、Phase 1/2から引き続くFreshness内訳・Duplicate Prevention・外部監視フィード・Source Intelligenceの詳細セクションが残っており、サマリーの根拠を掘り下げたい場合に参照できる。

**Editor Home（`editor_home.py`）との関係**：Editor Homeは「今日、人間が決めること」9項目（Ready to Publish／Published／Needs Update／Publish Approval Pending等）に特化した軽量ページとして引き続き存在する。AI Command Centerは、それに加えてAIが検知・提案した内容までを含む、より広い「編集長の毎日のホーム画面」という位置づけ。どちらか一方で完結させたい場合はAI Command Centerを開けばよい。

Dashboard（13＋1セクションのLinked Database View）は、これらの計算済みサマリーの「元データを直接触りたいとき」に使う一次情報源として引き続き機能する。

---

## ④ コンテンツ生成パイプライン

```
Research → Article（Update Level判定・9セクションテンプレート、Priority/Urgencyを自動継承）
  → Article Review（5観点スコアリング）
  → Translation → Translation Review（5観点）
  → SNS×3（Instagram/Threads/X） → SNS Review（5観点）
```

`generate_article_pipeline.py`（単発）／`bulk_generate_articles.py`（一括）のいずれも、生成**前**に`duplicate_guard.py`が「1 Research Topic = 1 Article」を強制。生成**後**に`render_article_layout.py`がArticleページ本文を9セクションの実ブロックとして自動描画する（Bodyプロパティ自体は不変）。

---

## ⑤ 公開ゲート

- `enforce_publish_gate.py`：Status=Published／Publishing Status=PublishedなのにQA未完了・Update Level 2/3で人間未レビューの記事を検知し、強制的にHuman Reviewへ差し戻す
- `publishing_center.py`：Publishing Status（Draft/Ready to Publish/Published/Needs Update/Archived/Duplicate）を一元管理。**Publishedへの変更は常に人間が行う**——ARuアプリへの実投稿APIが存在しないため、Publishedは「人間が手動掲載済み」という管理状態として定義されている

---

## ⑥ 公開後の鮮度管理（環流）

`article_freshness_monitor.py`は公開済み記事も継続的に監視し、Update Levelごとのレビュー間隔超過や外部情報源の変化を検知すると`Freshness Status=Needs Update`にする。`publishing_center.py`はこれを検知して自動的に`Publishing Status=Needs Update`へ切り替え、鮮度が回復すれば元の状態へ自動復帰する。この環流により、①の情報源監視で検知した変化が、最終的に公開済みコンテンツの更新判断まで一直線につながる。

---

## 全自動化スクリプト一覧（実行順の目安）

日次で実行する場合の推奨順序（すべて`notion-build/automation/`、スケジューリング自体は未設定・手動実行が前提）：

1. `source_watcher.py` — 情報源監視・変化検知
2. `sync_source_monitor_to_research.py` — 変化からResearch起票（編集者の判断で実行）
3. `article_freshness_monitor.py` — 記事の鮮度チェック・強制フラグ
4. `publishing_center.py` — Publishing Status同期
5. `enforce_publish_gate.py` — 公開ゲート違反チェック
6. `coverage_analyzer.py` / `editorial_planner.py` — 企画会議（週次程度でも可）
7. `duplicate_prevention_report.py` — 重複防止レポート
8. `ai_command_center.py` — 編集長の毎日のホーム画面を最新化（**1日の作業はここから始める**）
9. `editor_home.py` — 人間の意思決定項目サマリー

詳細な実行方法・実データでのテスト結果は各スクリプトについて[Automation Scripts](./Automation-Scripts.md)を参照。

---

*ARu HQ / Decode Japan — Editorial Workflow v1.0 — 2026-07-18*
