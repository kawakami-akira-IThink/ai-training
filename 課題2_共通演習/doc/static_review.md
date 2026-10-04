# 静的レビュー結果（Step 4: 受入条件との突合）: 在庫管理システム

- 対象コード: `課題2_共通演習/src/`（backend: `main.py` / `db.py` / `errors.py` / `i18n.py` / `requirements.txt`、frontend: `package.json` / `vite.config.ts` / `tsconfig.json` / `index.html` / `src/**`）
- 基準文書: `doc/pbi.md`、`doc/api_specification.md`（以下「API仕様書」）、`doc/error_and_i18n_definition.md`（以下「定義書」）、`doc/implementation_plan.md`（以下「計画書」。6章トレーサビリティ・7.3 静的レビュー手順）
- 方法: コードは**実行していない**（パッケージ導入・サーバ起動・npm install なし）。読み合わせによる机上検証。補助として以下のみ実施した。
  - `python -m py_compile`（backend 4ファイル）: 構文エラーなし。生成された `__pycache__` は削除済み。
  - 文言の突合: 定義書の表とコード内辞書を文字列比較する使い捨てスクリプト（標準ライブラリのみ・成果物には含めない）で、キー過不足・1文字単位の一致を確認。
  - `i18n.resolve_lang` 単体の判定例確認（FastAPI 非依存の純関数のみ）。
- 判定記号: ○ 満たす ／ △ 一部満たす・要確認 ／ × 満たさない ／ − 静的には判定不能（Step 5 で確認）
- 行番号は本レビュー時点のファイルに対するもの。

---

## 1. 受入条件の判定（pbi.md 全 28 件）

### PBI-1: 品目と在庫数の一覧を表示する

| AC | 条件の要約 | 判定 | 根拠（ファイル:行） | 備考 |
|---|---|---|---|---|
| 1 | 画面を開く・リロードで DB と一致 | ○ | BE `main.py:135-141`（全件 SELECT）, `main.py:200-204`, `db.py:52-60` ／ FE `App.tsx:57-73`（初回 `useEffect` → `refresh`）, `api.ts:67-71`, `ItemRow.tsx:24-25` | フロント側でキャッシュ・加工なし |
| 2 | マイナス在庫を赤文字 | ○ | BE `db.py:57`（負値のまま返却）／ FE `ItemRow.tsx:25`（`qty negative`）, `styles.css:13`, `ItemList.tsx:20,24`（注記） | |
| 3 | 0 件で空状態メッセージ | ○ | BE `main.py:138-139`（`[]`）／ FE `ItemList.tsx:17`（`msg.list.empty`） | 初回取得失敗時にも空状態文言が出る点は指摘 L-02 |
| 4 | ID 昇順・更新前後で不変 | ○ | BE `main.py:138`（`ORDER BY id ASC`）, `db.py:12`（AUTOINCREMENT）／ FE `ItemList.tsx:35`（並べ替えなし） | |
| 5 | 一覧取得失敗でトースト・直前一覧維持 | ○ | FE `App.tsx:60-67`（失敗時は `setItems` しない・トースト）, `api.ts:35-53`（network / unknown / api 正規化） ／ BE `main.py:40-44`（E099） | |

### PBI-2: 品目を追加する

| AC | 条件の要約 | 判定 | 根拠（ファイル:行） | 備考 |
|---|---|---|---|---|
| 1 | 有効な名称・初期在庫で 201、一覧に表示 | ○ | BE `main.py:207-216`, `main.py:144-162` ／ FE `App.tsx:95-101`, `AddItemForm.tsx:15-22`, `App.tsx:89`（再取得） | `Location` ヘッダー付与あり |
| 2 | 初期在庫数省略で 0 | ○ | BE `main.py:109-110` ／ FE `App.tsx:96`（空欄なら未送信）, `api.ts:76` | |
| 3 | 同一名称は 409・既存は不変 | ○ | BE `db.py:14`（`name_key UNIQUE`）, `main.py:148-155`（`IntegrityError`→E009。未コミットのまま close でロールバック） ／ FE `App.tsx:86-87` | |
| 4 | 前後空白除去＋大小無視で同一判定 | ○ | BE `main.py:99`（`strip()`。全角空白も除去）, `db.py:47-49`（`casefold()`）, `main.py:152` | NFKC なし（仕様どおり全角/半角は区別） |
| 5 | 品目名が空・空白のみで 400 | ○ | BE `main.py:96-101`（E002） | |
| 6 | 100 文字超で 400 | ○ | BE `main.py:102-103`（E003, `max_length:100`） | 100 文字は OK、101 文字で E003 |
| 7 | 初期在庫数が小数・文字列・負で 400 | △ | BE `main.py:107-114`（`type(q) is int` で bool/float/str を除外、負値・範囲外も E004）＝API としては ○ | 画面からは `<input type="number" step="1">` のブラウザ標準検証で小数・不正入力の送信自体がブロックされ、400・トーストにならない（指摘 M-01） |

### PBI-3: 品目を削除する

| AC | 条件の要約 | 判定 | 根拠（ファイル:行） | 備考 |
|---|---|---|---|---|
| 1 | 削除で DB・一覧から消え、他に影響なし | ○ | BE `main.py:165-173`（`WHERE id = ?` のみ）, `main.py:219-224`（204）／ FE `App.tsx:113-121`, `App.tsx:89` | |
| 2 | 確認ダイアログで承諾時のみ削除 | ○ | FE `ItemRow.tsx:40`（`onDelete` は対象設定のみ）, `App.tsx:144`, `ConfirmDialog.tsx:15-40`, `App.tsx:113-121`, `App.tsx:150`（キャンセルは API を呼ばない） | Esc 2 回等でネイティブに閉じた場合の状態ずれ（指摘 L-03） |
| 3 | 在庫数にかかわらず削除可 | ○ | BE `main.py:168`（在庫を条件にしない）, `db.py:15`（CHECK なし） | |
| 4 | 存在しない ID は 404・トースト・再取得 | ○ | BE `main.py:170-171`（E008, `{"id": id}`）／ FE `App.tsx:86-89` | |

### PBI-4: 在庫数を増減する

| AC | 条件の要約 | 判定 | 根拠（ファイル:行） | 備考 |
|---|---|---|---|---|
| 1 | +5 で 10→15（200）・画面 15 | ○ | BE `main.py:176-190`, `main.py:227-236` ／ FE `App.tsx:104-110`（`expected_quantity = item.quantity`）, `api.ts:86-90` | |
| 2 | -3 で 10→7 | ○ | 同上 | |
| 3 | マイナス在庫許容（2→-3）・赤文字 | ○ | BE 下限チェックなし `main.py:117-130`, `db.py:15` ／ FE `ItemRow.tsx:25` | |
| 4 | 不一致は 409＋最新 Item、トースト＋再取得 | ○ | BE `main.py:180-193`（条件付き単一 UPDATE、行ありなら E010 + `details.item`）／ FE `App.tsx:86-89` | FE は `details.item` を使わず再取得で反映（API仕様書 1.11 で許容） |
| 5 | 増減量が 0・非整数・未指定で 400 | △ | BE `main.py:117-122`（E005）＝API としては ○。FE `App.tsx:105`（空欄なら delta 未送信→E005）, 0 も送信→E005 | 小数・不正入力は画面のブラウザ標準検証で送信がブロックされる（指摘 M-01） |
| 6 | expected_quantity 未指定・非整数で 400 | ○ | BE `main.py:125-130`（E006） | 画面は常に整数を送るため API 直叩きで確認（Step 5） |
| 7 | 存在しない品目は 404・トースト・再取得 | ○ | BE `main.py:191-192`（UPDATE 0 件かつ行なし→E008）／ FE `App.tsx:86-89` | |

### 共通の受入条件

| AC | 条件の要約 | 判定 | 根拠（ファイル:行） | 備考 |
|---|---|---|---|---|
| 1 | 全操作 0.2 秒以内 | − | 単純クエリ・リクエスト単位接続のみ（`db.py:24-29`, `main.py:135-195`）。重い処理は無い | 実測は Step 5。`localhost` 解決遅延リスクあり（指摘 M-02） |
| 2 | 測定条件（ローカル・100 件） | − | 同上 | Step 5 で 100 件投入して測定 |
| 3 | 操作後（成功・失敗とも）に再取得 | ○ | FE `App.tsx:80-92`（`runOperation` の try/catch の後に必ず `await refresh()`） | ブラウザ標準検証で送信がブロックされた場合は操作自体が発生しない |
| 4 | 画面更新時の DB 一致 | ○ | PBI-1 AC1 と同じ | |
| 5 | エラー表示の統一（トースト・最新状態） | ○ | BE `errors.py:37-73`, `main.py:35-46` ／ FE `api.ts:14-27,45-53`, `App.tsx:18-25`, `ToastList.tsx` | ルーティング不一致の 404/405 は FastAPI 既定形式（FE は `msg.error.unknown` で表示。計画書 9章 #4 で対象外と合意済み。指摘 L-05） |

---

## 2. API仕様書との照合

### 2.1 エンドポイント・ステータス

| API | 仕様 | 実装 | 判定 |
|---|---|---|---|
| API-1 `GET /api/items` | 200 `{"items":[...]}` ID 昇順、0 件 `[]`、500 E099 | `main.py:200-204`, `main.py:138` | ○ |
| API-2 `POST /api/items` | 201 + Item + `Location: /api/items/{id}`、400 E001〜E004、409 E009、500 | `main.py:207-216`（`Location` あり）, `main.py:154-155` | ○ |
| API-3 `DELETE /api/items/{id}` | 204 Body なし、400 E007、404 E008、500 | `main.py:219-224`, `main.py:84-91`, `main.py:170-171` | ○ |
| API-4 `POST /api/items/{id}/adjust` | 200 + 更新後 Item、400 E001/E005〜E007、404 E008、409 E010、500 | `main.py:227-236`, `main.py:176-195` | ○ |
| Item オブジェクト | id / name / quantity / created_at / updated_at（name_key は含めない） | `db.py:52-60`, `db.py:21` | ○ |
| 日時形式 | ISO 8601 UTC 秒精度・末尾 Z、登録時 created_at = updated_at | `db.py:42-44`, `main.py:147,152` | ○ |
| 成功応答にメッセージを含めない | Item / `{"items"}` / 204 のみ | `main.py:204,214-216,224,236` | ○ |
| レスポンス Content-Type | `application/json; charset=utf-8` | Starlette `JSONResponse` 既定は `application/json`（charset なし） | △（指摘 L-06） |

### 2.2 エラーコード・details 形式

| コード | 仕様の details | 実装（ファイル:行） | 判定 |
|---|---|---|---|
| E001 | `{}` | `main.py:73,78,80`（`AppError("E001")`→`details or {}`） | ○ |
| E002 | `{"field":"name"}` | `main.py:98,101` | ○ |
| E003 | `{"field":"name","max_length":100}` | `main.py:103` | ○ |
| E004 | `{"field":"quantity"}` | `main.py:113` | ○ |
| E005 | `{"field":"delta"}` | `main.py:121,235` | ○ |
| E006 | `{"field":"expected_quantity"}` | `main.py:129` | ○ |
| E007 | `{"field":"id"}` | `main.py:87,90`, `errors.py:66` | ○ |
| E008 | `{"id": <ID>}` | `main.py:171,192`（int で返却） | ○ |
| E009 | `{"field":"name"}` | `main.py:155` | ○ |
| E010 | `{"item": <最新 Item>}` | `main.py:193` | ○ |
| E099 | `{}` | `main.py:44`, `errors.py:73` | ○ |
| ステータス対応 | 定義書 3.1 の 11 件 | `errors.py:13-25` で 11 件すべて一致 | ○ |
| 共通形式 `{"error":{code,message,details}}` | 1.5 | `errors.py:37-48` | ○ |

### 2.3 Accept-Language / Content-Language

| 観点 | 仕様 | 実装 | 判定 |
|---|---|---|---|
| 判定ルール | 先頭タグのプライマリ部分、大文字小文字無視、未対応・不正は ja | `i18n.py:7-14`。確認例: `en-US,en;q=0.9`→en、`zh-CN`→zh、`EN`→en、`fr`/`*`/空/未指定→ja、`en;q=0.5, ja`→en（q 値で並べ替えない） | ○ |
| 1 リクエスト 1 回決定 | `request.state.lang` | `main.py:38-39`, `errors.py:51-53`（例外ハンドラから参照。state は scope 共有） | ○ |
| Content-Language を全応答に付与 | 成功・204・エラーとも | `main.py:45`（http ミドルウェア）, `errors.py:48`（保険） | ○ |
| CORS で参照可能 | — | `main.py:54`（`expose_headers` に Content-Language, Location） | ○ |
| フロントが画面言語と同じ値を送る | 定義書 4.3-5 | `App.tsx:12-15,28-33,124-128`, `api.ts:8-11,31` | ○ |

### 2.4 422→400 変換・例外処理・CORS

| 観点 | 実装 | 判定 |
|---|---|---|
| 422 を外部に出さない | Body は Pydantic モデルを使わず自前検証（`main.py:69-130`）、パスは `str` 受け（`main.py:220,228`）。安全網 `RequestValidationError` ハンドラ（`errors.py:62-67`、path→E007／他→E001） | ○ |
| 想定外例外→E099・内部情報非開示 | `main.py:40-44`（ログのみ・定型文）, `errors.py:70-73` | ○ |
| E099 に CORS ヘッダーが付くか | http ミドルウェア（`main.py:35`）を先に、`CORSMiddleware`（`main.py:49-55`）を後に登録 → CORS が外側。エンドポイント内の未処理例外は ExceptionMiddleware を素通り → `call_next` から再送出 → `main.py:42-44` で E099 化 → 外側の CORS がヘッダー付与。fastapi==0.115.6（Starlette 0.41 系）の `BaseHTTPMiddleware.call_next` は下流例外を再送出する仕様で、想定どおり | ○ |
| CORS 設定値 | オリジン 2 件・メソッド `GET, POST, DELETE, OPTIONS`・ヘッダー `Content-Type, Accept-Language`（`main.py:51-53`）。API仕様書 1.2 と一致 | ○ |
| HTTPException ハンドラ | 未登録（コードからは送出しない。ルーティング不一致 404 / 405 は FastAPI 既定 `{"detail":...}`） | △（指摘 L-05。計画書で対象外と合意済み） |

### 2.5 検証の優先順位（API仕様書 1.7）

| API | 仕様 | 実装の呼び出し順 | 判定 |
|---|---|---|---|
| API-2 | E001 → name(E002/E003) → quantity(E004) → E009 | `main.py:210-213` | ○ |
| API-3 | E007 → E008 | `main.py:222-223` | ○ |
| API-4 | E001 → E007 → delta(E005) → expected(E006) → 範囲(E005) → E008 / E010 | `main.py:230-236`, `main.py:189-193` | ○ |
| 最初の 1 件のみ返す | 各検証で即 `raise` | ○ |

---

## 3. 文言の照合（定義書との 1 文字単位比較）

| 対象 | 定義書 | コード | キー数（ja/en/zh） | 不一致 | キー過不足 | プレースホルダ | 判定 |
|---|---|---|---|---|---|---|---|
| エラーメッセージ | 3.2（11 キー） | `backend/i18n.py:18-59` | 11 / 11 / 11 | 0 件 | なし | `{max_length}` が 3 言語で一致。置換後の ja は API仕様書の例文「品目名は100文字以内で入力してください。」と一致 | ○ |
| コード→ステータス→キー | 3.1（11 件） | `backend/errors.py:13-25` | 11 | 0 件 | なし | — | ○ |
| 画面文言 | 2章（19 キー） | `frontend/src/i18n.ts:11-75` | 19 / 19 / 19 | 0 件 | なし | `{name}` が 2.1・2.2 の該当キーで 3 言語一致 | ○ |
| 中国語の「参考訳」明記 | 1.1 / 8章 | `i18n.py:17,45`, `i18n.ts:3-4` | — | — | — | — | ○ |
| 定義書に無い画面文字列 | — | `App.tsx:133`（h1「在庫管理 / Inventory」固定）, `LanguageSwitcher.tsx:11`（`aria-label="Language"`）, `ToastList.tsx:19`（`aria-label="close"`）, `index.html:2,6`（`lang="ja"`・title 固定） | — | — | 定義書 2.5 に未定義 | — | △（指摘 L-09） |

---

## 4. 境界値の机上追跡

### 4.1 品目名（API-2）

| 入力 `name` | 追跡（`main.py:94-104` → `_insert`） | 結果 | 期待 | 判定 |
|---|---|---|---|---|
| キーなし / `null` / `123` | `isinstance(name, str)` が False | 400 E002 | E002 | ○ |
| `""` | strip 後 `""` | 400 E002 | E002 | ○ |
| `"   "`（半角空白のみ） | strip 後 `""` | 400 E002 | E002 | ○ |
| `"　　"`（全角空白のみ） | Python `str.strip()` は U+3000 を除去 | 400 E002 | E002 | ○ |
| 100 文字 | `len == 100` | 201 | 201 | ○ |
| 101 文字 | `len > 100` | 400 E003（`max_length:100`） | E003 | ○ |
| `" 100文字 "`（前後空白込み 102） | strip 後 100 | 201 | 201（除去後で判定） | ○ |
| `" ボールペン（黒） "`（既存あり） | strip → `casefold` が一致 → UNIQUE 違反 | 409 E009 | E009 | ○ |
| `"usb"`（`"USB"` 既存） | `casefold` 一致 | 409 E009 | E009 | ○ |
| `"ＵＳＢ"`（全角。`USB` 既存） | NFKC なしで別キー | 201 | 201（全角/半角は区別） | ○ |
| 孤立サロゲート `"\ud800"` | `json.loads` は通る → sqlite3 バインドで `UnicodeEncodeError` | 500 E099 | 未定義（400 が望ましい） | △（指摘 L-08） |

### 4.2 初期在庫数 `quantity`（API-2）

| 入力 | 追跡（`main.py:107-114`） | 結果 | 判定 |
|---|---|---|---|
| 省略 | `"quantity" not in body` | 0 で 201 | ○ |
| `0` | int・0 以上 | 201 | ○ |
| `-1` | `q < 0` | 400 E004 | ○ |
| `1.5` / `10.0` | float → `type is int` が False | 400 E004 | ○ |
| `"10"` | str | 400 E004 | ○ |
| `true` | `type(True) is int` は False | 400 E004 | ○ |
| `null` | キーあり・None | 400 E004 | ○ |
| `NaN` / `1e400` | Python json は float(nan/inf) に変換 | 400 E004 | ○ |
| 2^63 | `_in_int64` False | 400 E004 | ○ |
| 4300 桁超の整数 | `json.loads` が `ValueError`（int 桁数上限）→ `main.py:77` | 400 **E001** | △（E004 が自然。指摘 L-07） |

### 4.3 増減 `delta` / `expected_quantity`（API-4）

| 入力 | 追跡（`main.py:117-130, 227-236, 176-195`） | 結果 | 判定 |
|---|---|---|---|
| delta 省略 / `null` | `_is_int(None)` False | 400 E005 | ○ |
| delta `0` | `d == 0` | 400 E005 | ○ |
| delta `1.5` / `"5"` / `true` | 非 int | 400 E005 | ○ |
| delta `-5`, expected `2`（在庫 2） | UPDATE 成功 → `-3` | 200 quantity -3 | ○ |
| delta 不正 かつ expected 欠落 | delta を先に検証 | 400 E005 | ○（優先順位どおり） |
| expected 省略 / `null` / `"10"` / `10.5` | 非 int | 400 E006 | ○ |
| expected 不一致（サーバ 12、expected 10） | UPDATE 0 件 → SELECT で行あり | 409 E010 + `details.item`（quantity 12）、在庫不変 | ○ |
| expected + delta が 64bit 範囲外 | `main.py:234-235` | 400 E005 | ○ |
| 存在しない ID | UPDATE 0 件 → 行なし | 404 E008 `{"id": n}` | ○ |

### 4.4 パス `id`（API-3 / API-4）と形式

| 入力 | 追跡（`main.py:84-91`） | 結果 | 判定 |
|---|---|---|---|
| `abc` / `-1` / `+1` / `1.0` | `isdigit` False | 400 E007 | ○ |
| `0` | `value < 1` | 400 E007 | ○ |
| `9999999999999999999` | `> INT64_MAX` | 400 E007 | ○ |
| `１`（全角数字） / `²` | `isascii` False | 400 E007 | ○ |
| `007` | 7 として扱う | 存在すれば処理 | ○（仕様上の禁止なし） |
| API-4: `id=abc` かつ Body 不正 JSON | E001 を先に判定（`main.py:230-231`） | 400 E001 | ○ |
| Content-Type なし / `text/plain` | `main.py:71-73` | 400 E001 | ○ |
| `application/json; charset=utf-8` | パラメータ除去で一致 | 通過 | ○ |
| 空 Body / JSON 構文エラー / 非 UTF-8 | `main.py:75-78` | 400 E001 | ○ |
| Body が配列・数値 | `main.py:79-80` | 400 E001 | ○ |
| 仕様外フィールド付き | 取り出さないだけ | 無視 | ○ |

### 4.5 例外時の CORS ヘッダー

| 経路 | 追跡 | CORS ヘッダー | 判定 |
|---|---|---|---|
| `AppError`（400/404/409） | ExceptionMiddleware 内のハンドラ（`errors.py:57-59`）→ http ミドルウェア → CORS | 付く | ○ |
| DB エラー等の想定外例外 | ExceptionMiddleware 素通り → `call_next` 再送出 → `main.py:42-44` で E099 → CORS | 付く | ○ |
| ルーティング不一致 404 / 405 | Starlette 既定応答 → CORS | 付く（形式は既定） | ○（形式は L-05） |
| プリフライト（POST JSON / DELETE） | CORS が最外殻で応答。`Content-Type`・`Accept-Language` 許可済み | 付く | ○ |

---

## 5. バグ・型エラー・import・API 誤用の確認

| 観点 | 確認内容 | 結果 |
|---|---|---|
| Python 構文 | `py_compile`（4 ファイル） | 問題なし |
| import | `main.py` は `import db` / `from errors ...` / `from i18n ...` のフラット import。`uvicorn main:app` を `src/backend` で起動する前提（計画書 8章）で解決可能。循環 import なし（errors→i18n、main→db/errors/i18n） | 問題なし |
| FastAPI | `lifespan`（asynccontextmanager）, `@app.middleware("http")`, `add_middleware` の順序, `exception_handler(Exception)`, `Response(status_code=204)`（Starlette 0.41 は 204 で Content-Length を付けない）, `JSONResponse(status_code=201, headers=...)` | 誤用なし |
| 同期 DB の扱い | `async def` エンドポイントから `run_in_threadpool` で同期 sqlite3 を実行、接続はリクエスト単位（スレッド間共有なし） | 問題なし |
| 条件付き UPDATE | 1 文で判定と更新（`main.py:180-184`） | 問題なし。ただし更新後 SELECT がコミット後（指摘 L-01） |
| `IntegrityError` 後の接続 | commit せず close → 暗黙トランザクションはロールバック | 問題なし |
| TypeScript 型 | `ApiError extends Error`（target ES2020 で instanceof 有効）, `useRef<HTMLDialogElement>(null)`（React 19 型で ref に渡せる）, `<dialog onCancel>`（React DOM・@types/react 19 で対応） | 明らかな型エラーなし |
| tsconfig | `include` に `vite.config.ts` を含み `types: ["vite/client"]` のみ。`@types/node` 未導入でも `skipLibCheck: true` のため通る見込みだが `npm run build`（`tsc --noEmit`）で要確認 | 指摘 L-10 |
| React | `StrictMode` 下で初回 `refresh` が 2 回走るが `refreshSeq` で古い応答を破棄、`useState` 初期化子の `applyLang` は冪等 | 問題なし |
| 二重送信防止 | `busy` で追加・更新・削除ボタンを無効化（`AddItemForm.tsx:34`, `ItemRow.tsx:35,40`）。無効な送信ボタンのフォームは Enter による暗黙送信も行われない | 問題なし |
| 依存バージョン | fastapi 0.115.6 / uvicorn 0.34.0 固定、React 19.1 / Vite 7.1 / plugin-react 5 / TS 5.9（Node 24 で Vite 7 要件を満たす） | 問題なし（package-lock は導入時に生成） |

---

## 6. 指摘一覧

高（実行時に落ちる・受入条件を満たさない）: **該当なし**

| ID | 重大度 | ファイル:行 | 内容 | 修正案 |
|---|---|---|---|---|
| M-01 | 中 | `frontend/src/components/AddItemForm.tsx:25,32`、`frontend/src/components/ItemRow.tsx:27-34` | `<form>` に `noValidate` が無く、`<input type="number" step="1">` のブラウザ標準検証が働く。小数（1.5）や不正入力（`1e` 等）は submit 自体がブロックされ、ブラウザ言語のネイティブ吹き出しが出るだけで API 呼び出し・400・トースト・再取得が起きない。計画書 5.3「検証の責務をサーバに一本化」と異なり、PBI-2 AC7・PBI-4 AC5 を画面から確認できない／画面言語とずれる | 両フォームに `noValidate` を付与する。さらに不正入力を握りつぶさないよう `type="text" inputMode="numeric"` にして入力文字列をそのまま数値化（`Number` で NaN になる場合は文字列のまま送り E004/E005 を受ける等）にする |
| M-02 | 中 | `frontend/src/api.ts:4-5`（既定 `http://localhost:8000/api`）、計画書 8章（uvicorn `--host 127.0.0.1`） | API は IPv4 のみで待ち受けるが、フロント既定の接続先は `localhost`。Windows では `::1` を先に試して IPv4 にフォールバックするまで数百 ms かかる場合があり、共通 AC1（200ms）を満たせないおそれ（計画書 9章 リスク#1 が現実化しやすい構成） | 既定値を `http://127.0.0.1:8000/api` にする（CORS 許可済み・オリジンはフロント側なので影響なし）か、Step 5 の計測で遅延の有無を必ず確認する |
| L-01 | 低 | `backend/main.py:185-190` | 条件付き UPDATE を commit した**後**に SELECT しているため、その間に他者が削除すると `row is None` のまま `row_to_item(None)` → `TypeError` → 更新成功なのに E099。また他者更新後の値を「更新後の Item」として返しうる | commit 前（同一トランザクション内）に SELECT する、または `UPDATE ... RETURNING id, name, quantity, created_at, updated_at`（SQLite 3.35+）で取得する |
| L-02 | 低 | `frontend/src/App.tsx:60-67`、`frontend/src/components/ItemList.tsx:15-17` | 初回取得が失敗（サーバ停止等）すると `loading=false`・`items=[]` となり、エラートーストと同時に「品目がありません。」が表示され、0 件と誤認しうる | 初回失敗フラグを持ち、失敗時は空状態文言を出さない（または読み込み失敗の表示にする） |
| L-03 | 低 | `frontend/src/components/ConfirmDialog.tsx:23-29` | `cancel` イベントを経ずにダイアログが閉じた場合（Chrome の close watcher 仕様で Esc 連打時に cancel が抑止不可になる等）、`deleteTarget` が残り、同じ品目の削除ボタンを押しても state が変わらず再表示されない（削除が誤実行されることはない） | `<dialog onClose={onCancel}>` を追加し、ネイティブに閉じた場合も `deleteTarget` を null に戻す |
| L-04 | 低 | `frontend/src/App.tsx:80-91` | 操作がネットワークエラーのとき、操作のエラートーストと続く `refresh()` のエラートーストで同じ「サーバに接続できませんでした」が 2 件出る | `refresh` にトースト抑止の引数を設ける、または直前と同文のトーストは追加しない |
| L-05 | 低 | `backend/errors.py:56-73` | API仕様書 1.7 は `HTTPException` へのハンドラ登録も求めるが未登録。ルーティング不一致 404 / 405 は `{"detail": ...}` 形式で返る（計画書 9章 #4 で対象外と仮置き済み。FE は `msg.error.unknown` で表示） | 受講者判断。共通形式化するなら `StarletteHTTPException` ハンドラを追加し新コード（E011 等）を採番。対象外のままなら API仕様書 1.7 の記述と整合させる |
| L-06 | 低 | `backend/main.py:204,214`、`backend/errors.py:48` | API仕様書 1.3 はレスポンス Content-Type を `application/json; charset=utf-8` と定めるが、Starlette の `JSONResponse` は `application/json`（charset なし）を返す | `JSONResponse(..., media_type="application/json; charset=utf-8")` 相当にする（`default_response_class` を charset 付きのサブクラスに）か、仕様書の表記を実装に合わせる |
| L-07 | 低 | `backend/main.py:75-78` | 4300 桁を超える整数リテラルは Python の int 桁数上限で `json.loads` が `ValueError` となり、E004/E005/E006 ではなく E001 になる | 実害は小さい。厳密にするなら `json.loads(..., parse_int=...)` で範囲外を検出し各項目のエラーにする。または仕様上 E001 で可と明記 |
| L-08 | 低 | `backend/main.py:94-104, 149-153` | 孤立サロゲート（`"\ud800"`）を含む name は検証を通過し、sqlite3 バインド時の `UnicodeEncodeError` で E099（500）になる | `validate_name` で `name.encode("utf-8")` を試し、失敗時は E002（または E001）とする |
| L-09 | 低 | `frontend/src/App.tsx:133`、`frontend/src/components/LanguageSwitcher.tsx:11`、`frontend/src/components/ToastList.tsx:19`、`frontend/index.html:6` | 見出し「在庫管理 / Inventory」、`aria-label="Language"` / `"close"`、ページタイトルが定義書 2章に無い固定文字列（言語切り替えに追随しない） | 定義書 2.5 に `msg.label.app_title` 等を追記し `t()` 経由にする（定義書 2.5 注記の運用どおり） |
| L-10 | 低 | `frontend/tsconfig.json:14,16` | `vite.config.ts` を型チェック対象に含むが `@types/node` が無い。`skipLibCheck` で通る見込みだが未検証 | Step 5 で `npm run build` を実行して確認。エラー時は `@types/node` を devDependencies に追加するか `vite.config.ts` を include から外す |
| L-11 | 低 | `frontend/src/App.tsx:96,105` | 画面入力 `10.0` は `Number()` で `10` になり整数として送られる（API 単体では `10.0` は E004/E005）。画面と API で受理範囲がわずかに異なる | 仕様上の問題は小さい。M-01 の対応で入力文字列の扱いを決める際に合わせて整理する |

---

## 7. サマリ

### 受入条件の判定件数（全 28 件）

| 区分 | ○ | △ | × | − | 計 |
|---|---|---|---|---|---|
| PBI-1 | 5 | 0 | 0 | 0 | 5 |
| PBI-2 | 6 | 1 | 0 | 0 | 7 |
| PBI-3 | 4 | 0 | 0 | 0 | 4 |
| PBI-4 | 6 | 1 | 0 | 0 | 7 |
| 共通 | 3 | 0 | 0 | 2 | 5 |
| **合計** | **24** | **2** | **0** | **2** | **28** |

- △ の 2 件（PBI-2 AC7、PBI-4 AC5）は API としては満たしており、画面からの操作でブラウザ標準検証が先に働く点（M-01）が原因。
- − の 2 件（共通 AC1・AC2）は性能の実測が必要なため Step 5 で確認する（M-02 の遅延リスクに注意）。
- 文言は backend 11 キー・frontend 19 キーとも 3 言語で定義書と完全一致。エラーコード・HTTPステータス・details 形式・検証の優先順位・422→400 変換・E099 時の CORS も仕様どおり。

### Step 5 で確認すべき事項

1. 共通 AC1・AC2: 100 件投入状態で API-1〜4 の応答時間を計測（`localhost` と `127.0.0.1` の差も確認）。
2. PBI-4 AC4: 2 タブ（または curl）で同時更新し、E010 のトースト表示と再取得を確認。
3. E099 応答をブラウザで受け、CORS エラーにならず `error.message` がトースト表示されることを確認（DB ファイルをロック・破損させる等で再現）。
4. `npm run build`（`tsc --noEmit`）が通ること（L-10）。
5. M-01 対応後、画面から小数・文字列入力で E004 / E005 のトーストが出ること。

---

## 対応状況（レビュー後の修正）

| 指摘 | 対応 | 内容 |
|---|---|---|
| M-01 | 修正済み | `AddItemForm.tsx` と `ItemRow.tsx` のフォームに `noValidate` を付与し、入力検証をサーバ（E004/E005 → トースト＋再取得）に一本化 |
| M-02 | 修正済み | `api.ts` の既定ベースURLを `http://127.0.0.1:8000/api` に変更（計画書 8章も更新） |
| 低 L-01〜L-11 | 未対応 | Step 5 で実際に動かして確認しながら対応する |

あわせて `backend/requirements.txt` を推移的依存まで含めた全固定に変更した（`pip install --no-deps` で導入）。クリーンな venv で `pip install --no-deps` → `pip check`（問題なし）→ `import main`（4エンドポイント登録を確認）まで実施済み。
