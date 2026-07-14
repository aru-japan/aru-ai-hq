<title>ARu Constitution — 運営憲章 v2.0.0</title>

# ARu Constitution
### 運営憲章 Version 2.0.0

| | |
|---|---|
| **Status** | Active |
| **Date** | 2026-07-12 |
| **Author** | Rei（編集長）× System Architect |
| **Applies to** | ARu HQのすべてのAIエージェント・人間編集部・メンター |
| **Companion document** | [ARu HQ データベース設計書 v1.2](./aru-hq-er-design.html)（本憲章の運営思想を、実際のデータ構造として実装したもの） |

> この文書はガイドラインではない。ARu HQで働くすべてのAIエージェントと人間が、判断に迷ったときに立ち戻る場所である。
> コードは書き換えられる。データベースは作り直せる。だが、この憲章が定める「何を優先するか」の順序は、10年間変わらないことを前提に書く。

---

## Revision History

| Version | Date | 更新者 | 変更理由 | 影響範囲 | 承認者 |
|---|---|---|---|---|---|
| v1.0.0 | 2026-07-12 | Rei × System Architect | 初版制定 | 全章 | Rei |
| v2.0.0 | 2026-07-12 | Rei × System Architect | Governanceに改訂レベル（Level A/B/C）とレビュー期間を導入。Version Controlに Major.Minor.Patch の対応関係を明記。本Revision Historyを新設 | §17 Version Control, §20 Governance | Rei |

このRevision Historyは**追記のみ・削除不可**で運用する。以降のすべての改訂は、レベルにかかわらずここに1行を追加する（詳細は[§17 Version Control](#17-version-control)・[§20 Governance](#20-governance)）。

---

## Pending Amendments（改訂提案中）

[§20 Governance](#20-governance)の改訂プロセスに従い、承認前の改訂案をここに記載する。**Revision Historyへの記録・バージョン番号の更新は、レビュー期間満了後、編集長の正式な承認を経て初めて行う。** それまで本文（§4・§11）は現行のv2.0.0のまま変更しない。

| | |
|---|---|
| **提案日** | 2026-07-14 |
| **提案理由** | ARu公式記事テンプレート（9セクション構成）の導入、およびArticle Freshness Monitor（Update Levelごとに異なるレビュー間隔での定期再確認＋外部シグナル連動）の実装により、運営の実態が現行の§4・§11の記述と乖離したため |
| **レベル判定** | Level B（運営改善：ワークフロー変更） |
| **レビュー期間** | 72時間以上（起算日 2026-07-14） |
| **発効予定** | 2026-07-17以降、編集長の承認を得た時点でv2.1.0として本文に反映 |
| **承認** | 未承認（Pending） |

### 提案内容①：§4 Editorial Policy への追加

> 記事本文は「ARu公式テンプレート」（9セクション構成：Question／Basic Answer／More Details／Why Does Japan Do This?／Practical Steps and Cautions／Latest Information／ARu Tip／Related Questions／Mentor Support）に統一する。Basic Answerは、それだけ読んでも要点が分かる無料部分として単独で読める内容にする。Latest Informationには、最新情報があれば明記し、なければ最終確認日（Last Verified Date）を明記する。

### 提案内容②：§11 Update Rules の第4項目を置き換え

現行（v2.0.0）：
> Update Level 2・3のコンテンツは、変更が検知されなくても**定期的な再確認**（目安90日ごと）を行う。情報が「古いまま正しそうに見える」状態を放置しない。

提案（v2.1.0案）：
> すべてのUpdate Levelのコンテンツは、変更が検知されなくても**定期的な再確認**を行う。再確認の間隔はUpdate Levelごとに異なる：Level 1は90日、Level 2は30日、Level 3は14〜30日（運用上の設定値。Article Freshness Monitorのコードで管理し、変更する場合もこの憲章の改訂は不要）。間隔を超過した記事は Freshness Status＝Needs Update として Dashboard最上部（🔴 Update Needed）に表示し、情報が「古いまま正しそうに見える」状態を放置しない。加えて、Law Update・Source Monitor・Event Calendarで関連する変化が検知された記事は、間隔を待たずに再確認対象とする（実装：`notion-build/automation/article_freshness_monitor.py`。詳細は[Automation Scripts](./Automation-Scripts.md)）。

---

### 改訂提案（2件目）：§15 Publishing Workflow の「Level 1 ── 自動公開」表記の明確化

| | |
|---|---|
| **提案日** | 2026-07-14 |
| **提案理由** | Publishing Center（`notion-build/automation/publishing_center.py`）の実装により、「Level 1 ── 自動公開」という現行表記が誤解を招くことが明確になったため。実際には、Level 1でもAIが記事をARuアプリへ自動的に掲載することは一度もなく、これまでも今後も存在しない（§9 AI Behavior Rulesの「Publish Approvalのゲートを迂回しない」に一貫して従っている）。「自動公開」が指しているのは実際には「Translation.Publish Approvalが自動でNot Requiredへ解除されること」のみで、ARuアプリへの実際の掲載は常に人間の操作（Publishing Status＝Publishedへの変更）を要する。運営方針・AIの権限範囲そのものは一切変更しておらず、既存の実態を正確に記述し直すだけの改訂 |
| **レベル判定** | Level B（運営改善：ワークフロー記述の明確化） |
| **レビュー期間** | 72時間以上（起算日 2026-07-14） |
| **発効予定** | 2026-07-17以降、編集長の承認を得た時点でv2.1.0（または承認タイミングにより該当バージョン）に反映 |
| **承認** | 未承認（Pending） |

現行（v2.0.0）：
```
  ┌─ Level 1 ── 自動公開
  ├─ Level 2 ── 担当メンターの承認 → 公開
  └─ Level 3 ── 編集長／専門メンターの承認（Change Summary添付）→ 公開
```

提案：
```
  ┌─ Level 1 ── Publish Approval自動解除（Not Required）→ 人間がPublishing Statusを
  │              Ready to Publishへ、ARuアプリ掲載後にPublishedへ手動更新
  ├─ Level 2 ── 担当メンターの承認 → 人間がPublishing StatusをPublishedへ手動更新
  └─ Level 3 ── 編集長／専門メンターの承認（Change Summary添付）→ 人間がPublishing Status
                 をPublishedへ手動更新
```

> 本文にも一文追記：「ARuアプリへの実際の掲載（Publishing Status＝Published）は、いずれのUpdate Levelでも常に人間が行う。AIが承認ゲートを満たした記事を自動的にARuアプリへ掲載することはない（実装：`notion-build/automation/publishing_center.py`。詳細は[Automation Scripts](./Automation-Scripts.md)）。」

---

## 目次

- [Revision History](#revision-history)
1. [Mission](#1-mission)
2. [Vision](#2-vision)
3. [Core Values](#3-core-values)
4. [Editorial Policy](#4-editorial-policy)
5. [Cultural Policy](#5-cultural-policy)
6. [Translation Policy](#6-translation-policy)
7. [Source Policy](#7-source-policy)
8. [Trust Score Policy](#8-trust-score-policy)
9. [AI Behavior Rules](#9-ai-behavior-rules)
10. [Human Review Rules](#10-human-review-rules)
11. [Update Rules](#11-update-rules)
12. [Emergency Update Rules](#12-emergency-update-rules)
13. [Legal & Medical Rules](#13-legal--medical-rules)
14. [Quality Checklist](#14-quality-checklist)
15. [Publishing Workflow](#15-publishing-workflow)
16. [SNS Policy](#16-sns-policy)
17. [Version Control](#17-version-control)
18. [Audit Log](#18-audit-log)
19. [Future Expansion Policy](#19-future-expansion-policy)
20. [Governance](#20-governance)

---

## 1. Mission

**ARuは、日本で暮らし、旅し、働くすべての外国籍の人が、「何をすべきか」だけでなく「なぜそうするのか」を理解できるようにする。**

情報を届けるだけでは足りない。法律、マナー、行政手続き、生活習慣の背景にある文化的な理由まで伝えることで、外国籍の人が日本社会に不安ではなく理解を持って参加できるようにする。それがARuの存在理由であり、AIも人も、この一点に奉仕するために働く。

## 2. Vision

10年後、ARuは以下のような存在になっている。

- 日本を訪れる、または日本で暮らす外国籍の人にとって、**最初に頼る場所**になっている。
- AIと人間編集部が協働し、**毎日**ニュース・法改正・イベント・文化情報を12言語以上で発信し続けている。
- 個人利用者だけでなく、外国籍社員を雇用する**企業**、**自治体**、**日本語学校**からも、信頼できる情報基盤として選ばれている。
- 「AIが作った」という理由で情報の信頼性が疑われるのではなく、**ARuが公開した情報だから信頼できる**、という評判が確立している。

## 3. Core Values

ARuで働くすべてのAIエージェントと人間は、判断に迷ったとき、以下の順序で優先順位をつける。

1. **正確性 ＞ 速報性** — 一番乗りより、正しいことを優先する。不確実な情報は「速く出す」より「確認してから出す」。
2. **Whyを説明する** — 「何をすべきか」だけの情報は情報ではなく指示に過ぎない。必ず文化的・法的な背景（なぜ）を添える。
3. **人を置き去りにしない** — AIは反復作業を担うが、安全・法律・尊厳に関わる判断は必ず人が最終責任を持つ。
4. **尊厳の尊重** — 外国籍の人を「問題」「対応すべき対象」として描かない。当事者として、対等な生活者として描く。
5. **透明性** — AIが書いたものはAIが書いたと分かるようにする。出典と更新履歴は常に開示できる状態にする。
6. **10年後も読める設計** — すべてのルールとシステムは、Rei以外の誰かが引き継いでも運用できることを前提に作る。

## 4. Editorial Policy

- すべての記事は、[ARu HQ データベース設計書](./aru-hq-er-design.html)の **Article（日本語マスター）** レコードとして生まれる。カテゴリは Category プロパティで固定し、途中で曖昧にしない。
- 1記事＝1メッセージ。複数のテーマを1記事に詰め込まない。
- 記事には必ず「対象者（Target Audience）」を明記する。誰に向けた情報かが曖昧な記事は公開しない。
- 文体はカテゴリによって変える。
  - 法律・行政手続き・ビザ・税金等 → 正確・簡潔・断定を避ける（「〜となる場合があります」）
  - 文化・イベント・旅行情報 → 温かく、物語的に、体験として書く
- AIが下書きした記事には内部的に「AI Draft」のステータスを付け、公開後も内部監査でAI起筆であることを追跡できるようにする（読者への開示ポリシーは[SNS Policy](#16-sns-policy)・アプリ表示側の設計に準ずる）。
- 「マナー（すべき）」と「法律（しなければならない）」は文章内で明確に区別する。読者が両者を混同しないように、法的義務には必ずその根拠（法令名等）を添える。

## 5. Cultural Policy

ARuの根幹である「Decode Japan」は、扱いを誤ると最も読者を傷つけやすい領域でもある。

- **一般化を避ける。** 「日本人は〜する」という断定ではなく、「多くの地域で〜する慣習がある」のように、地域差・個人差の余地を残す。
- **マナーと法律を混同しない。** 「郷に入っては郷に従え」で片づけず、その慣習がなぜ生まれたか（歴史・宗教・気候・都市構造など）を可能な範囲で説明する。分からない場合は、分からないと書く。推測を事実のように書かない。
- **異国情緒化（エキゾチシズム）を避ける。** 日本文化を「不思議」「奇妙」として消費する視点ではなく、実用情報として、対等な視点で書く。
- **地域差を尊重する。** 日本文化を単一のものとして扱わず、都市部と地方、地域ごとの違いに触れる。
- リスクが高い文化的トピック（宗教儀礼、地域固有の慣習、繊細な歴史的背景を含むものなど）は、該当分野の経験を持つメンターのレビューを推奨する。

## 6. Translation Policy

翻訳は [Translation DB](./aru-hq-er-design.html) の子レコードとして管理され、以下を遵守する。

- 日本語Articleが唯一のマスター。翻訳は複製ではなく、Articleに従属する子レコードとして管理する。
- 翻訳は**直訳ではなく意味と文化的ニュアンスの翻訳**を優先する。慣用句・文化的言及がそのまま訳せない場合は、Translated Bodyに翻訳者注記を残す。
- 対応言語は [Language Master](./aru-hq-er-design.html) に登録された言語に限る。新言語の追加はLanguage Masterへの追加を起点とし、Article／Translationのスキーマ変更を伴わない。
- 日本語Articleが更新されると、該当するTranslationの `Needs Re-Translation` が自動的に真になる。これを **一定期間（目安30日）を超えて放置しない**。放置された「要再翻訳」記録はダッシュボードで可視化し、編集部の負債として扱う。
- 言語ごとの展開優先順位は、利用者数・支援の緊急性（例：技能実習生向けの生活情報は優先度高）に基づいて決定する。

## 7. Source Policy

- すべての記事は、[Source Library](./aru-hq-er-design.html) に登録された情報源に遡れなければならない。出典のない記事は公開しない。
- 情報源の信頼度は3段階で扱う。

| 信頼度 | 情報源の種類 | 扱い |
|---|---|---|
| 高 | 政府・自治体の公式発表 | 単独で採用可 |
| 中 | 報道機関・学術情報 | 単独で採用可、ただし一次情報の裏取りを推奨 |
| 低 | SNS・コミュニティ情報 | 単独では不可。高〜中の情報源による裏取りが必須 |

- 法律・ビザ・税金・年金・保険・医療・労働関係（Update Level 2・3対象）の記事は、**一次情報源（省庁・自治体の公式ページ）を必ず含める**。
- 情報源の `Last Checked` が一定期間（法制度系は目安90日）を過ぎている場合、Automationが再確認を促す。

## 8. Trust Score Policy

読者が「この情報はどれくらい信頼できるか」を判断できるようにするため、記事ごとに Trust Score を算出する。

**構成要素**

| 要素 | 説明 |
|---|---|
| Source Reliability | Source Libraryの信頼度（高・中・低） |
| Review Level | Update Level 1〜3のうち、実際に通過したレビュー段階 |
| Freshness | 最終確認日からの経過日数 |
| Mentor Endorsement | 専門メンターによる監修の有無 |

**表示方針**

- Trust Scoreは内部の管理指標であると同時に、将来的にアプリ上で簡易な信頼バッジ（例：確認済み／要再確認）として読者に提示することを目指す。
- Trust Scoreが一定水準を下回った記事は、Dashboardで「要点検」として一覧化し、編集部が優先的に手を入れる対象にする。
- Trust Scoreは検閲や非公開化の道具ではなく、**どこにレビューの手を割くべきかを示す羅針盤**として運用する。

## 9. AI Behavior Rules

ARu HQで稼働するすべてのAI Agent（Research／Writer／Translator／SNS／SEO／QC）は、以下を守る。

- **事実や出典を捏造しない。** 確認できない情報は「確認できていない」と明示する。存在しない法令・統計・引用を作らない。
- **個別の法律・医療・在留資格相談に、専門家であるかのように回答しない。** 一般的な情報提供にとどめ、個別の状況については人（メンターまたは有資格の専門家）へ接続する（詳細は[Legal & Medical Rules](#13-legal--medical-rules)）。
- **人間のメンターや専門家を装わない。** AIが生成した内容であることを、内部記録上常に追跡可能にする。
- **確信度が低い場合は、進んで人間レビューを要求する。** Update Levelが1であっても、AI自身が判断に自信が持てない場合はHuman Review Statusを Pending に切り替えてよい。
- **Prompt Libraryで承認されたプロンプトの範囲で動く。** 公開コンテンツに対して、その場限りの即興プロンプトを使わない。
- **Publish Approvalのゲートを迂回しない。** どんな自動化トリガーであっても、Update Level 2・3のコンテンツを人間の承認なしに公開状態にしない。

## 10. Human Review Rules

- **Update Level 1**：人間の事前レビューは不要。ただし月次で一定割合（目安10%）を無作為抽出し、事後品質監査を行う。
- **Update Level 2**：該当分野の専門性を持つメンター（例：法律・行政手続きは行政書士、医療は医療関係者）がレビューする。担当外のメンターによる承認は無効とする。
- **Update Level 3**：編集長（Rei）または該当分野の専門メンターが確認する。**AI単独での承認は存在しない。**
- レビュー担当者は、原則としてその記事の翻訳・執筆を行ったAI Agentと同一の主体であってはならない（人間によるダブルチェックの原則）。
- レビューの目安対応時間：Level 2は48時間以内、Level 3は24時間以内。超過した場合はDashboardにエスカレーション表示する。

## 11. Update Rules

- Articleの `Update Date` が変化した時点で、紐づくすべてのTranslationの再翻訳判定が走る（[ARu HQ データベース設計書](./aru-hq-er-design.html) 参照）。
- 内容に影響しない軽微な修正（誤字脱字、リンク切れ）は、Update Levelの再判定を伴わない「マイナー更新」として扱う。
- 事実・法令・数値に関わる修正は「実質更新」として扱い、通常の [Publishing Workflow](#15-publishing-workflow) を再度通過させる。
- Update Level 2・3のコンテンツは、変更が検知されなくても**定期的な再確認**（目安90日ごと）を行う。情報が「古いまま正しそうに見える」状態を放置しない。

## 12. Emergency Update Rules

公開済みの情報に誤りが見つかった場合、または法改正・災害・詐欺情報など、放置すると読者に実害が及ぶ変化が起きた場合、通常のワークフローを待たない。

1. 誰でも（AI Agentを含む）「Emergency」として記事にフラグを立てられる。
2. フラグが立った記事は、**日本語版・全翻訳版が同時に**「確認中」表示に切り替わる（言語間で放置期間の差が生まれないようにする）。
3. 編集長または当該分野のオンコールメンターが、目安6時間以内に内容を確認する。
4. 修正内容・原因・対応者・対応時刻は必ず [Audit Log](#18-audit-log) に記録する。
5. 緊急対応は承認プロセスを「速める」ものであり、[Legal & Medical Rules](#13-legal--medical-rules) が定める人間の承認そのものを省略するものではない。

## 13. Legal & Medical Rules

ARuは法律事務所でも医療機関でもない。この一線を最も厳格に守る領域である。

- 法律・ビザ・税金・年金・保険・医療・労働関係のコンテンツには、**必ず免責事項**（ARuは一般的な情報提供であり、個別の法的・医療的助言ではない旨）を明記する。
- この領域のコンテンツは、**有資格の専門メンター（行政書士・医療関係者等）のレビューなしに公開されることはない**。緊急対応であっても、この要件を省略しない。
- AIチャット（AI相談機能）は、個別の法律・医療・在留資格の判断を下さない。一般情報の提供に徹し、個別の相談は人間のメンターまたは有資格専門家への接続を案内する。
- 迷ったら公開しない。「おそらく正しい」情報は「要確認」として保留し、断定して公開しない。

## 14. Quality Checklist

公開前に、AIまたは人間が以下を確認する。

- [ ] 出典（Source Library）が明記されている
- [ ] Categoryと Target Audience が設定されている
- [ ] 「何をすべきか」だけでなく「なぜ」が書かれている
- [ ] マナーと法律が混同されずに区別されている
- [ ] 法律・医療系の場合、免責事項が入っている
- [ ] Update Level 2・3の場合、有資格メンターのレビューが完了している
- [ ] 翻訳がある場合、Needs Re-Translationが解消されている
- [ ] 一般化・ステレオタイプ表現がない
- [ ] リンク・日付・固有名詞が最新かつ正確である
- [ ] SNS投稿文が本文の趣旨と矛盾していない

## 15. Publishing Workflow

ARuの公開フローは、[データベース設計書](./aru-hq-er-design.html) が定める構造をそのまま運営ルールとして採用する。

```
Source Library
     ↓
  Research
     ↓
  Article（日本語マスター・Update Level判定）
     ↓
  Translation（言語ごとの子レコード）
     ↓
  ┌─ Level 1 ── 自動公開
  ├─ Level 2 ── 担当メンターの承認 → 公開
  └─ Level 3 ── 編集長／専門メンターの承認（Change Summary添付）→ 公開
     ↓
  SNS Queue（多言語展開）
```

- レベル別の詳細な分岐条件は、[データベース設計書 §6 自動化ワークフロー](./aru-hq-er-design.html#workflow) を正とする。本憲章は「なぜそのゲートが必要か」を定め、設計書は「どう実装するか」を定める。両者は常に一致していなければならない。

## 16. SNS Policy

- SNS投稿（Instagram／Threads／X）は、Update Level 2・3のコンテンツについて、**Publish Approvalが下りる前に投稿しない**。
- SNSの投稿文は記事の要約であり、代替ではない。「なぜ」の説明は本文へのリンクに委ねてよいが、誤解を招く切り取りはしない。
- プラットフォームごとにトーンを変える。
  - Instagram：文化・体験を視覚的に伝える
  - Threads：会話的、コミュニティとの対話を重視
  - X：速報性・簡潔さを重視（ただしUpdate Level 2・3は速報より承認を優先する）
- 多言語SNS展開は、各言語のTranslation.Publish Statusが「公開」になった言語から順次行う。
- コメント欄の外国人差別的・攻撃的な投稿への対応方針（削除・非表示・通報）は編集部が定め、対応記録を残す。

## 17. Version Control

- 本憲章は **Major.Minor.Patch**（例：v1.0.0）のセマンティックバージョニングを採用する。
- バージョン番号は、[§20 Governance](#20-governance) が定める**改訂レベル（Level A/B/C）**とそのまま対応する。

| 改訂レベル | 内容の例 | Versionへの影響 |
|---|---|---|
| Level A（軽微な変更） | 誤字修正 | **Patch**を上げる（v1.0.0 → v1.0.1） |
| Level B（運営改善） | 機能追加・ワークフロー変更 | **Minor**を上げる（v1.0.1 → v1.1.0） |
| Level C（理念・憲章変更） | 理念変更・Governanceそのものの変更 | **Major**を上げる（v1.1.0 → v2.0.0） |

- どのレベルの改訂であっても、変更点・変更理由・影響範囲・承認者・発効日を [Revision History](#revision-history) に1行追加する。省略は認めない。
- 過去バージョンは削除せず、アーカイブとして保持する（10年間の意思決定の履歴を追跡できるようにするため）。
- Prompt Library、Article、Translationなど、システム側の版管理は[データベース設計書](./aru-hq-er-design.html)の各DB仕様に従う。本憲章の版管理はそれらと独立して行う。

## 18. Audit Log

以下は必ず記録し、追記のみ・削除不可（append-only）で保持する。

- すべてのPublish Approval（誰が・いつ・何を承認したか）
- すべてのEmergency Update（発生・対応・原因）
- Update Level 2・3コンテンツに対するAI Agentの実行履歴
- 本憲章およびPrompt Libraryの変更履歴

保持期間は最低10年とする。これは、ARuが「作った時の判断」を将来のRei自身、あるいは後継者が検証できるようにするためである。

## 19. Future Expansion Policy

ARuの成長は、以下の原則の範囲内で行う。

- 新しい言語は、必ず [Language Master](./aru-hq-er-design.html) への登録を起点とし、Article／Translationのスキーマ変更を発生させない。
- 新しいコンテンツカテゴリを追加する際は、公開前に必ずUpdate Level（1・2・3のいずれか）を割り当てる。レベル未定義のカテゴリは公開しない。
- 新しいAI Agentを稼働させる際は、[AI Agents DB](./aru-hq-er-design.html)に役割・使用プロンプト・モデルを登録してからでなければ、本番コンテンツに触れさせない。
- 企業向け（BtoB）展開を行う場合、編集の独立性を損なわない。スポンサー・企業提供コンテンツは、通常の編集コンテンツと明確に区別して表示する。
- 自治体・企業との連携によって得られる情報源は、[Source Policy](#7-source-policy) の信頼度分類に従って扱い、特別扱いしない。

## 20. Governance

### 改訂レベル

本憲章の改訂は、影響範囲に応じて3段階のレベルに分類し、レベルに応じたレビュー期間と承認プロセスを経る。

| Level | 対象 | レビュー期間 | 承認 |
|---|---|---|---|
| **Level A（軽微な変更）** | 誤字脱字、表現改善、レイアウト変更、AIプロンプト改善 | なし（即日反映可） | 編集長（Rei）の承認のみ |
| **Level B（運営改善）** | ワークフロー変更、AIエージェント追加、新しいデータベース追加、翻訳対象言語追加、Source Policy更新 | 72時間以上 | 編集長の承認 |
| **Level C（理念・憲章変更）** | Mission、Vision、Core Values、Editorial Policy、Trust Score Policy、AI Behavior Rules、Governanceそのもの 等、ARuの根幹に関わる変更 | 最低7日間 | 編集長が最終決定する。将来的にはメンター・専門家の意見も参考にする |

- どのレベルに当たるか判断に迷う場合は、より慎重な上位レベルを適用する。
- Level B・Cの提案は、レビュー期間中に内容を凍結する必要はなく、フィードバックを受けて修正してよい。ただしレビュー期間の起算日は、修正の都度リセットせず、最初に提案した日を起点とする。
- 改訂プロセスの流れ：改訂案の提示 → レベル判定 → レベルに応じたレビュー期間 → 編集長の承認 → バージョン更新（[§17 Version Control](#17-version-control)） → [Revision History](#revision-history) への記録。

### 意思決定の原則

- AIの提案と人間の判断が食い違う場合、**常に人間の判断を優先する**。
- 現時点で、本憲章の最終承認権限は編集長（Rei）に属する。
- 将来、メンターが増え組織が拡大した場合、専門メンターによる諮問委員会を設置し、特にLevel C領域（法改正など重要な判断を含む）に助言を求める体制を検討する。

### 継承条項

編集長が意思決定を行えなくなった場合に備え、本憲章の改訂権限および緊急対応の最終承認権限を委譲できる後継者（副編集長、または信頼できる専門メンター）を、組織拡大の初期段階で指名する。10年という運営期間を掲げる以上、特定の個人に依存しない意思決定の継続性を、早い段階で設計しておく。

---

*ARu HQ / Decode Japan — Constitution v2.0.0 — 2026-07-12*
