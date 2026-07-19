<title>Article Brief Specification v1.0</title>

# Article Brief Specification v1.0
### Article Brief（Research）が満たすべき内容要件の正式仕様

| | |
|---|---|
| **Status** | 仕様確定（本書自体は仕様書であり、DB変更・自動化追加は未実施） |
| **Date** | 2026-07-19 |
| **位置づけ** | [Architecture-Specification-v1.0.md](./Architecture-Specification-v1.0.md)・[Mission-Control-Architecture.md](./Mission-Control-Architecture.md)・[ARu-Studio-Best-Practice-Report-v1.0.md](./ARu-Studio-Best-Practice-Report-v1.0.md)と同じ位置付けの設計文書。[ARu-Studio-Design-Reference-Audit-2026-07-19.md](./ARu-Studio-Design-Reference-Audit-2026-07-19.md)で「設計採用済み・実装方式未決定」と整理されたSource/Evidence/Claimの表現方法（§5）を含め、Article Briefの内容要件を確定する |
| **本書の範囲** | 今回の改訂は **Reader Need／Source／Evidence／Claim／Brief完成条件** の5項目に限定する。新規DB・新規プロパティ・自動化・Risk Matrix・ページレイアウト・AI Activity Logは対象外（§9） |

---

## 1. Article Briefの定義（1行で）

**Article Briefとは、読者の疑問を明確にし、記事で伝えるClaimと、それを支えるEvidenceおよびSourceが追跡可能な形で揃い、記事制作へ進めるかを判断できる状態である。**

「読者が最初に知るべき結論」「注意事項・例外」「CTA・次の行動」は、将来のArticle Brief拡張項目として扱う。これらはBest Practice Report §3.5が定義する必須項目に含まれるが、本書（v1.0）の設計対象（Reader Need／Source／Evidence／Claim／Brief完成条件）には含めず、§6の完成条件の判定対象にもしない（§7・§9参照）。

Article Brief自体はNotion上の新しいページ種別ではなく、既存Research DBの1レコードが到達すべき「完成状態」を指す（Automation-Scripts.md「Research → Article Brief」節で実装済みのリレーション拡張がその土台）。

Article Briefはこの1行の定義だけでは判断できない。**すべてのArticle Briefは、Reader Need（§2）を出発点として書き始め、Brief完成条件（§6）で終わる。** 以降の各セクションはこの一連の流れを構成する。

## 2. Reader Need（出発点の定義）

Article Briefは、記事のテーマやカテゴリからではなく、**Reader Need**——「誰が、どのような状況で、何に困っていて、記事を読んだ後にどうなればよいか」——から書き始める。

### 2.1 構成要素

| 要素 | 問い | 例（外国人の社会保険） |
|---|---|---|
| **誰が（Who）** | どんな属性・状況の読者か | 日本で就労を始めたばかりの技能実習生・技術者ビザ保有者 |
| **どのような状況で（Context）** | いつ・どんな場面でこの疑問にぶつかるか | 入社後、給与明細で初めて社会保険料の天引きを見たとき |
| **何に困っていて（Pain）** | 具体的に何が分からない・不安なのか | なぜ天引きされるのか、将来何に使われるのか、拒否できるのか分からない |
| **読んだ後にどうなればよいか（Outcome）** | 記事を読了した時点で読者が到達しているべき状態 | 社会保険の仕組みと自分が対象かどうかを理解し、次に確認すべき窓口が分かっている |

この4要素が、Best Practice Report §3.5の必須項目のうち「Reader Job」と「記事の約束」を1つに統合したものにあたる（§7の対応表を参照）。

### 2.2 記述場所

新規プロパティは追加しない。既存`Editor's Notes`（rich_text）の先頭に、決まった見出しで記述する：

```
## Reader Need
- Who: <誰が>
- Context: <どのような状況で>
- Pain: <何に困っていて>
- Outcome: <読んだ後にどうなればよいか>
```

### 2.3 Reader Needの役割

Reader Needは単なる項目の1つではなく、**後続のClaim・Evidence・Sourceすべてが「このReader Needに答えるために存在するか」を判定する基準**になる（§6 Brief完成条件①）。Reader Needが曖昧なまま執筆を始めると、Claimが読者の疑問と噛み合わない記事になる。

## 3. Source / Evidence / Claim の関係

3つの用語を、Best Practice Report §3.2〜§3.4の定義に沿って以下のように整理する。新規DB・新規プロパティは追加せず、既存の実装（`Related to Source Library`リレーション、`Evidence Level`、`Verification Status`）の上に、記述の構造だけを追加する。

| 用語 | 定義 | 現状の対応 |
|---|---|---|
| **Source** | 情報の出どころ（省庁サイト、法令、一次情報、報道等） | 既存**Source Library DB**（独立DBとして既に存在） |
| **Evidence** | あるSourceから読み取れる、検証可能な事実・裏付け | 独立実体ではなく、`Editor's Notes`内の記述規約（§4）の`### Evidence N`ブロックとして表現する |
| **Claim** | 記事で読者に伝える主張。1つ以上のEvidenceに支えられている必要がある | 独立実体ではなく、`Editor's Notes`内の記述規約（§4）の`### Claim N`ブロックとして表現する |

### 3.1 追跡可能性（Traceability）の要件

Brief完成条件（§6③）が要求する「EvidenceがSourceまで追跡できる」を満たすため、各Evidenceブロックの`Source:`欄は必ず`Related to Source Library`リレーションに紐づく具体的な1レコードのタイトルを指し示し、`Location:`欄でそのSource内のどこに当該情報があるかまで特定しなければならない。「一般的に知られている」「複数の情報から総合して」のような、特定のSource・箇所に遡れない記述はEvidenceとして扱わない。

## 4. Claims / Evidenceの記述規約

既存`Editor's Notes`内に、Reader Need（§2.2）に続けて以下の見出しで記述する。ClaimとEvidenceは別々のブロックとして分離し、Evidence側からClaim側を`Supports:`で参照する：

```
## Claims

### Claim 1
- Statement:
- Status: Proposed / Supported / Conflicted / Needs Review / Rejected / Superseded

### Evidence 1
- Supports: Claim 1
- Evidence:
- Source:
- Location:
- Evidence Level:
```

各フィールドの意味：

| フィールド | 内容 |
|---|---|
| Claim / Statement | 記事で読者に伝える主張そのもの |
| Claim / Status | §4.1参照 |
| Evidence / Supports | このEvidenceがどのClaimを支えるか（`Claim N`で参照。1つのClaimに複数のEvidenceが対応してよい） |
| Evidence / Evidence | Sourceから読み取れる具体的な事実・裏付けの内容 |
| Evidence / Source | 既存`Related to Source Library`に紐づくレコードのタイトル（§4.2） |
| Evidence / Location | Source内の具体的な参照箇所（ページ番号／セクション名／条文番号／URL内アンカー等） |
| Evidence / Evidence Level | このEvidence固有の確信度（§4.3） |

Claim・Evidenceはそれぞれ独立した通し番号を持つ（`Claim 1, Claim 2...` / `Evidence 1, Evidence 2...`）。1つのClaimに複数のEvidenceブロックが`Supports:`で対応してよい。

### 4.1 Claimの状態

Best Practice Report §3.4のClaim状態定義をそのまま使う：**Proposed／Supported／Conflicted／Needs Review／Rejected／Superseded**（Evidenceブロックには状態フィールドを持たせない）

### 4.2 Sourceの参照方法

新しいリレーションは作らず、既存`Related to Source Library (Related Research)`に紐づいているレコードのタイトルを、対応するEvidenceブロックの`Source:`欄に書く。タイトルが書けないEvidenceは、§3.1の追跡可能性要件を満たしていない。

### 4.3 Sourceの信頼性・鮮度の確認方法

新規プロパティは追加せず、既存Operating-Manual §13のSource Confidence／Freshnessルールをそのまま適用する。Evidenceブロックの`Evidence Level:`欄は、対応する`Related to Source Library`レコードの既存`Evidence Level`プロパティを踏まえつつ、そのEvidence固有の文脈での確信度を編集者が明記する：

- **信頼性** → Evidenceブロックの`Evidence Level`（Official／Verified／Reported／Rumor／AI Suggested）と、参照先Source Libraryレコードの`Evidence Level`／`Verification Status`（Unverified／Verified／Needs Recheck）の組み合わせ
- **鮮度** → `Last AI Update`と`Related Law Updates`の有無（詳細はOperating-Manual §13「Freshness」を参照。本書では重複定義しない）

### 4.4 Reportedの採用条件

`Reported`は無条件には採用できないが、一律禁止でもない。**Official／Verifiedを原則とし**、以下の条件をすべて満たす場合に限り`Reported`のEvidenceをBrief完成条件（§6④）の判定において「信頼性が確認された」ものとして扱う：

- Official情報（省庁・自治体・法令等の一次情報）がそのテーマについて存在しない、または該当しない
- 発信主体（誰が発信したか）が`Evidence`欄または`Location`欄から特定できる
- 掲載日が確認できる
- 具体的な根拠（伝聞・憶測ではなく、確認可能な事実）が示されている
- 必要に応じて、複数のSourceで裏付けられている（1件の報道のみで確信が持てない場合）

この条件は、行政・法律・医療等のOfficial情報が存在しうるテーマではなく、イベント・文化・生活情報等、報道・主催者情報がSourceの中心となるテーマを主に想定している。

`Rumor`／`AI Suggested`は、この条件を満たしても完成条件を満たすEvidenceとしては扱わない（§6④）。

## 5. 独立プロパティ化・DB化の判断基準（変更なし）

本書§2〜§4の記述規約は、まず次の2〜3件の実記事Article Briefで試験的に運用する。運用してみて次のいずれかが確認された場合、独立プロパティ化（例：`Claims`という新しいrich_textまたはmulti_selectプロパティの追加）を検討する：

- `Editor's Notes`内の自由記述とReader Need／Claims・Evidenceセクションが混在し読みにくくなる
- Claimの状態（Supported/Needs Review等）でフィルタ・ビューを作りたいという実運用上の要求が出る

さらに、以下が確認された場合は独立DB化（Evidence DB／Claim DBの新設）を検討する：

- 1つのClaimに複数のArticle・複数のSourceが対応するようになり、Editor's Notes内の記述だけでは関係を追えなくなる
- Claimの状態変化を監査ログとして残す必要が出る（AI活動ログ導入と合流する可能性がある改善候補。§9で対象外と明記）

**現時点ではどちらの閾値にも達していないため、独立プロパティ化・DB化は行わない。**

## 6. Brief完成条件

Article Briefは、必須項目（§7の対応表）が空欄でないことではなく、**以下6点をすべて判定できることをもって「完成」とする。** 判定は自動化せず、編集者が§2〜§4の記述を上から順に確認し、`Editor's Notes`の末尾に一行で判定結果を記録する（新規プロパティは追加しない）。

| # | 完成条件 | 判定方法 |
|---|---|---|
| ① | Reader Needに対してClaimが答えている | 少なくとも1つの`### Claim N`の`Statement`が、`## Reader Need`の**Outcome**（読んだ後にどうなればよいか）に直接対応しているか確認する。対応するClaimがなければ未完成 |
| ② | ClaimをEvidenceが支えている | 各Claimについて、`Supports: Claim N`でそのClaimを指す`### Evidence N`ブロックが1つ以上存在し、かつClaimの`Status`が`Supported`であるか確認する。対応するEvidenceがないまま`Proposed`のClaimが残っていれば未完成 |
| ③ | EvidenceがSourceまで追跡できる | 各Evidenceブロックの`Source:`欄に書かれたタイトルが実際に`Related to Source Library`リレーションの1レコードとして存在し、`Location:`欄で具体的な参照箇所が示されているか確認する（§3.1）。存在しない・特定できない場合は未完成 |
| ④ | Sourceの信頼性と鮮度が確認されている | ③で特定した各Evidenceについて、`Evidence Level`がOfficial／Verifiedであるか、またはReportedかつ§4.4の採用条件をすべて満たしているか確認する（Rumor／AI Suggestedのままでは完成としない）。あわせてFreshness（Operating-Manual §13）が「要更新」でないか確認する |
| ⑤ | 未解決のConflicted／Needs Reviewが残っていない | `### Claim N`のいずれかに`Status: Conflicted`または`Status: Needs Review`が1件でも残っていれば未完成（Evidenceブロックには状態フィールドを持たせないため、判定はClaimのStatusのみで行う） |
| ⑥ | 記事制作へ進めるかを明確に判断できる | ①〜⑤がすべて満たされて初めて判断可能になる。`Editor's Notes`の末尾に`Brief Status: 執筆可能`または`Brief Status: 材料不足 — <理由>`を編集者が明記する |

①〜⑤はいずれか1つでも満たされなければ、⑥は「材料不足」で確定する。⑥は新しい状態遷移やStatusプロパティの追加ではなく、既存`Editor's Notes`内の記述として運用する（§5の独立プロパティ化判断基準に照らして将来見直す）。

## 7. Best Practice Report必須12項目との対応（参考・全体像）

Best Practice Report §3.5が定義する12項目のうち、本書が今回設計対象とした4項目（Reader Need＝Reader Job＋記事の約束、Claim、Evidence・Sources）を反映した最新の対応表。残り8項目は本書の範囲外（§9）。

| Best Practice Report必須項目 | 現状のArticle Brief（Research）での対応 | ステータス |
|---|---|---|
| Reader Job／記事の約束 | §2「Reader Need」として統合・明文化 | **本書で定義済み** |
| 読者が最初に知るべき結論 | `Summary`（AI生成の要約）が近いが、「結論」に特化した項目ではない | 一部実装（本書の範囲外） |
| 採用するClaims | §4「Claims/Evidenceの記述規約」として定義済み | **本書で定義済み** |
| 使用するEvidence・Sources | §3「Source/Evidence/Claimの関係」として定義済み | **本書で定義済み** |
| 見出し案 | なし | 未実装（本書の範囲外） |
| 注意事項・例外 | なし（`Editor's Notes`に自由記述で混在可能） | 未実装（本書の範囲外） |
| ARu Tip候補 | なし | 未実装（本書の範囲外） |
| 必要な図表・UI要素 | なし | 未実装（本書の範囲外、ページレイアウト） |
| リスクと承認者 | なし（Risk & Approval Matrix自体が未実装） | 対象外（別トラック） |
| 更新期限 | `Last AI Update`はあるが「期限」ではなく「最終確認日」。Freshnessルール（§4.3）で代替運用中 | 一部実装（本書の範囲外） |
| CTA・次の行動 | なし | 未実装（本書の範囲外） |

## 8. Mission Controlとの接続

[Mission-Control-Architecture.md](./Mission-Control-Architecture.md) §9で定義されている通り、Article BriefはMission ControlのPhase 3（執筆）の遷移先である。Mission Controlは「決める」画面、Article Briefは「書く」画面という役割分担を維持し、Article Brief側に新しい「決める」機能（カテゴリ一覧・進捗集計等）を持たせない。§6の「Brief Status: 執筆可能」は、あくまでArticle Brief内で完結する判定であり、Mission Control側の表示・集計対象に含めるかは本書の範囲外（§9）とする。

## 9. 本書の範囲外（別トラックとして扱う項目）

今回の改訂はReader Need／Source／Evidence／Claim／Brief完成条件の5項目に限定しており、以下は設計対象に含めていない：

- 新規DB・新規プロパティ・自動化の追加（本書の記述規約はすべて既存`Editor's Notes`内で完結する）
- リスクと承認者（Risk & Approval Matrix）：優先順位付けでLow。既存Update Levelとの関係整理が先に必要（Design-Reference-Audit §2.5参照）
- ページのビジュアルレイアウト（トグル・Callout・埋め込みDatabase Viewの実際の配置）：既知の未着手事項
- AI活動ログとの統合：§5で触れた「Claim状態変化の監査ログ」は将来の統合候補だが、本書では仕様化しない
- 読者が最初に知るべき結論／見出し案／注意事項・例外／ARu Tip候補／必要な図表・UI要素／CTA・次の行動（§1・§7で将来のArticle Brief拡張項目と整理した残り項目）

## 10. 未決定事項

- Claims/Evidenceセクションの記述規約を、Research以外の起点（Source Library更新時の自動反映等）から自動生成するか、編集者の手動記述のみとするかは未決定
- §5の「独立プロパティ化／DB化」の閾値判断は、実際の運用ログ（Operating-Manual §13「運用ログ」）に基づいて行う。現時点で判断材料は1件（外国人の社会保険）のみで不十分
- §6⑥「Brief Status」の記録をArticle Brief単位を超えて集計・可視化する必要が出た場合、どこで（Mission Control／Dashboard等）扱うかは未決定

---

*ARu HQ / Decode Japan — Article Brief Specification v1.0 — 2026-07-19*
