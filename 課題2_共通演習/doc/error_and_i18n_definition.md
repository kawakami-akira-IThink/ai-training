# 多言語文言定義書 ＆ エラー番号定義書: 在庫管理システム

在庫管理システムで使用するメッセージ（日本語・英語・中国語）と、API が返すエラー番号を正式に定義する文書です（Step 3）。
Step 4（API 実装）ではエラー番号定義表（3章）をバックエンドのエラー辞書に、画面文言表（2章）をフロントエンドの i18n 辞書にそのまま変換できるよう、1行1エントリ・固定列の表形式で記述している。

関連文書: `doc/system_setting.md`、`doc/pbi.md`、`doc/api_specification.md`（以下「API仕様書」）

## 1. 共通事項

### 1.1 対象言語

| 言語コード | 言語 | 位置づけ |
|---|---|---|
| `ja` | 日本語 | 正。既定言語 |
| `en` | 英語 | 正 |
| `zh` | 中国語（簡体字） | **参考訳（未検証）**。ネイティブ・翻訳担当者による確認前であり、正式な文言としては扱わない |

### 1.2 メッセージキーの命名規則

- 形式: `<種別>.<区分>.<名前>`（小文字・スネークケース・ドット区切り）
- 種別:
  - `err.*` : API が返すエラーメッセージ（3章）。キーはエラーコードと 1:1 で対応する
  - `msg.*` : 画面（フロントエンド）のみで使う文言（2章）
- 同一キーは3言語すべてに必ず定義する（片言語のみの定義は不可）。

### 1.3 プレースホルダの書式

| 項目 | ルール |
|---|---|
| 書式 | `{名前}`（波括弧で囲んだ半角英小文字・スネークケース） |
| 置換 | 実行時に値で置換する。置換値は文字列化した値（数値は 10 進表記） |
| 3言語の整合 | あるキーで使うプレースホルダの集合は、3言語すべてで同一にする（語順は言語ごとに変えてよい） |
| 波括弧そのものを表示したい場合 | 現時点では不要のため定義しない（メッセージに `{` `}` を含めない） |
| 値の出所 | API メッセージ: `details` の同名フィールド。画面文言: 画面側が渡す値 |

使用するプレースホルダ一覧:

| プレースホルダ | 意味 | 使用キー | 値の出所 |
|---|---|---|---|
| `{max_length}` | 品目名の最大文字数（100） | `err.item_name_too_long` | `details.max_length` |
| `{name}` | 品目名 | `msg.confirm.delete_body`、`msg.toast.item_created`、`msg.toast.item_deleted` | 画面が保持する品目名 |

> API 側のメッセージで置換するのはサーバ側（`details` の値）、画面文言の置換はフロント側で行う。ただしフロントがエラー時に表示するのはサーバ生成済みの `error.message`（置換済み）であり、フロントが `err.*` を再置換することはない（4.3 参照）。

---

## 2. 文言定義表（画面側文言・フロント i18n 用）

API の成功レスポンスにはメッセージを含めない（API仕様書 1.4）ため、成功トースト・確認ダイアログ・空状態などの画面文言はフロントエンドで管理する。本章の表がその正式定義である。

> **注記: 中国語（`zh`）列は参考訳（未検証）です。** 正式な文言として使用する前に、ネイティブ話者等による確認が必要です。日本語・英語を正とします。

### 2.1 成功トースト

| メッセージキー | 用途 | 表示箇所 | 日本語 | 英語 | 中国語（参考訳・未検証） |
|---|---|---|---|---|---|
| `msg.toast.item_created` | 品目追加（API-2 が 201）成功時のトースト | 画面（トースト） | 「{name}」を登録しました。 | "{name}" has been added. | 已添加“{name}”。 |
| `msg.toast.item_deleted` | 品目削除（API-3 が 204）成功時のトースト | 画面（トースト） | 「{name}」を削除しました。 | "{name}" has been deleted. | 已删除“{name}”。 |
| `msg.toast.stock_updated` | 在庫増減（API-4 が 200）成功時のトースト | 画面（トースト） | 在庫を更新しました。 | Stock has been updated. | 库存已更新。 |

### 2.2 削除確認ダイアログ（PBI-3 AC2）

| メッセージキー | 用途 | 表示箇所 | 日本語 | 英語 | 中国語（参考訳・未検証） |
|---|---|---|---|---|---|
| `msg.confirm.delete_title` | 削除確認ダイアログのタイトル | 画面（ダイアログ） | 品目の削除 | Delete item | 删除品目 |
| `msg.confirm.delete_body` | 削除確認ダイアログの本文 | 画面（ダイアログ） | 「{name}」を削除します。この操作は元に戻せません。よろしいですか？ | "{name}" will be deleted. This cannot be undone. Are you sure? | 将删除“{name}”，此操作无法撤销。确定吗？ |
| `msg.confirm.delete_ok` | 削除確認ダイアログの実行ボタン | 画面（ダイアログ） | 削除する | Delete | 删除 |
| `msg.confirm.delete_cancel` | 削除確認ダイアログのキャンセルボタン | 画面（ダイアログ） | キャンセル | Cancel | 取消 |

### 2.3 一覧・状態表示

| メッセージキー | 用途 | 表示箇所 | 日本語 | 英語 | 中国語（参考訳・未検証） |
|---|---|---|---|---|---|
| `msg.list.empty` | 品目が0件のときの空状態表示（PBI-1 AC3） | 画面（一覧領域） | 品目がありません。 | No items found. | 没有品目。 |
| `msg.list.negative_stock_note` | マイナス在庫（赤文字）が存在することを示す注記。例外運用であることを明示する（system_setting.md の受入条件） | 画面（一覧付近） | 赤字の在庫数はマイナス在庫です（例外運用）。 | Stock shown in red is negative (exceptional operation). | 红色库存为负库存（例外运营）。 |
| `msg.list.loading` | 一覧取得中の表示 | 画面（一覧領域） | 読み込み中… | Loading… | 加载中… |

### 2.4 通信エラー・フォールバック（API が共通エラー形式を返せない場合）

| メッセージキー | 用途 | 表示箇所 | 日本語 | 英語 | 中国語（参考訳・未検証） |
|---|---|---|---|---|---|
| `msg.error.network` | サーバに接続できない（接続不可・タイムアウト等）場合のトースト（一覧取得失敗を含む。PBI-1 AC5） | 画面（トースト） | サーバに接続できませんでした。通信状況を確認して、もう一度お試しください。 | Could not connect to the server. Check your connection and try again. | 无法连接到服务器。请检查网络连接后重试。 |
| `msg.error.unknown` | 未知のエラーコード、または共通エラー形式でない応答を受けた場合の汎用トースト（4.3 参照） | 画面（トースト） | エラーが発生しました。しばらくしてからもう一度お試しください。 | An error occurred. Please try again later. | 发生错误。请稍后重试。 |

### 2.5 画面ラベル（フォーム・一覧）

| メッセージキー | 用途 | 表示箇所 | 日本語 | 英語 | 中国語（参考訳・未検証） |
|---|---|---|---|---|---|
| `msg.label.item_name` | 品目名の入力欄ラベル／一覧の列見出し | 画面（フォーム・一覧） | 品目名 | Item name | 品目名称 |
| `msg.label.initial_quantity` | 初期在庫数の入力欄ラベル | 画面（フォーム） | 初期在庫数 | Initial stock | 初始库存 |
| `msg.label.quantity` | 在庫数の列見出し | 画面（一覧） | 在庫数 | Stock | 库存 |
| `msg.label.delta` | 増減量の入力欄ラベル | 画面（一覧） | 増減量 | Adjustment | 增减量 |
| `msg.button.add` | 品目追加ボタン | 画面（フォーム） | 追加 | Add | 添加 |
| `msg.button.delete` | 品目削除ボタン（一覧の各行） | 画面（一覧） | 削除 | Delete | 删除 |
| `msg.button.adjust` | 在庫増減の実行ボタン | 画面（一覧） | 更新 | Update | 更新 |

> 画面ラベルは画面設計の進行により増減しうる。実装時に追加が必要になった場合は同じ書式で本表に追記する。

---

## 3. エラー番号定義表（API 用）

API仕様書 1.6 の仮採番（E001〜E010、E099）を、**採番・HTTPステータス・`details` の形を変更せずそのまま正式採用する**。変更点は無い（API仕様書 1.6 の「仮」注記は、本書をもって解除できる。9章参照）。

### 3.1 エラー定義（コード・条件・対応）

| エラーコード | HTTPステータス | エラー内容 | 発生条件 | 対応API | `details` の内容 | メッセージキー |
|---|---|---|---|---|---|---|
| E001 | 400 | リクエスト形式不正 | JSON 構文エラー、Body が JSON オブジェクトでない、Content-Type 不正 | API-2、API-4 | `{}` | `err.invalid_request` |
| E002 | 400 | 品目名が未指定・空 | `name` が未指定、`null`、文字列以外、または前後空白除去後に空 | API-2 | `{"field": "name"}` | `err.item_name_required` |
| E003 | 400 | 品目名が長すぎる | `name` が前後空白除去後に 101 文字以上（Unicode コードポイント数） | API-2 | `{"field": "name", "max_length": 100}` | `err.item_name_too_long` |
| E004 | 400 | 初期在庫数が不正 | `quantity` が整数でない（小数・文字列・真偽値・`null`）、負の値、または符号付き64bit整数の範囲外 | API-2 | `{"field": "quantity"}` | `err.initial_quantity_invalid` |
| E005 | 400 | 増減量が不正 | `delta` が未指定、`null`、0、整数でない、範囲外（増減後の在庫数が符号付き64bit範囲外となる場合を含む） | API-4 | `{"field": "delta"}` | `err.delta_invalid` |
| E006 | 400 | expected_quantity が不正 | `expected_quantity` が未指定、`null`、または整数でない | API-4 | `{"field": "expected_quantity"}` | `err.expected_quantity_invalid` |
| E007 | 400 | 品目IDの指定が不正 | パスパラメータ `id` が正の整数でない（例: `abc`、`0`、`-1`） | API-3、API-4 | `{"field": "id"}` | `err.item_id_invalid` |
| E008 | 404 | 品目が存在しない | 指定した `id` の品目が存在しない（他の利用者が先に削除した場合、増減の判定中に削除された場合を含む） | API-3、API-4 | `{"id": <指定されたID>}` | `err.item_not_found` |
| E009 | 409 | 品目名の重複 | 前後空白除去 + 大文字小文字無視（`casefold`）で、同一名称の品目が既に存在する（同時登録の競合を含む） | API-2 | `{"field": "name"}` | `err.item_name_duplicate` |
| E010 | 409 | 在庫数の不一致 | サーバ上の `quantity` と `expected_quantity` が異なる（在庫は更新されない） | API-4 | `{"item": <最新の品目オブジェクト>}` | `err.stock_conflict` |
| E099 | 500 | サーバ内部エラー | 上記以外の想定外のエラー（DB エラー、未処理の例外など） | API-1〜API-4 | `{}` | `err.internal_server_error` |

### 3.2 エラーメッセージ（言語別）

メッセージキー単位の辞書へ機械的に変換できるよう、3.1 とは別表にしている（結合キーは「エラーコード」「メッセージキー」）。

> **注記: 中国語（`zh`）列は参考訳（未検証）です。** 日本語・英語を正とします。

| エラーコード | メッセージキー | 日本語 | 英語 | 中国語（参考訳・未検証） |
|---|---|---|---|---|
| E001 | `err.invalid_request` | リクエストの形式が正しくありません。 | The request format is invalid. | 请求格式不正确。 |
| E002 | `err.item_name_required` | 品目名は必須です。 | Item name is required. | 品目名称为必填项。 |
| E003 | `err.item_name_too_long` | 品目名は{max_length}文字以内で入力してください。 | Item name must be {max_length} characters or fewer. | 品目名称不能超过{max_length}个字符。 |
| E004 | `err.initial_quantity_invalid` | 初期在庫数は0以上の整数で指定してください。 | Initial stock must be an integer of 0 or greater. | 初始库存必须是大于等于0的整数。 |
| E005 | `err.delta_invalid` | 増減量は0以外の整数で指定してください。 | Adjustment amount must be a non-zero integer. | 增减量必须是非0的整数。 |
| E006 | `err.expected_quantity_invalid` | 現在の在庫数（expected_quantity）は整数で指定してください。 | The current stock quantity (expected_quantity) must be an integer. | 当前库存数量（expected_quantity）必须是整数。 |
| E007 | `err.item_id_invalid` | 品目IDの指定が正しくありません。 | The item ID is invalid. | 品目ID不正确。 |
| E008 | `err.item_not_found` | 指定された品目が存在しません。 | The specified item does not exist. | 指定的品目不存在。 |
| E009 | `err.item_name_duplicate` | 同じ名称の品目が既に登録されています。 | An item with the same name already exists. | 已存在同名品目。 |
| E010 | `err.stock_conflict` | 在庫数が他の操作により更新されています。最新の在庫数を表示しました。 | The stock quantity was updated by another operation. The latest quantity is now displayed. | 库存数量已被其他操作更新，已显示最新库存数量。 |
| E099 | `err.internal_server_error` | サーバ内部でエラーが発生しました。しばらくしてからもう一度お試しください。 | An internal server error occurred. Please try again later. | 服务器内部发生错误，请稍后重试。 |

補足:

- 日本語メッセージは API仕様書の各レスポンス例の `message` と完全に一致させている（ただし E003 の「100」は `{max_length}` に置換する形で定義。置換後は同一文字列になる）。
- `{max_length}` は `details.max_length` と同じ値（現在は 100）。上限値を変更しても、メッセージ文言の修正は不要。
- メッセージ末尾の句点は、日本語・中国語は全角「。」、英語は半角「.」とする。

---

## 4. 補足

### 4.1 言語判定ルール

| 項目 | ルール |
|---|---|
| 判定に使うヘッダー | リクエストヘッダー `Accept-Language` |
| 対応言語 | `ja`、`en`、`zh` |
| 判定方法 | ヘッダー値の**先頭の言語タグ**を取り出し、そのプライマリ部分（`-` より前、大文字小文字を区別しない）で判定する。q 値による並べ替えは行わない |
| 判定例 | `en-US,en;q=0.9` → `en` ／ `zh-CN` → `zh` ／ `ja` → `ja` ／ `EN` → `en` |
| 既定 | ヘッダー未指定、先頭タグが未対応言語（例: `fr`、`*`）、または解釈不能な値（空文字、不正な書式）の場合は **`ja`** |
| 応答 | 実際に採用した言語を、レスポンスヘッダー `Content-Language`（`ja` / `en` / `zh`）で返す |
| 適用範囲 | エラーレスポンスの `error.message`（`details` 内の文字列を含む。現状 `details` に文言は含まれない）。成功レスポンスにはメッセージを含めない |
| `error.code` | 言語に依存しない固定値。フロントエンドはコードで処理を分岐できる |

### 4.2 メッセージ内容の方針

- メッセージは**利用者向けの文言**とする。利用者が原因と次の行動を理解できる内容にする。
- **内部情報を含めない**: スタックトレース、SQL 文、テーブル名・カラム名、ファイルパス、例外クラス名、ライブラリのエラー文などはメッセージ・`details` のいずれにも含めない。E099 のメッセージは常に定型文とし、詳細な原因はサーバ側ログにのみ記録する。
- 入力値そのもの（利用者が入力した文字列）はメッセージに埋め込まない（`{max_length}` のような仕様上の定数のみプレースホルダで埋め込む）。
- 言語を問わず、同じエラーコードは同じ意味を表す。

### 4.3 フロントエンドのエラー表示方針

1. API がエラーを返したときは、**`error.message` をそのままトースト表示する**（API は `Accept-Language` に応じて翻訳済みのメッセージを返す）。
2. 処理の分岐は `error.code` で行う。E010 は `details.item` または一覧の再取得で画面を更新、E008 はトースト表示後に一覧を再取得する（API仕様書 1.11）。
3. **未知のエラーコード**（本書に定義の無いコード）であっても、`error.message` が文字列として存在すれば、それを表示してよい。`error.message` が無い・共通エラー形式でない応答（HTML のエラーページ、想定外の JSON 等）の場合は、汎用文言 `msg.error.unknown` にフォールバックする。
4. サーバに接続できない場合（ネットワークエラー・タイムアウト）は `msg.error.network` を表示する。
5. フロントは API に送る `Accept-Language` と、画面文言（2章）の言語を同じ言語にそろえる（言語の切り替え UI の仕様は本書の対象外）。
6. 一覧取得の失敗時は、トーストを表示し、直前に表示していた一覧を維持する（PBI-1 AC5）。

### 4.4 実装（Step 4）向けの変換ガイド

| 本書の表 | 変換先 | 備考 |
|---|---|---|
| 3.1 + 3.2 | バックエンドのエラー辞書。例: `ERRORS = {"E001": {"status": 400, "key": "err.invalid_request"}, ...}`、`MESSAGES = {"ja": {"err.invalid_request": "..."}, "en": {...}, "zh": {...}}` | 1行が1エントリ。`details` の形は 3.1 を参照 |
| 2章の各表 | フロントエンドの i18n 辞書（`ja` / `en` / `zh` ごとのキー・値） | 表の区切りは見出しのみで、キーの名前空間は共通（`msg.*`） |
| 1.3 のプレースホルダ | `{name}` 形式の単純置換（例: `str.replace` / `format_map`） | サーバ側では未定義のプレースホルダが残らないことを確認する |
| 4.1 | `Accept-Language` の判定関数と `Content-Language` ヘッダー付与の共通処理 | |

---

## 5. 3言語の整合チェック（作成時点）

- 2章・3.2 のすべてのキーについて、日本語・英語・中国語の3列が埋まっている。
- プレースホルダの集合は3言語で一致している（`{name}`: 2.1、2.2 の各キー／`{max_length}`: `err.item_name_too_long`）。
- 3.1 と 3.2 のエラーコード・メッセージキーは1対1で対応している（E001〜E010、E099 の計11件）。

---

## 6. トレーサビリティ（PBI との対応）

| PBI の受入条件 | 使用するメッセージキー |
|---|---|
| PBI-1 AC3（0件の空状態） | `msg.list.empty` |
| PBI-1 AC2、system_setting.md（マイナス在庫の例外運用の明示） | `msg.list.negative_stock_note` |
| PBI-1 AC5（一覧取得の失敗） | `err.internal_server_error`（500）、`msg.error.network`（接続不可） |
| PBI-2 AC1（登録成功） | `msg.toast.item_created` |
| PBI-2 AC3・AC4（同一名称） | `err.item_name_duplicate`（E009） |
| PBI-2 AC5（品目名が空） | `err.item_name_required`（E002） |
| PBI-2 AC6（品目名が長すぎる） | `err.item_name_too_long`（E003） |
| PBI-2 AC7（初期在庫数が不正） | `err.initial_quantity_invalid`（E004） |
| PBI-3 AC1（削除成功） | `msg.toast.item_deleted` |
| PBI-3 AC2（削除確認） | `msg.confirm.delete_title` / `_body` / `_ok` / `_cancel` |
| PBI-3 AC4・PBI-4 AC7（存在しない品目） | `err.item_not_found`（E008） |
| PBI-4 AC1〜3（増減成功） | `msg.toast.stock_updated` |
| PBI-4 AC4（在庫数の不一致） | `err.stock_conflict`（E010） |
| PBI-4 AC5（増減量が不正） | `err.delta_invalid`（E005） |
| PBI-4 AC6（expected_quantity が不正） | `err.expected_quantity_invalid`（E006） |
| 共通 AC5（エラー表示の統一） | `error.message` の表示（4.3）、`msg.error.unknown`、`msg.error.network` |
| API仕様書 1.7（形式不正・id 不正） | `err.invalid_request`（E001）、`err.item_id_invalid`（E007） |

---

## 7. 採番ルール（今後の追加用）

- `E` + 3桁数字。`E001`〜`E098` は個別エラー、`E099` はサーバ内部エラー（予備ではなく固定）。
- 新規エラーを追加する場合は、既存コードの意味・番号を変更せず、末尾（E011 以降）に追加する。HTTPステータスを変更する場合は別コードを採番する。
- 追加時は 3.1・3.2 の両表、API仕様書 1.6、および 6章を同時に更新し、3言語のメッセージを必ず揃える。

## 8. 未確定・要確認事項

- 中国語（簡体字）は参考訳（未検証）であり、ネイティブ確認が未実施。特に「负库存（例外运营）」「品目」の訳語は確認が望ましい。
- 画面ラベル（2.5）は画面設計の確定に応じて変更・追加の可能性がある。
- フロントエンドの言語切り替え方法（ブラウザ設定連動／手動切り替え UI）は未定義（本書の対象外）。

## 9. API仕様書との関係

- 採番・HTTPステータス・`details` の形・日本語メッセージは API仕様書と一致しており、API仕様書の修正は不要。
- API仕様書 1.6 の「仮」の注記は本書の確定をもって解除（または本書への参照に置換）できる。
