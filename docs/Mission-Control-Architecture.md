<title>Mission Control Architecture v1.0</title>

# Mission Control Architecture v1.0
### ARu Studioのトップページ — 編集判断・編集進捗・パイプライン監視の司令室

| | |
|---|---|
| **Status** | Active（設計確定、実装は未着手） |
| **Date** | 2026-07-19 |
| **位置づけ** | [Architecture-Specification-v1.0.md](./Architecture-Specification-v1.0.md)・[User-Journey-Architecture-v1.0.md](./User-Journey-Architecture-v1.0.md)・[Knowledge-Lifecycle-Architecture-v1.0.md](./Knowledge-Lifecycle-Architecture-v1.0.md)と同じ位置付けのArchitecture文書。今後のMission Control関連の機能追加・改善は、実装前に必ず本書の3つの役割（§2）に照らして判断すること |
| **⚠️ 命名についての重要な注記** | 本書における今後の機能追加は「**ARu Studio v4.4**」以降として扱う。[Roadmap.md](./Roadmap.md)が定義するBusiness Roadmapには存在しない番号であり、対外的な事業判断とは独立したStudio側のエンジニアリング・マイルストーンである（[Version4-Completion-Report.md](./Version4-Completion-Report.md)で確立した命名規則にもとづく） |

---

## 1. Mission（1行で言うと）

**編集長が朝Notionを開いてから、30秒で日本全体の動きを把握し、5分以内に「今日はこれを書こう」と迷わず決められ、そのまま執筆へ進める。**

Mission Controlは情報を並べる画面ではない。**編集会議を1人で5分以内に終わらせるための司令室**である。

---

## 2. 3つの役割

Mission Controlは以下3つの役割を持つ。**今後の機能追加・改善は、必ずこの3つのいずれかを強化するものを優先する。** 単に情報量を増やすだけの追加は、たとえ善意の提案であっても却下する対象とする。

### ① 編集判断（Editorial Decision）
30秒で日本全体の動きを把握し、5分以内に今日書く記事を決められること。

### ② 編集進捗（Editorial Progress）
今日の記事・Premium・Instagram・Threadsの進捗を一画面で確認できること。

### ③ パイプライン監視（Pipeline Monitoring）
各カテゴリが0件の場合、それを「今日は平和」ではなく「その情報パイプラインが正常に動作しているか確認が必要」という運営上のシグナルとして扱うこと。

---

## 3. 成功の定義

Mission ControlはUIが完成すれば成功するものではない。**編集長が1週間実際に使ったあとに「Researchページをほとんど開かなくなった」と言える状態が成功である。** 逆に、Mission Controlを見たあとに毎回Researchや各DBを個別に開き直しているなら、Mission Controlに必要な情報が不足している、または裏側のパイプラインが機能していないことを意味する。

**情報を増やすことと、判断を速くすることが競合した場合は、常に判断速度を優先し、情報を減らす。**

---

## 4. 3段階フロー

| 段階 | 所要時間 | 内容 |
|---|---|---|
| **Phase 1 — 脈拍チェック** | 30秒 | 6カテゴリを数字だけで一覧。中身は読まず「今日は何件動きがあるか」だけ把握する |
| **Phase 2 — 判断** | 5分 | 0件ではないカテゴリの中身を読み、今日書くものを1つ選ぶ |
| **Phase 3 — 執筆** | — | 選んだ項目から直接Article Brief（Research）へ遷移し、そのまま執筆を開始する |

Phase 2で0件のカテゴリを隠さないことが§2③（パイプライン監視）の実装そのものである——「書く」ボタンの代わりに「要確認」を表示し、何が止まっているかを示す。

---

## 5. 6カテゴリと既存データの対応

新規データベース・新規プロパティは作らず、既存資産の再利用を優先する（本プロジェクトのNo New Databaseの原則どおり）。

| カテゴリ | 内容例 | 対応する既存データ |
|---|---|---|
| **NEW TODAY** | 法改正・制度変更・交通新情報・行政サービス変更 | 既存**Law Update**（更新キュー）＋**Source Monitor**（変更検知）。`Update Status=Confirmed`は「確定」、`Monitoring`は「先取り」として区別表示する |
| **EVENT** | 花火大会・祭り・フードフェス・蚤の市・スポーツイベント | 既存**Event Calendar.Type**（祭り／花火大会／フードフェス／蚤の市／マルシェ...）とほぼ完全一致 |
| **LIFE** | 小学校入学・保育園・健康保険・税金・住まい | 既存**Articles.Life Topics**（22値：住居・引っ越し／医療・健康／税金／子育て／教育...）＋**Research**（Status=New、Category=生活情報）候補 |
| **TRANSPORT** | 電車・Suica・Visaタッチ・新幹線・空港 | 既存Life Topics「交通」の範囲内。**細分化するかは未決定**（§8参照） |
| **MANNERS** | 女性専用車両・ゴミ分別・喫煙所・ポイ捨て・温泉 | 既存**Articles.Category**「日本文化」または Life Topics「文化・マナー」＋**Research**（Category=日本文化）候補 |
| **TREND** | 人気店・新店舗・ベジタリアン対応・外国人に人気のスポット | 既存**Articles.Category**「トレンド」＋**Research**（Category=トレンド）候補 |

**重要な設計上の注意**：既存Articles（公開済み記事）のLife Topics/Category件数は「何が既にカバーされているか」を示すものであり、「次に何を書くべきか」の候補にはならない。「次に書くべきもの」の実データソースは**Research（Status=New、未変換）**であり、ResearchにはLife Topicsが存在しないため、Category（7値）でのみ分類できる。§8「実データ検証で判明した現状」を参照。

---

## 6. 編集進捗（Editorial Progress）セクション

既存データの件数をそのまま数えるだけで、新しい集計ロジックは追加しない：

- **今日の記事**：既存の「🚀 公開待ちコンテンツ」（Articles Ready to Publish）
- **Premium**：Content Type=Premiumの記事のうち、公開待ちのもの
- **Instagram／Threads**：既存SNS QueueのStatus=Draft、Platform別件数

---

## 7. パイプライン監視（0件の扱い）

各カテゴリが0件の場合、Phase 1では警告色（⚠）で表示し、Phase 2では該当カテゴリを消さずに残し、「書く」ボタンの代わりに「要確認」と、何を確認すべきか（例：「Event Calendarに実データなし」「Research候補なし（トレンドカテゴリ未生成）」）を具体的に表示する。

これにより、Mission Controlは「今日書くものを決める画面」であると同時に、**編集部を支える6本の情報パイプラインが実際に機能しているかを毎日測る健康診断**として機能する。

---

## 8. 実データ検証で判明した現状（2026-07-19時点のスナップショット）

設計確定にあたり、実データで検証した結果、6カテゴリのうち複数が現時点で実質的に空であることが判明した。**これはMission Controlの設計上の欠陥ではなく、その手前にある情報収集パイプライン側の課題である**。今後実装を進める際は、この現状を踏まえたうえで着手すること。

| カテゴリ | 検証結果 |
|---|---|
| NEW TODAY | Law Update実レコード0件（既存5件は全て【テスト】でArchived。Law Update Pipelineが本番で稼働した実績なし） |
| EVENT | Event Calendar実レコード0件（既存1件も【テスト】） |
| LIFE | Research Status=New・Category=生活情報：4件（実データあり） |
| TRANSPORT | Research側に該当候補0件（Categoryに「交通」という値自体が存在しない） |
| MANNERS | Research Status=New・Category=日本文化：0件 |
| TREND | Research Status=New・Category=トレンド：0件 |
| （参考）法律・制度 | Research Status=New：14件（最も候補が厚い） |

このスナップショットは今後の実装判断の基準日として記録するものであり、日々更新される実際の状態を表すものではない。実装時は必ず最新のNotion実データで再確認すること。

---

## 9. 既存システムとの関係

- **Article Brief（Research）**：Mission ControlのPhase 3（執筆）の遷移先。Mission Controlが「決める」画面、Article Briefが「書く」画面という役割分担——Mission Control自体に執筆機能は持たせない
- **既存Dashboard 3ゾーン構成**（[Studio-v4.2-Editor-First-Guide.md](./Studio-v4.2-Editor-First-Guide.md)）：Zone 1「✍️ 今すぐ書く」の役割をMission Controlが吸収・強化する形になる想定。既存Zone 2「📋 今日の判断」の3数字（🔴Critical／🚀公開判断待ち／🔧更新が必要）は本書§6「編集進捗」と重複する可能性があり、実装時に統合を検討する
- **Law Update Pipeline**（`law_update_pipeline.py`）・**Editorial Planner**・**Coverage Analyzer**：Mission ControlのNEW TODAY／LIFE／MANNERS／TREND候補を実際に生成する裏側の仕組み。これらが法律・制度／生活情報以外のCategoryでも新規Research候補を作れているかは、本書§8の課題に直結する

---

## 10. 未決定事項（今後の設計判断が必要な点）

- **TRANSPORTの細分化**：Life Topics「交通」を新しい選択肢へ分割するか、既存のまま運用するかは未決定。5分判断に効くかどうかを実運用で確認してから判断する
- **6カテゴリすべてで候補を生成する仕組み**：§8の空欄カテゴリを埋めるために、Editorial Planner／Coverage Analyzerを法律・制度／生活情報以外のCategoryへ拡張する必要があるか、それとも新しい発見の仕組みが必要かは未検討
- **既存Dashboard Zone 1/2との統合方法**：Mission Controlを新設するのか、既存Zone構成を作り替えるのかは、実装ロードマップ提案時に判断する

---

*ARu HQ / Decode Japan — Mission Control Architecture v1.0 — 2026-07-19*
