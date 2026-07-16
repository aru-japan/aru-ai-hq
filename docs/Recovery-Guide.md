<title>Recovery Guide</title>

# Recovery Guide
### チャット履歴を失っても、ARu Studioプロジェクト全体を復旧する手順

| | |
|---|---|
| **Status** | Active |
| **対象** | チャット履歴・セッション・PC・AIツールのいずれかを失った、新しいAI／新しい開発者／記憶をなくしたRei自身 |
| **前提** | このプロジェクトの**唯一の正**はチャット履歴ではなく、**GitリポジトリとNotion上の実データ**である。チャットが消えても、この2つが無事なら全体は復旧できる |

> チャット履歴は一時的な作業記録に過ぎない。「チャットに書いてあったはず」を頼りにせず、必ずこのガイドの手順でGit／Notionの実データに立ち返ること。

---

## 復旧の10ステップ

### Step 1：READMEを読む

リポジトリ直下の[README.md](../README.md)を開く。プロジェクトの一言説明と、ドキュメント一覧表がある。**最初のリンクは[START-HERE.md](./START-HERE.md)** ——まずそちらで10分の全体像を掴む。

### Step 2：AI-Handoverを読む

[docs/AI-Handover.md](./AI-Handover.md)を読む。Architecture／Current Database Structure／Current Automation／Current Phase／Completed Features／**Remaining Tasks**／Known Limitations／Design Principlesがまとまっている、開発継続のための本体文書。

> 文書内の「Latest Commit」フィールドは経年劣化する。**必ずStep 8で実際の`git log`と突き合わせて古くなっていないか確認すること。**

### Step 3：Version4-Statusを読む

[docs/Version4-Status.md](./Version4-Status.md)を読む。直近セッションで何を実装したか、記事数・Research数・Translation数・SNS数などのコンテンツ量、現在の課題、明日／今週やるべきことがスナップショットとして残っている。**日付を確認し、今日からどれだけ経過しているかを把握する**（古いほど実態とズレている可能性が高い）。

### Step 4：Constitutionを読む

[docs/ARu-Constitution.md](./ARu-Constitution.md)を読む。最上位の権威。最低限、以下は必ず目を通す。

- §1〜3（Mission／Vision／Core Values）
- §9（AI Behavior Rules）・§13（Legal & Medical Rules）——AIが越えてはいけない一線
- **Pending Amendments節**——未承認の改訂提案が残っていないか、あれば発効予定日を確認
- §20（Governance）——改訂が必要になった場合の正規プロセス

### Step 5：Editorial Standardを読む（存在する場合）

`docs/Editorial-Standard.md`のような名前の専用文書は、**2026-07-14時点ではまだ存在しない**。編集基準に相当する内容は、現状以下に分散している。

- 記事の構成基準（ARu公式9セクションテンプレート）→ `notion-build/automation/generate_article_pipeline.py`の`ARU_ARTICLE_TEMPLATE_INSTRUCTIONS`
- 品質チェックリスト → Constitution §14 Quality Checklist
- 文体・トーンの方針 → Constitution §4 Editorial Policy・§5 Cultural Policy

もし`docs/Editorial-Standard.md`が将来作成されていたら、このStepで最優先に読むこと。存在しない場合はこのステップを飛ばしてよい。

### Step 6：Dashboardを確認する

Notionで「ARu Studio」ルートページ配下の「ARu Studio Dashboard」ページを開く（Page IDは`.env`の`DASHBOARD_PAGE_ID`）。上から🔴 Update Needed → 📊 Coverage Analysis → 📝 Editorial Planner → 🚀 Ready to Publish → 📚 Published Articles → 🛠 Needs Update → ①〜⑨の順。**Linked Viewが空白／未設定の場合は[Dashboard Setup Guide](./Dashboard-Setup-Guide.md)の手順で再設定する**（NotionパブリックAPIでは自動復元できない、人間の手作業が必要な部分）。

あわせて、Version 4 Phase 5で追加した2つのナビゲーションハブページも確認する（Page IDは`.env`の`EDITOR_HOME_PAGE_ID`／`AI_COMMAND_CENTER_PAGE_ID`）：🏠 Editor Home（今日、人間が決めること）、🤖 AI Command Center（AIが監視・検知していること）。この2ページはLinked Viewではなく`editor_home.py`／`ai_command_center.py`が毎回ブロックを上書き生成する専用ページなので、Dashboardと違って手動再設定は不要——スクリプトを再実行すれば復元される。

### Step 7：Notionデータベースを確認する

10個のデータベース（Articles／Research／Translation／Source Library／Editorial Calendar／Experience Intelligence／Source Monitor／Law Update／Event Calendar／SNS Queue）が実際に存在し、レコードが読めるか確認する。`.env`にDB IDが揃っていれば、以下で件数を確認できる（**値ではなく件数のみを出力する**、安全なコマンド）。

```bash
cd notion-build
python3 -c "
from notion_api import load_env, notion_request
env = load_env('.env')
token = env['NOTION_TOKEN']
for key in ['ARTICLES_DB_ID','RESEARCH_DB_ID','TRANSLATION_DB_ID','SNS_QUEUE_DB_ID']:
    res = notion_request(token, 'POST', f'/databases/{env[key]}/query', {'page_size': 1})
    print(key, 'reachable:', 'results' in res)
"
```

`automation/daily_briefing.py`を実行すれば、9セクション分の実データがテキストで一望できる（Dashboard未設定でも使える代替手段）。

### Step 8：最新のGitHubコミットを確認する

```bash
git log --oneline -20
git status
```

- AI-Handoverの「Latest Commit」フィールドと突き合わせ、古くなっていれば更新する
- `git status`が汚れている（未コミットの変更がある）場合、それが前回セッションの途中経過か確認してから作業を始める
- リモートと同期しているか：`git fetch && git log HEAD..origin/main --oneline`（何か出力されれば、ローカルが遅れている）

### Step 9：Remaining Tasksを読む

[AI-Handover.md](./AI-Handover.md)の**Remaining Tasks**節と、[Version4-Status.md](./Version4-Status.md)の**「現在の課題」「明日やるべきこと」「今週やるべきこと」**節をまとめて読む。ここに、前回セッションで終わらなかった／意図的に人間の判断待ちにした項目がすべて列挙されている。

### Step 10：開発を再開する

Step 1〜9で全体像・現状・残タスクが揃った状態で、Remaining Tasksの中から着手する項目をRei（または引き継いだ人間）と確認し、開発を再開する。再開時に必ず守ること。

- **新規データベースを追加しない**（既存DB拡張かPythonスクリプトで対応する）
- **Update Level 2・3はAIスコアに関わらず人間承認必須**（コードで強制されている制約、迂回しない）
- **`.env`・APIキーの値は一切表示・コミットしない**（キー名や件数は安全、値は絶対不可）
- 変更がConstitutionの運営方針に実質的な影響を与える場合は、§20 Governanceに従いPending Amendmentとして提案する（軽微な実装詳細なら不要）
- コミット前に必ずシークレットチェックを行う：`git diff --cached | grep -iE "sk-ant|sk-proj|_API_KEY=.+|NOTION_TOKEN=.+"`

---

## Emergency Recovery（緊急時の復旧シナリオ）

### 🔴 ChatGPTの会話を失った

このリポジトリの正はGit／Notionであり、特定のAIツールの会話履歴ではない。ChatGPTに新しいセッションでこのリポジトリ（またはクローン）へのアクセスを与え、Step 1〜9を実行させる。ChatGPTがファイル閲覧やコード実行のツールを持たない場合は、[START-HERE.md](./START-HERE.md)と[AI-Handover.md](./AI-Handover.md)の中身を貼り付けて渡す。

### 🔴 Claudeの会話を失った

同上。Claude Code（このツール）であれば、新しいセッションを開始し「docs/START-HERE.mdを読んで」と伝えるだけで、このガイドの手順を辿れる状態になる。過去の会話内容そのものは失われるが、**すべての意思決定・実装内容はコミットメッセージとドキュメントに残っている**ため、実質的な支障は少ない。

### 🔴 新しいAIセッション（同一ツール内でのコンテキスト切れ等）

Step 1〜9をそのまま実行する。特別な手順はない——これがこのガイドの標準ユースケース。

### 🔴 新しい開発者が参加する

1. Reiからリポジトリへのアクセス権（GitHub）とNotionワークスペースへの招待を受ける
2. `git clone https://github.com/aru-japan/aru-ai-hq.git`
3. [START-HERE.md](./START-HERE.md) → [AI-Handover.md](./AI-Handover.md) → [Operating-Manual.md](./Operating-Manual.md)の順に読む
4. `notion-build/.env`はGitに含まれない（`.gitignore`済み）。Reiから直接、安全な方法で共有を受ける（Slack/メール等の平文共有は避け、パスワードマネージャー等を使う）
5. `notion-build/.env.example`と照らし合わせ、必要なキーが揃っているか確認する

### 🔴 新しいコンピューターに移行する

1. `git clone https://github.com/aru-japan/aru-ai-hq.git`
2. `notion-build/.env`を旧環境から安全な方法で移行する（**Gitには絶対に含めない**。USBメモリの手渡し、パスワードマネージャーの共有機能等を推奨。チャットやメールでの平文送付は避ける）
3. `python3 notion-build/automation/daily_briefing.py`を実行し、実データが読めることを確認する（動けば移行成功）

### 🔴 APIキーを新しくした（ローテーションした）

1. 新しいキーを発行する（Claude: console.anthropic.com、Notion: notion.so/my-integrations）
2. `notion-build/.env`の該当行を書き換える（`CLAUDE_API_KEY=`または`NOTION_TOKEN=`）。**値をターミナルやチャットに出力しない**——`notion_api.py`の`set_env_value()`を使うか、エディタで直接編集する
3. 動作確認は「キーが存在するか」「文字数」「ファイルの更新日時」のみで行い、**値の一部（プレフィックス含む）も一切表示しない**（過去に実際にこの原則を破ってキーを露出させ、ローテーションが必要になった経緯がある。同じ失敗を繰り返さない）
4. 旧キーを発行元（Anthropic Console／Notion Integrations）で失効させる

### 🔴 GitHubリポジトリを復元する

1. `git clone https://github.com/aru-japan/aru-ai-hq.git`（リポジトリ自体が生きていればこれで全履歴が戻る）
2. リポジトリ自体が失われた場合、直近でリポジトリをcloneしていた別の端末があれば、そこから`git push`でGitHub側を復元できる
3. **どの端末にもローカルコピーが残っていない場合、コード資産は失われる。** Notion側のデータ（記事本文等）はGitとは独立して残っているため、最悪でもコンテンツ自体は失われない（実装コードのみ失われ、再実装が必要になる）

### 🔴 Notionワークスペースを復元する

1. **ページ単位の誤削除**：Notionのゴミ箱（Trash）から復元可能（ワークスペース設定にもよるが、一般的に30日以内）
2. **データベースのレコード単位の誤削除**：同じくTrashから復元可能
3. **データベース自体が失われた場合**：`notion-build/create_*.py`スクリプト群でスキーマ（プロパティ構成）は再構築できるが、**実際のレコード（記事本文・翻訳・レビュー結果等）を復元する手段は現状存在しない**。NotionのTrash期限を超えて削除された場合、そのデータは失われる
4. **正直な現状認識**：このプロジェクトには、Notionデータの外部バックアップ（エクスポート等）の仕組みが現時点で存在しない。Notion自体のTrash／Version Historyが唯一の実質的な復旧手段であり、これはKnown Limitationとして[AI-Handover.md](./AI-Handover.md)にも記載されている

---

*ARu HQ / Decode Japan — Recovery Guide — 2026-07-14*
