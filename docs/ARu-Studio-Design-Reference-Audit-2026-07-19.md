<title>ARu Studio Design Reference 整合性確認 ＋ 現状監査レポート（2026-07-19）</title>

# ARu Studio Design Reference 整合性確認 ＋ 現状監査レポート
### Best Practice Report v1.0を設計基準として採用したことに伴う、5文書の整合性確認と現状監査

| | |
|---|---|
| **Status** | 確定（監査完了、実装判断は未着手） |
| **Date** | 2026-07-19 |
| **対象文書** | [Architecture-Specification-v1.0.md](./Architecture-Specification-v1.0.md) / [User-Journey-Architecture-v1.0.md](./User-Journey-Architecture-v1.0.md) / [Knowledge-Lifecycle-Architecture-v1.0.md](./Knowledge-Lifecycle-Architecture-v1.0.md) / [Mission-Control-Architecture-v1.0.md](./Mission-Control-Architecture.md) / [ARu-Studio-Best-Practice-Report-v1.0.md](./ARu-Studio-Best-Practice-Report-v1.0.md) |
| **本書の位置づけ** | 監査レポート。実装仕様書ではない。改善案・新機能提案はこの後、別途検討する |
| **確認方法** | 4つの既存Architecture文書を全文再読 ＋ Notion実データ（Research/Articles/Law Update/Source Library）の実スキーマ照会 ＋ 既存自動化コード（`notion-build/automation/*.py`）のgrep・確認 |

---

## 1. 5文書の整合性確認

結論：**致命的な矛盾はない。** Best Practice Reportは既存4文書と競合する設計ではなく、既存の考え方を上位の運用思想として体系化し、いくつかの新しい概念（Source/Evidence/Claim分離、Risk & Approval Matrix、AI活動ログ）を追加するものである。ただし、**要確認・要判断の点が3つ**ある。

### 1.1 整合している点

| 概念 | 既存4文書での扱い | Best Practice Reportでの扱い | 整合性 |
|---|---|---|---|
| No New Database／既存資産の再利用 | Architecture-Specification 設計原則2「No New Database」 | §6.4「既存資産の再利用」 | ◎ 同一原則。矛盾なし |
| Article Brief | 本セッションで実装済み（Research拡張） | Step 5「Article Brief」として詳細定義 | ◎ 同じ実体を指している。Best Practice Reportの定義の方が詳細（Reader Job／採用Claims／リスクと承認者／更新期限などを含む） |
| Progressive Disclosure | Studio-v4.2-Editor-First-Guide（3ゾーン、トグルによる詳細折りたたみ） | §6.2「Progressive Disclosure」 | ◎ 既に実装されている考え方と一致 |
| Editor Home / AI Command Center分離 | `editor_home.py`（Version 4 Phase 5で実装済み）／`ai_command_center.py` | §6.1「Editor HomeとAI Command Centerの分離」 | ◎ 既にこの分離が実装済み。Best Practice Reportは名称こそ違うが同じ構造を推奨している |
| Mission Controlの「判断速度優先」原則 | Mission-Control-Architecture §3「情報を増やすことと判断を速くすることが競合したら判断速度を優先」 | §6.2 Progressive Disclosure、§8成功指標「編集判断までの時間」 | ◎ 同一方向性 |

### 1.2 要確認・要判断の点（矛盾ではないが、放置すると将来衝突する）

**① 「Constitution」の二重化**
既存の最上位文書 `ARu-Constitution.md` と、Best Practice Report §2「ARu Editorial Constitution（12原則）」がどちらも「憲法」を名乗っている。本プロジェクトの既存ルール（[[feedback_constitution_consistency_check]]）では、Constitution級の変更は「正式なPending Amendmentsとして提出し、無断で編集しない」ことになっている。
→ **対応案**：Best Practice Report §2の12原則をARu-Constitution.mdへの正式なPending Amendmentとして提出するか、それとも「Editorial領域に限定した下位憲章」として別文書のまま維持するかは、Rei自身の判断が必要。本監査では両文書とも変更していない。

**② Risk & Approval Matrix（R1-R4）と既存Update Level（1-2）の関係**
詳細は §3「設計衝突」参照。

**③ 「QA Card」の名称衝突（既知・本書が新たに悪化させたものではない）**
User-Journey-Architecture Content Ladder Level 1「QA Card」（＝完成された読み切りコンテンツ）と、Studio-Operating-Manual §9 編集フロー④「QA Card」（＝執筆前の内部品質チェックゲート、未実装の概念）が同じ名前で別の意味を持つ、既存の未解決事項。Best Practice ReportのStep 1〜5はContent Ladder側の意味（実コンテンツ）と一致しており、この衝突を悪化させてはいないが、解消もしていない。

---

## 2. 現状監査（Best Practice Reportを基準に）

### 2.1 既に実装済み

| Best Practice Reportの概念 | 実装箇所 | 備考 |
|---|---|---|
| Editor Home / AI Command Center分離（§6.1） | `editor_home.py`（Version 4 Phase 5）／`ai_command_center.py` | 名称は異なるが構造は一致 |
| Progressive Disclosure（§6.2） | Dashboard 3ゾーン構成、Article Brief内トグル | Studio v4.2で実装済み |
| 既存資産の再利用優先（§6.4） | Architecture-Specification 設計原則2/7 | 同一原則が既に確立 |
| Article Owner（DRI相当） | Articles DB `Article Owner`（people型プロパティ） | プロパティは存在。運用上の記入徹底は未確認（§2.2「一部実装」に近い） |
| Article Brief（Step 5） | 本セッションでResearchを拡張（Related Law Updates／Related QA／Related Articles、Editor's Notes） | Best Practice Report基準では一部の項目（採用Claims、Evidence一覧、CTA・次の行動）が未収録 |

### 2.2 一部実装

| Best Practice Reportの概念 | 現状 | ギャップ |
|---|---|---|
| Correction Propagation（修正の下流伝播） | `law_update_pipeline.py`の`run_impact_analysis()`／`sync_downstream_on_resolution()`が、Law Update解決時にStory Bank/Articlesへ影響分析・再翻訳フラグを伝播 | Law Update起点の伝播のみ。Source Library側の情報更新や、Research起点の伝播経路はない |
| Status Machine（状態遷移の明文化） | 各DBにStatusプロパティと事実上の遷移は存在（Publishing Status、Story Status、Update Status等） | 「entry condition／exit condition／次のアクション」を明文化した一元的なドキュメントは存在しない。Best Practice Report §5がこの形式で書かれた最初の文書 |
| Article Owner／DRI運用 | プロパティは存在 | 全記事に必須入力させる運用ルール・チェック機構はない |
| Freshness監視 | `article_freshness_monitor.py`が既に稼働 | Best Practice Reportが指す「根拠(Evidence)の鮮度」ではなく「記事自体の鮮度」のみを見ている。Evidence単位の鮮度監視は未実装 |

### 2.3 設計採用済み・実装方式未決定

Best Practice Reportの概念の中で、「設計として採用は決定しているが、実装方式（独立DB化するか否か）はまだ決めていない」という中間状態のもの。

| Best Practice Reportの概念 | 現状 | 採用方針 |
|---|---|---|
| Source → Evidence → Claim の3層分離 | 独立したデータ実体はまだ存在しない。現状はSource Library（情報源）→ Research（`Evidence Level`という単一プロパティのみ）→ Articles（`Review Evidence Score`という単一プロパティのみ） | **設計としては採用済み。独立DB化を前提とせず、まずArticle Brief内で論理構造（Sourceのどの主張をEvidenceとして採用し、どのClaimとして記事に反映するかを、既存プロパティ・関連の組み合わせと記述ルールで表現する）として先行利用する。運用してみて独立DB化の必要性が確認できた段階で改めて検討する** |

### 2.4 未実装

| Best Practice Reportの概念 | 現状 |
|---|---|
| Risk & Approval Matrix（R1-R4） | 存在しない。近い概念として`compute_update_level()`（`generate_article_pipeline.py`）があるが、これはCategoryから1か2の2値を返すだけの単純な関数で、R1-R4の4段階・承認者定義とは別物 |
| AI活動ログ（AI Activity Log） | リポジトリ全体をgrep確認したが該当する仕組みは存在しない。`duplicate_prevention_report.py`のJSONLログは重複検知イベントのみを記録する狭い用途のもので、汎用AI活動ログではない |
| Reader-choice personalization（読者側の選択によるパーソナライズ） | 存在しない。これは本リポジトリ（編集部バックエンド）の範囲外で、ARuアプリ側の実装が前提となる。Knowledge-Lifecycle-Architectureの「User Feedback Loop」が同じ理由でARuアプリ依存・未着手と既に整理されている |
| 記事の「昇格」ロジック（Article→Deep Guide等、深さの進化） | Knowledge-Lifecycle-Architecture §該当項で既に「未実装」と整理済み。Best Practice Reportの記述と矛盾なく、単に未着手のまま |

### 2.5 設計衝突（要判断）

**Risk & Approval Matrix（R1-R4） vs 既存Update Level（1-2）**

- 既存：`compute_update_level(category)`は7つのCategoryを2群に分け、Level 1（低頻度更新）／Level 2（高頻度更新）を返す。この値は主に更新頻度・レビュー間隔の判定に使われている。
- Best Practice Report：R1（コラム・文化紹介）〜R4（医療・法律・金融・安全）の4段階で、リスクの高さに応じた承認者・レビュー深度を定義する、目的が異なる軸（更新頻度ではなく「間違えたときの被害の大きさ」）。

この2つは**同じ「1〜4」に見えるが軸が違う**ため、そのまま統合すると意味が変わってしまう。実装するかどうかの判断の前に、「更新頻度の軸（既存Update Level）」と「リスクの軸（新Risk Matrix）」を別軸として並存させるのか、既存を置き換えるのかをRei自身が決める必要がある。**本監査ではどちらが正しいかの判断はしない。**

### 2.6 既存DB・Relation・Automationの再利用（Best Practice Report実装時に使えるもの）

| Best Practice Reportが必要とするもの | 転用できる既存資産 |
|---|---|
| Article Brief（Step 5） | 本セッションで拡張済みのResearch DB（Related Law Updates／Related QA／Related Articles／Editor's Notes） |
| Source→Evidence→Claim（論理構造として先行利用） | 既存Research（`Evidence Level`）／Articles（`Review Evidence Score`）／Source Libraryへのリレーション。新規プロパティ追加は最小限にとどめ、まずEditor's Notesの記述ルール・既存リレーションの組み合わせで表現する |
| Draft Generation〜Publish（Step 6-9） | 既存`generate_article_pipeline.py`／Publishing Status／SNS Queue／Translation |
| Correction Propagation（Step 10の一部） | 既存`law_update_pipeline.py`の`run_impact_analysis`／`sync_downstream_on_resolution` |
| Editor Home（§6.1） | 既存`editor_home.py` |
| Progressive Disclosure（§6.2） | 既存Article Brief内トグル構造、Dashboard 3ゾーン構成 |
| Article Owner／DRI | 既存Articles.`Article Owner`プロパティ（運用の徹底のみ課題） |

新規実装（新しいDB・自動化の追加）が必要となるのはRisk Matrix、AI活動ログの2点に絞られる。Source/Evidence/Claimは独立DB化を前提とせず、既存資産の組み替えで先行利用する方針のため、この段階では新規実装の対象に含めない。

### 2.7 Article Brief改善への影響

現在のArticle Brief（本セッションで実装したResearch拡張）は、Best Practice Report Step 5が定義する項目のうち以下をまだ持っていない：

- 採用するClaimsの論理構造（現状はEditor's Notes欄に自由記述で混在。独立DB化はせず、まずここに構造を持たせる先行利用を検討する）
- 使用するEvidence・Sourcesの明示的な一覧（現状はSource Libraryへのリレーションのみで、どのSourceのどの主張を採用したかの粒度がない。Source/Evidence/Claimの論理構造をArticle Brief内に先行導入する際の最初の対象になる）
- リスクレベルと承認者（R1-R4が未実装のため対応する項目がない）
- CTA・次の行動の明示欄

Source/Evidence/Claimの論理構造をArticle Brief内でどう表現するか（プロパティ追加か、既存Editor's Notesの記述ルール整備か）は、「材料収集基盤をどう整えるか」の検討の中心テーマとなる。次の検討フェーズで扱うが、本監査では実装しない。

### 2.8 既存データへの影響

- Source/Evidence/Claimは独立DB化を前提としない方針のため、既存Research 35プロパティ・Articles 77プロパティへの破壊的変更は想定していない。将来、運用実績から独立DB化の必要性が確認された場合のみ、その時点で「No New Database」原則との整合を改めて検討する。
- Risk Matrix導入の場合、既存`Update Level`を参照しているコード（レビュー間隔計算等）に影響する可能性がある。置き換えではなく併存とする場合は既存データへの影響はない。
- AI活動ログ導入は既存データへの破壊的影響はなく、新規追加のみで対応可能と見込まれる。

---

## 3. まとめ

- 5文書は致命的に矛盾していない。Best Practice Reportは既存の考え方を体系化し、Source/Evidence/Claim分離・Risk Matrix・AI活動ログという3つの新しい概念を追加するものである。
- Best Practice Reportが提案する構造の多く（Editor Home分離、Progressive Disclosure、既存資産再利用、Article Brief、Correction Propagationの一部）は**既に実装済みまたは一部実装済み**であり、ゼロから作るものではない。
- Source/Evidence/Claim分離は**設計として採用済み**。独立DB化は前提とせず、まずArticle Brief内の論理構造として先行利用し、必要性が確認できた段階で独立DB化を検討する方針。
- 新規実装（新しいDB・自動化の追加）が必要なのはRisk & Approval Matrix（既存Update Levelとの関係整理を含む）とAI活動ログの2点に絞られる。
- 「ARu Editorial Constitution」と既存ARu-Constitution.mdの関係、およびRisk MatrixとUpdate Levelの関係は、実装着手前にRei自身の判断が必要な2点として残っている。
- 本監査では実装・DB変更・自動化追加は一切行っていない。

*ARu HQ / Decode Japan — Design Reference整合性確認＋現状監査 — 2026-07-19*

---

## 後続実装による更新（2026-07-20 追記、元の監査内容は変更していません）

本監査（§2.7）が指摘した「Article Brief Step 5には採用Claimsの論理構造・使用Evidence/Sourcesの明示的な一覧が未収録」というギャップは、同日以降に確定・実装された次の2点により**一部解消済み**：

- `docs/Article-Brief-Specification-v1.0.md`（Reader Need／Source／Evidence／Claim／6点のBrief完成チェックリストを正式仕様化）
- コミット `b48ef91`「feat: add evidence-grounded Article Brief pipeline」（`article_brief.py`／`article_brief_status.py`／`article_brief_init.py`の実装）

**完全解消と断定はしない。** 本監査が挙げた4項目（採用Claimsの論理構造／Evidence一覧／リスクレベルと承認者／CTA・次の行動）のうち、リスクレベルと承認者（Risk & Approval Matrix R1-R4）は依然として未実装のまま。解消範囲は最新の仕様書・実装コードとの再確認を対象とする。
