<title>ARu Studio v4.1 Release Notes</title>

# ARu Studio v4.1 Release Notes
### Editorial Intelligence — Story Bank as QA-card origin, Law Update as the update queue

| | |
|---|---|
| **Status** | Released（正式リリース） |
| **Date** | 2026-07-19 |
| **対象読者** | 将来の開発者・協働者・ステークホルダー全員 |
| **位置づけ** | ARu Studioのエンジニアリング・マイルストーン。実運用フェーズへの移行に伴う正式クロージング文書 |
| **⚠️ 命名についての重要な注記** | 本書の「v4.1」は**Studio側のエンジニアリング・マイルストーン**であり、[Roadmap.md](./Roadmap.md)が定義する対外的な**Business Roadmap「Version 4 — Enterprise」**（自治体・JNTO連携等、現状0/5・未着手）とは独立したカウンタである（[Version4-Completion-Report.md](./Version4-Completion-Report.md)で確立した命名規則）。**Gitタグも同じ理由で`v4.1.0`ではなく`studio-v4.1.0`とした**——本リポジトリの既存タグ（`v1.1.0`／`v2.0.0`／`v3.0.0`／`v3.5.0`）は歴史的にBusiness Roadmapのバージョン番号に対応しており、Business Roadmapに存在しない「Version 4.1」として`v4.1.0`を打つと、あたかも3.5の次にBusiness Roadmapが4.1へ進んだかのような誤解を生むため |

---

## 1. Executive Summary

ARu Studio v4.1「Editorial Intelligence」は、Story Bankを**QAカードの起点**、Law Updateを**更新キュー**として本格運用する段階へ移行させ、Source Monitorの変更検知から影響コンテンツの抽出・優先度付け・定期レビューまでを一貫した編集運営フローとして実装した。

**方針**：新規プロパティの追加より既存資産の拡張を優先する（Rei明示指示）。実装前に4つのDBの実スキーマをAPIで取得し、要求項目の多くを既存プロパティ・既存リレーションの再利用で満たした——詳細な再利用表は[Automation-Scripts.md](./Automation-Scripts.md)参照。

**段階的実装**：Schema → Relations → Automation → Templates → Dashboard → Docsの順に実装し、各段階を実データで検証（データ損失ゼロ、重複プロパティ・重複リレーションゼロ）。初回リリース後、Reiからの2回の追加指示（編集運営フローの精緻化、Production Stage）を経て今回の正式リリースに至った。

---

## 2. What's New

### スキーマ（既存資産の再利用を優先）
- Story Bank：15→32プロパティ（QAカード関連フィールド、Content Category、Audience再利用等）
- Articles：66→77プロパティ（Content Type、Current Validity、Production Stage等）
- Source Monitor：18→25プロパティ（Target Category、Source Libraryからのrollup5種）
- Law Update：31→41プロパティ（Update Type、Previous/New Rule、Affected Category等）
- 新規リレーション7本（Story Bank⇄Source Library、Source Monitor⇄Law Update等、重複0件確認済み）

### 自動化
- `notion-build/automation/law_update_pipeline.py`（新規）：Source Monitorの変更検知→Law Update候補作成→**人間の確認**→影響するQA・記事(Content Type別)・SNS投稿の一覧化とPriority自動算出→**人間の改訂**→Translation連携→**人間の公開**→Version/Last Verified Date更新、という8段階のHuman-in-the-loopパイプライン。AIはPublishedを一切設定しない
- `notion-build/automation/review_scheduler.py`（新規）：Update Frequencyにもとづく Next Review自動算出と、定期レビュー期限切れコンテンツの自動抽出（Event-Basedは年が特定できないため対象外、意図的）

### テンプレート
- `article_template.py`のTEMPLATESレジストリへ5種追加：headline／deep_guide／premium／update_notice／food_restriction（安全性に関わるため専用の捏造禁止プレースホルダーつき）
- QA Card Template・Existing Article Revision Templateを追加（前者はStory Bank内容所有権ルールにより自動生成には接続していない）

### ダッシュボード（`ai_command_center.py`）
- 先頭3セクションを「🆕 今日追加するQA」「🔴 更新が必要な記事」「🚀 公開待ちコンテンツ」に再構成（Rei指示）
- 「⚖️ 法改正・制度変更キュー」「📋 Production Stage内訳」等を追加。既存セクションは削除せず詳細として維持

### Production Stage（Story Bank・Articles両方）
- 「Today's QA → Headline Ready → Basic Writing → Deep Writing → Translation → SNS → Ready → Published」という制作パイプラインを、両DBに独立したSelectとして追加
- 既存のStatus（編集・承認状態）とは明確に役割分離。スキーマのみでバックフィルなし

### 手動設定（Notion公開APIの制約により自動化不可）
- 24＋2ビュー（Story Bank 8／Articles 8／Source Monitor 4／Law Update 6、うちProduction Stage用Kanban 2）の設定手順を[Studio-v4.1-View-Setup-Guide.md](./Studio-v4.1-View-Setup-Guide.md)に記載

---

## 3. Verification Summary

- 各段階で実データに対して実行し、レコード件数の減少がないことを確認（Story Bank 21件・Articles 59件・Source Monitor 2件・Law Update 5件、いずれも操作前後で一致）
- 重複プロパティ・重複リレーションともに0件（既存の意図的な2重リレーションは本リリース以前からのもの、区別済み）
- 標準回帰スクリプト（`article_freshness_monitor.py`／`publishing_center.py`／`enforce_publish_gate.py`／`coverage_analyzer.py`／`duplicate_prevention_report.py`／`source_watcher.py`／`template_migration_report.py`）を各実装段階で再実行、全通過
- 検証のため一時的に作成したテストレコード（Law Update候補2件、E/F動作確認用1件）は検証後すべてArchived。実データ検証で一時的に使用したStory Bank本番レコード1件（Update Frequency／Last Reviewed／Next Review）は確認後に元の未設定状態へ復元済み

---

## 4. Known Limitations（リリース時点）

- `Previous Rule`（変更前の生テキスト）は自動保存できない——`source_watcher.py`はSimHash指紋のみ保存し全文を残さないため
- SNS Queueには「要更新」を表すプロパティが無く、Law Update Pipeline のGステップはTranslationのみ対応
- `generate_article_pipeline.py`のCLIは`--content-type`引数を持たず、新規生成記事のテンプレート振り分けは記事作成後の手動設定に依存
- Food Restriction Supportテンプレートは登録済みだが、Story Bank→Article自動生成パイプライン自体が未実装のため到達しない
- Production Stageを自動で進める仕組み（QA Question設定→Headline Ready等）は未実装
- Next Reviewの起点日はLast Reviewed／Last Verified Date未設定の場合ページ作成日にフォールバックするのみで、Event-Based頻度は自動算出対象外
- カンバン（Board View）そのものはNotion公開APIで作成不可のため手動設定が必要

---

## 5. What's Next

**v4.1をもって新機能開発を一時停止し、実運用フェーズへ移行する（Rei決定、2026-07-19）。** Version 4.2は、実運用から得られる知見（どの自動化が実際に使われるか、Production Stageの手動運用で見えてくる摩擦点、Law Update Pipelineの実際の検知頻度等）にもとづいて設計する。したがって、上記「Known Limitations」を今すぐ埋める計画は現時点ではない——実運用が必要性を証明したものから着手する。

---

*ARu HQ / Decode Japan — ARu Studio v4.1 Release Notes — 2026-07-19*
