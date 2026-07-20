<title>全国情報収集 登録台帳（本番Notion実データ照合済み）</title>

# 全国情報収集 登録台帳
### 本番Notion APIへの直接読み取りクエリで確認した実データ（2026-07-20 作成、Notion書き込みは一切行っていない）

> **97はNotionページ総数であり、イベント数ではない。** 情報源（Source Library）・イベント（Event Calendar）・施設/トレンド等（Experience Intelligence）・未整理の発見情報（Source Monitor）を合算した、4DB横断のページ総数。「イベント件数」として引用しないこと。Reiの2026-07-20付指示により、33件・47件・65件は今後の集計基準としない。

| | |
|---|---|
| **確認方法** | `notion-build/notion_api.py`（既存の読み取り専用クライアント）で本番4DBを直接クエリ。ドキュメントやチャット履歴の記載ではなく、Notion側のpage created_time/プロパティ値を正とした |
| **重要な訂正** | 過去のやり取り・設計文書で言及された「33件」「47件」「65件」「Source Library 28件」は、いずれも実際にNotionへ書き込まれた件数と一致しない。実際の新規登録は下記の**97件**（4DB合計） |
| **書き込み・生成の状況** | 今回のセッションでは新規Notion書き込み・新規プロパティ追加・記事生成・公開は一切行っていない（読み取りのみ） |

---

## 1. 件数の正しい内訳（本番Notion実データ）

今回の「全国情報収集」バッチは、Notion上のタイムスタンプで **2026-07-19T18:31:00Z 〜 18:53:00Z**（日本時間 2026-07-20 03:31〜03:53）の一括登録として確認できる。

| 保存先DB | このバッチでの新規件数 | DB内の既存件数（バッチ以前） | DB総件数（現在） |
|---|---|---|---|
| Source Library | **38** | 23（テスト1、法律更新系ソース9、社会保険Article Brief用ソース8、大和市パイロット5） | 61 |
| Event Calendar | **26** | 1（テストレコード） | 27 |
| Experience Intelligence | **17** | 2（テストレコード） | 19 |
| Source Monitor | **16** | 2（テストレコード） | 18 |
| **合計（このバッチ）** | **97** | — | — |

**「33件」の出所は本セッションでは特定できない。** 引き継ぎプロンプートに貼り付けられているはずの「前回セッションの最後の完了・停止報告」はプレースホルダーのまま（実際のテキストが貼られていない）だったため、33という数字の根拠を確認できていない。また `docs/ARu-Studio-Handoff-2026-07-20.md` はリポジトリ内に存在せず、まだ作成されていない。

---

## 2. Source Library — 新規38件

| タイトル | Status | Source URL | ページID |
|---|---|---|---|
| 食べログ ハビービ講道館レストラン | Active | https://tabelog.com/tokyo/A1310/A131003/13302760/dtlrvwlst/B523817553/ | 3a2157f0-f15d-81a3-957c-e4583916c65a |
| SHOPCOUNTER MAGAZINE 南関東編 | Active | https://shopcounter.jp/magazine/area-guide/new-commercial-facilities-in-south-kanto | 3a2157f0-f15d-819e-b1d4-eb560b8d0bb5 |
| SHOPCOUNTER MAGAZINE 東京編 | Active | https://shopcounter.jp/magazine/area-guide/new-commercial-facilities-in-tokyo | 3a2157f0-f15d-818a-913c-c1651dafc336 |
| じゃらんnet 東北果物狩りランキング | Active | https://www.jalan.net/kankou/pro_002/g1_A8/ | 3a2157f0-f15d-814a-9a96-d8432d76449b |
| いこーよ 福島県収穫体験ガイド | Active | https://iko-yo.net/facilities?genre_ids%5B%5D=14&prefecture_ids%5B%5D=7 | 3a2157f0-f15d-81bd-bf46-fe36a8bdf811 |
| せんだい農業園芸センター みどりの杜 | Active | https://stbl-fruit-farm.jp/arai/harvest/ | 3a2157f0-f15d-81f9-8630-ca8eb5d21b3c |
| 仙台市新田東総合運動場 元気フィールド仙台 | Active | https://www.spf-sendai.jp/genki/program/ | 3a2157f0-f15d-81ca-b9c1-ff1dc650bca5 |
| Hokkaido A4JP ヴィーガンガイド | Active | https://hokkaido.a4jp.com/category/jp-vegan/ | 3a2157f0-f15d-8184-8add-f8253e09d468 |
| Vegewel 札幌ベジタリアン・ヴィーガンガイド | Active | https://vegewel.com/ja/style/sapporo/ | 3a2157f0-f15d-8199-9b45-e951f6a2adab |
| イオン北海道 公式ニュースリリース | Active | https://www.aeon-hokkaido.jp/corporation/news/ | 3a2157f0-f15d-8103-a256-d3f929550f63 |
| 令和ジャパン 北海道新店情報 | Active | https://reiwajpn.net/archives/12416 | 3a2157f0-f15d-8174-bb6a-dd2b54ce1da3 |
| 札幌開店閉店インフォ（さっぽろ速報） | Active | https://sapporo-sokuho.com/archives/category/開店・閉店 | 3a2157f0-f15d-8106-adf1-e6b1e1f30d03 |
| 四国中央市スポーツ協会 | Active | http://sports.shikokuchuo.or.jp/ | 3a2157f0-f15d-81c8-8c45-e83f197a3945 |
| aumo 中国地方おすすめスポットガイド | Active | https://aumo.jp/regions/7/scenes/15 | 3a2157f0-f15d-817d-8e66-e9ec4a29ab46 |
| 大阪・関西万博 公式サイト（ポップアップストア情報） | Active | https://www.expo2025.or.jp/news/news-20260702-01/ | 3a2157f0-f15d-8146-8e04-c0d4e8f58932 |
| LUCUA osaka 公式ポップアップ情報 | Active | https://www.lucua.jp/topics_category/popup/ | 3a2157f0-f15d-810a-864b-e0c7fc7229f3 |
| ニュースサイト anna-media（キャラクター系ポップアップ情報） | Active | https://anna-media.jp/archives/1187557 | 3a2157f0-f15d-8174-ac22-fc3da3a2ecd9 |
| 愛知県国際交流協会(AIA) | Active | https://www2.aia.pref.aichi.jp/ | 3a2157f0-f15d-8131-90b8-da58291e6d5f |
| 体験農園みとか | Active | https://mitoca-gifu.com/ | 3a2157f0-f15d-81fd-b2f5-ca798fc85837 |
| 中込農園 | Active | https://nakagominouen.com/ | 3a2157f0-f15d-8110-98d0-fad7b4d084b6 |
| MOSHI MOSHI BOX 原宿観光案内所 | Active | https://www.japanpromotion.org/en/project/moshimoshi-box | 3a2157f0-f15d-81c4-a764-ec2645f7efef |
| つるぎ町 公式サイト | Active | https://www.town.tokushima-tsurugi.lg.jp/docs/3394.html | 3a2157f0-f15d-81cc-ac00-e987bca079ee |
| 福岡県国際交流センター | Active | https://fief.or.jp/ | 3a2157f0-f15d-81fc-b313-e26b5195c42a |
| JICA沖縄 おきなわ国際協力・交流フェスティバル | Active | https://www.jica.go.jp/domestic/okinawa/activities/kaihatsu/festival/index.html | 3a2157f0-f15d-8153-b58b-c1e02a7116a0 |
| ホテル日航アリビラ 公式サイト | Active | https://www.alivila.co.jp/topics/15470/ | 3a2157f0-f15d-819d-ab53-e3ffe06148b7 |
| ハラールグルメジャパン 沖縄県ガイド | Active | https://www.halalgourmet.jp/ja/prefectures/okinawa | 3a2157f0-f15d-815b-955f-cc6e6c68618d |
| クロスロードふくおか ベジタリアン・ムスリムガイド | Active | https://www.crossroadfukuoka.jp/feature/vegetarian-muslim | 3a2157f0-f15d-8105-b3d2-d17b40cdfea6 |
| 阿波友禅工場（藍染工芸館） | Active | https://www.awaai.jp/ | 3a2157f0-f15d-81e9-9aed-da3caf200ac0 |
| アイハウス多文化交流プラットフォーム（大阪国際交流センター） | Active | https://osaka-ihouse.net/ | 3a2157f0-f15d-8130-9d79-f5c682c2e034 |
| 仙台 一番町四丁目商店街 | Active | http://www.ban-bura.com/ | 3a2157f0-f15d-81c6-882f-c58049a0c4fd |
| 秋田県国際交流協会(AIA秋田) | Active | https://www.aiahome.or.jp/ | 3a2157f0-f15d-81b0-a3d0-f4c8709e48d1 |
| 広島平和文化センター 国際市民交流課 | Active | https://h-ircd.jp/ | 3a2157f0-f15d-81b1-bed2-f75eaa6647af |
| 仙台市公式イベントカレンダー | Active | https://www.city.sendai.jp/cgi-bin/event_cal_multi/calendar.cgi | 3a2157f0-f15d-8177-b999-df7b20585946 |
| 北海道国際交流・協力総合センター(HIECC) | Active | https://www.hiecc.or.jp/ | 3a2157f0-f15d-81ee-9836-da662cc96385 |
| ぐうたび北海道（さっぽろ夏まつり特集） | Active | https://www.gutabi.jp/event/detail/1544 | 3a2157f0-f15d-8134-95da-ec90fb2ea3f6 |
| 日本文化体験 庵an東京 | Active | https://tokyo.nipponbunkan.com/ | 3a2157f0-f15d-8181-9c5f-f69dfa8fe444 |
| 那覇市国際通り商店街 | Active | https://naha-kokusaidori.okinawa/en/ | 3a2157f0-f15d-81dd-9f44-ebbcfc4ed8f2 |
| 徳島県国際交流協会(TOPIA) | Active | https://www.topia.ne.jp/ | 3a2157f0-f15d-81f7-b099-d07c939d17a8 |

## 3. Event Calendar — 新規26件

| タイトル | Status | ページID |
|---|---|---|
| せんだい農業園芸センター みどりの杜 ブルーベリー狩り | Completed | 3a2157f0-f15d-8122-bb68-da0ba6d05ef2 |
| 元気フィールド仙台 スポーツプログラム | Planning | 3a2157f0-f15d-8117-a46a-f826b2ba6cc7 |
| 四国中央市スポーツ協会 チャレンジ水泳教室 | Planning | 3a2157f0-f15d-8184-a6fe-cb03e47069e8 |
| 四国中央市スポーツ協会 初心者テニスサークル | Planning | 3a2157f0-f15d-8166-b10b-dea6c6483684 |
| EXPO2025オフィシャルポップアップストア 京都髙島屋店 | Confirmed | 3a2157f0-f15d-81a5-b9d0-f655b38cc99c |
| 劇場版「チェンソーマン レゼ篇」ポップアップストア | Planning | 3a2157f0-f15d-8104-80f4-ea9b70e069bf |
| 「きんいろモザイク」ポップアップストア（コトブキヤ大阪日本橋） | Planning | 3a2157f0-f15d-81f6-a8b1-fe3ca302f0c6 |
| 「オールドベティーズ」ポップアップショップ（LUCUA osaka） | Completed | 3a2157f0-f15d-819a-ab55-c790faff1be9 |
| 「ポケピース」ポップアップストア | Completed | 3a2157f0-f15d-815b-97e7-f56f7b943a62 |
| 体験農園みとか ぶどう狩り | Planning | 3a2157f0-f15d-81cb-af39-eee73f15e8a0 |
| 中込農園 黒系ぶどう狩り | Planning | 3a2157f0-f15d-81d0-8b9c-de5c489ba99c |
| つるぎ町夏まつり 阿波踊り大会 | Planning | 3a2157f0-f15d-81f5-acb6-e17970eaff9f |
| 福岡県国際交流センター 多文化共生ひろばカフェ | Completed | 3a2157f0-f15d-8161-97de-e9319e9d1add |
| アイハウス大阪「七絃琴の夕へ」 | Planning | 3a2157f0-f15d-811d-b4f7-deebe1e62df7 |
| 写真展「歴史や文化から学ぶ平和」 | Completed | 3a2157f0-f15d-8122-af58-e90a20502565 |
| 愛知県国際交流協会 日本語ボランティア入門講座 | Completed | 3a2157f0-f15d-815c-a328-cdb6b7224744 |
| 仙台市商店街イベント（Bang BAR SENDAI） | Completed | 3a2157f0-f15d-81cc-a013-c2a3d7d880bc |
| やさしい日本語キャラバン in みたね | Planning | 3a2157f0-f15d-819f-b3f0-f29750b65ac0 |
| 夏の特別版インターナショナルデイ（中高生対象） | Planning | 3a2157f0-f15d-81c6-8cbd-c32e1dc205cd |
| 夏の特別版インターナショナルデイ（小学生対象） | Completed | 3a2157f0-f15d-8186-86f7-ffcff593ce7f |
| Have a Chat!（アメリカ） | Planning | 3a2157f0-f15d-810a-8789-e554933f55aa |
| モントリオールの日 | Completed | 3a2157f0-f15d-8144-bf9b-c805b29f9c92 |
| 広島平和文化センター「やさしい日本語」連続講座 | Completed | 3a2157f0-f15d-81bb-bc8d-e89279d9424e |
| 中込農園 シャインマスカット狩り | Planning | 3a2157f0-f15d-81df-b4da-da87658cb9a9 |
| 沖縄国際文化祭 | Completed | 3a2157f0-f15d-8128-8021-fd8d260103af |
| 年金セミナー（徳島） | Completed | 3a2157f0-f15d-8134-80da-f2a6121e38e3 |

*Source URLプロパティは全て空欄（未設定）——このバッチではEvent Calendar側にSource URLを入力しなかった模様。*

## 4. Experience Intelligence — 新規17件

| タイトル | Status | ページID |
|---|---|---|
| ニュウマン高輪「ミムレ」小川珈琲新業態 | New | 3a2157f0-f15d-8101-9768-c6265b5b1595 |
| 六本木ヒルズ 2026年春リニューアル「RAWROW（ローロー）」 | New | 3a2157f0-f15d-81df-ade1-cb147a730a54 |
| あんざい果樹園（福島市） | New | 3a2157f0-f15d-813f-b5b3-eaff2009a24a |
| 福の樹（ハラール対応ラーメン） | New | 3a2157f0-f15d-8172-a84d-dda24c300a5f |
| すべてヴィーガン（札幌市中央区） | New | 3a2157f0-f15d-81da-8fec-f362f910be14 |
| マックスバリュ共和店 リニューアルオープン | New | 3a2157f0-f15d-8153-af5f-ef451246710a |
| イオン北海道「ザ・ビッグ厚別店」 | New | 3a2157f0-f15d-81f2-93a6-ebf1c75bf42b |
| Marley ROASTER（札幌市中央区） | New | 3a2157f0-f15d-811b-88b9-e431887ade14 |
| SNOW MILK（札幌市白石区） | New | 3a2157f0-f15d-81da-a31b-e6c5dc84f4ee |
| とりやき酒場 鶏ん家 札幌麻生店 | New | 3a2157f0-f15d-81e7-a1fd-d1ba2c3f67f7 |
| 尾道「U2」（サイクリスト向け複合施設） | New | 3a2157f0-f15d-817b-a495-d78847f1d469 |
| 体験農園みとか | New | 3a2157f0-f15d-811b-87df-ef2606d43212 |
| 中込農園 | New | 3a2157f0-f15d-81ba-8716-d04f68d6bd66 |
| ハビービ 講道館レストラン | New | 3a2157f0-f15d-81c7-836a-d35a7707dad9 |
| ホテル日航アリビラ ヴィーガン会席 | New | 3a2157f0-f15d-818d-8384-deb9021581f2 |
| 阿波友禅工場 藍染体験 | New | 3a2157f0-f15d-81f2-93cb-ddf6ee25f779 |
| 庵an東京（和菓子作り体験） | New | 3a2157f0-f15d-8135-be43-f2311684b1c3 |

*Source URLプロパティは全て空欄——Experience Intelligence側でも同様に未設定。*

## 5. Source Monitor — 新規16件

| タイトル | Status | ページID |
|---|---|---|
| 山元いちご農園 発見 2026-07-20 | Check Required | 3a2157f0-f15d-8116-a622-d27af000e10e |
| 愛知県国際交流協会 ワールド・コラボ・フェスタ2026（ブース募集） 発見 2026-07-20 | Check Required | 3a2157f0-f15d-810a-ac26-db12b6b41c94 |
| おきなわ国際協力・交流フェスティバル 発見 2026-07-20 | Check Required | 3a2157f0-f15d-8173-84e5-e685eea8f37f |
| 対話型オリエンテーション 発見 2026-07-20 | Check Required | 3a2157f0-f15d-815a-989e-eb82e84c8ba0 |
| インド舞踊とインド音楽の鑑賞 発見 2026-07-20 | Check Required | 3a2157f0-f15d-812b-96af-d9fa85839bbe |
| 2026年度 外国人による徳島県日本語弁論大会 発見 2026-07-20 | Check Required | 3a2157f0-f15d-8156-95e5-d17beaf10c4d |
| 夏休み子ども日本語教室2026 発見 2026-07-20 | Check Required | 3a2157f0-f15d-81dc-8cf3-efd6c8a1c4f6 |
| 外国人市民向け防災研修（ミニ防災ツアー） 発見 2026-07-20 | Check Required | 3a2157f0-f15d-816d-ada2-d0a10c2f28be |
| 日本語ボランティア養成講座（広島） 発見 2026-07-20 | Check Required | 3a2157f0-f15d-817c-a6bd-d16d0bdbb65f |
| 令和8年度 地域の外国人相談研修会 発見 2026-07-20 | Check Required | 3a2157f0-f15d-81a1-8a08-f9589488c053 |
| 愛知県国際交流協会 スキルアップ講座in豊川市 発見 2026-07-20 | Check Required | 3a2157f0-f15d-81e1-84d5-dd6f4fe854f1 |
| 愛知県国際交流協会 スキルアップ講座in津島市 発見 2026-07-20 | Check Required | 3a2157f0-f15d-81d6-98af-f904b4a6ccb7 |
| 仙台市イベントカレンダー掲載イベント（複数） 発見 2026-07-20 | Check Required | 3a2157f0-f15d-81a7-b88a-f41db322a052 |
| 2026済州国際青少年フォーラム 発見 2026-07-20 | Check Required | 3a2157f0-f15d-81f6-8637-e52eddcf0519 |
| くしろ国際交流フェスタ2026 発見 2026-07-20 | Check Required | 3a2157f0-f15d-81b7-8736-d0502ba41516 |
| 北海盆踊り（さっぽろ夏まつり） 発見 2026-07-20 | Check Required | 3a2157f0-f15d-8173-91b7-fa47b6ff08a5 |

---

## 6. 重複チェック

- 各DB内での**タイトル重複は0件**（Source Library/Event Calendar/Experience Intelligence/Source Monitorそれぞれ、同一タイトルの二重登録なし）
- 「体験農園みとか」「中込農園」がSource Library・Experience Intelligence・Event Calendarの複数DBに登場するのは、[Nationwide-Intelligence-DryRun-Reclassified-2026-07-20.md](./Nationwide-Intelligence-DryRun-Reclassified-2026-07-20.md) 区分4で確定した「施設＝Experience Intelligence／個別開催企画＝Event Calendar／発信元＝Source Library」という**意図的な複数DB関連付け**であり、誤った重複登録ではない

## 7. 未登録として残っている項目（再分類文書との照合）

[Nationwide-Intelligence-DryRun-Reclassified-2026-07-20.md](./Nationwide-Intelligence-DryRun-Reclassified-2026-07-20.md) 区分3（Source Monitorのみ登録予定、25件）のうち、実際にSource Monitorへ登録されているのは15件。以下の**10件は本番Notionに見当たらない**——次回登録の残件候補：

| # | タイトル | 地域 | 備考 |
|---|---|---|---|
| 2 | ワッショイはこだて | 北海道 | 公式Source未特定のまま |
| 5 | 秋田竿燈まつり | 東北 | 公式Source未特定のまま |
| 12 | パルテノン大通りマルシェ | 関東 | 公式Source未特定のまま |
| 13 | 流山おおたかの森駅前広場フリマ | 関東 | 公式Source未特定のまま |
| 23 | 地蔵盆 | 関西 | 単一の公式主催者が構造的に存在しない可能性 |
| 25 | 三原やっさ祭り | 中国 | 公式Source未特定のまま |
| 26 | くか夢夏まつり大会 | 中国 | 公式Source未特定のまま |
| 27 | 秋吉台カルスト展望台周辺イベント | 中国 | ほぼ全て未確認 |
| 34 | 松山中央商店街 土曜夜市 | 四国 | 公式Source未特定のまま |
| 43 | コザ日曜夜市ナイトマーケット | 沖縄 | 公式Source未特定のまま |

*なぜ止まったかは本セッションでは特定できない（前回セッションの完了報告が引き継がれなかったため）。公式Sourceが未特定の項目を意図的に見送ったのか、単に途中で打ち切られたのかは、Reiの判断を仰ぐ。*

**上記10件のステータス（2026-07-20 Rei確認）：「未登録・Source確認待ち」。公式Sourceが特定できるまで本番登録は行わない。**

## 8. 今回の全国情報収集バッチと混同してはいけない、別系統の登録

| バッチ | Notionタイムスタンプ(UTC) | 件数 | 位置づけ |
|---|---|---|---|
| 大和市（Yamato）地域パイロット | 2026-07-19T16:25 | Source Library 5件 | [Regional-Event-Discovery-Yamato-Sources-2026-07-20.md](./Regional-Event-Discovery-Yamato-Sources-2026-07-20.md) — 全国収集とは別の地域限定パイロット |
| 社会保険Article Brief用ソース | 2026-07-19T14:30/15:43 | Source Library 8件 | Article Briefパイプライン（外国人の社会保険）用、全国情報収集と無関係 |
| 法律更新監視ソース | 2026-07-18T02:22 | Source Library 9件 | Law Update Pipeline設計時の登録、全国情報収集と無関係 |
| テストレコード | 2026-07-12 / 07-16 | 各DB1〜2件 | 【テスト】接頭辞、実データではない |

---

## 9. Source URLクリック化 dry-run（2026-07-20、Notion未反映）

**スキーマ確認結果**：新規プロパティは不要。Event Calendar／Experience Intelligence／Source Monitorとも既存の`Source URL`プロパティが`url`型で存在する（Source Libraryは既存の`URL`が`url`型）。Source Monitorの`Official URL`はrollup型で直接書き込み不可。

**対象件数**：59件（Event Calendar 26／Experience Intelligence 17／Source Monitor 16）のうち、Source URL未設定＝58件、設定済み＝1件（「オールドベティーズ」、ただし本文リンクの表示名が今回の新方式と不一致のため要更新）。59件全てがRelated Source Library（Source Monitorは「Source」）リレーション経由でURLを解決可能——URL不明レコードは0件。

各列の意味：現URL＝現在のSource URLプロパティ値／URL種別＝修正候補URLが情報元の個別ページか一覧・トップページか／現在クリック可＝プロパティ・本文とも現状の状態／修正候補URL＝Related Source LibraryのURLをそのまま使用／確認状態＝公式確認済み・第三者情報のいずれか（今回のバッチにSNS投稿由来のレコードは0件）。

### Event Calendar（26件）

| タイトル | ページID | 現URL | URL有無 | URL種別 | 現在クリック可 | 修正候補URL | 確認状態 | SLリレーション | Status | 要修正 |
|---|---|---|---|---|---|---|---|---|---|---|
| せんだい農業園芸センター みどりの杜 ブルーベリー狩り | 3a2157f0-f15d-8122-bb68-da0ba6d05ef2 | (空欄) | なし | 個別ページ | 不可（未設定） | https://stbl-fruit-farm.jp/arai/harvest/ | 公式確認済み | あり | Completed | 必要 |
| 元気フィールド仙台 スポーツプログラム | 3a2157f0-f15d-8117-a46a-f826b2ba6cc7 | (空欄) | なし | 個別ページ | 不可（未設定） | https://www.spf-sendai.jp/genki/program/ | 公式確認済み | あり | Planning | 必要 |
| 四国中央市スポーツ協会 チャレンジ水泳教室 | 3a2157f0-f15d-8184-a6fe-cb03e47069e8 | (空欄) | なし | 一覧・トップページ | 不可（未設定） | http://sports.shikokuchuo.or.jp/ | 公式確認済み | あり | Planning | 必要 |
| 四国中央市スポーツ協会 初心者テニスサークル | 3a2157f0-f15d-8166-b10b-dea6c6483684 | (空欄) | なし | 一覧・トップページ | 不可（未設定） | http://sports.shikokuchuo.or.jp/ | 公式確認済み | あり | Planning | 必要 |
| EXPO2025オフィシャルポップアップストア 京都髙島屋店 | 3a2157f0-f15d-81a5-b9d0-f655b38cc99c | (空欄) | なし | 個別ページ | 不可（未設定） | https://www.expo2025.or.jp/news/news-20260702-01/ | 公式確認済み | あり | Confirmed | 必要 |
| 劇場版「チェンソーマン レゼ篇」ポップアップストア | 3a2157f0-f15d-8104-80f4-ea9b70e069bf | (空欄) | なし | 個別ページ | 不可（未設定） | https://anna-media.jp/archives/1187557 | 第三者情報 | あり | Planning | 必要 |
| 「きんいろモザイク」ポップアップストア（コトブキヤ大阪日本橋） | 3a2157f0-f15d-81f6-a8b1-fe3ca302f0c6 | (空欄) | なし | 個別ページ | 不可（未設定） | https://anna-media.jp/archives/1187557 | 第三者情報 | あり | Planning | 必要 |
| 「オールドベティーズ」ポップアップショップ（LUCUA osaka） | 3a2157f0-f15d-819a-ab55-c790faff1be9 | https://www.lucua.jp/topics_category/popup/ | あり | 一覧ページ | 可能（既設定） | https://www.lucua.jp/topics_category/popup/ | 公式確認済み | あり | Completed | 不要（設定済み・ラベル要更新のみ） |
| 「ポケピース」ポップアップストア | 3a2157f0-f15d-815b-97e7-f56f7b943a62 | (空欄) | なし | 個別ページ | 不可（未設定） | https://anna-media.jp/archives/1187557 | 第三者情報 | あり | Completed | 必要 |
| 体験農園みとか ぶどう狩り | 3a2157f0-f15d-81cb-af39-eee73f15e8a0 | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://mitoca-gifu.com/ | 公式確認済み | あり | Planning | 必要 |
| 中込農園 黒系ぶどう狩り | 3a2157f0-f15d-81d0-8b9c-de5c489ba99c | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://nakagominouen.com/ | 公式確認済み | あり | Planning | 必要 |
| つるぎ町夏まつり 阿波踊り大会 | 3a2157f0-f15d-81f5-acb6-e17970eaff9f | (空欄) | なし | 個別ページ | 不可（未設定） | https://www.town.tokushima-tsurugi.lg.jp/docs/3394.html | 公式確認済み | あり | Planning | 必要 |
| 福岡県国際交流センター 多文化共生ひろばカフェ | 3a2157f0-f15d-8161-97de-e9319e9d1add | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://fief.or.jp/ | 公式確認済み | あり（**異常：無関係な沖縄ホテルとのリレーションが混在、下記参照**） | Completed | 必要 |
| アイハウス大阪「七絃琴の夕へ」 | 3a2157f0-f15d-811d-b4f7-deebe1e62df7 | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://osaka-ihouse.net/ | 公式確認済み | あり | Planning | 必要 |
| 写真展「歴史や文化から学ぶ平和」 | 3a2157f0-f15d-8122-af58-e90a20502565 | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://www2.aia.pref.aichi.jp/ | 公式確認済み | あり | Completed | 必要 |
| 愛知県国際交流協会 日本語ボランティア入門講座 | 3a2157f0-f15d-815c-a328-cdb6b7224744 | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://www2.aia.pref.aichi.jp/ | 公式確認済み | あり | Completed | 必要 |
| 仙台市商店街イベント（Bang BAR SENDAI） | 3a2157f0-f15d-81cc-a013-c2a3d7d880bc | (空欄) | なし | 一覧・トップページ | 不可（未設定） | http://www.ban-bura.com/ | 公式確認済み(商店街主催情報) | あり | Completed | 必要 |
| やさしい日本語キャラバン in みたね | 3a2157f0-f15d-819f-b3f0-f29750b65ac0 | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://www.aiahome.or.jp/ | 公式確認済み | あり | Planning | 必要 |
| 夏の特別版インターナショナルデイ（中高生対象） | 3a2157f0-f15d-81c6-8cbd-c32e1dc205cd | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://www.aiahome.or.jp/ | 公式確認済み | あり | Planning | 必要 |
| 夏の特別版インターナショナルデイ（小学生対象） | 3a2157f0-f15d-8186-86f7-ffcff593ce7f | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://www.aiahome.or.jp/ | 公式確認済み | あり | Completed | 必要 |
| Have a Chat!（アメリカ） | 3a2157f0-f15d-810a-8789-e554933f55aa | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://h-ircd.jp/ | 公式確認済み | あり | Planning | 必要 |
| モントリオールの日 | 3a2157f0-f15d-8144-bf9b-c805b29f9c92 | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://h-ircd.jp/ | 公式確認済み | あり | Completed | 必要 |
| 広島平和文化センター「やさしい日本語」連続講座 | 3a2157f0-f15d-81bb-bc8d-e89279d9424e | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://h-ircd.jp/ | 公式確認済み | あり | Completed | 必要 |
| 中込農園 シャインマスカット狩り | 3a2157f0-f15d-81df-b4da-da87658cb9a9 | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://nakagominouen.com/ | 公式確認済み | あり | Planning | 必要 |
| 沖縄国際文化祭 | 3a2157f0-f15d-8128-8021-fd8d260103af | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://naha-kokusaidori.okinawa/en/ | 公式確認済み | あり | Completed | 必要 |
| 年金セミナー（徳島） | 3a2157f0-f15d-8134-80da-f2a6121e38e3 | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://www.topia.ne.jp/ | 公式確認済み | あり | Completed | 必要 |

### Experience Intelligence（17件）

| タイトル | ページID | 現URL | URL有無 | URL種別 | 現在クリック可 | 修正候補URL | 確認状態 | SLリレーション | Status | 要修正 |
|---|---|---|---|---|---|---|---|---|---|---|
| ニュウマン高輪「ミムレ」小川珈琲新業態 | 3a2157f0-f15d-8101-9768-c6265b5b1595 | (空欄) | なし | 個別ページ | 不可（未設定） | https://shopcounter.jp/magazine/area-guide/new-commercial-facilities-in-south-kanto | 第三者情報 | あり | New | 必要 |
| 六本木ヒルズ 2026年春リニューアル「RAWROW（ローロー）」 | 3a2157f0-f15d-81df-ade1-cb147a730a54 | (空欄) | なし | 個別ページ | 不可（未設定） | https://shopcounter.jp/magazine/area-guide/new-commercial-facilities-in-tokyo | 第三者情報 | あり | New | 必要 |
| あんざい果樹園（福島市） | 3a2157f0-f15d-813f-b5b3-eaff2009a24a | (空欄) | なし | 一覧ページ | 不可（未設定） | https://iko-yo.net/facilities?genre_ids%5B%5D=14&prefecture_ids%5B%5D=7 | 第三者情報 | あり | New | 必要 |
| 福の樹（ハラール対応ラーメン） | 3a2157f0-f15d-8172-a84d-dda24c300a5f | (空欄) | なし | 一覧ページ | 不可（未設定） | https://hokkaido.a4jp.com/category/jp-vegan/ | 第三者情報 | あり | New | 必要 |
| すべてヴィーガン（札幌市中央区） | 3a2157f0-f15d-81da-8fec-f362f910be14 | (空欄) | なし | 一覧ページ | 不可（未設定） | https://vegewel.com/ja/style/sapporo/ | 第三者情報 | あり | New | 必要 |
| マックスバリュ共和店 リニューアルオープン | 3a2157f0-f15d-8153-af5f-ef451246710a | (空欄) | なし | 一覧ページ | 不可（未設定） | https://www.aeon-hokkaido.jp/corporation/news/ | 公式確認済み | あり | New | 必要 |
| イオン北海道「ザ・ビッグ厚別店」 | 3a2157f0-f15d-81f2-93a6-ebf1c75bf42b | (空欄) | なし | 一覧ページ | 不可（未設定） | https://www.aeon-hokkaido.jp/corporation/news/ | 公式確認済み | あり | New | 必要 |
| Marley ROASTER（札幌市中央区） | 3a2157f0-f15d-811b-88b9-e431887ade14 | (空欄) | なし | 個別ページ | 不可（未設定） | https://reiwajpn.net/archives/12416 | 第三者情報 | あり | New | 必要 |
| SNOW MILK（札幌市白石区） | 3a2157f0-f15d-81da-a31b-e6c5dc84f4ee | (空欄) | なし | 個別ページ | 不可（未設定） | https://reiwajpn.net/archives/12416 | 第三者情報 | あり | New | 必要 |
| とりやき酒場 鶏ん家 札幌麻生店 | 3a2157f0-f15d-81e7-a1fd-d1ba2c3f67f7 | (空欄) | なし | 一覧ページ | 不可（未設定） | https://sapporo-sokuho.com/archives/category/%E9%96%8B%E5%BA%97%E3%83%BB%E9%96%89%E5%BA%97 | 第三者情報 | あり | New | 必要 |
| 尾道「U2」（サイクリスト向け複合施設） | 3a2157f0-f15d-817b-a495-d78847f1d469 | (空欄) | なし | 一覧ページ | 不可（未設定） | https://aumo.jp/regions/7/scenes/15 | 第三者情報 | あり | New | 必要 |
| 体験農園みとか | 3a2157f0-f15d-811b-87df-ef2606d43212 | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://mitoca-gifu.com/ | 公式確認済み | あり | New | 必要 |
| 中込農園 | 3a2157f0-f15d-81ba-8716-d04f68d6bd66 | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://nakagominouen.com/ | 公式確認済み | あり | New | 必要 |
| ハビービ 講道館レストラン | 3a2157f0-f15d-81c7-836a-d35a7707dad9 | (空欄) | なし | 個別ページ | 不可（未設定） | https://tabelog.com/tokyo/A1310/A131003/13302760/dtlrvwlst/B523817553/ | 第三者情報 | あり | New | 必要 |
| ホテル日航アリビラ ヴィーガン会席 | 3a2157f0-f15d-818d-8384-deb9021581f2 | (空欄) | なし | 個別ページ | 不可（未設定） | https://www.alivila.co.jp/topics/15470/ | 公式確認済み | あり | New | 必要 |
| 阿波友禅工場 藍染体験 | 3a2157f0-f15d-81f2-93cb-ddf6ee25f779 | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://www.awaai.jp/ | 公式確認済み | あり | New | 必要 |
| 庵an東京（和菓子作り体験） | 3a2157f0-f15d-8135-be43-f2311684b1c3 | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://tokyo.nipponbunkan.com/ | 公式確認済み | あり | New | 必要 |

### Source Monitor（16件）

| タイトル | ページID | 現URL | URL有無 | URL種別 | 現在クリック可 | 修正候補URL | 確認状態 | SLリレーション | Status | 要修正 |
|---|---|---|---|---|---|---|---|---|---|---|
| 山元いちご農園 発見 2026-07-20 | 3a2157f0-f15d-8116-a622-d27af000e10e | (空欄) | なし | 一覧ページ | 不可（未設定） | https://www.jalan.net/kankou/pro_002/g1_A8/ | 第三者情報 | あり | Check Required | 必要 |
| 愛知県国際交流協会 ワールド・コラボ・フェスタ2026（ブース募集） 発見 2026-07-20 | 3a2157f0-f15d-810a-ac26-db12b6b41c94 | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://www2.aia.pref.aichi.jp/ | 公式確認済み | あり | Check Required | 必要 |
| おきなわ国際協力・交流フェスティバル 発見 2026-07-20 | 3a2157f0-f15d-8173-84e5-e685eea8f37f | (空欄) | なし | 個別ページ | 不可（未設定） | https://www.jica.go.jp/domestic/okinawa/activities/kaihatsu/festival/index.html | 公式確認済み | あり | Check Required | 必要 |
| 対話型オリエンテーション 発見 2026-07-20 | 3a2157f0-f15d-815a-989e-eb82e84c8ba0 | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://www.topia.ne.jp/ | 公式確認済み | あり | Check Required | 必要 |
| インド舞踊とインド音楽の鑑賞 発見 2026-07-20 | 3a2157f0-f15d-812b-96af-d9fa85839bbe | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://www.topia.ne.jp/ | 公式確認済み | あり | Check Required | 必要 |
| 2026年度 外国人による徳島県日本語弁論大会 発見 2026-07-20 | 3a2157f0-f15d-8156-95e5-d17beaf10c4d | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://www.topia.ne.jp/ | 公式確認済み | あり | Check Required | 必要 |
| 夏休み子ども日本語教室2026 発見 2026-07-20 | 3a2157f0-f15d-81dc-8cf3-efd6c8a1c4f6 | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://www.topia.ne.jp/ | 公式確認済み | あり | Check Required | 必要 |
| 外国人市民向け防災研修（ミニ防災ツアー） 発見 2026-07-20 | 3a2157f0-f15d-816d-ada2-d0a10c2f28be | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://h-ircd.jp/ | 公式確認済み | あり | Check Required | 必要 |
| 日本語ボランティア養成講座（広島） 発見 2026-07-20 | 3a2157f0-f15d-817c-a6bd-d16d0bdbb65f | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://h-ircd.jp/ | 公式確認済み | あり | Check Required | 必要 |
| 令和8年度 地域の外国人相談研修会 発見 2026-07-20 | 3a2157f0-f15d-81a1-8a08-f9589488c053 | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://www2.aia.pref.aichi.jp/ | 公式確認済み | あり | Check Required | 必要 |
| 愛知県国際交流協会 スキルアップ講座in豊川市 発見 2026-07-20 | 3a2157f0-f15d-81e1-84d5-dd6f4fe854f1 | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://www2.aia.pref.aichi.jp/ | 公式確認済み | あり | Check Required | 必要 |
| 愛知県国際交流協会 スキルアップ講座in津島市 発見 2026-07-20 | 3a2157f0-f15d-81d6-98af-f904b4a6ccb7 | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://www2.aia.pref.aichi.jp/ | 公式確認済み | あり | Check Required | 必要 |
| 仙台市イベントカレンダー掲載イベント（複数） 発見 2026-07-20 | 3a2157f0-f15d-81a7-b88a-f41db322a052 | (空欄) | なし | 一覧ページ | 不可（未設定） | https://www.city.sendai.jp/cgi-bin/event_cal_multi/calendar.cgi | 公式確認済み | あり | Check Required | 必要 |
| 2026済州国際青少年フォーラム 発見 2026-07-20 | 3a2157f0-f15d-81f6-8637-e52eddcf0519 | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://www.hiecc.or.jp/ | 公式確認済み | あり | Check Required | 必要 |
| くしろ国際交流フェスタ2026 発見 2026-07-20 | 3a2157f0-f15d-81b7-8736-d0502ba41516 | (空欄) | なし | 一覧・トップページ | 不可（未設定） | https://www.hiecc.or.jp/ | 公式確認済み | あり | Check Required | 必要 |
| 北海盆踊り（さっぽろ夏まつり） 発見 2026-07-20 | 3a2157f0-f15d-8173-91b7-fa47b6ff08a5 | (空欄) | なし | 個別ページ | 不可（未設定） | https://www.gutabi.jp/event/detail/1544 | 第三者情報 | あり | Check Required | 必要 |

### 未登録10件（Source確認待ち）は今回のURL対応の対象外

Section 7の10件はSource Monitorに未登録のため、今回のURLクリック化dry-runにも含めていない。公式Sourceが特定でき本番登録された後に、あらためて対象に含める。

### 実施前に確認が必要な2点（未回答）

1. **本文リンクの表示名**：「確認状態＝公式確認済み」の約37件は「公式情報を開く」で問題ない。しかし「確認状態＝第三者情報」の約22件（じゃらん・いこーよ・令和ジャパン・さっぽろ速報・aumo・anna-media・SHOPCOUNTER・食べログ・ハラールグルメジャパン等のまとめ/メディア/口コミサイト）は公式情報ではなく、Verification Notesにも「個別公式ページ未確認」と明記されている。これらに「公式情報を開く」と表示すると事実と異なる。今回のバッチにSNS投稿は0件のため「元の投稿を開く」も該当しない。**「情報元を開く」等の第三の表示名を許可するか、それとも別の対応方針か、指示を求める。**
2. **福岡県国際交流センター 多文化共生ひろばカフェのリレーション異常**：Related Source Libraryに無関係な「ホテル日航アリビラ 公式サイト」が混入している。Source URLの値は正しい方（fief.or.jp）を採用する想定だが、リレーション自体の修正は今回の指示に含まれていないため、**リレーションはそのまま維持し、Source URLの値だけ設定する方針で良いか確認**したい。

---

## 10. 後続作業履歴（2026-07-20 追記、上記1〜9の97件の記録は削除・再作成していません）

本ledger作成後、同日中の後続セッションで以下を実施：

- Experience Intelligenceへ共通プロパティ5件（Region／Experience Genre／Reservation Status／Language Support／Family Participation Status）とDietary Accommodation Type（1件）を追加
- 文化体験2件（庵an東京、阿波友禅工場）と食関連4件（ホテル日航アリビラ、ハビービ、福の樹、すべてヴィーガン）を確認し、確認できた値のみ設定（詳細は§11参照）
- ARu Studio Dashboardへ「ARu編集デスク｜今日の情報」セクションを追加（既存9セクション・AI Command Center・自動生成マーカーは無変更）
- ARu Studio Homeへ「🎎 日本文化体験」「🥗 食の安心・お店情報」の2callout追加
- 実装コミット：`5e1b8d6`（`notion-build/automation/editor_desk_digest.py`のみ、他8件のdocsファイルは含まず）
- アプリ公開・記事生成・全国収集は行っていない

## 11. 6件の詳細台帳（プロパティ追加対象、2026-07-20 追記）

| 項目 | 庵an東京（和菓子作り体験） | 阿波友禅工場 藍染体験 | ホテル日航アリビラ ヴィーガン会席 | ハビービ 講道館レストラン | 福の樹（ハラール対応ラーメン） | すべてヴィーガン（札幌市中央区） |
|---|---|---|---|---|---|---|
| 保存先DB | Experience Intelligence | Experience Intelligence | Experience Intelligence | Experience Intelligence | Experience Intelligence | Experience Intelligence |
| ページID | 3a2157f0-f15d-8135-be43-f2311684b1c3 | 3a2157f0-f15d-81f2-93cb-ddf6ee25f779 | 3a2157f0-f15d-818d-8384-deb9021581f2 | 3a2157f0-f15d-81c7-836a-d35a7707dad9 | 3a2157f0-f15d-8172-a84d-dda24c300a5f | 3a2157f0-f15d-81da-8fec-f362f910be14 |
| Source URL | https://tokyo.nipponbunkan.com/ | https://www.awaai.jp/ | https://www.alivila.co.jp/topics/15470/ | https://tabelog.com/tokyo/A1310/A131003/13302760/dtlrvwlst/B523817553/ | https://hokkaido.a4jp.com/category/jp-vegan/ | https://vegewel.com/ja/style/sapporo/ |
| Status | New | New | New | New | New | New |
| 登録日 | 2026-07-19T18:53Z（本番バッチ） | 2026-07-19T18:34Z（本番バッチ） | 2026-07-19T18:34Z（本番バッチ） | 2026-07-19T18:32Z（本番バッチ） | 2026-07-19T18:31Z（本番バッチ） | 2026-07-19T18:31Z（本番バッチ） |
| 更新日 | 2026-07-20（本セッション、プロパティ値追加） | 2026-07-20（同左） | 2026-07-20（同左） | 2026-07-20（同左） | 2026-07-20（同左） | 2026-07-20（同左） |
| 重複確認 | 重複なし（§6参照） | 重複なし | 重複なし | 重複なし | 重複なし | 重複なし |
| 実行セッション | 本セッション（2026-07-20、日本文化体験・食の安心窓 実装セッション） | 同左 | 同左 | 同左 | 同左 | 同左 |
| 今回設定した値 | Region=関東／Experience Genre=和菓子作り／Reservation Status=予約受付あり・必須か未確認／Language Support=多言語Webページあり／Family Participation Status=未確認 | Region=四国／Experience Genre=染物・藍染め／Reservation Status=予約必須／Language Support=日本語のみと記載／Family Participation Status=未確認 | Region=九州・沖縄／Dietary Accommodation Type=ヴィーガン／Reservation Status=未確認／Language Support=未確認／Family Participation Status=未確認 | Region=関東／Reservation Status=未確認／Language Support=未確認／Family Participation Status=未確認 | Region=北海道／Reservation Status=未確認／Language Support=未確認／Family Participation Status=未確認 | Region=北海道／Reservation Status=予約方法のみ確認済み／Language Support=未確認／Family Participation Status=未確認 |
| 未確認のため設定しなかった値 | Dietary Accommodation Type（食事条件と無関係のため対象外） | Dietary Accommodation Type（同左） | Experience Genre（食事条件レコードのため対象外） | Experience Genre（同左）／Dietary Accommodation Type（第三者情報のみ、認証機関未確認のため空欄） | Experience Genre（同左）／Dietary Accommodation Type（同左、認証対象・有効性未確認のため空欄） | Experience Genre（同左）／Dietary Accommodation Type（同左、公式サイト・公式表記未確認のため空欄） |

---

## 12. 食のお店16件 登録記録（2026-07-20 追記、上記1〜11の記録は削除・再作成していません）

食の安心・お店情報窓（🥗）向けにExperience Intelligenceへ新規登録した16件（全国8地域×各2件）。登録実行はscratchpadスクリプト（`register_16.py`）経由、Status=New、既存プロパティ・既存選択肢のみ使用。登録後、本番Notionへの読み取りクエリで全16件を再確認済み（下表は2026-07-20時点の実データ）。

| # | タイトル | 保存先DB | ページID | Source URL | Status | 登録日時（created_time） | 更新日時（last_edited_time） | 重複確認結果 | 実行セッション |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 新宿亭 札幌店 | Experience Intelligence | 3a3157f0-f15d-8104-be8b-fafaf40b88f5 | https://www.halal-shinjukutei.com/sapporo-store | New | 2026-07-20T08:47:00.000Z | 2026-07-20T09:10:00.000Z | 重複なし（登録前に既存レコードとのlive再チェック実施） | 本セッション（2026-07-20、食のお店16件登録セッション） |
| 2 | 味楽屡ゆきや | Experience Intelligence | 3a3157f0-f15d-8114-ac4d-df78bc46b453 | https://nisekofood.jp/ | New | 2026-07-20T08:47:00.000Z | 2026-07-20T09:10:00.000Z | 重複なし | 同左 |
| 3 | いたがき本店カフェ | Experience Intelligence | 3a3157f0-f15d-81d3-8ba1-c9ab2a5df493 | https://www.itagaki-jp.com/shop/cms-images/4ad8fc12671c3fbf824a51243977cd09212a781f.pdf | New | 2026-07-20T08:47:00.000Z | 2026-07-20T09:10:00.000Z | 重複なし | 同左 |
| 4 | 旅の宿斉川 | Experience Intelligence | 3a3157f0-f15d-8167-9045-ca3ef9ef1e56 | https://ryokansaikawa.com/top/ | New | 2026-07-20T08:47:00.000Z | 2026-07-20T09:10:00.000Z | 重複なし | 同左 |
| 5 | 川越幸すし | Experience Intelligence | 3a3157f0-f15d-8178-92ac-d7101d68d19e | https://www.kawagoe-kousushi.com/restaurant | New | 2026-07-20T08:47:00.000Z | 2026-07-20T09:10:00.000Z | 重複なし | 同左 |
| 6 | カフェ トスカ（横浜ベイホテル東急） | Experience Intelligence | 3a3157f0-f15d-816d-86ad-e12caafccacb | https://ybht.co.jp/restaurant/plan/vegetarian-veganTC.php | New | 2026-07-20T08:47:00.000Z | 2026-07-20T09:10:00.000Z | 重複なし | 同左 |
| 7 | Montmartre（名古屋東急ホテル） | Experience Intelligence | 3a3157f0-f15d-817e-b0a9-cae28830baab | https://www.tokyuhotels.co.jp/en/nagoya-h/restaurant/montmartre/plan/100641/index.html | New | 2026-07-20T08:47:00.000Z | 2026-07-20T09:10:00.000Z | 重複なし | 同左 |
| 8 | ホテルアソシア静岡 | Experience Intelligence | 3a3157f0-f15d-81d8-a54b-c117372d5751 | https://www.associa.com/sth/event/417675082660a77d3b9fec/ | New | 2026-07-20T08:47:00.000Z | 2026-07-20T09:10:00.000Z | 重複なし | 同左 |
| 9 | CHOICE（GLUTEN FREE AND VEGAN CAFE） | Experience Intelligence | 3a3157f0-f15d-81e8-bcf5-ee244e7bd0c1 | https://hs-choice.com/ | New | 2026-07-20T08:47:00.000Z | 2026-07-20T09:10:00.000Z | 重複なし | 同左 |
| 10 | 帝国ホテル大阪 カフェ クベール | Experience Intelligence | 3a3157f0-f15d-817b-8058-f6a135c537e6 | https://www.imperialhotel.co.jp/osaka/restaurant/couvert/plan/vegan-menu | New | 2026-07-20T08:48:00.000Z | 2026-07-20T09:10:00.000Z | 重複なし | 同左 |
| 11 | 山一別館 | Experience Intelligence | 3a3157f0-f15d-8143-9256-fd6d2e42a8bb | https://yamaichibekkan.com/vegetarian.html | New | 2026-07-20T08:48:00.000Z | 2026-07-20T09:10:00.000Z | 重複なし | 同左 |
| 12 | ホテルグランヴィア広島 | Experience Intelligence | 3a3157f0-f15d-8183-853d-c1ae94349846 | https://www.hgh.co.jp/rest/specialmenu/ | New | 2026-07-20T08:48:00.000Z | 2026-07-20T09:10:00.000Z | 重複なし | 同左 |
| 13 | 高松国際ホテル | Experience Intelligence | 3a3157f0-f15d-8108-8e10-e56b8f49b651 | https://tkh.anabuki-enter.jp/restaurant/dinner.html | New | 2026-07-20T08:48:00.000Z | 2026-07-20T09:10:00.000Z | 重複なし | 同左 |
| 14 | レストラン ボルベール | Experience Intelligence | 3a3157f0-f15d-81de-bce9-fb535eb3e4e0 | https://xn--zck4azcl8dnbb0eze.com/ | New | 2026-07-20T08:48:00.000Z | 2026-07-20T09:10:00.000Z | 重複なし | 同左 |
| 15 | EM Wellness 暮らしの発酵DELI&CAFE | Experience Intelligence | 3a3157f0-f15d-811e-987b-d4075f4d3e98 | https://kurashinohakko.jp/eat/ | New | 2026-07-20T08:48:00.000Z | 2026-07-20T09:10:00.000Z | 重複なし | 同左 |
| 16 | 沖縄ハーバービューホテル クラブラウンジ | Experience Intelligence | 3a3157f0-f15d-8186-9c06-cb22c04ec870 | https://oka-hvh.com/8412/ | New | 2026-07-20T08:48:00.000Z | 2026-07-20T09:10:00.000Z | 重複なし | 同左 |

備考：last_edited_timeは、登録直後に実施したURL種別整理（Description追記、同日09:10前後）の反映時刻であり、Dietary Accommodation Type等の判定内容自体への変更はない。

---

## 13. 🎎日本文化体験窓の5DB横断拡張に伴うNotion更新履歴（2026-07-20 追記、上記1〜12の記録は削除・再作成していません）

食のお店16件登録後、🎎日本文化体験窓をExperience Intelligence単独表示から5DB横断設計へ拡張した際、事前diff確認（タイトル・ページID・Source URL完全一致）のうえ、以下4件のプロパティ値のみを更新した。新規DB・新規プロパティ・新規レコードの作成はなし。

| # | 対象ページ | 保存先DB | プロパティ | 更新前 | 更新後 |
|---|---|---|---|---|---|
| 1 | 中込農園 黒系ぶどう狩り | Event Calendar | Related Experience Intelligence | 空欄 | Experience Intelligence「中込農園」へ接続 |
| 2 | 体験農園みとか ぶどう狩り | Event Calendar | Related Experience Intelligence | 空欄 | Experience Intelligence「体験農園みとか」へ接続 |
| 3 | 中込農園 | Experience Intelligence | Region | 未設定 | 中部 |
| 4 | 体験農園みとか | Experience Intelligence | Region | 未設定 | 中部 |

既存の「中込農園 シャインマスカット狩り」のリレーション、および他の全レコードのプロパティは変更していない。詳細な監査結果・件数・回帰テスト結果は`docs/Version4-Status.md`§13および`docs/Nationwide-Intelligence-Collection-Design-2026-07-20.md`を参照。

---

*ARu HQ / Decode Japan — Nationwide Registration Ledger — 2026-07-20 — 本番Notion API直接クエリにより作成（§13のみ実際のNotion更新を記録）*
