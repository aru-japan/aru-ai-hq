<title>START HERE</title>

# START HERE
### このプロジェクトを10分で理解する

**新しいAI（ChatGPT・Claude・Cursor等）、新しい開発者、あるいは記憶をなくした未来のRei自身へ。**
このドキュメントは、ARu HQリポジトリに初めて（あるいは久しぶりに）触れる誰かが、10分でプロジェクト全体像を掴めることだけを目的に書かれている。ここから先の詳細作業は[AI-Handover.md](./AI-Handover.md)、セッションを完全に失った場合は[Recovery-Guide.md](./Recovery-Guide.md)を使う。

---

## 1. Project Overview（このプロジェクトは何か）

**ARu**は、外国籍の方が日本で安心して暮らし、旅行し、働けるようにサポートするAIプラットフォーム。コンセプトは**「Decode Japan（日本を読み解く）」**——「何をすべきか」だけでなく「なぜそうするのか」という文化的・制度的背景まで伝える。

このリポジトリ（`aru-ai-hq`）は、**ARuというアプリ本体ではない**。ARuを支える**編集部（ARu HQ）の運営基盤**——理念（Constitution）、データ設計（Notion）、実装（Python自動化スクリプト＋AI生成パイプライン）を1つにまとめたもの。「記事を作り、翻訳し、SNSへ出し、公開管理するまでの編集部そのもの」がここにある。

**最上位の権威は[ARu Constitution](./ARu-Constitution.md)。** コードとConstitutionが矛盾する場合、直すべきはコードであってConstitutionではない。

---

## 2. Required Reading Order（読む順番）

| 順番 | 読むもの | 目的 | 所要時間 |
|---|---|---|---|
| 0 | **この文書（START-HERE.md）** | 全体像の把握 | 10分 |
| 1 | [AI-Handover.md](./AI-Handover.md) | 開発を継続するための本体文書。Architecture／Current Phase／Remaining Tasksまで | 15分 |
| 2 | [ARu-Constitution.md](./ARu-Constitution.md) | 何を優先するかの原則。ここに反する変更は絶対にしない | 20分（§1〜3, §9, §13, §20だけなら5分） |
| 3 | [Roadmap.md](./Roadmap.md) | 現在地（Version 1〜5のどこにいるか） | 5分 |
| 4 | [Automation-Scripts.md](./Automation-Scripts.md) | 実際に存在するコードと実行方法・実データでのテスト結果 | 必要な箇所だけ拾い読み |
| 5 | [Version4-Status.md](./Version4-Status.md) | 直近のスナップショット（実装機能・記事数・課題・次にやること） | 5分 |

**セッション（チャット履歴）を完全に失った場合は、上記の代わりに[Recovery-Guide.md](./Recovery-Guide.md)の10ステップに従うこと。**

---

## 3. Current Version（現在のバージョン）

- **Roadmap**：Version 1・2・3は完了（一部Deferred）。**Version 3.5（Pilot Operation：7日間実運用）Day 2/7まで完了**。Version 4（Enterprise）は前提条件（Pilot完了）未達のため正式着手前——ただし技術的な準備作業（Phase 1〜3）はPilot期間中に先行実装済み。
- **Version 4準備状況**：Phase 1 Article Freshness Monitor／Phase 1 Coverage Analyzer／Phase 2 Editorial Planner／Phase 3 Publishing Center、すべて実装・実データテスト済み（詳細は[Version4-Status.md](./Version4-Status.md)）。
- **ARu Constitution**：v2.0.0（Active）。**Pending Amendments（未承認の改訂提案）が2件**、§20 Governanceの正規プロセスに沿って承認待ち（発効予定2026-07-17以降）。詳細はConstitution本文の「Pending Amendments」節を参照。

---

## 4. Current Architecture（現在の構成）

**新規データベースは追加しない**のが一貫した方針。既存10DB＋Pythonスクリプトの拡張だけで機能を積み上げている。

**Notion 10データベース**：Articles／Research／Translation／Source Library／Editorial Calendar／Experience Intelligence／Source Monitor／Law Update／Event Calendar／SNS Queue

**実装場所**：

| フォルダ | 役割 |
|---|---|
| `notion-build/` | Notion APIでDBを構築するスクリプト一式（`notion_api.py`が最小限のAPIクライアント、標準ライブラリのみ） |
| `notion-build/automation/` | 日々の運用を担う自動化スクリプト（生成・レビュー・鮮度管理・カバレッジ分析・編集計画・公開管理） |
| `scripts/ai_gateway.py` | Claude API／OpenAI APIのどちらでも呼び出せる共通ゲートウェイ |

**Update Level（1・2・3）による人間承認ゲート**が全体を貫く中核ロジック：Level 1はAIレビューPass＋文化的補足完了で承認ゲートが自動解除されるが、**Level 2・3はAIスコアに関わらず必ず人間が承認する**（コードで強制、方針ではない）。**ARuアプリへの実際の掲載（Publishing Status=Published）は、どのUpdate Levelでも常に人間が行う。AIが自動公開することは一度もない。**

---

## 5. Current Dashboard（現在のDashboard構成）

Notion上の「ARu Studio Dashboard」ページ（編集長ホーム画面）。上から順に、今すぐ判断が必要なもの→今日の予定→外部シグナルの並び。

| # | セクション | 見るもの |
|---|---|---|
| 🔴 | Update Needed | 鮮度切れ（Freshness Status=Needs Update）の記事、外部シグナル起因を含む全件 |
| 📊 | Coverage Analysis | 生活トピック別の記事数・不足分析・おすすめ新規テーマ（専用ページへのリンク） |
| 📝 | Editorial Planner | ★1〜5の優先編集プラン（専用ページへのリンク、Research自動作成アクション付き） |
| 🚀 | Ready to Publish | 公開条件をすべて満たした未公開記事 |
| 📚 | Published Articles | ARuアプリへ手動掲載済みの記事 |
| 🛠 | Needs Update（公開済み） | 掲載済みだが鮮度切れになった記事 |
| ① | Publish Approval Pending | 人間の承認待ちTranslation |
| ② | Article Review Waiting | AIレビュー待ちArticle |
| ③ | Translation Review Waiting | AIレビュー待ちTranslation |
| ④ | SNS Draft Waiting | レビュー未通過のSNS Draft |
| ⑤ | Today's Editorial Calendar | 今日の編集予定 |
| ⑥ | Today's Research | 新規Research（Editorial Plannerの提案もここに現れる） |
| ⑦ | Source Monitor Alerts | 情報源の変化検知 |
| ⑧ | Recent Law Updates | 最近の法改正 |
| ⑨ | Recent Event Calendar | 直近のイベント |

**NotionパブリックAPIは「Linked view of database」を自動作成できないため、🔴〜🛠と①〜⑨の13セクションすべて、Linked View自体は人間が手動で設定する必要がある**（手順：[Dashboard Setup Guide](./Dashboard-Setup-Guide.md)）。📊と📝の2つだけは専用ページへのリンクなので対象外。

**Editor Home／AI Command Center（Version 4 Phase 5、2026-07-16追加）**：上記Dashboardとは別の、ARu Studioルート配下にある2つの独立したナビゲーションハブページ。Dashboardの13 Linked Viewを再現するのではなく、その数値だけを同一フィルタで再計算して見せ、実際の操作はDashboardへのリンクで戻す設計。

- 🏠 **Editor Home**：「今日、人間が決めること」——Ready to Publish／Published／Needs Update／Publish Approval Pending／Article Review Waiting／Translation Review Waiting／SNS Draft Waiting／Today's Editorial Calendar／Today's Researchの9件数
- 🤖 **AI Command Center**：**ARu Intelligence Phase 3（2026-07-18）で「編集長が毎日最初に見るページ」として再構成。** 先頭5セクションが🎯 Today's Opportunities（近日イベント・本日の情報源変化・法改正・季節性Research候補）／🔴 Critical Updates／📊 Top Research Candidates（`research_prioritizer.py`の5軸スコアリング）／🚀 Publishing Queue／🕐 Recently Updated Articles。その下にPhase 1/2からのFreshness内訳・Duplicate Prevention・外部監視フィード・Source Intelligence・Coverage Analysis/Editorial Plannerへのポインタが根拠情報として続く

両ページとも`notion-build/automation/editor_home.py`／`ai_command_center.py`を再実行すれば最新値に上書きされる（ページIDは`.env`の`EDITOR_HOME_PAGE_ID`／`AI_COMMAND_CENTER_PAGE_ID`）。あわせて、Articleページ本文自体も`render_article_layout.py`によりARu公式9セクション（5つは本文フロー、4つはtoggle折りたたみ）としてブロック描画されるようになった（Bodyプロパティは不変、表示専用）。プロパティパネルのグループ化は[Article Property Panel Guide](./Article-Property-Panel-Guide.md)（手動設定、Notion UI機能のためAPI非対応）を参照。編集ワークフロー全体の1枚図は[Editorial Workflow](./Editorial-Workflow.md)を参照。

---

## 6. Current Workflow（現在のワークフロー）

**コンテンツ生成パイプライン**（1記事あたり）：

```
Source Library → Research → Article（Update Level判定・9セクションテンプレート）
  → Article Review → Translation → Translation Review → SNS×3 → SNS Review
  → Publish Gate（enforce_publish_gate.py） → Publishing Center（人間がPublished判定）
```

**日々の企画サイクル**（Version 4準備で追加）：

```
Article Freshness Monitor（鮮度チェック） → Coverage Analyzer（不足分析）
  → Editorial Planner（優先プラン生成 → --generate-researchでResearch自動作成）
  → （↑ 生成パイプラインの先頭 Research へループバック）
```

すべて`notion-build/automation/`配下のPythonスクリプトを手動実行する（**スケジューリング＝cron/launchd等の定期実行は未設定**、既知の制約）。

---

## 7. Current Documentation Hierarchy（ドキュメント階層）

```
README.md ─┬─ START-HERE.md（このファイル。最初に読む）
            ├─ Recovery-Guide.md（セッション消失時のみ）
            │
            ├─ AI-Handover.md（開発継続の本体文書）
            ├─ ARu-Constitution.md（最上位の権威、Pending Amendments含む）
            ├─ Roadmap.md（現在地）
            ├─ Automation-Scripts.md（実装カタログ）
            ├─ Version4-Status.md（直近スナップショット）
            │
            ├─ AI-Agent-Constitution.md ─┬─ AI-Agent-Architecture.md
            │                              └─ AI-Agent-Workflow.md
            ├─ AI-Editorial-Brain.md（Version 2.0 総括構想）
            │
            ├─ Notion-Builder-Spec.md（Notion実装仕様）
            ├─ ER-Design.html（データベース設計書）
            ├─ View-Template-Guide.md（Notion UI手動設定手順）
            ├─ Dashboard-Setup-Guide.md（Dashboard初回セットアップ、初心者向け）
            ├─ Article-Property-Panel-Guide.md（Articleプロパティのグループ化手順、Version 4 Phase 5）
            ├─ Editorial-Workflow.md（編集ワークフロー全体像、ARu Intelligence Phase 3）
            │
            ├─ Operating-Manual.md（編集長向けSOP）
            ├─ Pilot-Operation-Guide.md（7日間実運用の手順）
            └─ Operation-Checklist.md（日次チェックリスト＋Operation Log）
```

**権威の強さの順**：Constitution（理念・原則） > AI-Handover（現状の要約） > Roadmap／Automation-Scripts／Version4-Status（実装の記録） > その他の設計・手順書。矛盾を見つけたら、上位のドキュメントを正とし、下位を修正する。

---

*ARu HQ / Decode Japan — START HERE — 2026-07-14（Dashboard節・ドキュメント階層は2026-07-18追記）*
