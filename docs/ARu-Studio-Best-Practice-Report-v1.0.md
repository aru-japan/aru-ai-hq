<title>ARu Studio Best Practice Report v1.0</title>

# ARu Studio Best Practice Report v1.0

| | |
|---|---|
| **作成日** | 2026-07-19 |
| **対象** | ARu Studio Research 200件統合 |
| **位置づけ** | **設計基準（Design Reference）／設計憲章。実装仕様書ではない。** [Architecture-Specification-v1.0.md](./Architecture-Specification-v1.0.md)・[User-Journey-Architecture-v1.0.md](./User-Journey-Architecture-v1.0.md)・[Knowledge-Lifecycle-Architecture-v1.0.md](./Knowledge-Lifecycle-Architecture-v1.0.md)・[Mission-Control-Architecture.md](./Mission-Control-Architecture.md)と合わせて、現時点のARu Studioの設計基準5文書を構成する |
| **注意** | 本書は設計判断をまとめるものであり、**この段階では実装・DB変更・自動化追加への反映は行わない**。改善案・新機能提案は、本書を基準とした現状監査（[ARu-Studio-Design-Reference-Audit-2026-07-19.md](./ARu-Studio-Design-Reference-Audit-2026-07-19.md)）の確認後に検討する |

---

## 0. 結論

ARu Studioは、単なるNotion製CMSやAIライターではなく、**Evidence-centered AI Editorial Operating System（根拠中心のAI編集OS）**として設計する。

AIの役割は、情報収集、整理、比較、下書き、検査、更新候補の提示まで。人間の役割は、編集方針、採否、高リスク判断、公開、訂正に責任を持つことである。

ARuが最初に解決すべき問題は「記事候補が足りない」ことではない。現在の本質的な問題は、議題は存在するが、記事を書くための材料が一か所に集まっていないことである。そのため、最優先で構築すべき論理は次の流れとなる。

Reader Need → Research Theme → Source → Evidence → Claim → Article Brief → Draft → Review → Publish → Feedback / Correction

研究200件の成果は、参考事例集として保管するのではなく、以下の5つへ変換して利用する。

1. ARu Editorial Constitution（編集憲法）
2. Article Type Playbook（記事タイプ別手順）
3. Risk & Approval Matrix（リスク・承認基準）
4. Quality Evaluation Rubric（品質評価基準）
5. Claude Implementation Brief（実装依頼仕様）

## 1. 研究から得た主要判断

### 1.1 採用する設計

| 設計 | 採用理由 | ARuでの利用 |
|---|---|---|
| Source・Evidence・Claimの分離 | 出典を保存しただけでは、記事中の主張を検証できないため | 情報源、根拠断片、記事内主張を関連付ける |
| Article Owner / DRI | AIが増えるほど最終責任者が曖昧になるため | 各記事に一人の責任者を設定する |
| AI提案・人間決定 | 効率と説明責任を両立できるため | 採用、公開、訂正は人間が判断する |
| リスク適応型ワークフロー | コラムと法律記事を同じ厳しさで扱うのは非効率なため | R1〜R4で検査と承認を変える |
| Correction Propagation | 一つの根拠変更が複数記事・翻訳へ波及するため | 関連記事と派生版を更新候補にする |
| Reader-choice personalization | 属性の推定だけに頼ると誤配信や固定観念が生じるため | 読者自身が目的・言語・詳しさを選ぶ |
| Status machine | ステータス名だけでは次の行動が分からないため | 入場条件、退出条件、担当、次アクションを定義する |
| AI activity log | AIの判断を後から検証する必要があるため | 入力、出力、使用根拠、結果、承認者を記録する |
| 公開後の継続監視 | 公開時に正しくても制度・料金・日程は古くなるため | 鮮度期限、リンク切れ、根拠更新を監視する |
| 読者成果の測定 | PVだけでは記事が役立ったか分からないため | 保存、完了、次行動、質問解消、訂正率を測る |

### 1.2 改良して採用する設計

| 元の考え方 | ARu向けの改良 |
|---|---|
| 多数の専門AIエージェント | 初期は役割を論理的に分け、実体は少数のAI処理に統合する |
| 詳細な多段階ワークフロー | 普段の画面には「今日判断するもの」だけを表示する |
| 高度な自動パーソナライズ | まず読者の自己選択と簡単なルールベースから始める |
| 全言語同時展開 | 日本語マスターを安定させ、優先言語から段階展開する |
| 大規模な独立CMS | 現在のNotion DB・既存Relation・既存パイプラインを再利用する |
| AIによる包括的品質評価 | 決定論的チェックとAI評価を併用し、検査結果を構造化する |

### 1.3 将来採用する設計

行動データを用いた高度なレコメンド、ARu Academy、Mentor、Community、Certification、企業・団体向けマルチテナント、11言語以上の完全運用、ネイティブレビュー体制の大規模化、高度な実験基盤と自動最適化、専門家ネットワークによるR4コンテンツ承認。

### 1.4 採用しない設計

| 不採用設計 | 理由 |
|---|---|
| 単一の巨大データベース | 関係が曖昧になり、UIと自動化が複雑になる |
| AIによる無承認の自動公開 | 誤情報、権利侵害、ブランド毀損の責任を負えない |
| PVだけの成功評価 | 読者が問題を解決できたか判断できない |
| すべての記事への同一チェック | 低リスク記事が停滞し、高リスク記事の検査が不足する |
| AIによる出典の後付け | 本文に合う出典を探す行為は誤引用を生みやすい |
| 最初から全機能・全言語を構築 | 一人運営では品質と保守性が下がる |
| AIエージェント数を成果として増やす | 役割間の重複、コスト、障害点が増える |
| 非公開情報を一般の執筆コンテキストへ混在 | 権限とデータ流出の境界が不明確になる |

## 2. ARu Editorial Constitution

1. 読者の課題から始める。キーワードや話題だけで記事を作らない。
2. 根拠を先に集める。原稿を書いてから出典を付けない。
3. 事実・解釈・編集判断を分ける。読者が確実性を理解できるようにする。
4. 一次情報を優先する。法律、制度、料金、日程、安全情報は公式情報で確認する。
5. 重要な主張を追跡可能にする。ClaimからEvidence、Sourceへ戻れる状態にする。
6. AIは提案し、人間が決定する。公開、訂正、高リスク判断は人間が担う。
7. リスクに応じて厳しさを変える。すべての記事を同じ工程に通さない。
8. 分からないことを埋めない。根拠不足は「要調査」として残す。
9. 多文化・多言語の読者を固定観念で分類しない。読者自身の選択を優先する。
10. 公開後も記事を管理する。更新、訂正、アーカイブまでを記事のライフサイクルとする。
11. 自動化より説明責任を優先する。なぜ生成・変更・公開されたかを記録する。
12. ARuの目的に役立たない複雑性を持ち込まない。機能数ではなく、迷わず判断できることを重視する。

## 3. 記事作成自動化への変換

### 3.1 Step 1: Reader Need / Article Intake

必須項目：想定読者／読者の状況／解決したい質問・課題／読後にできるようになること／記事タイプ／対象地域・言語／情報の有効期限／初期リスクレベル

AIが行うこと：読者課題の明確化／類似記事と重複候補の検出／調査質問の分解／必要情報源の種類の提案
人間が行うこと：企画の採用・修正・却下／誰のための記事かの最終決定

### 3.2 Step 2: Research Plan

| 記事タイプ | 最低限必要な情報源 |
|---|---|
| 法律・行政手続き | 官公庁、法令、自治体等の一次情報 |
| 医療・安全 | 公的機関、専門機関、必要に応じ専門家確認 |
| 製品・サービス比較 | 公式仕様、料金、利用条件、更新日 |
| 文化解説 | 一次資料、信頼できる専門資料、地域差への注意 |
| イベント | 主催者公式、会場、日時、変更・中止情報 |
| 体験・コラム | 体験主体、事実と意見の区別 |

### 3.3 Step 3: Source → Evidence

Sourceは文書やWebページ全体。Evidenceは記事で利用できる具体的な根拠断片とする。

Evidenceに必要な情報：根拠の要約／原文または該当箇所／SourceへのRelation／公開日・確認日／適用地域・対象者／信頼度／有効期限・再確認日／反対情報・例外／利用可能な記事候補

### 3.4 Step 4: Evidence → Claim

Claimは、記事で読者へ伝える検証可能な主張である。

Claimの状態：Proposed／Supported／Conflicted／Needs Review／Rejected／Superseded

重要なClaimには、最低一つの強いEvidenceを関連付ける。高リスクのClaimでは、一次情報や複数根拠を求める。

### 3.5 Step 5: Article Brief

Article Briefは「議題」を「書ける記事」へ変換する中心成果物である。

必須構成：Reader Job／記事の約束／読者が最初に知るべき結論／採用するClaims／使用するEvidence・Sources／見出し案／注意事項・例外／ARu Tip候補／必要な図表・UI要素／リスクと承認者／更新期限／CTA・次の行動

Article Briefの完了条件は、単に項目が埋まったことではない。本文を書けるだけの根拠が揃っていることである。

### 3.6 Step 6: Draft Generation

AIは承認済みClaimsとEvidenceのみを使って下書きを作る。根拠がない箇所を一般知識で補完しない。

ARu記事テンプレートでは、少なくとも次を安定させる：読者の疑問／短い回答・結論／背景と意味／実際の行動手順／例外・注意／ARu Tip／Sources／Related Articles／Last Updated

既存のブランド品質標準化方針に従い、記事テンプレートは単一の正本を持つ。テンプレート準拠は、AIの感想ではなく構造検査でも確認する。

### 3.7 Step 7: Automated Quality Review

**決定論的チェック**：必須セクションの有無／空欄、リンク切れ、日付形式／Sourceの有無／ClaimとEvidenceのRelation／重複タイトル／ステータス遷移条件／最終更新日・次回確認日

**AIチェック**：根拠と本文の意味が一致しているか／根拠のない断定がないか／誇張・偏見・固定観念がないか／例外条件を落としていないか／読者の疑問に答えているか／やさしい日本語・翻訳適性／Premium Sectionが本当に付加価値を持つか

AIレビューの出力は自由文だけにせず、Pass / Warning / Fail、対象箇所、理由、修正案を構造化する。

### 3.8 Step 8: Human Approval

人間は全文を毎回同じ方法で読むのではなく、以下を優先確認する：Fail・Warningの箇所／高リスクClaims／AIが変更した重要表現／タイトルと結論／公開範囲／個人情報・権利・安全性

最終操作は「採用」「修正」「却下」「保留」「公開」の少数の判断にまとめる。

### 3.9 Step 9: Publish and Derivatives

日本語マスター承認後に、翻訳、SNS、ニュースレター、短縮版などを派生させる。派生版はマスター記事とRelationを持ち、原文更新時に要再確認となる。

翻訳とSNSの生成処理は、記事テンプレート再設計と独立させ、安定している既存処理を不要に変更しない。

### 3.10 Step 10: Feedback, Update, Correction

公開後に収集するもの：検索語／該当記事なし検索／保存数／読了・スクロール／繰り返される質問／誤りの指摘／次の行動の完了／Sourceの更新

訂正が発生した場合は、Claimを起点に関連記事、翻訳、SNS、FAQ、学習コンテンツへ影響を伝播させる。

## 4. Risk & Approval Matrix

| Level | 代表例 | AI自動化 | 人間確認 |
|---|---|---|---|
| R1 | コラム、一般文化紹介 | 調査・執筆・検査を広く自動化可能 | 簡易承認 |
| R2 | 操作解説、SEO記事、商品比較 | 下書き・通常検査まで自動化 | 重要主張と公開前確認 |
| R3 | 在留手続き、雇用、税、制度、重要な費用 | 一次情報整理と差分検出まで | 根拠・適用条件・日付を必須確認 |
| R4 | 医療、法律助言、金融、安全・緊急情報 | 候補作成と検査補助に限定 | 専門確認を含む厳格承認 |

リスクレベルは記事単位だけでなく、Claim単位でも設定できるようにする。一般記事の中に高リスクな一文が含まれる場合があるためである。

## 5. 品質評価基準

公開可否は100点満点より、必須ゲートと改善スコアを分ける。

### 5.1 必須ゲート

読者課題が明確／重要Claimに根拠がある／高リスク情報が人間確認済み／出典と本文が一致／公開範囲が適切／重大な差別・安全・権利問題がない／更新責任者と再確認日がある

一つでも重大なFailがあれば公開しない。

### 5.2 改善スコア

| 評価軸 | 主な問い |
|---|---|
| Useful | 読者が次の行動を取れるか |
| Accurate | 主張は根拠に支えられているか |
| Clear | 一度で理解できるか |
| Inclusive | 多文化・多言語の読者へ配慮しているか |
| Current | 情報は現在も有効か |
| Distinctive | ARu独自の説明・整理・支援価値があるか |
| Accessible | 見出し、表、言葉、モバイル表示が利用しやすいか |
| Maintainable | 更新箇所と影響範囲を追跡できるか |

## 6. Notion UI / UX設計原則

### 6.1 ホームを役割で分ける

**Editor Home**（人間が今日判断する場所）：今日の採用判断／記事材料が揃ったBrief／人間レビュー待ち／高リスク警告／公開可能記事／訂正・更新期限

**AI Command Center**（AIの処理状況を監督する場所）：実行中・失敗した処理／Source監視／Evidence抽出結果／品質検査ログ／AI提案の採用率／権限・外部接続の異常

日常運用ではEditor Homeを使い、技術的なAIログは必要時だけ開く。

### 6.2 Progressive Disclosure

最初から全プロパティを表示しない。上部：結論、次アクション、担当、期限、リスク／通常表示：Brief、本文、Sources、レビュー結果／「その他の詳細」：内部ID、AIログ、技術メタデータ／「Premium Section」：本当に追加価値がある場合だけ表示

### 6.3 状態ではなく次の行動を表示する

悪い表示：Researching　良い表示：Evidenceをあと2件確認する
悪い表示：Review　良い表示：R3 Claimを人間が確認する

ダッシュボードでは、ステータス名より「次に誰が何をするか」を優先する。

### 6.4 既存資産の再利用

既存DBとRelationを優先する／Related Articlesは既存のKnowledge Links等を再利用する／新しいDBは、既存構造では意味が保てない場合だけ追加する／現在の単一Body rich_textは、表示時には見出し・Sources・Related Articles・Last Updatedをページブロックとして読みやすくする／旧記事にはTemplate Status（Up to Date / Update Needed）を持たせ、移行を一度に強制しない

## 7. 運用モデル

### 7.1 毎日30〜60分の人間運用

AIが用意した候補と警告を見る／採用・修正・却下を判断する／材料の揃ったArticle Briefを承認する／公開前の重要箇所を確認する／公開または保留を決める

人間が情報を探し回る運用に戻してはならない。AIは、人間が判断できる状態まで材料を準備する。

### 7.2 週次運用

未処理候補の整理／更新期限超過の確認／AI提案の採用率・誤警告率／読者の質問ギャップ／訂正・品質問題／翌週の重点テーマ決定

### 7.3 月次運用

読者成果の確認／不要なDB・プロパティ・ビューの削減判断／プロンプト・評価基準の改訂／権限・外部接続の確認／ARu Editorial Constitutionの改訂要否

## 8. 成功指標

### 8.1 制作効率
企画からBrief完成までの時間／Brief完成から下書きまでの時間／人間レビュー時間／1記事あたりの手戻り回数／AI提案の採用率

### 8.2 品質
根拠なしClaim率／公開後訂正率／期限超過記事率／リンク切れ率／翻訳差分未反映率／高リスク記事の承認漏れ率

### 8.3 読者成果
保存・共有／読了／FAQ解決率／該当記事なし検索の減少／次の行動への遷移／同一質問の再発率

PVは参考値として残すが、単独の成功指標にはしない。

## 9. Claudeへ依頼する実装内容

**本章は実装開始時の依頼範囲であり、現段階では実行しない。**

- **Priority 0: 現状監査** — 現在のNotion DB、Relation、Rollup、View、Automationの一覧化／Article作成パイプラインと既存コードの確認／重複DB、孤立Relation、壊れたステータス遷移の検出／既存ユーザーデータを保持した移行方針
- **Priority 1: Canonical Data Model** — Source、Evidence、Claim、Article Brief、Articleの正本定義／既存DBを再利用する項目と新設が必要な項目の区別／Relationと一意性ルール／必須項目と検証条件
- **Priority 2: Status Machine** — 状態、入場条件、退出条件、担当、次アクション／例外、差し戻し、保留、失敗、再実行／R1〜R4に応じた異なる承認ルート
- **Priority 3: Role Dashboards** — Editor Home／AI Command Center／Article Brief Workspace／Review Queue／Update・Correction Queue
- **Priority 4: Article Quality System** — 記事テンプレートの単一正本／必須セクション解析と検証／Evidence・Claim整合性チェック／構造化されたレビュー結果／旧記事のTemplate Status移行
- **Priority 5: Correction Propagation** — Source更新→Evidence要確認／Evidence変更→Claim要確認／Claim変更→記事・翻訳・SNS・FAQへの影響通知／訂正履歴と承認記録
- **Priority 6: AI Log and Security Boundary** — AI処理の入力・出力・根拠・モデル・日時・結果／Public・Working・Internal・Restrictedの区分／外部AIがアクセスできるページの最小化／自動公開禁止とHuman Approval Gate
- **Priority 7: Migration Plan** — 既存データを壊さない段階移行／バックフィル手順／ロールバック方法／検証用サンプル記事／受入テストと完了条件

## 10. 推奨実施順序

- **Phase A: 研究統合と規格化** — 本レポートの承認／Editorial Constitutionの確定／採用・不採用判断の固定／記事タイプとリスク分類の確定
- **Phase B: Article Brief中心化** — Reader Need、Source、Evidence、ClaimをBriefへ集約／「材料不足」と「執筆可能」を明確に区別／記事を書く前の完了条件を設定
- **Phase C: 品質と承認** — 自動検査／Risk & Approval Matrix／Human Approval Gate／テンプレート準拠確認
- **Phase D: 公開後管理** — 更新期限／Source監視／Correction Propagation／Reader Outcomeの測定
- **Phase E: 派生自動化** — 翻訳／SNS／ニュースレター／学習コンテンツ／パーソナライズ

最初の実装テーマは「Article Briefを完成させる仕組み」とする。SNS自動化や高度なパーソナライズを先行させない。

## 11. ARu独自に進化させる設計

### 11.1 ARu Evidence Graph
一般的なCMSは記事を中心に管理する。ARuは、読者課題・情報源・根拠・主張・編集判断・記事・訂正を一つのグラフとして管理する。これにより：ある制度変更がどの記事へ影響するか分かる／記事の一文がどの根拠から作られたか分かる／同じ根拠を複数記事で再利用できる／矛盾する根拠を公開前に検知できる／翻訳やSNSまで訂正を伝播できる。

### 11.2 Three-Layer Truth Model
Evidence（情報源が実際に示していること）／Interpretation（ARuがその意味をどう説明するか）／Decision（記事へ採用するか、どの表現で伝えるか）。AIがEvidenceとInterpretationを混同しないため、生成物の信頼性と説明責任が高まる。

### 11.3 Risk-adaptive Editorial Engine
記事全体に一つのリスクを付けるだけでなく、Claimごとのリスクと読者への影響を評価し、必要な根拠・検査・承認を自動的に変える。一人運営でも低リスク記事は速く、高リスク記事は慎重に扱える。

### 11.4 Reader Choice Personalization
国籍などからAIが一方的に推定するのではなく、読者が次を選べるようにする：今知りたい目的／使用言語／やさしい説明・詳しい説明／来日前・来日直後・生活中／手続き・文化・学習・緊急情報。「あなたはこの属性だからこれを読むべき」ではなく「今のあなたは何を必要としているか」を中心にする。

### 11.5 Correction as a First-class Product
訂正を失敗として隠すのではなく、信頼を育てる機能として設計する：何が変わったか／なぜ変えたか／どの根拠が更新されたか／関連する記事に反映済みか／読者が再確認すべきこと、を記録・表示できるようにする。

### 11.6 Human Accountability Gate
公開／重大訂正／高リスク情報／個人情報／契約・権利／外部送信／AI権限の拡張には明示的な人間承認を要求する。

### 11.7 Learning Editorial Loop
読者行動を単なるPVとして扱わず、編集知識へ戻す：質問・検索・保存・離脱・訂正 → Reader Need更新 → Research Theme → Evidence → Article改善。

### 11.8 ARuの最終定義
ARu Studioは、外国籍の方や日本を理解したい人の「今、何を知り、何をすればよいか」を、追跡可能な根拠と人間の責任ある判断によって、多言語で届け、公開後も学習・訂正し続けるAI編集OSである。

## 12. 研究記録に関する注記

研究は200/200件まで完了している。統合結論として、Source / Evidence / Claim分離、DRI、Human Approval、Risk-adaptive workflow、Correction propagation、Reader-choice personalization等は確認できた。

一方、個別200件の番号・対象名・各回の分析全文を一つにまとめた原票は、現時点で確認できる保存資料には存在しない。本書は、確定済みの統合結論、ARuの既存設計資料、記事テンプレート・UI/UX方針を基に作成した。

個別事例の索引が必要になった場合は、推測で再作成せず、会話記録または保存済み原稿から復元し、別冊 ARu Studio Research Index 001-200 として管理する。

## 13. 次の意思決定

次に確認するべき事項は一つである。ARuの最初の実装対象を「Article Brief中心の材料収集・執筆準備」に固定するか。

承認後、Claudeへ渡す最初の依頼書は、現状監査とArticle Brief Workspaceの設計に限定する。実装前に、既存DBとの重複、Relation、移行影響、受入条件を明示する。

---

*ARu HQ / Decode Japan — ARu Studio Best Practice Report v1.0 — 2026-07-19*
