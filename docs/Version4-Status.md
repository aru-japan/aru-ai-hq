<title>ARu Version 4 Current Status Report</title>

# ARu Version 4 Current Status Report

| | |
|---|---|
| **Date** | 2026-07-14 |
| **対象** | Version 4（Enterprise）準備状況のスナップショット |
| **最新Commit** | `2e1f4ce` |
| **位置づけ** | [Roadmap](./Roadmap.md)・[AI-Handover](./AI-Handover.md)・[README](../README.md)との整合性を確認済み |

> このレポートは特定時点のスナップショット。「本日」は2026-07-14を指す。数値はすべてNotion実データへの実クエリで取得したもので、推測値ではない。

---

## 1. 本日実装した機能（2026-07-14）

### ① ARu公式記事テンプレート統一（9セクション構成）
記事本文の構成をQuestion／Basic Answer／More Details／Why Does Japan Do This?／Practical Steps and Cautions／Latest Information／ARu Tip／Related Questions／Mentor Supportの9セクションに統一。Update Levelに関わらず全記事に`Verification Status`・`Last Verified Date`を保存するようにした（`generate_article_pipeline.py`）。

### ② 15記事の一括生成
`bulk_generate_articles.py`（旧`bulk_generate_20_articles.py`をリネーム・汎用化）で新規15テーマを一括生成。最初の1記事のみ先にテスト実行し、テンプレート出力を人手で確認してから残り14記事を実行する手順を踏んだ。Research／Article／Article Review／Translation／Translation Review／SNS×3／SNS Review×3のフルパイプラインを実行し、Update Level 2・3のPublish Approvalは例外なくPendingを維持した。

### ③ Article Freshness Monitor（Version 4準備）
`article_freshness_monitor.py`を新規実装。既存Articles DBに5プロパティ（`Freshness Status`／`Days Since Verification`／`Freshness Urgency Score`／`Freshness Checked Date`／`Freshness Note`）を追加し、新規データベースなしで運用。

- Update Levelごとのレビュー間隔超過を検知（Level 1=90日／Level 2=30日／Level 3=14〜30日・設定可能）
- Law Update／Source Monitor／Event Calendarの変化検知を、既存Relationのみを辿って（新規Relation追加なし）関連記事に反映し、時間経過を待たずAIの推奨コメント付きで強制的に再レビュー対象化
- Dashboard最上部に「🔴 Update Needed」セクションを追加、`daily_briefing.py`にも同内容をセクション0として反映

53記事全件に対して実行し、Fresh 51件／Needs Update（外部シグナル起因）2件を正しく検知（詳細は[Automation Scripts](./Automation-Scripts.md)）。

### ④ Coverage Analyzer（Version 4準備）
`coverage_analyzer.py`（＋`life_topics.py`／`backfill_life_topics.py`）を新規実装。既存の`Category`（Update Level判定用、変更していない）とは別に、外国籍の方の生活ニーズに基づく**Life Topics**（22トピック、Multi-select）をArticlesに新設し、既存53記事全件をAIで分類した。

- **①カテゴリ分析**：Life Topicごとに記事数／直近更新日／Freshness状況／Update Level構成／Review待ち件数を集計（既存Category別の参考表も併記）
- **②不足分析**：件数だけでなく「生活への影響度・緊急性」の視点でAIが不足トピック・優先トピックを判定し、おすすめ新規記事テーマを10件生成
- Dashboard最上部（🔴 Update Neededの直下）に「📊 Coverage Analysis」を追加。詳細は専用Notionページ（Table Blockとして毎回上書き生成、Linked View手動設定は不要）

**実行結果（実データ・実API、2026-07-14）**：`介護`／`妊娠・出産`／`高齢者支援`／`障がい者支援`が0件、`教育`／`ニュース・トレンド`が1件のみと判明。AIは医療・健康／妊娠・出産／介護／障がい者支援を優先トピックとして提案し、質問形式の新規テーマ案10件を生成した（詳細は[Automation Scripts](./Automation-Scripts.md)）。

### ⑤ Editorial Planner（Version 4 Phase 2）
`editorial_planner.py`を新規実装。Coverage Analyzerが「何が足りないか」を示すのに対し、Editorial Plannerは「次に何を書くべきか」を編集会議でそのままアサインできる粒度まで具体化する。

- **検出・優先度算出は決定論的**：`life_topics.py`に追加した`LIFE_TOPIC_IMPACT`（Critical／High／Medium／Low）と現在の記事数を組み合わせ、影響度別の許容記事数を超えていないトピックを★1〜5でプランに含める。AIは各トピックのReason・タイトル案・Expected Categoryの生成のみ担当し、優先順位そのものはAIに委ねない
- **Expected Update Level**：AIには聞かず、AIが提案したExpected Category（7値のうち無効な場合はフォールバック）を既存の`compute_update_level()`にそのまま渡して算出——ロジックの二重管理を避けた
- **Generate Research アクション**：`--generate-research`（＋`--topics`／`--limit`で選択）で、プラン項目の提案タイトルをResearchレコードとして自動作成。新規プロパティは追加せず、Research DB既存の`Status=New`／`Evidence Level=AI Suggested`／`Discovery Method=Gap Engine`をそのまま利用するため、作成したResearchはDashboard「⑥ Today's Research」に自動的に現れる
- Dashboard「📊 Coverage Analysis」の直下に「📝 Editorial Planner」セクションを追加

**実行結果（実データ・実API、2026-07-14）**：53記事に対して実行し10トピックがプランに検出された（★5：妊娠・出産／★4：介護・高齢者支援・障がい者支援・医療・健康・防災・緊急対応／★3：子育て／★2：教育・年金・社会保険／★1：ニュース・トレンド）。`--generate-research`を実行し、実際に**Researchレコード19件**を新規作成（Category／Priority／Urgencyがすべて正しく設定されていることを実データで確認）。

---

## 2. 現在のコンテンツ量（Notion実データ、2026-07-14時点）

| データベース | 件数 | 内訳 |
|---|---|---|
| **Articles（記事数）** | **53件** | Status: AI Draft 52／Draft 1　｜　Update Level: L1=37／L2=16　｜　Article Review: Pass 51／Needs Revision 1／未レビュー 1　｜　Freshness Status: Fresh 51／Needs Update 2 |
| **Research** | **71件** | Status: Converted 52（Articleへ転換済み）／New 19（すべてEditorial Plannerが本日提案、Discovery Method=Gap Engine、レビュー待ち） |
| **Translation** | **54件** | Publish Approval: Pending 15／Not Required 39　｜　Quality Result: Pass 52／Needs Revision 1／未レビュー 1 |
| **SNS Queue** | **160件** | Platform: X 53／Threads 53／Instagram 54　｜　Status: 全件Draft　｜　Review Result: Pass 152／Needs Revision 7／Fail 1 |

**注**：Articles(53)×3プラットフォーム=159に対しSNSは160件、Translation(54)がArticles(53)より1件多い。これは今回の一括生成以前に存在していた個別テストレコード（例：「【テスト】在留カードの更新手続きガイド」関連）による差分で、パイプライン自体の不整合ではない。念のため要確認（下記「現在の課題」参照）。

### Life Topic別カバレッジ（最も手薄な10トピック、Coverage Analyzer実データ）

| Life Topic | 記事数 |
|---|---|
| 介護 | 0 |
| 妊娠・出産 | 0 |
| 高齢者支援 | 0 |
| 障がい者支援 | 0 |
| 教育 | 1 |
| ニュース・トレンド | 1 |
| 医療・健康 | 2 |
| 子育て | 2 |
| 防災・緊急対応 | 2 |
| 年金・社会保険 | 3 |

全22トピックの完全な内訳は[Coverage Analysis Notionページ](https://www.notion.so/39d157f0f15d8151ae56dcb0e25ac853)（`COVERAGE_ANALYSIS_PAGE_ID`、実行のたびに上書き更新される）を参照。

---

## 3. Version 4 完成率

Version 4本体は**前提条件（Pilot Operation 7日間の実運用完了）を満たしておらず、正式着手前**（[Roadmap](./Roadmap.md#version-4--enterprise)）。単一の「％」で表すと実態より進んでいるように見えてしまうため、3層に分けて評価する。

| 層 | 内容 | 進捗 |
|---|---|---|
| **前提条件** | Version 3.5 Pilot Operation（7日間実運用） | **2/7日（約29%）** |
| **Version 4準備作業**（技術的土台） | Article Freshness Monitor、Coverage Analyzer、Editorial Planner | **3/3件 実施済み（100%）**（現時点でRoadmapに明記された準備作業はこの3件） |
| **Version 4本体**（Roadmap記載5項目：Usage Scope実運用／自治体・観光協会・企業とのデータ連携／JNTO・Visit Japan連携／企業向けダッシュボード／Mentorネットワーク本格拡大） | いずれも対外的な契約・意思決定を伴う | **0/5件（0%）** |

**総合評価**：技術的な土台固め（Freshness Monitor）は計画通り先行実装できたが、Version 4本体は実装だけでは進められない項目が大半を占める。次のゲートはPilot Operation Day 3〜7の完走と、その後の対外的な方針確認。**全体としては「本体着手前」であり、大まかな目安としては一桁%〜10%程度**（前提条件の進捗と、技術準備1件の完了を反映した粗い目安であり、対外交渉が絡む項目のため精緻な%算出はできない）。

---

## 4. 現在の課題

1. **Pilot Operation Day 3〜7が未実施**：7日間のうち2日のみ完了。Version 4着手前の「完了条件」（7日分のOperation Checklist記入＋最終振り返り）にまだ届いていない
2. **スケジューリング未設定**：Freshness Monitor・daily_briefing等はすべて手動実行。cron/launchd等の定期実行が未導入
3. **Article.Statusの自動昇格が未実装**：Translation側のPublish Approvalゲートは実証済みだが、Article本体のStatus（AI Draft→Published）を進める自動化がなく、52件がAI Draftのまま滞留
4. **人間レビュー待ちの滞留**：Article Needs Revision 1件、Translation Needs Revision 1件、SNS Needs Revision 7件／Fail 1件が未対応
5. **未レビューレコードが残存**：Article Review Result・Translation Quality Resultにそれぞれ1件、値が空（None）のレコードがある。過去のテストレコード起因の可能性が高いが未確認
6. **Freshness Monitorで検知された2件が未対応**：外部シグナル（入管法改正・情報源変化）により再レビュー対象となった記事が、まだ実際にレビューされていない
7. **SNS実投稿は未実装**：Draft生成・レビューまでで、実際のプラットフォームへの投稿は手動または未着手
8. **外部通知の仕組みがない**：Critical Gap等の重要検知をSlack/メール等へ通知する機能は未実装
9. **Deferred中の6DB**（Language Master／Region Master／Mentor／AI Agents／Prompt Library／Automation）は引き続き未着手（方針通り、削除ではなく保留）
10. **コンテンツの偏りが明確に**：Coverage Analyzerにより、`介護`／`妊娠・出産`／`高齢者支援`／`障がい者支援`が0件、`教育`が1件のみと判明。現状53記事の大半が「文化・マナー」「行政手続き・相談窓口」に偏っており、外国籍の方の生活に不可欠な医療・福祉系トピックが手薄
11. **ARu Constitutionの改訂提案が承認待ち**：Pending Amendments（Level B、提案日2026-07-14、発効予定2026-07-17以降）。ARu公式テンプレートとArticle Freshness Monitorの実態を§4・§11へ反映する内容で、編集長の承認待ち
12. **Editorial Plannerが提案した19件のResearchが未レビュー**：`Status=New`のままDashboard「⑥ Today's Research」に滞留中。優先度（Priority/Urgency）は機械的に設定されているが、実際に記事化するかどうかはRei自身の判断が必要

---

## 5. 明日やるべきこと（2026-07-15予定）

1. **Pilot Operation Day 3を実施**（[Pilot Operation Guide](./Pilot-Operation-Guide.md)・[Operation Checklist](./Operation-Checklist.md)に沿って9工程を実行し記録）
2. **Article Freshness Monitorの2回目実行**：Days Since Verificationが正しく増分するか、Freshness Checked Dateが更新されるかなど、日次運用としての耐久性を確認
3. **滞留中のレビュー対応**：Needs Revision/Fail状態のSNS 8件・Article 1件・Translation 1件を人間が確認し、Publish可否を判断
4. **外部シグナル起因の要更新記事2件を実際に再レビュー**し、Freshness Monitor→人間レビューのワークフローが実運用でも機能することを確認
5. **未レビュー（None）の2件を調査**し、過去のテストレコードかどうかを特定・整理
6. **Editorial Plannerが作成した19件のResearch（★5：妊娠・出産を最優先）から2〜3件を選び、実際に記事化**する。Research自体は既に`Status=New`で存在するため、`generate_article_pipeline.py article --keyword "..."`で直接拾える（Statusを`Converted`へ変更してから実行）。9セクションテンプレート・3段レビュー・Life Topics自動付与はそのまま適用される

## 6. 今週やるべきこと

1. **Pilot Operation Day 3〜7を完走**し、7日間の振り返り（何が自動化できたか／何が依然手作業か／Version 4着手前に直すべき設計上の不備）を実施
2. **スケジューリング方針の決定**：cron/launchd導入か、Rei手動実行を継続するかを判断し、Freshness Monitor・daily_briefing等の実行頻度を決める
3. **Article Status自動昇格スクリプトの設計検討**：Publish Gate（`enforce_publish_gate.py`）との整合性を保ちながら、AI Draft→Published経路を設計
4. **Dashboard Linked Viewの手動設定**：「🔴 Update Needed」を含む全セクションが未設定であれば[Dashboard Setup Guide](./Dashboard-Setup-Guide.md)に沿って設定完了させる
5. **Version 4本体着手に向けた優先順位の方針確認**：自治体連携／JNTO連携／企業向けダッシュボード／Mentorネットワーク拡大のうち、どれから対外的な意思決定を進めるかをReiと確認
6. **医療・福祉系トピックの記事化計画**：Coverage Analyzerが検知した0件トピック（介護／妊娠・出産／高齢者支援／障がい者支援）について、少なくとも各1本ずつ着手する計画を立てる。Update Level判定（現行Categoryでは「生活情報」等に該当し原則Level 1だが、内容次第では専門家レビューが望ましい場合もあるため、着手時に個別判断する）
7. **ARu Constitutionの改訂承認**：2026-07-17以降、Pending Amendments（§4・§11）をRei自身が確認し、承認する場合はv2.1.0へ反映
8. **Editorial Plannerの週次運用リズムを決める**：毎朝実行するのか、週1回の編集会議前に実行するのか。19件のResearchが一度に滞留した経験を踏まえ、`--limit`や`--topics`での小分け運用が実務上ちょうどよいかを検証する

---

## 7. README／AI-Handover／Roadmapとの整合性確認

本レポート作成にあたり、以下を確認・修正した。

| ドキュメント | 確認内容 | 結果 |
|---|---|---|
| [README.md](../README.md) | 「現在地」節がARu公式テンプレート統一・Freshness Monitor・Coverage Analyzer・Editorial Planner実装（いずれも2026-07-14）を反映しているか | ✅ 一致（本レポートと同時に更新） |
| [Roadmap.md](./Roadmap.md) | Version 4節に「Version 4準備作業」としてArticle Freshness Monitor・Coverage Analyzer・Editorial Plannerが記載されているか、前提条件（Pilot Operation完了）の位置づけが変わっていないか | ✅ 一致。前提条件は変更なし、準備作業として正しく記載済み |
| [AI-Handover.md](./AI-Handover.md) | Completed Features／Current Automationに本日の実装が反映されているか、Latest Commitが最新か | ✅ Completed Features／Current Automationとも一致（本レポートと同時に更新）。Latest Commitは前回のレポート作成時（`5e82259`→`c661ed3`）に一度修正済みで、以降の修正は都度反映している |
| [ARu-Constitution.md](./ARu-Constitution.md) | 本日の実装（9セクションテンプレート、Freshness Monitorのレビュー間隔、Coverage Analyzer、Editorial Planner）が本文の記述と矛盾していないか | ⚠️ 9セクションテンプレートとFreshness Monitorのレビュー間隔については**不一致を検出し、Level B Pending Amendmentとして提案済み**（2026-07-14提案、発効予定2026-07-17以降、編集長の承認を得るまで本文v2.0.0は変更しない）。Coverage Analyzer・Editorial Plannerは既存の§7 Source Policy／§9 AI Behavior Rulesの範囲内（Research作成のみでPublish Approvalには一切触れない）で動作しており、**改訂提案は不要と判断** |

**整合性上の結論**：README／Roadmap／AI-Handoverの3文書は本日の実装内容と矛盾しない。ARu Constitutionのみ、本日の実装によって記述が実態と乖離したため、正規の改訂プロセス（§20 Governance）に沿ってPending Amendmentとして提案し、承認待ちの状態。

---

*ARu HQ / Decode Japan — Version 4 Current Status Report — 2026-07-14*
