<title>在住外国人向け地域イベント情報 継続収集の仕組み ― 現状監査・設計</title>

# 在住外国人向け地域イベント情報 継続収集の仕組み
### 現状監査・設計（2026-07-20）

| | |
|---|---|
| **Status** | 監査・設計完了。実装は未着手 |
| **位置づけ** | [Mission-Control-Architecture.md](./Mission-Control-Architecture.md)・[Article-Brief-Specification-v1.0.md](./Article-Brief-Specification-v1.0.md)と同じ位置付けの設計文書 |
| **目的** | 観光情報の収集ではなく、外国人が地域の日常・人とのつながりを楽しめる情報（餅つき、盆踊り、公民館・図書館・商店街の催し、国際交流会、地域スポーツ、ボランティア、防災訓練、蚤の市、収穫体験、文化体験等）を継続的にARuアプリへ提供する仕組み |
| **範囲** | 現状監査・設計のみ。新規DB・プロパティ追加、自動化実装、Notion変更、本番データ書き込み、Gitコミット・pushは行っていない |

---

## 1. 現在すでにできること

実データ・実コードを確認した結果、**構造としては驚くほど揃っている**ことが分かった。

| 既存資産 | 現状の能力 |
|---|---|
| **Source Library**（既存DB） | Source Name/URL/Category/Region/Source Type/Importance/Check Frequency等を持つ、信頼できる情報源の台帳。`Source Type`には既に「商店街」「地域メディア」「コミュニティ」「自治体」という選択肢が存在する（未使用のまま） |
| **`source_watcher.py`** | **実際に動く変更検知エンジン**。任意のURLを取得し、テキストをsimhashでフィンガープリント化、前回との差分で「変化あり」を検出。robots.txt順守。`Update Classification`には既に「Event Update」「Festival Schedule」という値が用意されている——今回のテーマを見越して設計されていたが、実データで一度も稼働していない |
| **Source Monitor**（既存DB） | 変更検知結果を記録するDB。Change Detected／Impact Level／Diff Summary／Update Classification等、揃っている |
| **`sync_source_monitor_to_research.py`** | Source Monitorで変化検知→Researchへ自動起票する既存ブリッジ |
| **Event Calendar**（既存DB、33プロパティ） | Type／Event Date／Location／Repeat Schedule／Rain Policy／Family Friendly／Accessibility／Reservation Required／Recommended Audience／Related Source Library／Related Article など、イベント情報として必要な項目がほぼ揃っている |
| **Experience Intelligence**（既存DB、44プロパティ） | Opportunity Window Start/End／Days Until Opportunity Expires（自動計算）／Intelligence Type=Event／Trend Signal Strength等、「今が旬か」「いつまでに使うべきか」を扱う設計が既にある |
| **Research → Article Brief**（既存パイプライン） | Reader Need／Claim／Evidence／Grounding Check／Brief完成条件の仕組みは、社会保険記事に限らずイベント記事にもそのまま使える |
| **Research↔Event Calendar** | `Related to Event Calendar (Linked Research)`という既存リレーションが両DB間に既に存在する |
| **Dashboard** | Event Calendarの折りたたみセクションが既に存在する（ただし目立たない位置） |

## 2. 不足していること

| 項目 | 現状 |
|---|---|
| 地域・コミュニティ単位のSource登録 | Source Library実データ17件はすべて中央省庁（政府）。商店街・自治体・公民館・地域メディア・コミュニティ由来のSourceは**1件も登録されていない** |
| SNSからの候補発見 | `source_watcher.py`は通常のWebページ取得のみ。Instagram/X等のSNS投稿を取得する仕組みは**存在しない** |
| Dashboardでの可視性 | Event Calendarは「📅 その他の外部監視」という折りたたみに埋もれており、独立したセクションになっていない |
| Event Calendar.Typeのカバー範囲 | 祭り・花火大会・フードフェス・蚤の市・マルシェ・文化イベント・自治体イベント等は対応できるが、「国際交流会」「ボランティア」「防災訓練」「いちご狩り等の収穫体験」に直接対応する値がない |
| Source Monitor→Event Calendarの自動反映 | 既存ブリッジ（`sync_source_monitor_to_research.py`）はResearchへの起票のみ。Event Calendarレコードの自動更新・中止フラグ付けは存在しない |
| 期限切れ検知 | `article_freshness_monitor.py`と同型の仕組みがEvent Calendar向けには存在しない（Event Dateを見て過去日付を検知する処理がない） |
| Reiへの通知 | メール・Slack・LINE等、Notion外への通知チャネルは本リポジトリのどこにも存在しない |

## 3. 既存DBだけで対応できる範囲

**設計上の骨格はSource Library→Source Monitor→Event Calendar→Research（Article Brief）→Articles/Dashboardという既存5点セットだけで組める。** 新規DBは不要という見立てで問題ない。Experience Intelligenceも「これは今読者に刺さるトレンドか」を判断する既存の場として転用できる。

## 4. 追加が本当に必要な項目（将来フェーズ向け、今回は実装しない）

以下だけが、既存資産の組み合わせでは埋まらない、真に新しい要素：

1. **SNSからの候補発見の仕組み**（新規自動化。ただし取得した投稿はEvent Calendar.Status=Planningの「未確認候補」としてのみ扱い、Reported Evidenceと同じ「単独では確定情報にしない」設計にする）
2. **Reiへの通知チャネル**（現状皆無。まずはDashboard強化で代替できないか5節で検討）
3. **Event Calendar.Typeの追加選択肢**（国際交流会／ボランティア／防災訓練／収穫体験など。既存プロパティへの選択肢追加のみで、新規プロパティではない）
4. **Event Date経過検知スクリプト**（`article_freshness_monitor.py`と同型の小規模スクリプト）

## 5. 情報収集から公開候補までの流れ（設計案）

```
Source Library に地域Sourceを登録
（商店街振興組合／自治体公式サイト／公民館／観光協会／地域メディア等）
        │
        ▼
source_watcher.py が既存の仕組みで定期チェック（Check Frequency）
        │  （SNS由来の候補は将来フェーズで別ルートから合流）
        ▼
変化検知 → Source Monitor レコード作成
（Update Classification = Event Update / Festival Schedule）
        │
        ▼
Event Calendar レコードを作成・更新
  ・公式Source（自治体・主催者・会場）で確認できた情報 → Status = Confirmed
  ・SNSのみで確認できた情報 → Status = Planning（未確認候補のまま）
        │
        ▼
Dashboard（強化後）で編集者が一覧を確認
        │
        ▼
記事化する価値がある場合のみ → Research（Article Brief）へ
   Reader Need／Claim／Evidence／Grounding Checkは既存の仕組みをそのまま使う
        │
        ▼
Article → 既存の編集フロー（レビュー・翻訳・SNS・公開）
```

## 6. 変更・中止・終了・期限切れの検知方法

- **変更・中止の検知**：`source_watcher.py`の既存フィンガープリント機構をそのまま使う。イベントページの日付変更・中止告知はテキスト変化として検出され、Source Monitorに新規レコードが立つ。Event Calendar.Statusには既に`Cancelled`という値がある——Source Monitor側の変化を見て、この値へ更新する運用ルールを決めればよい（自動化は将来フェーズ）
- **終了・期限切れ**：Event Calendar.Event Dateは既存フィールド。`article_freshness_monitor.py`と同じ設計思想（基準日との比較）で、過去日付になったPlanning/Confirmedレコードを検知する小さな新規スクリプトが必要（④参照）

## 7. Reiへの通知方法

現状、Notion外への通知手段は本リポジトリに一切存在しない。ゼロから通知チャネル（メール・Slack・LINE等）を作るのは新規統合コストが大きい。

**代替案（既存活用優先）**：Reiは既にMission Control設計（[Mission-Control-Architecture.md](./Mission-Control-Architecture.md)）の前提として、毎朝Dashboardを開く習慣を確立している。したがって最小構成では、**新しい通知チャネルを作らず、Dashboardの「📅 その他の外部監視」を独立した目立つセクションへ格上げする**（Mission ControlのEVENT枠と同じ役割）ことで代替できる可能性が高い。外部通知が本当に必要かどうかは、この代替案で実際に運用してから判断することを推奨する。

## 8. 外国人が安心して参加するために必要な項目

確認したところ、**Event Calendarの既存プロパティは、この観点をかなりよくカバーしている**：

| 既存プロパティ | 対応する安心材料 |
|---|---|
| `Accessibility`（車椅子対応／ベビーカー可／多言語対応あり／高齢者配慮） | アクセシビリティ |
| `Family Friendly` | 家族連れの参加可否 |
| `Reservation Required` | 予約要否 |
| `Rain Policy` | 荒天時の扱い |
| `Recommended Audience` | 誰向けか |

**不足しているのは1点**：読者から見て「これは確定情報か、まだ未確認の候補か」が分かる仕組み。5節の設計案通り、Event Calendar.Status（Planning=候補／Confirmed=確認済み）をそのまま「確認状況」の表示に使う（Article Brief仕様のSource Confidenceと同じ考え方の転用）。

## 9. 最小構成で試験運用を始める方法

新規DB・プロパティ追加なしで、以下の手順で試験できる：

1. 試験地域を1つ選び、その地域の公式Source（自治体公式サイト、公民館、観光協会、商店街振興組合等）を3〜5件、既存Source Libraryへ手動登録する（Source Type=自治体／商店街／地域メディア等、既存の選択肢を使う）
2. 既存の`source_watcher.py`を、その3〜5件だけを対象に手動実行する（コード変更なし）
3. 変化検知されたSource Monitorレコードを編集者が目視確認し、該当すればEvent Calendarレコードを手動作成する（公式Sourceで確認できたものはStatus=Confirmed、未確認はPlanning）
4. Dashboardの既存Event Calendarセクション（今は埋もれている）で一覧を確認する
5. この最小ループが実運用で機能するか（本当に地域イベントが拾えるか、Confirmed/Planningの区別が編集判断に役立つか）を確認してから、SNS取得・通知チャネル・Dashboard強化などの投資判断に進む

SNS取得も通知チャネルもこの段階では組み込まない。

## 10. 最初の試験地域と情報源の登録案（確定：神奈川県大和市、南林間・中央林間を含む）

試験地域を神奈川県大和市に確定し、実在する一次情報・公式情報源を10件調査した。詳細は別紙 [Regional-Event-Discovery-Yamato-Sources-2026-07-20.md](./Regional-Event-Discovery-Yamato-Sources-2026-07-20.md) を参照。**推薦する最初の監視対象5件**：①大和市国際化協会 ②大和市市民交流拠点ポラリス（中央林間） ③大和市立中央林間図書館 ④大和市公式イベントカレンダー ⑤大和市文化創造拠点シリウス生涯学習センター。

---

*ARu HQ / Decode Japan — Regional Event Discovery Audit — 2026-07-20*
