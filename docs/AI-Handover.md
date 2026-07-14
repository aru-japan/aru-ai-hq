<title>AI Handover Document</title>

# AI Handover Document

**この文書は人間の開発者向けではない。ChatGPT・Claude・Cursor・その他将来のAIが、この1ファイルだけを読んでこのプロジェクトの開発を継続できることを唯一の目的として書かれている。**

> この文書自体が古くなる可能性がある。「Latest Commit」「Current Phase」等のスナップショット情報は、必ず`git log`とNotionの実際の状態で裏を取ってから信じること。この文書は「地図」であり「現在地のGPS」ではない。

---

## ■ Project Overview

**ARu**は、外国籍の方が日本で安心して暮らし、旅行し、働けるようにサポートするAIプラットフォーム。コンセプトは「Decode Japan（日本を読み解く）」——「何をすべきか」だけでなく「なぜそうするのか」という文化的・制度的背景まで伝える。

このリポジトリ（`aru-ai-hq`）は、ARuを支える**編集部（ARu HQ）の運営基盤**——理念（Constitution）、設計（ER Design／Notion Builder Spec）、実装（Notion API連携スクリプト＋AI生成パイプライン）を1つにまとめたもの。ARuというアプリ本体のコードはこのリポジトリには含まれない。ここにあるのは「記事を作り、翻訳し、SNSへ出すまでの編集部そのもの」。

## ■ Mission

ARu Constitution（`docs/ARu-Constitution.md`）が定める最上位の目的：

> AIが調査・執筆・翻訳・SNSを担当し、人は最終確認だけを行う体制を作る。

ただし、これは「AIに任せて終わり」という意味ではない。**Update Level 2・3（法律・ビザ・税金・医療等）の内容は、AIがどれだけ高いスコアで評価しても、必ず人間が最終承認する。** この一線は、コード（`enforce_publish_gate.py`等）でも強制されている、単なる方針ではなく実装上の制約。

## ■ Architecture

編集部のコンテンツパイプラインは、以下の9段階（Notionデータベース＋Pythonスクリプトの組み合わせ）で構成される。

```
Research → Article → Article Review → Translation → Translation Review → SNS → SNS Review → Publish Gate
```

| 段階 | スクリプト | 入出力 |
|---|---|---|
| Research | `sync_source_monitor_to_research.py` | Source Monitor → Research |
| Article | `generate_article_pipeline.py article` | Research → Articles（実Claude API生成、**ARu公式テンプレート＝9セクション構成**で統一。`Verification Status`／`Last Verified Date`を必ず保存） |
| Article Review | `reviewer_agent.py` | Articles（5観点スコアリング：Accuracy/Evidence/Readability/Risk/Localization） |
| Translation | `generate_article_pipeline.py translation` | Articles → Translation（実Claude API生成、文化的補足を自己評価） |
| Translation Review | `translation_quality_reviewer.py` | Translation（5観点：Meaning Accuracy/Naturalness/Cultural Adaptation/Terminology/Hallucination Risk） |
| SNS | `generate_article_pipeline.py sns` | Articles → SNS Queue（Instagram/Threads/X、実Claude API生成） |
| SNS Review | `sns_quality_reviewer.py` | SNS Queue（5観点：Accuracy/Platform Fit/Engagement/Cultural Sensitivity/Risk） |
| Publish Gate | `enforce_publish_gate.py` | Articles（QA Status・Review Result・Human Reviewedを横断確認） |

**ゲートの核心ロジック**：Update Level（Articleのプロパティ、1〜3）によって挙動が分岐する。

- **Level 1**（イベント・観光・文化・生活情報等）：レビューPass＋Localization Status=Culturally Adaptedが揃えば、Translation.Publish Approvalは**AIが自動で`Not Required`へ**遷移させてよい（実証済み、Day 2）
- **Level 2・3**（法律・ビザ・税金・医療・重要な法改正等）：レビューが何点でも、Publish Approvalは**必ずPendingのまま**。人間（編集長Reiまたは専門家）の承認を経て初めてPublished

## ■ Current Database Structure（既存10DBのみ）

すべて実際にNotion上に作成済み。**新規データベースは追加しない**のが原則（後述）。

| Database | 役割 |
|---|---|
| Articles | 日本語マスター記事（唯一の公開DB） |
| Research | 調査・記事候補 |
| Translation | 記事の子DB。言語ごとの翻訳・レビュー・公開状況 |
| Source Library | 情報源のマスター台帳 |
| Editorial Calendar | 編集スケジュール・公開予定管理 |
| Experience Intelligence | Knowledge Gap Engine／Opportunity Intelligence |
| Source Monitor | 情報源の変化検知ログ |
| Law Update | 法改正の編集管理DB |
| Event Calendar | 祭り・イベント等の体験編集DB |
| SNS Queue | Instagram/Threads/X/Facebook/LinkedIn/TikTok投稿管理 |

**まだ存在しないDB（Deferred、削除ではなく保留）**：Language Master、Region Master、Mentor、AI Agents、Prompt Library、Automation。これらは実運用で必要性が確認できてから個別に追加する方針（`docs/Roadmap.md`参照）。**新しいAIがこれらを勝手に作らないこと。**

## ■ Current Automation（Phase B3.6〜B3.10、コードで実装済み）

すべて`notion-build/automation/`（一部`scripts/`）にあり、標準ライブラリのみで動作（pip installは不要）。

- **B3.6** `scripts/ai_gateway.py`：Claude API／OpenAI APIのどちらでも呼び出せる共通ゲートウェイ
- **B3.7/B3.11** `notion-build/automation/generate_article_pipeline.py`：`article`／`translation`／`sns`／`all`の4サブコマンド。Research→Article→Translation→SNSを実Claude APIで生成
- **B3.8** `reviewer_agent.py`：Article 5観点レビュー
- **B3.9** `translation_quality_reviewer.py`：Translation 5観点レビュー＋Publish Approvalゲート
- **B3.10** `sns_quality_reviewer.py`：SNS 5観点レビュー
- その他：`daily_briefing.py`（CLI版Dashboard）、`check_translation_gaps.py`、`sync_source_monitor_to_research.py`、`escalate_law_significance.py`、`sync_editorial_calendar_status.py`、`enforce_publish_gate.py`、`research_assistant.py`、`article_assistant.py`
- **一括生成** `notion-build/bulk_generate_articles.py`（旧`bulk_generate_20_articles.py`）：`TOPICS`リストを差し替えるだけで、Research→Article（9セクションテンプレート）→Review→Translation→Review→SNS×3→Reviewのフルパイプラインを日々再利用できる汎用スクリプト
- **Version 4準備** `article_freshness_monitor.py`：Update Levelごとのレビュー間隔（L1=90日／L2=30日／L3=14〜30日）を超過した記事、およびLaw Update/Source Monitor/Event Calendarで変化が検知された記事を`Freshness Status=Needs Update`にし、Dashboard最上部の「🔴 Update Needed」へ反映（新規DBなし、既存Articles DBへのプロパティ追加のみ）
- **Version 4準備** `coverage_analyzer.py`（＋`life_topics.py`／`backfill_life_topics.py`）：既存Category（Update Level判定用、変更なし）とは別に`Life Topics`（22トピックのMulti-select）を新設し、記事数・鮮度・Review待ちをトピック別に集計。AIが不足トピック・優先トピック・おすすめ新規テーマ（10件）を「外国籍の方の生活への影響度」の視点で提案し、Dashboard「📊 Coverage Analysis」＋専用Notionページ（計算済みサマリーをTable Blockとして毎回上書き生成）に反映
- **Version 4 Phase 2** `editorial_planner.py`：Coverage Analyzerのデータから★1〜5の優先編集プランを生成（★の算出はLife Topic Impact×記事数の決定論的ロジック、AIはReason／タイトル案／Expected Categoryの生成のみ担当）。`--generate-research`で選択したプラン項目のResearchレコードを自動作成（新規プロパティなし、Research DB既存の`Gap Engine`／`AI Suggested`選択肢を利用）。Dashboard「📝 Editorial Planner」＋専用Notionページに反映

詳細と実行方法は`docs/Automation-Scripts.md`。

## ■ Current Phase

**Roadmap Version 3.5（Pilot Operation）Day 2まで完了。** AI編集部を7日間実運用して検証する段階の2日目。

## ■ Latest Commit

`5cbd2de`（このHandover文書を書いた時点でのHEAD）。**必ず`git log --oneline -10`で実際の最新を確認すること。** このフィールドは経年劣化する。

## ■ Roadmap Current Position

（`docs/Roadmap.md`が正。ここは要約）

| Version | 状態 |
|---|---|
| 1 — Foundation | ✅ 完了 |
| 2 — AI Intelligence | ✅ 完了（Language Master/Region Master/MentorはDeferred） |
| 3 — AI Automation | ✅ 完了（AI Agents/Prompt Library/Automation DBはDeferred、実体はPythonスクリプト） |
| 3.5 — Pilot Operation | 🔶 進行中（Day 2／7完了） |
| 4 — Enterprise | ⏳ 未着手。Pilot完了後、かつ対外的な意思決定を要するため、実装だけでは進められない |
| 5 — Global | ⏳ 未着手 |

## ■ Completed Features

- ARu Constitution v2.0.0、AI Agent Constitution v1.1.0（統治文書一式）
- ER Design／Notion Database Builder Spec（全DB設計、Universal Properties）
- 実装済み10DB（すべて実データ・テストレコードあり）
- View/Template設定ガイド（Notion UI手動設定手順）
- Operating Manual（編集長向けSOP）
- AI Editorial Brain設計（6エージェント：Editor-in-Chief/Researcher/Writer/Reviewer/Translator/Social Manager、既存9ロールとのマッピング済み）
- AI Gateway（実Claude API接続確認済み。OpenAI経路は未検証）
- Research→Article→Translation→SNSの生成パイプライン（独立サブコマンド化済み、Phase B3.11）
- Article／Translation／SNSの3段階品質レビュー（すべて実データ・実APIでテスト済み）
- Publish Gate（Constitution §9/§13をコードで強制）
- Update Level 1の自動承認経路（Publish Approval→Not Required）を実データで実証
- 記事本文のARu公式テンプレート統一（9セクション）、`Verification Status`／`Last Verified Date`の記録（2026-07-14）
- Article Freshness Monitor（Version 4準備）：Update Levelごとのレビュー間隔管理＋Law Update/Source Monitor/Event Calendarとの連携による強制再レビューフラグ、Dashboard最上部「🔴 Update Needed」（2026-07-14）
- Coverage Analyzer（Version 4準備）：Life Topics（22トピック）によるカテゴリ分析＋AIによる不足分析・優先トピック・新規テーマ提案、Dashboard「📊 Coverage Analysis」＋専用ページ（2026-07-14）
- Editorial Planner（Version 4 Phase 2）：★1〜5の優先編集プラン自動生成＋`--generate-research`によるResearchレコード自動作成、Dashboard「📝 Editorial Planner」＋専用ページ（2026-07-14）

## ■ Remaining Tasks

- **ARu Constitutionの改訂提案が承認待ち**（Pending Amendments、提案日2026-07-14、Level B、レビュー期間72時間→発効予定2026-07-17以降）。ARu公式9セクションテンプレートとArticle Freshness Monitorの実態を§4・§11へ反映する内容。**2026-07-17以降、編集長（Rei）の承認を得たら**、`docs/ARu-Constitution.md`の該当箇所を本文へ反映し、v2.0.0→v2.1.0へバージョンアップ、Revision Historyに記録し、Pending Amendments節から該当エントリを削除すること
- **Editorial Plannerが提案した19件のResearch（Status=New、Discovery Method=Gap Engine）がレビュー待ち**（2026-07-14、`editorial_planner.py --generate-research`で作成）。Dashboard「⑥ Today's Research」に表示される。Reiが内容を確認し、実際に記事化するものを選んで`generate_article_pipeline.py article`または`bulk_generate_articles.py`のTOPICSへ追加する
- Article.Status自体をAI Draft→Publishedへ自動昇格させるスクリプトが存在しない（Translation側のゲートのみ実証済み）
- 定期実行（cron/launchd）は未設定。すべて手動実行
- Critical Gap等の外部通知（Slack/メール）は未実装
- SNS実投稿（実際にプラットフォームへ投稿する部分）は未実装。Draft生成まで
- Pilot Operation Day 3〜7が残っている
- Deferred中の6DB（Language Master等）
- Audit Logの永続化（現状はGitコミット履歴とターミナル出力のみ）
- AI Gatewayのopenaiプロバイダ経路は未検証（Claudeのみ実績あり）

## ■ Known Limitations

- **NotionパブリックAPIはViewやTemplateを作成できない。** 手動設定が必要（`docs/View-Template-Guide.md`）
- **NotionパブリックAPIは「Linked view of database」ブロックを作成できない。** DashboardはPage＋説明文のみで、実際のフィルタ済みビューは手動で埋め込む必要がある
- Notionのrich_textは1項目あたり2000文字制限（`rich_text_chunks()`で分割対応済み）
- Notion Formulaの構文は不安定な場合がある（`dateBetween()`は動くが、日付プロパティ同士の直接`>`比較が失敗した例がある）
- GitHubへのPushは、このBash実行環境では非対話認証ができず失敗する。人間が自身のターミナルで`git push`を実行する必要がある（過去、一度認証が通れば以降のPushは成功している）
- スケジューリングの仕組みがないため、すべてのスクリプトは手動実行が前提

## ■ Design Principles

新しいAIがこのプロジェクトに手を加える際、必ず守ること。

1. **Constitution First**：`docs/ARu-Constitution.md`が最上位の権威。コードの挙動とConstitutionが矛盾する場合、直すべきはコードであってConstitutionではない
2. **No New Database**：新規データベースの追加は、Reiに個別確認してからのみ行う。既存DB・既存プロパティの拡張、またはPythonスクリプトでの対応をまず検討する
3. **Human Review First**：Update Level 2・3のコンテンツは、AIのスコアがどれだけ高くても、AI単独でPublished／Publish Approval=Approvedにしてはならない。これは方針ではなくコードで強制されている制約
4. **Provider Agnostic**：AI呼び出しは`scripts/ai_gateway.py`経由で行い、Claude/OpenAIどちらか一方に決め打ちしない
5. **Quality First**：生成されたコンテンツは、Article／Translation／SNSそれぞれ5観点でスコアリングしてから次の工程へ進める。低スコアは黙って無視せず、Statusを進めない形でブロックする

## ■ Recovery Procedure（新しいAIが読む順番）

1. **この文書（`docs/AI-Handover.md`）** — 最初に全体像をつかむ
2. **`docs/ARu-Constitution.md`** — 何を優先するかの原則。ここに反する変更は絶対にしない
3. **`docs/Roadmap.md`** — 現在地と、次に何をすべきか
4. **`docs/Automation-Scripts.md`** — 実際に存在するコードと、その動作実績
5. **`docs/Operation-Checklist.md`** — 実データ・実APIで何を検証済みか（Day別ログ）
6. **`docs/AI-Agent-Constitution.md` → `AI-Agent-Architecture.md` → `AI-Agent-Workflow.md` → `AI-Editorial-Brain.md`** — AIエージェントの権限・振る舞いを変更する場合はここを必ず参照
7. **`notion-build/.env.example`** — 必要な設定キーの一覧を確認する（**`notion-build/.env`自体は絶対に読み上げない・表示しない・コミットしない。中身は秘密情報**）
8. **`git log --oneline -20`** — この文書の「Latest Commit」が古くなっていないか確認する
9. Notion側の実データを確認する（`NOTION_TOKEN`を使い、`notion-build/automation/daily_briefing.py`を実行すると現状が一望できる）

---

*ARu HQ / Decode Japan — AI Handover Document v1.1 — 2026-07-14*
