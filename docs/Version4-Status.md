<title>ARu Version 4 Current Status Report</title>

# ARu Version 4 Current Status Report

| | |
|---|---|
| **Date** | 2026-07-14（本体）／2026-07-16・2026-07-18 追記あり |
| **対象** | Version 4（Enterprise）準備状況のスナップショット |
| **最新Commit** | `6584101` |
| **位置づけ** | [Roadmap](./Roadmap.md)・[AI-Handover](./AI-Handover.md)・[README](../README.md)との整合性を確認済み |

> このレポートは特定時点のスナップショット。本体は2026-07-14時点、「8. Dashboard運用整備」「9. Version 4 Phase 5」は2026-07-16の追記、「10. ARu Intelligence Phase 1〜3」「11. ARu公式記事テンプレート再設計」は2026-07-18の追記。数値はすべてNotion実データへの実クエリで取得したもので、推測値ではない。

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

### ⑥ Publishing Center（Version 4 Phase 3）
`publishing_center.py`を新規実装。編集長がARuアプリへ何を掲載するか一目で判断できるようにする、Version 4準備の最終ピース。**AIによる自動公開は一切行わない**——ARuアプリへの実投稿APIが存在しないため、Publishedは「人間が手動掲載済み」の管理状態として定義した。

- 新規プロパティ：`Publishing Status`（Draft／Ready to Publish／Published／Needs Update／Archived）、`Published By`、`ARu App URL`、`Previous Publishing Status`、`Publishing Status Updated Date`（`Published Date`は既存プロパティを再利用、重複追加していない）
- Ready to Publish判定は5条件すべてが必要：Article Review Result=Pass／全Translation Quality Result=Pass／全Translation Publish Approvalが Not Required か Approved（Update Level 2・3の人間承認必須がそのまま担保される）／Freshness Status=Fresh／必須項目（Title・Body・Category・Last Verified Date、Summary相当はSource Researchので代替判定）が揃っていること。**自動でPublishedにはしない**
- Article Freshness Monitorと双方向連携：Published記事が要更新になれば自動でNeeds Updateへ、鮮度回復時は`Previous Publishing Status`を見て元の状態へ自動復帰
- 人間がPublishedへ変更すると、次回実行時にPublished Date・Published By（実際の`last_edited_by`、存在しないAPIは仮定せず）を自動記録
- `enforce_publish_gate.py`を拡張し、Publishing Status=Publishedも既存ゲート基準（QA Status／Update Level 2・3のHuman Reviewed・Review Result）で監視
- Dashboard「📝 Editorial Planner」の直下に「🚀 Ready to Publish」「📚 Published Articles」「🛠 Needs Update」の3セクションを追加

**実行結果（実データ・実API、2026-07-14）**：既存53記事を初期分類し、**Ready to Publish 20件／Draft 33件／Published 0件**（一括自動設定はしていない）。Update Level 1で全条件Passの記事は正しくReady to Publishへ、Update Level 2でPublish Approval=Pendingの記事は正しくDraftのまま、Freshness Needs Updateの2記事はReady to Publishにならないことを確認。Publishing Statusを人間がPublishedへ変更→Published Date/By自動記録→Freshness悪化でNeeds Updateへ自動遷移→鮮度回復で自動復帰、という一連のライフサイクルをテストで実証。`enforce_publish_gate.py`実行で違反0件を確認したが、その過程で**`QA Status`（既存の手動プロパティ）が全53記事で未設定という実在のギャップを検知**（詳細は[Automation Scripts](./Automation-Scripts.md)、下記「現在の課題」参照）。

### ⑦ Articles DB正規化＋Duplicate Prevention（Version 4 Phase 4）
Publishing Center導入直後、Reiから「Articles DBに同じテーマの記事が複数存在している」と指摘を受け、**公開作業を一時停止して調査**した。

**調査結果**：Article.Titleではなく紐づくResearch.Topicでグループ化して検出したところ、**15グループ・記事30件**が完全重複（Article・Translation・SNS×3まで含めてフルパイプラインが2回実行されていた）と判明。原因は2026-07-14の一括生成でバックグラウンド処理を2回起動してしまったこと（13グループ）、2026-07-13のTOPICSリストの重複（1グループ）、2026-07-12の【テスト】記事の残存（1グループ）。判定基準（① Article・Translation・SNS全件Pass優先 → ② Review Overall Score → ③ 作成が早い方）で各グループ1件を残し、**14件をArchive、1件（テスト記事）もArchive**、計15件をPublishing Status=`Duplicate`（新設の選択肢）へ移動した。**削除はしていない。**

**再発防止（`duplicate_guard.py`）**：ARuの原則「**1 Research Topic = 1 Article**」を生成**前**にコードで強制。①Research.Topic ②非ArchivedのArticle ③Translation ④SNS Queueの存在を順に確認し、既存なら生成せず「Already Exists」（到達段階付き）を記録する。`bulk_generate_articles.py`は処理ループ**開始前**にTOPICS全件を事前チェックし除外する設計に変更（検知ではなく防止）。Dashboard「📝 Editorial Planner」の直下に「🛡 Duplicate Prevention」を追加。

**テスト結果**：既存の完全重複記事に対する再生成試行が、AI Gatewayを呼ばず・Notionレコードを作らずに正しくスキップされることを確認。現在の`bulk_generate_articles.py`のTOPICS（15件、すべて生成済み）を事前チェックしたところ、**全15件が正しく「既に存在」と判定**され、2026-07-14と同じ事故は構造的に再発不可能になったことを実証した。

---

## 2. 現在のコンテンツ量（Notion実データ、2026-07-14時点）

| データベース | 件数 | 内訳 |
|---|---|---|
| **Articles（記事数）** | **53件**（うち15件は重複としてArchive、実質稼働38件） | Status: AI Draft 38／Draft 0／Archived 15（重複整理後）　｜　**Publishing Status: Ready to Publish 11／Draft 27／Duplicate 15／Published 0** |
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
| **前提条件** | Version 3.5 Pilot Operation（7日間実運用） | **2/7日（約29%、Day 2から変わらず）** |
| **Version 4準備作業**（技術的土台） | Article Freshness Monitor、Coverage Analyzer、Editorial Planner、Publishing Center、Duplicate Prevention、Editor Experience（Phase 5）、ARu Intelligence Phase 1（Source Watcher）、Phase 2（Source Library Expansion）、Phase 3（Editorial Intelligence） | **9/9件 実施済み（100%）**（現時点でRoadmapに明記された準備作業はこの9件。詳細は本レポート10節、および[Roadmap](./Roadmap.md#version-4--enterprise)） |
| **Version 4本体**（Roadmap記載5項目：Usage Scope実運用／自治体・観光協会・企業とのデータ連携／JNTO・Visit Japan連携／企業向けダッシュボード／Mentorネットワーク本格拡大） | いずれも対外的な契約・意思決定を伴う | **0/5件（0%）** |

**注**：上記とは別に、**ARu公式記事テンプレート再設計（2026-07-18、本レポート11節）**をブランド品質標準化として実施済み。これはRoadmapの「Version 4準備作業」箇条書きにはまだ記載がなく（Roadmap.mdは2026-07-18時点で未反映）、Version 4本体の前提条件でもないため上記9件の集計には含めていない。

**総合評価**：技術的な土台固め（Freshness Monitor以降、ARu Intelligenceまでの9件）は計画通り・前倒しで先行実装できたが、Version 4本体は実装だけでは進められない項目が大半を占める。次のゲートはPilot Operation Day 3〜7の完走と、その後の対外的な方針確認。**全体としては「本体着手前」であり、大まかな目安としては一桁%〜10%程度**（前提条件の進捗と、技術準備9件の完了を反映した粗い目安であり、対外交渉が絡む項目のため精緻な%算出はできない）。

---

## 4. 現在の課題

1. **Pilot Operation Day 3〜7が未実施**：7日間のうち2日のみ完了。Version 4着手前の「完了条件」（7日分のOperation Checklist記入＋最終振り返り）にまだ届いていない
2. **スケジューリング未設定**：Freshness Monitor・daily_briefing等はすべて手動実行。cron/launchd等の定期実行が未導入
3. **Article.Statusの自動昇格が未実装**：Translation側のPublish Approvalゲートは実証済みだが、Article本体のStatus（AI Draft→Published）を進める自動化がなく、38件（重複整理後）がAI Draftのまま滞留
4. **人間レビュー待ちの滞留**：Article Needs Revision 1件、Translation Needs Revision 1件、SNS Needs Revision 7件／Fail 1件が未対応
5. **未レビューレコードが残存**：Article Review Result・Translation Quality Resultにそれぞれ1件、値が空（None）のレコードがある。過去のテストレコード起因の可能性が高いが未確認
6. **Freshness Monitorで検知された2件が未対応**：外部シグナル（入管法改正・情報源変化）により再レビュー対象となった記事が、まだ実際にレビューされていない
7. **SNS実投稿は未実装**：Draft生成・レビューまでで、実際のプラットフォームへの投稿は手動または未着手
8. **外部通知の仕組みがない**：Critical Gap等の重要検知をSlack/メール等へ通知する機能は未実装
9. **Deferred中の6DB**（Language Master／Region Master／Mentor／AI Agents／Prompt Library／Automation）は引き続き未着手（方針通り、削除ではなく保留）
10. **コンテンツの偏りが明確に**：Coverage Analyzerにより、`介護`／`妊娠・出産`／`高齢者支援`／`障がい者支援`が0件、`教育`が1件のみと判明。現状53記事の大半が「文化・マナー」「行政手続き・相談窓口」に偏っており、外国籍の方の生活に不可欠な医療・福祉系トピックが手薄
11. **ARu Constitutionの改訂提案が承認待ち**：Pending Amendments（Level B、提案日2026-07-14、発効予定2026-07-17以降）。ARu公式テンプレートとArticle Freshness Monitorの実態を§4・§11へ反映する内容で、編集長の承認待ち
12. **Editorial Plannerが提案した19件のResearchが未レビュー**：`Status=New`のままDashboard「⑥ Today's Research」に滞留中。優先度（Priority/Urgency）は機械的に設定されているが、実際に記事化するかどうかはRei自身の判断が必要
13. **`QA Status`が全53記事で未設定**：`enforce_publish_gate.py`が元々必須としている項目だが、これまで誰も設定していなかった（AI生成パイプラインには組み込まれていない、人間専用の項目）。Ready to Publish 20件のうち、実際にPublishedへ進めようとすると、この既存ゲートに引っかかる可能性がある。QA Statusを誰がいつ設定する運用にするか、Ready to Publish条件に含めるべきかはRei自身の判断待ち
14. **ARu Constitutionの改訂提案が3件に増加**：①9セクションテンプレート・Freshness Monitor（§4・§11）、②Publishing Centerで判明した「Level 1 ── 自動公開」表記の誤解（§15）、③Reiが明示的に指示した「1 Research Topic = 1 Article」原則（§4）。いずれもLevel B、発効予定2026-07-17以降、編集長の承認待ち
15. **アーカイブした重複記事15件のTranslation・SNS Queueレコードが未整理**：親Articleが Archived/Duplicate のため公開経路には現れないが、レコード自体の削除・アーカイブは今回のスコープ外。要判断
16. **Duplicate Preventionのログはローカルファイル**：`notion-build/automation/logs/duplicate_prevention.jsonl`はGit・Notionいずれとも同期しない。「本日の生成件数」等はスクリプトを実行した端末上の活動のみを反映する（既知の制約として明記済み）
17. **Source Libraryの実監視網はまだ10件のみ**（ARu Intelligence Phase 1のテストレコード1件＋Phase 2のシード9件）：Immigration／Tax／Health Insurance／Disaster／Weather／Emergency／Pension／Employment／Transportation／Tourismはカバー済みだが、Visa（外務省サイトが自動フェッチをブロックし見送り）／Student／Events／Festivals／Municipal Governments／Universities／Japanese Language Schools／Culture／Consumer Information／Housing／Banking／Trending Topicsは未着手。数百件規模の監視網にするにはRei（または今後のフェーズ）による継続的なソース登録が前提
18. **SimHashの変化検知閾値は調整可能なヒューリスティックであり「解決済みの問題」ではない**：`SIMHASH_CHANGE_THRESHOLD=2`（64bit中）は限られた実データでの初期値。ソース数が増えるにつれ、実運用のfalse positive/false negative発生率を見ながら再調整が必要になる可能性がある
19. **Archived記事のFreshness Statusが自動でクリアされないバグの根本原因は未修正**：ARu Intelligence Phase 3の実装中、この既知の制約が原因でCritical UpdatesにArchived済みテスト記事が誤って混入する事象を発見し、当該集計側（`Status`除外条件の追加）では対処済みだが、Archive時にFreshness Statusをクリアする処理自体はまだ存在しない。新しい集計ロジックを書く際は同様の除外条件を忘れないこと
20. **全38記事がTemplate Status＝Update Needed**：ARu公式記事テンプレート再設計（9セクション→8セクション）に伴い`template_migration_report.py`を実データ全件に対して実行した結果、Up to Dateは0件。新テンプレート導入前に生成された記事は必然的にすべて旧構成のため想定どおりだが、実際にどの記事から・どのペースで移行するかはRei自身の判断待ち
21. **テンプレート移行の改訂版サンプル1件がRei承認待ち**：テスト記事「日本のカフェ文化が変わった理由」について、新8セクション構成への改訂版を実データから生成済みだが、承認までは本番記事を上書きしていない
22. **Roadmap.mdがARu公式記事テンプレート再設計（2026-07-18）を未反映**：README.md・AI-Handover.mdはこの再設計を反映済みだが、`docs/Roadmap.md`の「Version 4準備作業」箇条書きには2026-07-18時点でまだ記載がない（本レポート作成時に発見。本レポートの更新スコープには含めていないため、Roadmap.md自体の修正はRei確認後に別途行う）

---

## 5. 明日やるべきこと（2026-07-15予定）

1. **Pilot Operation Day 3を実施**（[Pilot Operation Guide](./Pilot-Operation-Guide.md)・[Operation Checklist](./Operation-Checklist.md)に沿って9工程を実行し記録）
2. **Article Freshness Monitorの2回目実行**：Days Since Verificationが正しく増分するか、Freshness Checked Dateが更新されるかなど、日次運用としての耐久性を確認
3. **滞留中のレビュー対応**：Needs Revision/Fail状態のSNS 8件・Article 1件・Translation 1件を人間が確認し、Publish可否を判断
4. **外部シグナル起因の要更新記事2件を実際に再レビュー**し、Freshness Monitor→人間レビューのワークフローが実運用でも機能することを確認
5. **未レビュー（None）の2件を調査**し、過去のテストレコードかどうかを特定・整理
6. **Editorial Plannerが作成した19件のResearch（★5：妊娠・出産を最優先）から2〜3件を選び、実際に記事化**する。Research自体は既に`Status=New`で存在するため、`generate_article_pipeline.py article --keyword "..."`で直接拾える（Statusを`Converted`へ変更してから実行）。9セクションテンプレート・3段レビュー・Life Topics自動付与はそのまま適用される
7. **Ready to Publish 11件のうち1〜2件を実際にARuアプリへ手動掲載してみる**：QA Status未設定の問題を先に解消（値を`Passed`に設定）した上で、Publishing Statusを`Published`へ変更し、`publishing_center.py`実行でPublished Date/Byが正しく記録されることを実運用でも確認する
8. **アーカイブした重複記事15件のTranslation・SNS Queueレコードの扱いを決める**：残すか、Archiveへ揃えるか

## 6. 今週やるべきこと

1. **Pilot Operation Day 3〜7を完走**し、7日間の振り返り（何が自動化できたか／何が依然手作業か／Version 4着手前に直すべき設計上の不備）を実施
2. **スケジューリング方針の決定**：cron/launchd導入か、Rei手動実行を継続するかを判断し、Freshness Monitor・daily_briefing等の実行頻度を決める
3. **Article Status自動昇格スクリプトの設計検討**：Publish Gate（`enforce_publish_gate.py`）との整合性を保ちながら、AI Draft→Published経路を設計
4. **Dashboard Linked Viewの手動設定**：「🔴 Update Needed」を含む全セクションが未設定であれば[Dashboard Setup Guide](./Dashboard-Setup-Guide.md)に沿って設定完了させる
5. **Version 4本体着手に向けた優先順位の方針確認**：自治体連携／JNTO連携／企業向けダッシュボード／Mentorネットワーク拡大のうち、どれから対外的な意思決定を進めるかをReiと確認
6. **医療・福祉系トピックの記事化計画**：Coverage Analyzerが検知した0件トピック（介護／妊娠・出産／高齢者支援／障がい者支援）について、少なくとも各1本ずつ着手する計画を立てる。Update Level判定（現行Categoryでは「生活情報」等に該当し原則Level 1だが、内容次第では専門家レビューが望ましい場合もあるため、着手時に個別判断する）
7. **ARu Constitutionの改訂承認**：2026-07-17以降、Pending Amendments（§4・§11、§15、および§4「1 Research Topic = 1 Article」の3件）をRei自身が確認し、承認する場合はv2.1.0（以降）へ反映
8. **Editorial Plannerの週次運用リズムを決める**：毎朝実行するのか、週1回の編集会議前に実行するのか。19件のResearchが一度に滞留した経験を踏まえ、`--limit`や`--topics`での小分け運用が実務上ちょうどよいかを検証する
9. **QA Statusの運用方針を決める**：Ready to Publish条件に含めるか、掲載直前チェックリストとして人間が別途確認する運用にするか。決めた方針を`publishing_center.py`のevaluate_readiness()または運用手順として反映する
10. **ARu App URLの記録方法を決める**：ARuアプリ側にスラッグ／IDの命名規則があるか確認し、Publishedへ変更する際の入力ルールを定める
11. **他のAI生成スクリプトも`duplicate_guard.py`の対象範囲を再確認する**：現状は`generate_article_pipeline.py`と`bulk_generate_articles.py`のみに組み込み済み。将来Research/Article生成の新しい経路を追加する場合は、必ず同様のチェックを組み込む

---

## 7. README／AI-Handover／Roadmapとの整合性確認

本レポート作成にあたり、以下を確認・修正した。

| ドキュメント | 確認内容 | 結果 |
|---|---|---|
| [README.md](../README.md) | 「現在地」節がARu公式テンプレート統一・Freshness Monitor・Coverage Analyzer・Editorial Planner・Publishing Center・Duplicate Prevention実装（いずれも2026-07-14）を反映しているか | ✅ 一致（本レポートと同時に更新） |
| [Roadmap.md](./Roadmap.md) | Version 4節に「Version 4準備作業」としてArticle Freshness Monitor・Coverage Analyzer・Editorial Planner・Publishing Center・Duplicate Preventionが記載されているか、前提条件（Pilot Operation完了）の位置づけが変わっていないか | ✅ 一致。前提条件は変更なし、準備作業として正しく記載済み |
| [AI-Handover.md](./AI-Handover.md) | Completed Features／Current Automationに本日の実装が反映されているか、Latest Commitが最新か | ✅ Completed Features／Current Automationとも一致（本レポートと同時に更新）。Latest Commitは前回のレポート作成時（`5e82259`→`c661ed3`）に一度修正済みで、以降の修正は都度反映している |
| [ARu-Constitution.md](./ARu-Constitution.md) | 本日の実装（9セクションテンプレート、Freshness Monitorのレビュー間隔、Coverage Analyzer、Editorial Planner、Publishing Center、Duplicate Prevention）が本文の記述と矛盾していないか | ⚠️ **不一致・追加原則を3件検出し、いずれもLevel B Pending Amendmentとして提案済み**（2026-07-14提案、発効予定2026-07-17以降、編集長の承認を得るまで本文v2.0.0は変更しない）：①9セクションテンプレートとFreshness Monitorのレビュー間隔（§4・§11）、②Publishing Centerの実装で判明した「Level 1 ── 自動公開」という表記の誤解（§15、AIが自動公開したことは元々一度もなく運営方針の変更ではない）、③Reiが明示的に指示した「1 Research Topic = 1 Article」原則の明文化（§4）。Coverage Analyzer・Editorial Plannerは既存の§7 Source Policy／§9 AI Behavior Rulesの範囲内（Research作成のみでPublish Approvalには一切触れない）で動作しており、改訂提案は不要と判断 |

**整合性上の結論**：README／Roadmap／AI-Handoverの3文書は本日の実装内容と矛盾しない。ARu Constitutionのみ、本日の実装によって記述が実態と乖離した箇所・明文化すべき新原則が3件見つかり、いずれも正規の改訂プロセス（§20 Governance）に沿ってPending Amendmentとして提案し、承認待ちの状態。

**2026-07-18追記（本レポート更新時の再確認）**：ARu Intelligence Phase 1〜3およびARu公式記事テンプレート再設計を反映するにあたり、上記4文書を再度確認した。

| ドキュメント | 結果 |
|---|---|
| [README.md](../README.md) | ✅ 「現在地」節がARu Intelligence Phase 1〜3、およびテンプレート再設計（9→8セクション）まで反映済み |
| [AI-Handover.md](./AI-Handover.md) | ✅ Completed Features／Current Automationとも反映済み（v1.9、Latest Commit `6584101`） |
| [Roadmap.md](./Roadmap.md) | ⚠️ **一部不一致**：「Version 4準備作業」節はARu Intelligence Phase 1〜3まで反映済みだが、ARu公式記事テンプレート再設計（2026-07-18）は未記載。本レポートの更新スコープには含めていないため、Roadmap.md自体の修正はRei確認後に別途対応する（本レポート4節17〜22項にも記載） |
| [ARu-Constitution.md](./ARu-Constitution.md) | ✅ 新たな不一致・追加原則は検出されなかった。ARu Intelligence Phase 1〜3は既存の§7 Source Policy／§9 AI Behavior Rulesの範囲内（変化検知・優先順位付けのみでPublish Approvalに触れない）で動作。テンプレート再設計も記事本文の構成変更に留まり、Pending Amendments（3件、承認待ち）から件数の増減なし |

---

## 8. Dashboard運用整備（2026-07-16追記）

Reiと一緒に、Dashboardの全13セクションのLinked Database View設定を完了した（Notion UIでの手動設定、AIが代行できない部分）。設定の過程で2件の不具合を発見・修正した。

1. **Select型プロパティの「降順」が意図と逆だった**：`Priority`／`Urgency`のSelectオプション定義順が「重要度が高い→低い」だったため、Notionの仕様上「降順」がその逆——**重要度が低いものが先頭に来る**、意図と正反対の並びになっていた。Articles・Research・Editorial Calendarの3DBでオプション定義順を並べ替えて解消（データそのものは変更していない）。
2. **Articles.Priorityが記事生成パイプラインで一度も書き込まれていなかった**：既存53記事中52件が未設定だった。ArticleがResearchの`Priority`／`Urgency`を生成時に自動継承する設計へ変更し（`generate_article_pipeline.py`／`bulk_generate_articles.py`）、既存53記事も一括バックフィル（53件成功）。バックフィル後は全件`Priority=Medium`（Researchが一律Mediumで作成されていたことをそのまま反映、バグではない）。Editorial Planner提案のResearch（★評価に基づきHigh／Critical含む）が今後Article化されれば自然に分散する設計。

詳細は[Automation Scripts](./Automation-Scripts.md)の該当節を参照。**Dashboard 13セクションのLinked View設定・データ側の不具合修正・実データでの動作確認まで完了し、編集長がDashboardのみで公開待ち・翻訳待ち・SNS待ち・Research・要更新記事を運営できる状態になった。**

## 9. Version 4 Phase 5（Editor Experience、2026-07-16）

Reiから「編集長が記事を開いた瞬間に必要な情報だけを見られるようにしたい」との要望を受け実施。**制約：Version 4のデータベーススキーマ・プロパティ名・リレーション・Formula・既存自動化は一切変更しない。表示とナビゲーションだけを改善する。**

1. **`render_article_layout.py`**：Articles.Bodyの9セクションテンプレートを、Articleページの実ブロック（見出し＋段落、4セクションはtoggle折りたたみ）として描画。Bodyプロパティ自体は不変、表示専用の追加レイヤー。全リポジトリgrepで「他のスクリプトはArticleページのブロック子要素を一切読み書きしていない」ことを確認済みのため、安全に追加できると判断。既存Articles全38件（Archived除く）へ一括バックフィル実行 → **38件処理、0件失敗**。`generate_article_pipeline.py`／`bulk_generate_articles.py`双方にフック済み（レンダリング失敗はnon-fatal）。
2. **`editor_home.py`**：「今日、人間が決めること」9項目（Ready to Publish／Published／Needs Update／Publish Approval Pending／Article Review Waiting／Translation Review Waiting／SNS Draft Waiting／Today's Editorial Calendar／Today's Research）をDashboardと完全に同一のフィルタで集計し、専用Notionページ（ナビゲーションハブ）に反映。実データで合計92件を確認。
3. **`ai_command_center.py`**：「AIが監視・検知していること」（Freshness内訳、Duplicate Prevention本日の活動、外部監視フィード3種、Coverage Analysis／Editorial Plannerへのポインタ）を専用Notionページに反映。AI分析内容自体の再計算はしない設計（AI Gateway呼び出しを増やさない）。
4. **`docs/Article-Property-Panel-Guide.md`**：Articleページのプロパティを【本文】【公開情報】【関連情報】【AI Review】【System】へグループ化する手動Notion UI手順書。View設定と同じくAPIから設定不可なため人間の作業として文書化。

**回帰テスト（実データ、2026-07-16）**：`article_freshness_monitor.py`／`publishing_center.py`／`coverage_analyzer.py`／`editorial_planner.py`／`duplicate_prevention_report.py`／`enforce_publish_gate.py`を再実行し、いずれもエラーなく完走、既存ロジックどおりの結果を確認。**Dashboard互換性100%・既存自動化のすべてが引き続き正常動作することを実証した。**

詳細は[Automation Scripts](./Automation-Scripts.md)の該当節を参照。

## 10. ARu Intelligence Phase 1〜3（2026-07-16〜2026-07-18追記）

Version 4 Phase番号とは別の独立トラックとしてRei自身が命名（目的が「編集長の作業体験の改善」ではなく「コンテンツの鮮度・信頼性の担保」および「ARuを毎日使うプラットフォームにする」ことのため）。いずれも新規データベースは追加していない。詳細は[Automation Scripts](./Automation-Scripts.md)、編集ワークフロー全体像は[Editorial Workflow](./Editorial-Workflow.md)を参照。

### Phase 1：Source Watcher（2026-07-16）

`source_watcher.py`を新規実装。これまでSource Monitor.`Change Detected`は完全に手動チェックボックスで、外部URLを実際にフェッチして変化を検知するコードは1件も存在しなかった——下流（Research自動起票／Article強制フラグ／Publishing Center連携／Dashboard／AI Command Center）はすべて実装・テスト済みだったが、実データを受け取ったことがなかった。stdlibのみでURLをフェッチしSHA-256でハッシュ比較、変化検知時のみSource Monitorレコードを新規作成する。新規スキーマはSource Libraryへの`Last Content Hash`（rich_text）1プロパティのみ。政府・自治体系情報源の変化はフラグ立てのみに留め、Law Updateの自動作成はしない（人間が判断）。

**実行結果（実データ、2026-07-16）**：Source Library実データ1件（テストレコード、出入国在留管理庁の実URL）に対し実行。初回実行でbaseline確立（誤検知0件）、変化検知パスを意図的なハッシュ改変で実証（`Impact Level=Critical`、AI生成Diff Summaryを確認）。既存6スクリプトの回帰テストで異常なし。**Phase 1時点での実運用上の網羅範囲は実URL1件のみ**（コードの欠陥ではなく、Source Libraryへの実データ投入がまだこれからだったため）。

### Phase 2：Source Library Expansion（2026-07-17）

`source_categories.py`／`bulk_import_sources.py`（新規）、`source_watcher.py`／`ai_command_center.py`（拡張）。Phase 1が残した「監視エンジンはできたが監視対象がほぼ空」という課題を解消。Source LibraryへCategory（22種）／Country／Region／City／Importance（Critical/High/Medium/Low、旧`Tier`を代替）／`Last Check Error`を追加（既存DBへの追加のみ、Region Masterは既存のDeferred方針どおり作成せず）。本リポジトリ初のCSV一括登録機能（`bulk_import_sources.py`）を実装し、変化検知をSHA-256完全一致からSimHash近似指紋＋ハミング距離比較へ変更（広告・タイムスタンプ・訪問者数等のノイズを除去）。Source Monitorへ`Update Classification`（11分類、AI判定）を追加。

**実行結果（実データ、2026-07-17）**：WebFetchで実在確認済みの9ソース（国税庁／厚生労働省／内閣府防災情報／気象庁／消防庁／日本年金機構／ハローワーク／国土交通省／JNTO）を投入——**9件成功、0件重複、0件エラー**。投入後の`source_watcher.py`実行で9件すべて正しくbaseline確立。SimHashのノイズ耐性テスト（ノイズ追加→ハミング距離2、閾値以下で正しく「変化なし」）・実質変更検知テスト（本文15%置換→ハミング距離13、正しく「変化あり」）を実データで確認。既存6スクリプトの回帰テストで異常なし。**未着手のカテゴリ**：Visa（外務省サイトが自動フェッチをブロックし見送り）、Student／Events／Festivals／Municipal Governments／Universities／Japanese Language Schools／Culture／Consumer Information／Housing／Banking／Trending Topics。

### Phase 3：Editorial Intelligence（2026-07-18）

`research_prioritizer.py`／`today_opportunities.py`（新規）、`ai_command_center.py`（再構成）、`docs/Editorial-Workflow.md`（新規）。新機能追加ではなく既存システムの再利用・統合が目的。`research_prioritizer.py`はStatus=NewのResearchをFreshness／Foreign Resident Value／Tourism Value／Seasonal Relevance／Premium Potentialの5軸（各20点）で決定論的にスコアリング（新規スキーマ・追加AI呼び出しなし）。`today_opportunities.py`はEvent Calendar／Source Monitor／Law Update／Researchの4つの既存システムを統合。`ai_command_center.py`を「編集長が毎日最初に見るページ」として再構成し、先頭5セクション（🎯 Today's Opportunities／🔴 Critical Updates／📊 Top Research Candidates／🚀 Publishing Queue／🕐 Recently Updated Articles）を追加（Phase 1/2の監視詳細セクションは根拠情報として下部に残置）。

**実行結果（実データ、2026-07-18）**：Status=New 19件全件をスコアリング（5軸すべて正しく算出。上位10件が同点48点で並ぶ結果になったが、現状のResearch backlogがCategory・Season的に同質であることを正直に反映したもので、ロジックの不具合ではない）。実装中、`Status=Archived`の除外漏れによりCritical Updatesへ古いテスト記事が誤混入するバグを発見・修正（3件→2件の正しい件数に修正確認）。既存8スクリプトの回帰テストで異常なし。

## 11. ARu公式記事テンプレート再設計（2026-07-18追記）

`article_template.py`（新規、共有モジュール）、`render_article_layout.py`／`generate_article_pipeline.py`／`reviewer_agent.py`（更新）、`template_migration_report.py`（新規）。ブランド品質の標準化が目的で、既存の生成・レビュー・翻訳・SNSパイプラインはそのまま、記事本文の構成だけを刷新した。

**変更内容**：旧9セクションテンプレート（Question／Basic Answer／More Details／Why Does Japan Do This?／Practical Steps and Cautions／Latest Information／ARu Tip／Related Questions／Mentor Support）を、新しい8セクション公式構成（Basic Answer／More Details／Cultural Background／ARu Tip［必須］／Things to Know／FAQ／Premium Section／Sources）へ置き換え。Title・Related Articles・Last Updatedは既存プロパティ（記事タイトル・`Knowledge Links`・`Last Verified Date`）のまま扱い、Bodyには含めない。従来`generate_article_pipeline.py`と`render_article_layout.py`に別々に重複定義されていたセクション構成を`article_template.py`へ一本化。`reviewer_agent.py`は既存5観点スコアリングに加え、決定論的なセクション有無チェックとAIによるPremium価値・重複・fact/interpretation/recommendation区別の評価を追加（新規レビュープロパティなし）。`template_migration_report.py`は新規プロパティ`Template Status`（Up to Date／Update Needed）で全記事の移行優先度を可視化するのみで、**既存記事を自動的に書き換えることはしない**。

**発見・修正したバグ**：AIが箇条書き内で使うインライン太字（例:「**浴衣を着てみましょう**：...」）を、旧パーサーが誤ってセクション境界と認識し本文が途中で途切れる潜在バグ（旧テンプレートにも存在）を発見。正規のセクション名に一致した太字だけを境界とみなすよう修正し、実データで全文が正しく保持されることを確認。

**実行結果（実データ、2026-07-18）**：`template_migration_report.py`を全38件（Archived除く）に対して実行 → **全38件がUpdate Needed（Up to Date 0件）**——新テンプレート導入前に生成された記事は必然的にすべて旧構成のため想定どおりで、コード側の不具合ではない。テスト記事「日本のカフェ文化が変わった理由」の改訂版を実データから生成し、8セクションへの再編成を確認（**Rei承認まで本番記事は上書きしていない**）。`render_article_layout.py`・`reviewer_agent.py`の実データ確認も完了（詳細は[Automation Scripts](./Automation-Scripts.md)）。

---

*ARu HQ / Decode Japan — Version 4 Current Status Report — 2026-07-14（8〜9節は2026-07-16追記、10〜11節は2026-07-18追記）*
