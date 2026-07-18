<title>ARu Studio Operating Manual</title>

# ARu Studio Operating Manual
### 開発フェーズから運用フェーズへ — セッションの型（Session Types & Workflow Discipline）

| | |
|---|---|
| **Status** | Active |
| **Date** | 2026-07-18 |
| **対象読者** | このリポジトリで作業するすべてのAI・人間（Rei本人、将来この役割を引き継ぐ人、Claude/ChatGPT/Cursor等） |
| **位置づけ** | [`docs/Operating-Manual.md`](./Operating-Manual.md)（ARu Intelligence Operating Manual）は**編集運用**（記事・翻訳・SNS・公開判断）の手順書。本書はそれとは別に、**このリポジトリに対する作業そのもの**を6種類の「セッションの型」に分類し、それぞれの開始条件・標準手順・終了条件・Gitルールを定める。矛盾する場合は[ARu Constitution](./ARu-Constitution.md)・[AI-Handover.md](./AI-Handover.md)のDesign Principlesが優先 |
| **背景** | Version 1〜3・Version 4準備作業（Freshness Monitor〜ARu Intelligence Phase 3〜テンプレート再設計）が完了し、Reiが開発フェーズから運用フェーズへの移行を決定（2026-07-18）。新機能追加よりも「安定した運用の型」を優先する方針にもとづき作成 |

> 本書のセッション定義は、このリポジトリで実際に繰り返されてきたパターン（例：機能実装コミットの直後に実コミットハッシュを埋めるフォローアップコミットを作る、docs更新は必ずコードと同じセッション内で行う等）を明文化したものであり、新しいルールを外から持ち込んだものではない。

---

## セッションの選び方

| やりたいこと | 選ぶセッション |
|---|---|
| Pythonスクリプトの新規追加・既存ロジックの拡張 | [1. Development Session](#1-development-session) |
| 記事のレビュー・公開判断・Source Library/Event Calendarの更新など、Notion上の編集業務 | [2. Editorial Session](#2-editorial-session) |
| コードは変えず、docsを実態に合わせて更新する | [3. Documentation Session](#3-documentation-session) |
| ローカルのコミットをGitHubへ反映する | [4. Release Session](#4-release-session) |
| 既存の自動化・スキーマの不具合を直す（新機能は追加しない） | [5. Bug Fix Session](#5-bug-fix-session) |
| 毎日の始業・終業ルーティン | [6. Daily Operation Checklist](#6-daily-operation-checklist) |

判断に迷う場合、または具体例で確認したい場合は[7. Session Selection Guide](#7-session-selection-guide)の決定木を参照。AIどうしの役割分担（ChatGPT／Claude Code）は[8. AI Collaboration Rules](#8-ai-collaboration-rules)を参照。

---

## 1. Development Session

### Purpose
新しい自動化スクリプト・既存スクリプトへのロジック追加など、**コードに変更を加える**セッション。

### When to use
- 新しいPythonスクリプトを`notion-build/automation/`または`scripts/`に追加する
- 既存スクリプトに新しい判定ロジック・新しいプロパティ連携を追加する
- Notion DBへ新規プロパティを追加する実装を伴う（**新規データベースの追加はDesign Principle「No New Database」によりRei個別確認が前提**）

### Standard workflow
1. `git status`・現在のブランチを確認する
2. [`Version4-Status.md`](./Version4-Status.md)と[`AI-Handover.md`](./AI-Handover.md)の最新節を読み、実態を確認する（スナップショットを鵜呑みにせず`git log`と併用する）
3. 実装計画（対象ファイル・変更内容・確認方法）を提示し、**承認を待つ。承認前にコードは書かない**
4. 承認後、小さな単位で実装する
5. **実データ**に対して実行し動作確認する（テストデータではなく、実際のNotion DBに対して）。実行結果（件数・成功/失敗）を記録する
6. 影響範囲の回帰テストを実行する（§5 Bug Fix Sessionの標準回帰テストリストと共通）
7. `feat:` commitを作る
8. 該当するdocs（[Automation-Scripts.md](./Automation-Scripts.md)／[AI-Handover.md](./AI-Handover.md)／[README.md](../README.md)の「現在地」／[Roadmap.md](./Roadmap.md)）を**同じセッション内で**更新する（更新自体は[3. Documentation Session](#3-documentation-session)のルールに従ってよい）
9. 必要なら`docs: fill in actual commit hash for <feature> in AI-Handover.md`のフォローアップコミットを作る（このリポジトリの既存慣習）

### Start checklist
- [ ] `git status`を確認し、作業ツリーの状態を把握した
- [ ] 現在のブランチを確認した（通常は`main`）
- [ ] `Version4-Status.md`・`AI-Handover.md`の最新節を読んだ
- [ ] 実装計画をユーザーに提示し、承認を得た

### End checklist
- [ ] 実データで動作確認済み（実行結果を記録した）
- [ ] 標準回帰テスト対象スクリプトが全て正常動作した
- [ ] `git diff`が意図した範囲のみであることを確認した（`.env`等の秘密情報が含まれていないこと）
- [ ] `Automation-Scripts.md`／`AI-Handover.md`／`README.md`／`Roadmap.md`のうち該当するものを更新した、または更新タスクとして明示的に残した
- [ ] コミット済み

### Git rules
- 新しいコミットを作る（`--amend`はユーザーの明示的指示がない限り使わない）
- コミットメッセージは`feat: <内容>`
- 機能実装コミットの直後、`AI-Handover.md`のLatest Commitがまだplaceholderの場合は別コミット`docs: fill in actual commit hash for <feature> in AI-Handover.md`で追従する
- pushは行わない（[4. Release Session](#4-release-session)へ引き継ぐ）

---

## 2. Editorial Session

### Purpose
記事の企画・レビュー・翻訳確認・SNS確認・公開判断など、**コンテンツそのものを動かす**セッション。コードは変更しない。

### When to use
毎日の編集業務（AI Command Center確認、Research判断、公開判断、Source Library/Event Calendarの更新等）。

### Standard workflow
[`Operating-Manual.md` §1 Daily Editor Workflow](./Operating-Manual.md#1-daily-editor-workflow毎日やること)をそのまま使う（重複を避けるため本書では再掲しない）。週次・月次のメンテナンスも同じくOperating-Manual.md §2・§3を参照。

### Start checklist
- [ ] `python3 source_watcher.py` → `python3 ai_command_center.py`を実行し最新化した
- [ ] 🔴 Critical Updatesを最優先で確認した

### End checklist
- [ ] 新しく知った情報源・イベントをSource Library／Event Calendarへ登録した
- [ ] `Published`へ変更した記事があれば`Published By`／`ARu App URL`等が正しく記録されているか確認した
- [ ] Criticalとして扱った案件の経緯メモを残した（Audit Log DB未実装のため手動メモ、Operating-Manual.md §1参照）

### Git rules
通常なし（Notion操作のみで、このリポジトリのコード・docsには触れない）。運用手順書自体をセッション中に修正した場合は[3. Documentation Session](#3-documentation-session)のルールに従う。

---

## 3. Documentation Session

### Purpose
**コードは変更せず**、ドキュメントを実態（コード・Notion実データ・コミット履歴）と一致させるセッション。

### When to use
- Development Sessionでの実装後、反映が漏れているdocsに気づいた時
- 定期的なドキュメント点検（例：Version4-Status.mdのように、複数フェーズ分の追記が溜まった時）
- ユーザーから明示的に依頼された時

### Standard workflow
1. `git status`を確認する（作業ツリーがクリーンな状態から始める）
2. 対象ドキュメントを読む
3. 実際のコード・Notion実データ・`git log`と突き合わせ、差分を洗い出す
4. [README.md](../README.md)／[AI-Handover.md](./AI-Handover.md)／[Roadmap.md](./Roadmap.md)／[ARu-Constitution.md](./ARu-Constitution.md)との整合性を確認する（このリポジトリの既存慣習）
5. 発見した不一致・ギャップのうち、今回の更新スコープ外のものは直さず「発見事項」として明記する（例：Version4-Status.md 2026-07-18更新時に見つけた「Roadmap.mdがテンプレート再設計を未反映」という指摘）
6. 編集する
7. `git diff --stat`で変更がdocsのみであることを確認する
8. `docs:` commitを作る

### Start checklist
- [ ] `git status`がクリーン
- [ ] 対象ドキュメントと、関連する実装・コミット履歴を確認済み

### End checklist
- [ ] `git diff --stat`で変更がdocs配下のみであることを確認した
- [ ] クロスチェック対象（README／AI-Handover／Roadmap／Constitution）を確認し、結果を記載した
- [ ] コミットメッセージが変更内容を正確に説明している

### Git rules
- コミットメッセージは`docs: <内容>`
- 1回のセッションにつき基本1コミット
- pushはユーザーの指示を待つ（[4. Release Session](#4-release-session)参照）

---

## 4. Release Session

### Purpose
ローカルのコミットをGitHub（`origin/main`）へ反映し、関連ドキュメントの「Latest Commit」等を実際のハッシュで確定させるセッション。

### When to use
Development／Bug Fix／Documentation Sessionで作成したコミットを、GitHubへ送り出す時。

### Standard workflow
1. `git log --oneline -5`で直前のコミットを確認する
2. `git status`でクリーンであることを確認する
3. `AI-Handover.md`（該当すれば`Version4-Status.md`）の「Latest Commit」フィールドが実際のHEADと一致しているか確認し、placeholderのままなら`docs: fill in actual commit hash for <feature> in AI-Handover.md`コミットを追加する
4. **ユーザーに明示的なpush許可を確認する**（1回の許可を他のセッションに流用しない）
5. `git push origin main`を実行する
   - このBash実行環境からのGitHub非対話認証は失敗することがある（既知の制約、`AI-Handover.md` Known Limitations参照）。失敗した場合は実行すべきコマンドをユーザーに伝え、ユーザー自身のターミナルでの実行を依頼する
6. push成功をユーザーに報告し、実際にpushされたコミットハッシュを明示する

### Start checklist
- [ ] ローカルに未コミットの変更が残っていないか確認した
- [ ] Latest Commit系のドキュメントフィールドが最新か確認した
- [ ] ユーザーからpushの明示的な許可を得た

### End checklist
- [ ] `git status`で「up to date with origin/main」を確認した
- [ ] pushしたコミットハッシュをユーザーに報告した

### Git rules
- **force pushは使わない**（ユーザーが明示的に要求し、かつ理由を理解した場合を除く）
- pushは毎回ユーザーの明示的な許可を得てから実行する
- 非対話認証が失敗した場合、代替として`--no-verify`等でごまかさず、正直に失敗を報告してユーザーに実行してもらう

---

## 5. Bug Fix Session

### Purpose
既存の自動化・DBスキーマの不具合を修正するセッション。**新機能は追加しない**。

### When to use
[`Operating-Manual.md` §9 Troubleshooting Guide](./Operating-Manual.md#9-troubleshooting-guideトラブルシューティング)に載っている症状、または[`AI-Handover.md`](./AI-Handover.md) Known Limitationsに記載された未修正の根本原因に対応する時。

### Standard workflow
1. `git status`を確認する
2. 症状を**実データで再現・特定する**（推測で直さない）
3. 修正方針を提示し、承認を待つ（Development Sessionと同様、承認前にコードは書かない）
4. 承認後、最小の変更で修正する
5. 標準回帰テストを実データに対して再実行する
6. `fix:` commitを作る
7. `AI-Handover.md`のKnown Limitations／`Version4-Status.md`の該当項目を更新する（直した場合は該当項目を除去、根本原因が残る場合はその旨を明記する）

### Start checklist
- [ ] `git status`がクリーン
- [ ] 症状を実データで再現した（再現できない場合はその旨を記録）
- [ ] 修正方針をユーザーに提示し、承認を得た

### End checklist
- [ ] 標準回帰テスト（下記）を実データで再実行し異常なし
- [ ] `AI-Handover.md`のKnown Limitations／`Version4-Status.md`の現在の課題の記載を更新した
- [ ] コミット済み

### 標準回帰テスト（Development・Bug Fix Session共通）
```bash
cd notion-build/automation
python3 article_freshness_monitor.py
python3 publishing_center.py
python3 enforce_publish_gate.py
python3 coverage_analyzer.py
python3 editorial_planner.py
python3 duplicate_prevention_report.py
python3 source_watcher.py
```
いずれもエラーなく完走し、既存ロジックどおりの結果になることを確認する（Phase 1〜3・テンプレート再設計のいずれでもこのリストで回帰確認済み）。

### Git rules
- コミットメッセージは`fix: <内容>`
- 1つの不具合につき1コミットを基本とし、無関係な変更を混ぜない

---

## 6. Daily Operation Checklist

### Purpose
毎日の運用を型化し、抜け漏れなく回すための最短チェックリスト。判断に迷ったら該当するセッションへ進む。

### When to use
毎日、業務の開始時と終了時。

### Start checklist（朝）
- [ ] `python3 source_watcher.py` → `python3 ai_command_center.py`を実行した
- [ ] 🔴 Critical Updatesを最優先で確認した
- [ ] 📊 Top Research Candidates／🚀 Publishing Queueを確認した
- [ ] `git status`でリポジトリがクリーンな状態から始まっているか確認した（前回セッションの残作業がないか）

### End checklist（夜）
- [ ] 今日行った編集操作（公開判断・Source Library／Event Calendar登録等）を確認した
- [ ] コードを変更した場合、[1. Development Session](#1-development-session)または[5. Bug Fix Session](#5-bug-fix-session)の終了チェックリストを満たしている
- [ ] ドキュメントを変更した場合、[3. Documentation Session](#3-documentation-session)の終了チェックリストを満たしている
- [ ] `git status`で未コミットの変更が残っていないか確認した
- [ ] pushが必要な場合は[4. Release Session](#4-release-session)へ進んだ

### Git rules
このチェックリスト自体は原則コミットを発生させない。何かが発生した場合は、該当するセッション種別のGitルールに従う。

---

## 7. Session Selection Guide

### Purpose
複数のセッションにまたがりそうな依頼を受けたとき、どのセッション（またはその組み合わせ）から始めるべきかを1分で判断するためのガイド。

### 決定木

```
質問1: コード（.pyファイル、Notionスキーマ）を変更する必要があるか？
├─ Yes
│   質問2: 既存の不具合を直すのか、新しい機能を追加するのか？
│   ├─ 既存の不具合を直す        → 5. Bug Fix Session
│   └─ 新しい機能・ロジックを追加  → 1. Development Session
└─ No（コードは変更しない）
    質問3: 何を変更・実行するのか？
    ├─ .md等のドキュメントの記述を実態に合わせる → 3. Documentation Session
    ├─ Notion上の記事・翻訳・SNS・公開判断         → 2. Editorial Session
    └─ ローカルのコミットをGitHubへ反映するだけ     → 4. Release Session

補足：1・3・5のセッションは、作業完了後に必ず4. Release Sessionへ引き継ぐ
     （コミットは作るが、pushはRelease Sessionの役割）
```

### 実例（Practical examples）

| 依頼・状況の例 | 選ぶセッション |
|---|---|
| 「Source Watcherが特定のサイトで毎回タイムアウトする」 | 5. Bug Fix Session（既存スクリプトの不具合） |
| 「Editorial PlannerにVisa関連トピックの重み付けを追加したい」 | 1. Development Session（既存ロジックへの機能追加） |
| 「今日の🔴Critical Updatesを確認して、公開判断をしたい」 | 2. Editorial Session |
| 「Version4-Status.mdがまた古くなっている、直近のPhaseを反映して」 | 3. Documentation Session |
| 「さっきの修正コミットをGitHubに送って」 | 4. Release Session |
| 「新しいPythonスクリプトを書いて実データで確認、docsも直して、GitHubにも送って」 | 1 → 3 → 4 の順（1つの依頼が3セッションにまたがる複合依頼） |
| 「Roadmap.mdがテンプレート再設計を反映していない、直して」 | 3. Documentation Session（Version4-Status.md更新時に発見済みの既知ギャップ、§3参照） |
| 「毎朝やることを型通りにやりたい」 | 6. Daily Operation Checklist |

### 複合依頼の扱い方
1つの依頼が複数セッションにまたがる場合（例：「実装して、確認して、pushして」）は、**この順番を守る**：`1. Development` → （必要なら）`3. Documentation` → `4. Release`。Release Sessionのpushだけは、他の3つと違い**毎回独立してユーザーの許可を得る**（§4参照）。

---

## 8. AI Collaboration Rules

### Purpose
このプロジェクトでは、計画・設計を担当するAI（ChatGPT）と、実装・ドキュメント・Git操作を担当するAI（Claude Code）を役割分担する。両者が同じ作業を重複して行わないこと、また実装が承認前のプランを追い越さないようにすることが目的。

### 役割定義

| | ChatGPT | Claude Code |
|---|---|---|
| **担当** | Planning／Architecture／Prioritization／Review | Implementation／Documentation／Git operations |
| **主な成果物** | 実装計画、設計判断（例：DBスキーマ変更の要否、新規DB追加の是非）、複数候補の優先順位付け、実装後のレビュー観点の提示 | 実際のコード変更、docsの更新、コミット・push |
| **判断すること** | 「何を」「なぜ」「どの順番で」やるか | 承認された計画を「どう正確に実装するか」 |
| **判断しないこと** | コードの具体的な書き方 | 実装するかどうかの意思決定（Reiの承認なしに新規実装を始めない） |

### ChatGPTの役割
- **Planning**：次に何を実装すべきかの計画立案
- **Architecture**：DBスキーマ・リレーション・自動化フローの設計判断（例：新規DB追加が本当に必要か、既存DBの拡張で足りるか——Design Principle「No New Database」の判断もここに含まれる）
- **Prioritization**：Bug Fix／新機能／ドキュメント整備など複数候補の優先順位付け
- **Review**：実装後の内容レビュー、Constitution・Design Principlesとの整合性チェック

### Claude Codeの役割
- **Implementation**：承認された計画に基づくコード実装（[1. Development Session](#1-development-session)／[5. Bug Fix Session](#5-bug-fix-session)）
- **Documentation**：実装内容のdocsへの反映（[3. Documentation Session](#3-documentation-session)）
- **Git operations**：コミット作成・[4. Release Session](#4-release-session)によるpush

### 原則：実装は承認された計画があって初めて始まる

**Claude Codeは、Rei本人（またはChatGPTが立案しReiが承認した計画）から明示的に承認された実装計画がない限り、コードの実装を開始しない。** これは[1. Development Session](#1-development-session)・[5. Bug Fix Session](#5-bug-fix-session)のStandard workflowに既に組み込まれている「実装計画を提示し、承認を待つ」というステップと同じ原則であり、本節はそれをAI間の役割分担として明文化したものにすぎない。

- ChatGPTが計画を作った場合も、Claude Codeはその計画をそのまま鵜呑みにせず、実際のリポジトリの状態（`git status`／`git log`／`Version4-Status.md`／`AI-Handover.md`）と突き合わせてから実装に入る（計画立案時点と実装時点でリポジトリの状態がずれている可能性があるため）
- 計画とレビューをChatGPT、実装とその後の記録（コミット・docs）をClaude Codeが担当することで、「計画した人がそのまま実装し、自分で自分をチェックする」ことによるチェック漏れを防ぐ

---

## 9. Editorial Content Lifecycle

### Purpose
ARuのコンテンツが「発見」されてから「アーカイブ」されるまでの全体像を1本の流れとして定義する。個々の工程の実装詳細は[Automation Scripts](./Automation-Scripts.md)・[Editorial Workflow](./Editorial-Workflow.md)・[Operating-Manual.md](./Operating-Manual.md) §8 Publishing Workflowを参照し、本節はそれらを1つのライフサイクルとして串刺しで見せることに専念する。

### ライフサイクル全体図

```
Source Discovery
   ↓
Research Candidate
   ↓
Category Classification
   ↓
QA Card
   ↓
Standard Article
   ↓
Premium Article
   ↓
Translation
   ↓
Editorial Review
   ↓
Approved
   ↓
Published in ARu App
   ↓
SNS Distribution
   ↓
Periodic Update
   ↓
Archive
```

**凡例**：✅ 実装済み（実データで動作確認済み）／🔶 部分実装（一部は既存機能で担保、一部は人間の手作業または未実装）／🧭 概念段階（本書が定義する到達点で、現時点では専用の実装を持たない）。**正直な報告を優先する本プロジェクトの原則（Operating-Manual.md §12）に従い、まだ実装されていない工程も「実装済み」であるかのようには書かない。**

---

### ① Source Discovery ✅

- **Purpose**：ARuが常に最新・信頼できる情報を保つための入り口。既存コンテンツの鮮度維持と、新規ネタの発見の両方を担う
- **Input**：Source Library（`Status=Active`のレコード、`Check Frequency`で定義された巡回間隔）
- **Output**：変化を検知した場合のSource Monitorレコード（`Change Detected=true`、`Impact Level`、`Update Classification`、AI生成`Diff Summary`）。変化がなければSource Libraryの`Last Checked`のみ更新
- **Responsible AI workflow**：`source_watcher.py`（ARu Intelligence Phase 1/2、SimHash近似指紋比較）
- **Exit criteria**：ソースが正しくbaseline化されている、または変化がSource Monitorに記録されている。政府・自治体系の変化はフラグを立てるのみで、次工程（Research Candidate）へ進めるかどうかは人間が判断する

### ② Research Candidate ✅

- **Purpose**：Source Discoveryで見つかった変化、またはCoverage Analyzerが見つけた「不足」を、実際に記事化を検討できる粒度の候補へ変換する
- **Input**：Source Monitor（`sync_source_monitor_to_research.py`経由）、Coverage Analyzerの不足トピック（`editorial_planner.py --generate-research`経由）
- **Output**：Research DBレコード（`Status=New`、Category／Priority／Urgency設定済み）
- **Responsible AI workflow**：`sync_source_monitor_to_research.py`、`editorial_planner.py`、`research_prioritizer.py`（Freshness／Foreign Resident Value／Tourism Value／Seasonal Relevance／Premium Potentialの5軸スコアリングで優先順位付け）
- **Exit criteria**：編集者（Rei）が`Status`を`Converted`に変更し、実際に記事化することを決定する。`Rejected`になった場合はここでライフサイクルが終了する

### ③ Category Classification ✅

- **Purpose**：記事が「どのくらい慎重な取り扱いが必要か」（Update Level）と「誰の生活のどの場面に役立つか」（Life Topics）を、記事執筆の前に確定させる
- **Input**：Research CandidateのCategory（7分類）
- **Output**：`Update Level`（1〜3、`compute_update_level()`による決定論的な算出）、`Life Topics`（22トピック、Coverage Analyzer/`life_topics.py`による分類）
- **Responsible AI workflow**：`compute_update_level()`（決定論的）、`coverage_analyzer.py`／`life_topics.py`（Life Topics付与）、Editorial Plannerの`Expected Category`提案
- **Exit criteria**：Update Levelが確定している（Level 2・3であれば、この時点で「人間の最終承認が必須」という下流のゲート条件が確定する）

### ④ QA Card 🧭（概念段階）

- **Purpose**：本文を書き始める前に、情報源・想定読者・法的リスクの有無を短くチェックする「執筆前の最終チェックポイント」として位置づける
- **Input**：Category Classification済みのResearch Candidate
- **Output**：（目標）執筆着手の可否判定、注意事項のメモ
- **Responsible AI workflow**：**現時点で専用の実装はない。** 最も近い既存機能は、Articles DBの`QA Status`プロパティ（現状全記事で未設定、[Version4-Status.md](./Version4-Status.md) 4節13項参照）と、`reviewer_agent.py`が記事生成後に行う決定論的なテンプレート準拠チェック
- **Exit criteria**：（目標）QA Statusが設定され、執筆に進んで良いことが確認されている。**この工程を正式な実装にするかどうか（新規プロパティで足りるか、専用のチェックリストが必要か）はDevelopment Sessionでの計画立案（[8. AI Collaboration Rules](#8-ai-collaboration-rules)のPlanning）を経てから着手する**

### ⑤ Standard Article ✅

- **Purpose**：ARu公式テンプレートに沿った、無料で読める記事本体を生成する
- **Input**：Category Classification済みのResearch Candidate（`Status=Converted`）
- **Output**：Articles DBレコード（8セクション構成：Basic Answer／More Details／Cultural Background／ARu Tip［必須］／Things to Know／FAQ／Premium Section／Sources、`Priority`／`Urgency`をResearchから自動継承）
- **Responsible AI workflow**：`generate_article_pipeline.py article`、`article_template.py`（単一の情報源）、`reviewer_agent.py`（5観点スコアリング＋決定論的テンプレート準拠チェック）
- **Exit criteria**：Article Review Result=Pass、かつARu Tipセクションが存在する（`validate_sections()`で機械的に検証）

### ⑥ Premium Article 🔶（部分実装）

- **Purpose**：Standard Articleの中に、より実用的で対価に見合う付加価値（場所・タイミング・費用・予約・現地マナー等）を追加する
- **Input**：Standard Articleの`Premium Section`
- **Output**：確認済みの実用情報が入った`Premium Section`。確信が持てない情報は捏造せず「編集者による追加取材が必要」と明記する
- **Responsible AI workflow**：`generate_article_pipeline.py`（Standard Articleと同じ生成パスの一部としてPremium Sectionも生成）、`reviewer_agent.py`（Premium Sectionが無料部分の繰り返しでなく実用的価値を追加できているかをAIが評価）
- **Exit criteria**：Premium Sectionが存在し、reviewer_agentのレビューで「無料部分の重複ではない」と判定されている。**現状はStandard Articleと同じ1つのArticleページ内の1セクションであり、独立した別のレコード・別工程としては実装されていない**（`Usage Scope`＝Enterprise/Municipal PartnershipのようなDB単位でのプレミアム区分とは別物である点に注意）

### ⑦ Translation ✅

- **Purpose**：日本語のマスター記事を、対応言語へ展開する
- **Input**：Articles（Standard／Premium Articleとして完成した記事）
- **Output**：Translation DBレコード（言語ごと、`Quality Result`、`Publish Approval`）
- **Responsible AI workflow**：`generate_article_pipeline.py translation`、`translation_quality_reviewer.py`（5観点：Meaning Accuracy/Naturalness/Cultural Adaptation/Terminology/Hallucination Risk）
- **Exit criteria**：Translation Quality Result=Pass、かつPublish Approvalが`Not Required`（Update Level 1、AIが自動遷移可）または`Approved`（Level 2・3、人間の承認必須）

### ⑧ Editorial Review ✅

- **Purpose**：Article／Translation／SNSそれぞれの品質を、AIのスコアリングと（必要な場合の）人間のレビューで確定させる
- **Input**：Standard／Premium Article、Translation、SNS Queueの各ドラフト
- **Output**：各`Review Result`（Pass／Needs Revision／Fail）、Update Level 2・3では`Human Reviewed`フラグ
- **Responsible AI workflow**：`reviewer_agent.py`／`translation_quality_reviewer.py`／`sns_quality_reviewer.py`（いずれも5観点スコアリング）＋Update Level 2・3における人間（Reiまたは専門家）のレビュー
- **Exit criteria**：関係するすべての`Review Result`がPass。Update Level 2・3は追加で`Human Reviewed=true`が必須（**AIのスコアがどれだけ高くてもこの条件は省略されない**、Constitution §9・§13でコード上も強制）

### ⑨ Approved ✅

- **Purpose**：「ARuアプリに掲載してよい状態」であることを、5つの条件から機械的に判定する
- **Input**：Editorial Review済みのArticle／Translation
- **Output**：`Publishing Status=Ready to Publish`
- **Responsible AI workflow**：`publishing_center.py`（`evaluate_readiness()`：Article Review Result=Pass／全Translation Quality Result=Pass／全Translation Publish Approvalが Not Required か Approved／Freshness Status=Fresh／必須項目充足、の5条件すべて）
- **Exit criteria**：5条件をすべて満たし`Ready to Publish`になっている。**この時点でもAIはPublishedへは進めない**——次工程は必ず人間の操作

### ⑩ Published in ARu App 🔶（部分実装）

- **Purpose**：実際にARuアプリの読者へ届ける
- **Input**：`Publishing Status=Ready to Publish`の記事
- **Output**：`Publishing Status=Published`、`Published Date`／`Published By`／`ARu App URL`の記録
- **Responsible AI workflow**：**ARuアプリへの実投稿APIは存在しないため、掲載作業自体は人間が行う。** `publishing_center.py`は、人間がNotion上で`Publishing Status`を`Published`に変更した後、`Published Date`／`Published By`を自動記録するのみ
- **Exit criteria**：ARuアプリに実際に掲載され、Notion側の`Publishing Status=Published`が実態と一致している

### ⑪ SNS Distribution 🔶（部分実装）

- **Purpose**：公開された記事の認知を広げる
- **Input**：Published（または少なくともReview済み）のArticle
- **Output**：SNS Queueレコード（Instagram/Threads/X、ドラフト＋レビュー結果）
- **Responsible AI workflow**：`generate_article_pipeline.py sns`、`sns_quality_reviewer.py`（5観点：Accuracy/Platform Fit/Engagement/Cultural Sensitivity/Risk）
- **Exit criteria**：SNS Review Result=Pass。**実際のプラットフォームへの投稿は未実装で、Draft生成・レビューまでが自動化範囲**（[Version4-Status.md](./Version4-Status.md) 4節7項）

### ⑫ Periodic Update ✅

- **Purpose**：公開後の記事が古くなったり、外部の変化（法改正・情報源変化・イベント終了等）で実態と乖離したりしないようにする
- **Input**：Published記事、Update Levelごとのレビュー間隔（L1=90日／L2=30日／L3=14〜30日）、Law Update／Source Monitor／Event Calendarの変化シグナル
- **Output**：`Freshness Status=Needs Update`フラグ、Dashboard「🔴 Update Needed」への表示
- **Responsible AI workflow**：`article_freshness_monitor.py`
- **Exit criteria**：Needs Updateの記事が人間によって再レビューされ、内容が更新されて再度Editorial Reviewへ戻るか、現状のままで問題ないと確認される。**既知の制約**：`Status=Archived`になってもFreshness Statusは自動でクリアされない（根本原因は未修正、[5. Bug Fix Session](#5-bug-fix-session)の対象候補）

### ⑬ Archive ✅

- **Purpose**：重複・陳腐化・誤って作成された記事を、削除せず安全に退避する
- **Input**：重複と判定された記事（`duplicate_guard.py`／`duplicate_prevention_report.py`）、または編集者が掲載を見送ると判断した記事
- **Output**：`Publishing Status=Archived`（または`Duplicate`）。Dashboard・Editor Home・AI Command Centerの集計からは除外される
- **Responsible AI workflow**：`duplicate_guard.py`（生成前の重複防止）、`duplicate_prevention_report.py`（事後の可視化）。Archive自体への変更は人間が行う
- **Exit criteria**：記事が`Archived`／`Duplicate`としてマークされ、**削除はされていない**（Notion Trash／Version Historyのみが実質的な復旧手段、[Recovery-Guide.md](./Recovery-Guide.md)参照）

---

### Editorial Philosophy

**ARu Studioが存在する理由は、日本についての信頼できる知識を、継続的に発見し（Discover）、検証し（Verify）、整理し（Organize）、届け続けること（Deliver）にある。**

- **Discover**：Source DiscoveryとResearch Candidateが担う。ARuは「待っている」メディアではなく、情報源を能動的に監視し続ける
- **Verify**：Category ClassificationからEditorial Reviewまでの各工程が担う。Update Level 2・3（法律・ビザ・税金・医療等）は、AIのスコアがどれだけ高くても必ず人間が最終確認する——これは方針ではなくコードで強制される制約であり、ARuが「速さ」より「正しさ」を優先することの表れ
- **Organize**：Category ClassificationとLife Topics、Translationによる多言語展開が担う。情報は存在するだけでなく、必要な人に、必要な言語・粒度で届く形に整理されて初めて価値を持つ
- **Deliver**：Published in ARu AppとSNS Distributionが担う。ただし配信は目的そのものではなく、正しく検証・整理された知識を届けるための最後の1歩に過ぎない
- **そしてこの4つは1周で終わらない**：Periodic UpdateとArchiveが、Deliverされた知識をDiscoverの入力へ再び戻す。ARu Studioは「記事を作って終わり」の工場ではなく、知識を常に最新の状態に保ち続けるための循環（ループ）そのものである

この哲学は[ARu Constitution](./ARu-Constitution.md)のMission（「AIが調査・執筆・翻訳・SNSを担当し、人は最終確認だけを行う体制を作る」）を、本書のセッションの型・ライフサイクルという実務レベルまで一貫して落とし込んだものである。

### Implementation Note

この編集ライフサイクル（①〜⑬）は、ARu Studioが長期的に目指す運用アーキテクチャそのものを表しており、特定時点のスナップショットではない。一方で各工程に付けた成熟度指標（✅／🔶／🧭）は**2026-07-18時点の実装状況**を示すものであり、固定的なものではない。QA Card・Premium Article・Published in ARu App・SNS Distributionが今後実装・拡張されれば、該当する指標も更新されるべきであり、その更新は[3. Documentation Session](#3-documentation-session)の対象になる（新しい実装が入ったのに指標を古いままにしないこと）。

---

*ARu HQ / Decode Japan — ARu Studio Operating Manual v1.3 — 2026-07-18*
