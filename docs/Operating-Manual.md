<title>ARu Studio Operating Manual v1</title>

# ARu Studio Operating Manual
### 標準運用手順書（SOP）Version 1.0

| | |
|---|---|
| **Status** | Active — Phase B1 MVP（Articles／Research／Translation／Source Library／Editorial Calendar）に基づく |
| **Date** | 2026-07-12 |
| **対象読者** | 編集長（Rei） |
| **位置づけ** | [ARu Constitution v2.0.0](./aru-constitution.md)が定める「何を優先するか」を、日々の具体的な操作手順に落とし込んだもの。矛盾する場合はConstitutionが優先する |
| **関連文書** | ARu Constitution／AI Agent Constitution／Notion Database Builder Spec／View & Template設定ガイド |

> この手順書は、ARu Studioを10年以上運営するための土台である。今日の自分だけでなく、10年後にこの役割を引き継ぐ誰かが読んでも実行できるように書く。

---

## 現時点の運用スコープについて（重要）

本マニュアルはPhase B1 MVP（5DB：Articles／Research／Translation／Source Library／Editorial Calendar）を前提にしている。Knowledge Gap Engine、Opportunity Intelligence、Source Monitor、Dashboard、Mentor、AI Agents／Prompt Library／Automation、Language Master／Region Master、Law Update、Event Calendar、SNS Queueは**まだ実装されていない**。そのため、本来は自動化される予定の作業の多くを、**現時点ではRei自身が手動で行う**。該当箇所には都度「（現在：手動／将来：自動化）」と注記する。

---

## 1. 朝やること

1. **Editorial CalendarのDaily Viewを開く。**（Status: Idea／Planned／In Progressを、Urgency降順→Planned Date昇順で表示）これが実質的な「今日の編集会議」。
2. **ArticlesのDaily Viewを確認する。**（Status: AI Draft／Human Reviewを、Urgency降順→Updated Date昇順で表示）今日中に承認・レビューすべき記事を把握する。
3. **TranslationのDaily Viewを確認する。**（Needs Re-Translationがチェック済み、またはAI Translation Status=Queuedを、Review Level降順で表示）翻訳待ちの言語を把握する。
4. **Source LibraryのDaily Viewを確認する。**（Status=Activeを、Last Checked昇順で表示）長期間チェックしていない情報源がないか確認する。（現在：手動／将来：Source Monitorが自動検知）
5. Urgency=Criticalの項目があれば、他の何よりも先に着手する。

## 2. 昼やること

1. Editorial CalendarのIdea／Plannedを、実際の執筆・調査（Research作成、Article起筆）へ進める。
2. ResearchのDaily View（Status=New）を確認し、Categoryを確定させてStatus=Reviewingへ進めるか、Status=Rejectedにする。
3. Human Review待ちのArticleを確認し、Constitution第14章 Quality Checklist（Article Template本文のTo-do）を満たしているか確認してからStatusを進める。
4. Translationの翻訳作業を進める。AI Translation Status→Done、Localization Status→Culturally Adaptedまで確認してから、Human Review Status／Publish Approvalを進める。

## 3. 夕方やること

1. 今日Publishedにした記事・言語版を、Editorial CalendarのStatusにも反映する（現在：手動／将来：Article.Status=Published検知でAutomationが自動反映）。
2. 未完了で残ったDaily Viewの項目を確認し、明日以降のPlanned Dateを見直す。
3. Source Libraryで新しく見つかった情報源があれば登録する（Tier・Source Type・Check Frequencyを設定）。
4. その日Criticalとして扱った案件があれば、経緯を記録に残す（現在：手動メモ／将来：Audit Log DBへ自動記録）。

## 4. 週次レビュー

1. 各DBのWeekly Viewを開く。
   - Editorial Calendar：Calendar view（Planned Date軸）で今週〜来週の計画を俯瞰する
   - Articles：Calendar view（Published Date軸）
   - Research：Board（Discovery Method別）
   - Translation：Board（Language別）— 言語ごとの翻訳の偏りを確認する（現在：手動集計／将来：Translation Progress・Language Masterで自動可視化）
   - Source Library：Board（Source Type別）
2. Update Level 2・3の記事のうち、Last Verified Dateが古いものがないか確認する（Constitution §11：目安90日）。
3. Editorial CalendarでStatus=Ideaのまま長期間動いていない項目を見直す。
4. Constitution／AI Agent ConstitutionのRevision Historyに、レビュー中の改訂案（Level B：72時間以上）がないか確認する。

## 5. 月次レビュー

1. Article全体のTrust Score／Verification Statusを俯瞰し、更新優先度の高い記事を洗い出す（現在：手動／将来：Knowledge Gap Engineの Trust Gap／Freshness Gapが自動検出）。
2. Source Libraryの Tier・Check Frequencyが実態と合っているか見直す。
3. Audience／Region／Season別の記事分布を目視で確認し、著しく手薄な領域がないか確認する（現在：手動／将来：Audience Gap／Region Gap／Seasonal Gapが自動検出）。
4. ARu Constitution・AI Agent Constitutionの内容が実態と乖離していないか確認する。乖離があればLevel A/B/Cを判定し、改訂プロセスに乗せる（Constitution §20）。
5. 月間の公開記事数・言語別カバレッジ・完了できなかった計画数を振り返る（現在：手動集計／将来：Dashboardが自動集計）。

## 6. 緊急更新時の対応

ARu Constitution §12 Emergency Update Rulesに基づく。

1. 誰でも（自分自身も含め）「これは緊急対応が必要」と判断した時点で着手する。基準：Urgency=Criticalに相当する内容、または読者に実害が及ぶ誤り・変化。
2. 対象のArticleのStatusを Human Review に戻す（現時点では専用の「確認中」状態がないため、この状態を暫定の「非公開扱い」として運用する）。**日本語版だけでなく、紐づく全Translationについても同様に扱う**（言語間で対応の差が生まれないようにするため）。
3. 6時間以内を目安に内容を確認し、修正する。
4. 対応内容・原因・対応時刻を記録に残す（現在：手動メモ／将来：Audit Log DBへ自動記録）。
5. 対応が「速める」のはレビューの速度であり、Update Level 2・3で必要な人間の確認そのものを省略しない（Constitution §13）。

## 7. 法改正対応

1. Source LibraryでSource Type=政府／自治体、Tier=高の情報源を定期的に確認する（現在：手動／将来：Source Monitorが自動検知しResearchを自動起票）。
2. 変化を見つけたら、Researchを新規作成する。Category=法律・制度、Evidence Levelを設定する（一次情報源で確認できた場合のみOfficial／Verifiedにする。推測の段階ではAI Suggested／Reportedのままにする）。
3. Research.Status=ConvertedとしてArticleを作成する。Update Levelは2（通常の法律・制度）または3（重要な法改正）を手動で設定する（現在：手動／将来：Law Update.SignificanceからFormulaで自動算出）。
4. Update Level 3相当の場合、内容を編集長自身が確認するか、法律に詳しい第三者に確認を依頼してから公開する（Mentor DBが未実装のため、現時点では編集部外の専門家への確認を都度手配する）。
5. 公開後、紐づく全Translationについて、Needs Re-Translationを手動でチェックし、翻訳を更新する。

## 8. 記事公開フロー

1. Editorial CalendarでStatus=Idea（着想）→ Planned（計画確定、Planned Date設定）
2. 調査が必要な場合はResearchを作成し、Linked Researchでリンクする
3. Articleを作成し、Linked Articleでリンクする。Status=Draft→AI Draft→Human Review→Approved→Published と進める
4. 各段階でConstitution第14章 Quality Checklistを満たしているか確認する
5. Published になったら、Editorial CalendarのStatusもPublishedへ更新する（現在：手動）

## 9. 翻訳フロー

1. Articleが Published になったら、対応するTranslationレコードを作成する（対象言語はLanguageプロパティで設定。現時点ではLanguage Master未実装のため11言語のSelectから選ぶ）
2. AI Translation Status：Not Started→Queued→In Progress→Done
3. Localization Status：Translated→Culturally Adapted（文化的補足が終わるまで、この先には進めない）
4. Review Level（Rollup、Article.Update Levelを反映）に応じて、Human Review Status／Publish Approvalを進める
5. Publish Status=Publishedにする
6. Article本体が更新された場合は、Needs Re-Translationを手動でチェックし、1〜5を再実行する（現在：手動／将来：Article.Updated Date変化でAutomationが自動検知）

## 10. 品質確認フロー

1. Article Templateの本文に埋め込まれたConstitution第14章 Quality Checklist（To-do）をすべて確認する
2. QA Statusを Not Started→Passed／Failed／Needs Reworkのいずれかに設定する
3. Failedの場合はStatusをHuman Reviewに戻し、修正後に再度確認する
4. Update Level 2・3の記事は、Human Reviewedにチェックが入るまでPublishedにしない
5. 翻訳がある場合、Localization Status=Culturally Adaptedを満たしているか確認する

---

## 現時点で手動運用となっている項目（一覧）

| 項目 | 現在 | 将来（実装フェーズ） |
|---|---|---|
| 情報源の変化検知 | 手動確認 | Source Monitor（Phase B3） |
| 記事不足・トレンド検出 | 目視 | Experience Intelligence／Knowledge Gap Engine（Phase B1後半〜B3） |
| Update Levelの自動算出 | 手動設定 | Law Update連携のFormula（Phase B3） |
| 専門家レビュー | 都度手配 | Mentor DB（Phase B5） |
| 実行ログ・監査記録 | 手動メモ | Audit Log／Dashboard（Phase B5） |
| KPI・カバレッジの集計 | 目視集計 | Dashboard（Phase B5） |
| 再翻訳の自動検知 | 手動チェック | Automation（Phase B2） |

---

*ARu HQ / Decode Japan — ARu Studio Operating Manual v1.0 — 2026-07-12*
