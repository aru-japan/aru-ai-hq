<title>ARu Version 4 Current Status Report</title>

# ARu Version 4 Current Status Report

| | |
|---|---|
| **Date** | 2026-07-14 |
| **対象** | Version 4（Enterprise）準備状況のスナップショット |
| **最新Commit** | `c661ed3` |
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

---

## 2. 現在のコンテンツ量（Notion実データ、2026-07-14時点）

| データベース | 件数 | 内訳 |
|---|---|---|
| **Articles（記事数）** | **53件** | Status: AI Draft 52／Draft 1　｜　Update Level: L1=37／L2=16　｜　Article Review: Pass 51／Needs Revision 1／未レビュー 1　｜　Freshness Status: Fresh 51／Needs Update 2 |
| **Research** | **52件** | Status: Converted 52（全件Articleへ転換済み） |
| **Translation** | **54件** | Publish Approval: Pending 15／Not Required 39　｜　Quality Result: Pass 52／Needs Revision 1／未レビュー 1 |
| **SNS Queue** | **160件** | Platform: X 53／Threads 53／Instagram 54　｜　Status: 全件Draft　｜　Review Result: Pass 152／Needs Revision 7／Fail 1 |

**注**：Articles(53)×3プラットフォーム=159に対しSNSは160件、Translation(54)がArticles(53)より1件多い。これは今回の一括生成以前に存在していた個別テストレコード（例：「【テスト】在留カードの更新手続きガイド」関連）による差分で、パイプライン自体の不整合ではない。念のため要確認（下記「現在の課題」参照）。

---

## 3. Version 4 完成率

Version 4本体は**前提条件（Pilot Operation 7日間の実運用完了）を満たしておらず、正式着手前**（[Roadmap](./Roadmap.md#version-4--enterprise)）。単一の「％」で表すと実態より進んでいるように見えてしまうため、3層に分けて評価する。

| 層 | 内容 | 進捗 |
|---|---|---|
| **前提条件** | Version 3.5 Pilot Operation（7日間実運用） | **2/7日（約29%）** |
| **Version 4準備作業**（技術的土台） | Article Freshness Monitor | **1/1件 実施済み（100%）**（現時点でRoadmapに明記された準備作業はこれのみ） |
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

---

## 5. 明日やるべきこと（2026-07-15予定）

1. **Pilot Operation Day 3を実施**（[Pilot Operation Guide](./Pilot-Operation-Guide.md)・[Operation Checklist](./Operation-Checklist.md)に沿って9工程を実行し記録）
2. **Article Freshness Monitorの2回目実行**：Days Since Verificationが正しく増分するか、Freshness Checked Dateが更新されるかなど、日次運用としての耐久性を確認
3. **滞留中のレビュー対応**：Needs Revision/Fail状態のSNS 8件・Article 1件・Translation 1件を人間が確認し、Publish可否を判断
4. **外部シグナル起因の要更新記事2件を実際に再レビュー**し、Freshness Monitor→人間レビューのワークフローが実運用でも機能することを確認
5. **未レビュー（None）の2件を調査**し、過去のテストレコードかどうかを特定・整理

## 6. 今週やるべきこと

1. **Pilot Operation Day 3〜7を完走**し、7日間の振り返り（何が自動化できたか／何が依然手作業か／Version 4着手前に直すべき設計上の不備）を実施
2. **スケジューリング方針の決定**：cron/launchd導入か、Rei手動実行を継続するかを判断し、Freshness Monitor・daily_briefing等の実行頻度を決める
3. **Article Status自動昇格スクリプトの設計検討**：Publish Gate（`enforce_publish_gate.py`）との整合性を保ちながら、AI Draft→Published経路を設計
4. **Dashboard Linked Viewの手動設定**：「🔴 Update Needed」を含む全セクションが未設定であれば[Dashboard Setup Guide](./Dashboard-Setup-Guide.md)に沿って設定完了させる
5. **Version 4本体着手に向けた優先順位の方針確認**：自治体連携／JNTO連携／企業向けダッシュボード／Mentorネットワーク拡大のうち、どれから対外的な意思決定を進めるかをReiと確認

---

## 7. README／AI-Handover／Roadmapとの整合性確認

本レポート作成にあたり、以下を確認・修正した。

| ドキュメント | 確認内容 | 結果 |
|---|---|---|
| [README.md](../README.md) | 「現在地」節がARu公式テンプレート統一・Freshness Monitor実装（いずれも2026-07-14）を反映しているか | ✅ 一致（本レポート作成前の作業で既に更新済み） |
| [Roadmap.md](./Roadmap.md) | Version 4節に「Version 4準備作業」としてArticle Freshness Monitorが記載されているか、前提条件（Pilot Operation完了）の位置づけが変わっていないか | ✅ 一致。前提条件は変更なし、準備作業として正しく記載済み |
| [AI-Handover.md](./AI-Handover.md) | Completed Features／Current Automationに本日の実装が反映されているか、Latest Commitが最新か | ⚠️ **Latest Commitが`5e82259`のまま古くなっていたため、本レポート作成時に`c661ed3`へ修正した。** それ以外（Completed Features、Current Automation一覧）は一致 |

**整合性上の結論**：3文書とも本日の実装内容と矛盾しない。唯一のズレ（AI-HandoverのLatest Commit）は本レポート作成と同時に修正済み。

---

*ARu HQ / Decode Japan — Version 4 Current Status Report — 2026-07-14*
