# 実装計画（Step 4: APIの実装）: 在庫管理システム

本書は Step 4 の「実装計画」であり、**コードは含まない**。受講者の承認後に、本書に沿って最小ドラフトを生成し、静的レビュー（受入条件との突合）まで行う。起動・動作確認は Step 5 / 自習パートで行う。

関連文書: `doc/system_setting.md`、`doc/pbi.md`、`doc/api_specification.md`（以下「API仕様書」）、`doc/error_and_i18n_definition.md`（以下「定義書」）

- 成果物の配置: `課題2_共通演習/src/backend/`（Python 3.12 + FastAPI + 標準ライブラリ `sqlite3`）、`課題2_共通演習/src/frontend/`（React + TypeScript、Vite）。Step 5 のテストは `課題2_共通演習/test/`。
- 実行環境: Windows、Node.js v24 / npm 11、Python 3.12（fastapi は未インストール。venv + requirements.txt で導入）。
- 方針: 研修用の小規模アプリ。ORM・状態管理ライブラリ・UI ライブラリ・過剰な層分けは使わず、最小で受入条件を満たす。

---

## 1. 全体構成

```
ブラウザ (React + TS)                FastAPI (uvicorn)               SQLite
http://localhost:5173  --fetch-->  http://localhost:8000/api  --sqlite3-->  inventory.db
  Accept-Language: ja|en|zh          (リクエストごとに接続)              (items テーブル 1つ)
  <-- JSON / エラー共通形式 + Content-Language
```

| 項目 | 内容 |
|---|---|
| API ポート | 8000（uvicorn。`--host 127.0.0.1`） |
| フロント ポート | 5173（Vite。`strictPort: true` で固定し、CORS 許可オリジンと一致させる） |
| DB | `src/backend/inventory.db`（環境変数 `INVENTORY_DB` で上書き可。Step 5 のテスト用 DB 分離のため） |

### CORS と Vite proxy の選択

**推奨: CORS（`CORSMiddleware`）を採る。**

理由:
1. API仕様書 1.2 が「本仕様では CORS 許可を標準とする」と定めており、仕様と実装を一致させられる。
2. Step 5 の curl / スクリプトからの検証（ブラウザ非経由）も、同じベースURL（`http://localhost:8000/api`）で行え、フロント経由と直叩きで差が出ない。
3. フロントのコードは `fetch(BASE + path)` の1箇所で済み、Vite 側に追加設定が要らない。

代替（proxy）の位置づけ: CORS 不要になる利点はあるが、仕様書の記述変更が必要になる。Windows で `localhost` の名前解決（IPv6 `::1` → IPv4 のフォールバック）による遅延が出た場合の逃げ道として、フロントのベースURLを `VITE_API_BASE_URL` で切り替え可能にしておく（`http://127.0.0.1:8000/api` も CORS 許可済み。9章のリスク参照）。

CORS 設定値: 許可オリジン `http://localhost:5173` / `http://127.0.0.1:5173`、許可メソッド `GET, POST, DELETE, OPTIONS`、許可ヘッダー `Content-Type, Accept-Language`（API仕様書 1.2 のとおり）。

---

## 2. ディレクトリ・ファイル一覧

```
課題2_共通演習/src/
├── .gitignore                  (新規) .venv/ node_modules/ __pycache__/ *.db dist/ を除外
├── backend/
│   ├── requirements.txt
│   ├── main.py
│   ├── db.py
│   ├── errors.py
│   └── i18n.py
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── api.ts
        ├── types.ts
        ├── i18n.ts
        ├── styles.css
        └── components/
            ├── AddItemForm.tsx
            ├── ItemList.tsx
            ├── ItemRow.tsx
            ├── ConfirmDialog.tsx
            ├── ToastList.tsx
            └── LanguageSwitcher.tsx
```

### バックエンド

| ファイル | 責務（1行） |
|---|---|
| `requirements.txt` | 直接依存（`fastapi`、`uvicorn`）と推移的依存の全パッケージを `==` で固定（`pip install --no-deps` で導入） |
| `main.py` | FastAPI アプリ生成・ミドルウェア登録・4つのエンドポイント・入力検証関数（name / quantity / delta / expected_quantity / id）を持つ |
| `db.py` | SQLite 接続（リクエスト単位）・スキーマ作成・Item の dict 変換・UTC 時刻文字列生成・正規化名称の算出 |
| `errors.py` | `AppError` 例外、エラー辞書（コード→HTTPステータス・メッセージキー）、共通エラーレスポンス生成、例外ハンドラの登録 |
| `i18n.py` | `Accept-Language` 判定関数、3言語のエラーメッセージ辞書（定義書 3.2）、プレースホルダ置換 |

### フロントエンド

| ファイル | 責務（1行） |
|---|---|
| `package.json` / `vite.config.ts` / `tsconfig.json` / `index.html` | Vite + React + TS の最小設定（ポート 5173 固定） |
| `src/main.tsx` | React のエントリポイント |
| `src/App.tsx` | 状態（品目一覧・言語・トースト・ダイアログ・処理中フラグ）の保持と、全操作後の一覧再取得の制御 |
| `src/api.ts` | `fetch` のラッパ（Accept-Language 付与、エラー応答の `ApiError` への正規化）と 4 API の呼び出し関数 |
| `src/types.ts` | `Item`、`Lang`、`ApiError`、エラーコード型の型定義 |
| `src/i18n.ts` | 画面文言辞書（定義書 2章・3言語）、`t(key, params)`、言語の初期値判定・localStorage 保存 |
| `src/styles.css` | 最小限のスタイル（マイナス在庫の赤文字 `.negative`、トースト、ダイアログ） |
| `components/AddItemForm.tsx` | 品目名・初期在庫数の入力と追加ボタン |
| `components/ItemList.tsx` | 一覧表（列見出し）、空状態・読み込み中表示、マイナス在庫注記 |
| `components/ItemRow.tsx` | 1行分の表示（マイナスは赤文字）、増減量入力＋更新ボタン、削除ボタン |
| `components/ConfirmDialog.tsx` | 削除確認ダイアログ（ネイティブ `<dialog>` を使用） |
| `components/ToastList.tsx` | 自前の小さなトースト表示（成功/エラー、自動消去、手動クローズ） |
| `components/LanguageSwitcher.tsx` | ja / en / zh の選択 UI |

> 初回は `npm create vite` を使わず、上記ファイルを最小内容で手書きする（テンプレートの不要ファイルを増やさないため）。README は作らず、起動手順は本書 8章を正とする。

---

## 3. DB スキーマ

```sql
CREATE TABLE IF NOT EXISTS items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,                 -- 前後空白除去後の表示用名称（大文字小文字は入力のまま）
    name_key    TEXT    NOT NULL UNIQUE,          -- 正規化名称 = name.casefold()（同一名称判定用）
    quantity    INTEGER NOT NULL DEFAULT 0,       -- 符号付き整数。マイナス可。CHECK 制約は付けない
    created_at  TEXT    NOT NULL,                 -- ISO 8601 UTC 秒精度 末尾Z
    updated_at  TEXT    NOT NULL
);
```

- `AUTOINCREMENT`: API仕様書 1.8「id は 1 以上・単調増加」を満たすため（削除した ID を再利用しない）。
- `name_key UNIQUE`: 同時登録の競合時も DB 側で重複を検出し、`sqlite3.IntegrityError` を E009 に変換する（API仕様書 1.10）。
- 一覧は `SELECT ... ORDER BY id ASC`（PBI-1 AC4）。API 応答の Item には `name_key` を含めない。
- 接続: リクエストごとに `sqlite3.connect`（`row_factory = sqlite3.Row`、`PRAGMA busy_timeout`）、書き込み後に commit、終了時に close。FastAPI の同期関数エンドポイント（スレッドプール実行）でスレッド間共有を避けるための最小構成。起動時（lifespan）に `CREATE TABLE IF NOT EXISTS` を実行。

---

## 4. バックエンドの主要処理の方針

### 4.1 入力検証（422 → 400 変換と E001〜E007 の振り分け）

API仕様書 1.7 の検証優先順位（① 形式 E001 → ② id E007 → ③ Body 各項目 → ④ 業務チェック）を**確実に守る**ため、次の構成とする。

- Body は Pydantic モデルを使わず、`Request` から自前で読み取って検証する。理由: Pydantic のエラーは `loc`/`type` からの逆引きが必要で複雑になり、`true`/`10.0`/`"10"` を整数と区別する厳密判定や、優先順位（最初の1件のみ返す）の制御が自前の方が単純なため。
- パスパラメータ `id` は `str` で受け、Body 検証の**後**ではなく **E001 の後**に自前検証する（FastAPI の `int` 型にすると E007 が E001 より先に判定されてしまうため）。
- それでも `RequestValidationError` ハンドラは**安全網として登録**する（想定外の検証エラーが FastAPI 既定の 422 `{"detail": ...}` で漏れないよう、`loc` が `path` なら E007、それ以外は E001 の 400 に変換）。

検証関数（`main.py` 内。いずれも失敗時に `AppError(コード, details)` を送出）:

| 関数 | 検証内容 | エラー |
|---|---|---|
| `read_json_object(request)` | Content-Type が `application/json`（`charset` 等のパラメータ許容）／JSON として解析可能（空 Body・構文エラー・UTF-8 不正を含む）／トップレベルが object | E001 |
| `parse_item_id(raw)` | ASCII 数字のみ・1 以上・符号付き64bit範囲内。範囲外は E007 とする | E007 |
| `validate_name(body)` | 未指定・`null`・文字列以外 → E002／`strip()`（全角空白を含む Unicode 空白）後に空 → E002／コードポイント数 101 以上 → E003。戻り値は strip 後の名称 | E002, E003 |
| `validate_initial_quantity(body)` | キー未指定なら 0。指定時は `int` かつ `bool` でない・0 以上・64bit 範囲内。`null`・小数・文字列・真偽値・負値・範囲外は E004 | E004 |
| `validate_delta(body)` | 未指定・`null`・`bool`・非 `int`・0・64bit 範囲外 → E005 | E005 |
| `validate_expected(body)` | 未指定・`null`・`bool`・非 `int` → E006。64bit 範囲外も E006 とする（9章） | E006 |

- Body 内の検証順は定義順（`name` → `quantity`、`delta` → `expected_quantity`）で、最初の1件のみ返す。
- 増減後の範囲チェック: `expected_quantity + delta` が符号付き64bit範囲外なら **E005**（API仕様書 1.9）。UPDATE の条件が `quantity = expected` であり、成功時の結果は `expected + delta` と一致するため、DB アクセス前に決定的に判定できる。この判定は `validate_expected` の後に行い、優先順位（delta → expected_quantity）には影響しない（delta 単体の不正を先に判定）。
- 未定義フィールドは無視（取り出さないだけ）。

### 4.2 エラー辞書・例外ハンドラ（`errors.py`）

- `ERRORS`: `{"E001": (400, "err.invalid_request"), ..., "E010": (409, "err.stock_conflict"), "E099": (500, "err.internal_server_error")}` の 11 件（定義書 3.1 をそのまま転記）。
- `AppError(code, details=None)`: ハンドラが `ERRORS` からステータスとメッセージキーを引く。
- 共通エラーレスポンス生成関数 `build_error_response(code, details, lang)`: `{"error": {"code", "message", "details"}}` を組み立て、`Content-Language` ヘッダーを付与。メッセージは `i18n` の辞書から `lang` で取得し、`details` の値（`max_length` のみ）でプレースホルダを置換する。未置換の `{...}` が残らないことをレビュー項目とする。
- 登録する例外ハンドラ:
  1. `AppError` → 対応するステータスと共通形式。
  2. `RequestValidationError` → 400（4.1 の安全網）。
  3. `Exception` → E099（500）。スタックトレースは `logging` でサーバログのみに出力し、応答には出さない（定義書 4.2）。
- **E099 と CORS の注意**: Starlette では、`Exception` ハンドラの応答は最外殻の ServerErrorMiddleware が返すため CORS ヘッダーが付かず、ブラウザが E099 の本文を読めない。これを避けるため、`@app.middleware("http")` 内で `call_next` を `try/except Exception` で囲んで E099 を生成し、**CORS ミドルウェアより内側**になるよう「http ミドルウェアを先に、`CORSMiddleware` を後に」登録する（後に追加したものが外側になる）。`Exception` ハンドラも念のため併設する。
- ルーティング不一致の 404 / 許可されないメソッドの 405 は、API仕様書 1.7 のとおり FastAPI 既定のままとする（共通形式化は対象外。9章で確認）。

### 4.3 同名判定（API-2）

1. `name = validate_name(...)`（strip 済み）、`name_key = name.casefold()`。NFKC 正規化はしない（全角/半角は区別。API仕様書 1.9）。
2. `INSERT INTO items(name, name_key, quantity, created_at, updated_at)` を直接実行し、`sqlite3.IntegrityError`（name_key の UNIQUE 違反）を捕捉して E009（`details: {"field": "name"}`）。事前 SELECT は行わない（競合時も正しく 409 になるため）。
3. 成功時は 201、Body は登録した Item、`Location: /api/items/{id}` ヘッダー付き。`created_at` と `updated_at` は同値。

### 4.4 在庫増減（API-4）の条件付き UPDATE と 404/409 判定

処理順（API仕様書 5章「処理ルール」）:

1. `read_json_object`（E001）→ `parse_item_id`（E007）→ `validate_delta`（E005）→ `validate_expected`（E006）→ 増減後の範囲チェック（E005）。
2. 1 文の UPDATE を実行:
   `UPDATE items SET quantity = quantity + :delta, updated_at = :now WHERE id = :id AND quantity = :expected`
3. `rowcount == 1` → `SELECT` で更新後の Item を取得し 200 で返す。
4. `rowcount == 0` → `SELECT ... WHERE id = :id`:
   - 行なし → **404（E008, `details: {"id": id}`）**（事前に存在しない場合も、判定の間に削除された場合も同じ経路）。
   - 行あり → **409（E010, `details: {"item": <最新の Item>}`）**。在庫は更新されていない。
5. 「事前の存在確認 SELECT」は行わない。UPDATE 結果だけで 404/409 を分岐するため、判定と更新の間に他の更新が入る余地がない。ただし優先順位（④ 存在確認 → 不一致）とは整合する（存在しなければ E008、存在して不一致なら E010）。

### 4.5 削除（API-3）

`parse_item_id`（E007）→ `DELETE FROM items WHERE id = :id` → `rowcount == 0` なら E008、それ以外は 204（Body なし）。在庫数は条件にしない（マイナス在庫も削除可）。削除済み ID の再 DELETE は 404。

### 4.6 一覧（API-1）

`SELECT id, name, quantity, created_at, updated_at FROM items ORDER BY id ASC` → `{"items": [...]}`（0 件は `[]`）。Query は無視。

### 4.7 Accept-Language 判定と Content-Language（`i18n.py`）

- `resolve_lang(header: str | None) -> str`: ヘッダーが無い・空 → `ja`。カンマで分割した**先頭のタグ**を取り、`;`（q 値）より前を取り出し、前後空白を除去、`-` より前（プライマリ部分）を小文字化。`ja`/`en`/`zh` ならそれを、それ以外（`fr`、`*`、不正書式）は `ja`。q 値による並べ替えはしない（定義書 4.1）。
  - 判定例: `en-US,en;q=0.9` → `en`、`zh-CN` → `zh`、`EN` → `en`、`fr` → `ja`、`*` → `ja`、`` → `ja`。
- 言語はリクエストごとに 1 回だけ決定し、`request.state.lang` に保持する（http ミドルウェアで設定）。
- `Content-Language`: http ミドルウェアで**全レスポンス**（成功・204 を含む）に付与。エラー応答は `build_error_response` でも付与する（ミドルウェアを通らない経路の保険）。
- メッセージ辞書: 定義書 3.2 の 11 キー × 3 言語を `MESSAGES[lang][key]` として転記（中国語は参考訳のまま。コメントで「参考訳（未検証）」と明記）。

### 4.8 例外時 E099

- DB エラー（`sqlite3.Error`（`IntegrityError` による E009 を除く））・想定外例外はすべて E099（500）。メッセージは定型文のみ（SQL・パス・例外名を含めない。定義書 4.2）。詳細は `logging` でサーバログのみに記録。
- 対象は API-1〜4 すべて（http ミドルウェアでの一括捕捉）。

### 4.9 レスポンス時間（共通 AC1・2）

- 同期 SQLite・主キー/UNIQUE インデックスのみの単純クエリで、100 件規模では 200ms を十分下回る見込み。追加の最適化・キャッシュは行わない。
- 性能を悪化させる処理（リクエストごとのスキーマ再作成、重い初期化、同期ログの大量出力）を入れないことを静的レビューの確認項目とする。実測は Step 5 / 自習。

---

## 5. フロントエンドの方針

### 5.1 状態と再取得（共通 AC3・PBI-1 AC5）

- `App` が `items`、`loading`（初回のみ true）、`busy`（操作実行中）、`lang`、`toasts`、`deleteTarget`（確認ダイアログ対象）を `useState` で保持。外部の状態管理ライブラリは使わない。
- **一覧再取得 `refresh()`**: `GET /api/items` を呼び、成功時のみ `items` を更新。失敗時はトースト表示のみで**直前の一覧を維持**（PBI-1 AC5）。応答の順序逆転を避けるため、リクエスト連番を持ち古い応答は破棄する。
- **追加・削除・増減の各ハンドラ**は共通の流れ: `busy=true` → API 呼び出し → 成功ならトースト → 失敗ならエラートースト → **成功・失敗を問わず `await refresh()`** → `busy=false`。`busy` 中は追加・更新・削除ボタンを無効化し、非冪等な増減の二重送信を防ぐ。
- 画面の初回表示・リロード時は `useEffect` で `refresh()` を 1 回実行（PBI-1 AC1、共通 AC4）。DB の値を直接表示し、フロント側でのキャッシュ・並べ替えはしない（ID 昇順は API の順序のまま）。

### 5.2 エラー処理（共通 AC5、定義書 4.3）

`api.ts` が失敗を 3 種の `ApiError` に正規化する:

| 種別 | 判定 | トースト文言 |
|---|---|---|
| `api` | 非 2xx かつ JSON が `{"error": {"code", "message"(文字列), "details"}}` 形式 | `error.message` をそのまま表示（サーバが翻訳済み） |
| `network` | `fetch` が例外（接続不可など） | `msg.error.network` |
| `unknown` | 非 2xx で共通形式でない応答（HTML・想定外 JSON 等） | `msg.error.unknown` |

- 処理の分岐は `error.code` で行う。**E010（409）**: `error.message` をトースト表示し、続く `refresh()` で最新状態に更新（PBI-4 AC4）。**E008（404）**: トースト後に `refresh()`（PBI-3 AC4、PBI-4 AC7）。その他（E001〜E007・E009・E099）: トースト表示＋`refresh()`（共通 AC3 の「成功・失敗を問わず再取得」の解釈。9章で確認）。
- 追加フォームは**成功時のみ**入力欄をクリア（失敗時は入力を残して再試行可能にする）。

### 5.3 表示

- **マイナス在庫の赤文字**: `quantity < 0` の行の在庫数セルに `.negative`（赤）クラスを付与し、負値のまま表示（PBI-1 AC2、PBI-4 AC3）。マイナス在庫が 1 件以上あるとき、一覧付近に `msg.list.negative_stock_note` を表示（例外運用の明示）。
- **空状態**: `items.length === 0` で `msg.list.empty`。初回取得中は `msg.list.loading`。
- **増減 UI**: 各行に増減量入力（`type="number" step="1"`）と更新ボタン。送信時、`expected_quantity` には**その行の画面表示中の在庫数**（`item.quantity`）を送る（不一致検知の要）。入力欄が空の場合は `delta` を送らず、サーバの E005 をトースト表示する（検証の責務をサーバに一本化し、PBI-4 AC5 の振る舞いを画面でも確認できるようにする）。
- **追加フォーム**: 品目名（text）と初期在庫数（number、空なら `quantity` を送らない＝省略時 0。PBI-2 AC2）。クライアント側の長さ・形式検証は最小限（`maxLength` 等は付けず、サーバの E002〜E004 をトースト表示）。
- **削除確認ダイアログ**: 削除ボタンで `deleteTarget` を設定し `ConfirmDialog` を表示（`msg.confirm.delete_*`）。「削除する」押下時のみ DELETE を実行、「キャンセル」では何も呼ばない（PBI-3 AC2）。成功時は `msg.toast.item_deleted`（`{name}` は削除対象の表示名）。
- **成功トースト**: 追加 `msg.toast.item_created`（`{name}` はレスポンスの `name`）、増減 `msg.toast.stock_updated`。
- **トースト**: 自前の `ToastList`（`id`・種別・本文の配列。成功 3 秒・エラー 6 秒で自動消去、×で手動クローズ。エラーは `role="alert"`）。

### 5.4 言語切り替え UI（Accept-Language 送信）

- `LanguageSwitcher`（`<select>`: 日本語 / English / 中文）で `lang` を変更。
- `api.ts` は現在言語を保持するモジュール変数を持ち、**全リクエストに `Accept-Language: <lang>` を付与**（`ja`/`en`/`zh` の単純値）。画面文言（`i18n.ts`）の言語と API の言語を同じ値にそろえる（定義書 4.3-5）。
- 初期言語: localStorage の保存値 → `navigator.language` のプライマリ部分（対応言語なら）→ `ja`。変更時に localStorage へ保存し、`document.documentElement.lang` も更新。
- 言語切り替え時に一覧の再取得は行わない（一覧の内容は言語非依存）。すでに表示中のトーストは元の言語のまま。
- 画面文言辞書は定義書 2章の全キー（トースト・ダイアログ・一覧・通信エラー・ラベル）を 3 言語で転記。`{name}` を `t(key, {name})` で置換。中国語は参考訳（未検証）のコメントを付す。

---

## 6. 受入条件トレーサビリティ

BE = backend、FE = frontend。関数名・コンポーネント名は実装時の予定名。

### PBI-1: 一覧表示

| AC | 条件の要約 | 実装箇所 |
|---|---|---|
| 1 | 画面更新時に DB と一致 | BE `main.py: list_items`（`db.py` の全件 SELECT）／FE `App.tsx: useEffect → refresh`、`api.ts: fetchItems`、`ItemList` |
| 2 | マイナス在庫を赤文字 | BE: `quantity` を負値のまま返す（`db.py` の Item 変換で加工しない）／FE `ItemRow.tsx`（`.negative`）、`styles.css`、`ItemList.tsx`（`msg.list.negative_stock_note`） |
| 3 | 0 件の空状態 | BE `list_items`（`{"items": []}`）／FE `ItemList.tsx`（`msg.list.empty`） |
| 4 | ID 昇順 | BE `list_items`（`ORDER BY id ASC`）／FE: 並べ替えをしない（`App.tsx` の `items` を API 順のまま描画） |
| 5 | 一覧取得失敗でトースト・一覧維持 | BE `errors.py`（E099 の共通形式）／FE `App.tsx: refresh`（失敗時は `items` を更新しない）、`api.ts`（`network`/`unknown` の正規化）、`ToastList` |

### PBI-2: 品目追加

| AC | 条件の要約 | 実装箇所 |
|---|---|---|
| 1 | 有効な名称・初期在庫で登録（201） | BE `main.py: create_item`、`db.py`（INSERT・Item 変換）、201 と `Location`／FE `AddItemForm.tsx`、`App.tsx: handleAdd`、`msg.toast.item_created` |
| 2 | 初期在庫省略時 0 | BE `validate_initial_quantity`（未指定→0）、スキーマ `DEFAULT 0`／FE `AddItemForm`（空なら `quantity` を送らない） |
| 3 | 同一名称は 409 | BE `create_item`（`IntegrityError` → `AppError("E009")`）、`name_key UNIQUE`／FE `App.tsx: handleAdd` の失敗経路（`error.message` をトースト） |
| 4 | 空白除去＋大小無視で同一判定 | BE `validate_name`（`strip()`）、`db.py: normalize_name`（`casefold()`）、`name_key UNIQUE` |
| 5 | 品目名が空・空白のみ（400） | BE `validate_name`（E002）／FE: トースト表示 |
| 6 | 100 文字超（400） | BE `validate_name`（E003, `max_length: 100`）、`i18n.py`（`{max_length}` 置換） |
| 7 | 初期在庫が不正（400） | BE `validate_initial_quantity`（E004。`bool` 除外・負値・非整数・範囲外） |

### PBI-3: 品目削除

| AC | 条件の要約 | 実装箇所 |
|---|---|---|
| 1 | 削除・他品目に影響なし | BE `main.py: delete_item`（`WHERE id` のみ）／FE `ItemRow`（削除ボタン）、`App.tsx: handleDelete`、`msg.toast.item_deleted` |
| 2 | 削除前の確認ダイアログ | FE `ConfirmDialog.tsx`、`App.tsx`（`deleteTarget` 経由でのみ DELETE を実行）、`msg.confirm.delete_*` |
| 3 | 在庫が 0 でなくても削除可 | BE `delete_item`（在庫を条件にしない） |
| 4 | 存在しない ID は 404＋トースト＋再取得 | BE `delete_item`（`rowcount == 0` → E008）／FE `App.tsx: handleDelete` の失敗経路（トースト→`refresh`） |

### PBI-4: 在庫増減

| AC | 条件の要約 | 実装箇所 |
|---|---|---|
| 1 | +5 で 10→15（200） | BE `main.py: adjust_item`（条件付き UPDATE → 更新後 Item を返す）／FE `ItemRow`（`expected_quantity = item.quantity`）、`msg.toast.stock_updated` |
| 2 | -3 で 10→7 | 同上 |
| 3 | マイナス在庫を許容（2→-3） | BE: スキーマに CHECK 無し、`adjust_item` に下限チェック無し／FE `ItemRow`（`.negative`） |
| 4 | 不一致は 409＋最新 Item、トースト＋再取得 | BE `adjust_item`（`rowcount == 0` かつ行あり → E010, `details.item`）／FE `App.tsx: handleAdjust` の失敗経路（トースト→`refresh`） |
| 5 | 増減量が 0・非整数・未指定（400） | BE `validate_delta`（E005） |
| 6 | expected_quantity 未指定・非整数（400） | BE `validate_expected`（E006） |
| 7 | 存在しない品目は 404＋トースト＋再取得 | BE `adjust_item`（`rowcount == 0` かつ行なし → E008）／FE `handleAdjust` の失敗経路 |

### 共通の受入条件

| AC | 条件の要約 | 実装箇所 |
|---|---|---|
| 1 | 全操作 0.2 秒以内 | BE 全体（同期 SQLite・単純クエリ・追加処理なし）。実測は Step 5 |
| 2 | 測定条件（ローカル・100 件） | 同上（Step 5 で 100 件投入して測定） |
| 3 | 操作後（成功・失敗とも）に再取得 | FE `App.tsx`（追加・削除・増減ハンドラの共通フロー末尾で `await refresh()`） |
| 4 | 画面更新時に DB と一致 | PBI-1 AC1 と同じ |
| 5 | エラー表示の統一 | BE `errors.py`（全エラーを共通形式で返す。`AppError`／`RequestValidationError`／`Exception` ハンドラ、http ミドルウェアの E099）／FE `api.ts`（`ApiError` 正規化）、`ToastList.tsx` |

### その他（API仕様書・定義書の要求）

| 要求 | 実装箇所 |
|---|---|
| 422 を使わず 400 に統一（API仕様書 1.7） | `errors.py`（`RequestValidationError` ハンドラ）、`main.py` の自前検証 |
| 検証優先順位（1.7） | `main.py` の各エンドポイントでの検証関数の呼び出し順 |
| 言語切り替え・`Content-Language`（1.4、定義書 4.1） | `i18n.py: resolve_lang`、`main.py` の http ミドルウェア、`errors.py: build_error_response` |
| CORS（1.2） | `main.py` の `CORSMiddleware` |
| E001〜E010・E099 の定義（定義書 3章） | `errors.py: ERRORS`、`i18n.py: MESSAGES` |
| 画面文言の 3 言語（定義書 2章） | `frontend/src/i18n.ts` |
| 成功レスポンスにメッセージを含めない（1.4） | `main.py`（Item / `{"items": [...]}` / 204 のみ返す） |
| 内部情報を応答に出さない（定義書 4.2） | `errors.py`（E099 は定型文、トレースはログのみ） |

---

## 7. 実装の順序と最小ドラフトの範囲

### 7.1 実装の順序（各ステップは小さく、バックエンド → フロント）

| # | 作業 | 完了の目安 |
|---|---|---|
| 1 | `src/.gitignore`、`backend/requirements.txt` | 依存が 2 つで確定 |
| 2 | `i18n.py`（`resolve_lang`、`MESSAGES` 11 キー × 3 言語） | 定義書 3.2 と文言が一致 |
| 3 | `errors.py`（`ERRORS`、`AppError`、`build_error_response`、ハンドラ登録） | 定義書 3.1 の 11 件が網羅されている |
| 4 | `db.py`（接続、スキーマ、Item 変換、時刻、`normalize_name`） | スキーマが本書 3章と一致 |
| 5 | `main.py` 骨格（アプリ生成、http ミドルウェア、CORS、起動時の DB 初期化）＋ API-1 | ミドルウェアと CORS の登録順が 4.2 のとおり |
| 6 | 検証関数群と API-2（追加） | E001〜E004・E009 が仕様どおり |
| 7 | API-3（削除） | E007・E008・204 |
| 8 | API-4（増減） | E005〜E008・E010、条件付き UPDATE |
| 9 | フロント基盤（`package.json`、Vite 設定、`types.ts`、`i18n.ts`、`api.ts`） | 3 言語辞書が定義書 2章と一致 |
| 10 | `ToastList`・`ConfirmDialog`・`LanguageSwitcher` | |
| 11 | `ItemList`・`ItemRow`・`AddItemForm` | |
| 12 | `App.tsx`（状態・再取得フロー・各ハンドラ）、`main.tsx`、`styles.css` | 全操作後に `refresh()` が呼ばれる |
| 13 | 静的レビュー（7.3） | 突合表の全行が OK、または指摘事項として記録 |

### 7.2 最小ドラフトの範囲

**含める**: 上記ファイル一覧のすべてを、受入条件（PBI-1〜4・共通）と API仕様書・定義書の要求を満たす最小の内容で作成する。

**含めない**:
- 自動テスト・テストスクリプト（Step 5）
- 認証、ページング、ソート、検索、編集（名称変更）
- ORM、マイグレーション、Docker、CI、lint/format 設定
- Vite proxy 設定、本番ビルド用の設定、`.env` ファイル本体（`VITE_API_BASE_URL` は未設定時に既定値を使う）
- ルーティング不一致の 404 / 405 の共通形式化
- README（起動手順は本書 8章）

### 7.3 静的レビュー（受入条件との突合）のやり方

コードを**実行せず**、読み合わせで行う。

1. **突合表の作成**: 本書 6章のトレーサビリティ表の各行について、実際のコード上の該当箇所（ファイル・関数・行）を確認し、「条件を満たす / 欠落 / 逸脱」を判定する。pbi.md の各 AC（PBI-1: 5、PBI-2: 7、PBI-3: 4、PBI-4: 7、共通: 5）が漏れなく対応づけられていることを確認する。
2. **API仕様書との突合**: 各エンドポイントについて、HTTP メソッド・URI・ステータスコード・レスポンス JSON のキー名と型・`details` の形・ヘッダー（`Location`、`Content-Language`）を API仕様書 2〜6章と照合。
3. **エラー・文言の突合**: `ERRORS` と `MESSAGES` が定義書 3.1・3.2 と 1 文字単位で一致していること、フロント辞書が定義書 2章と一致すること、3 言語でキーとプレースホルダの集合が一致することを確認（定義書 5章のチェックと同じ観点）。
4. **検証ロジックの机上テスト**: 境界値（名称 100/101 文字・全角空白のみ・`USB`/`usb`・`true`/`10.0`/`"10"`・`delta=0`・`expected_quantity` 欠落・`id=0/abc/9999999999999999999`・Content-Type 不正・空 Body）を、コードを読んで期待どおりのエラーコードになるか追跡する。
5. **特有の観点**: ① 検証優先順位（E001 → E007 → Body）② 条件付き UPDATE が 1 文で、判定と更新が分離していない ③ 例外が E099 になり内部情報が漏れない（CORS ヘッダー込み）④ 全操作後に `refresh()` が呼ばれる（成功・失敗の両経路）⑤ `expected_quantity` に画面表示中の値を送っている ⑥ 422 / FastAPI 既定形式が外部に出る経路がない。
6. **結果の扱い**: 指摘事項（欠落・逸脱・仕様の曖昧点）を一覧にして受講者に報告し、修正方針の承認を得てから直す。突合表自体は新規ファイルにはせず、報告に含める（ファイル化が必要なら受講者が判断）。

---

## 8. 起動手順（予定）

> 実行は Step 5 / 自習パート。以下は PowerShell での想定（リポジトリルート `D:\ClaudeCode\git\ai-training\` から）。

**バックエンド**
```powershell
cd 課題2_共通演習\src\backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1          # 実行ポリシーで拒否される場合: Set-ExecutionPolicy -Scope Process RemoteSigned
python -m pip install --no-deps -r requirements.txt   # 推移的依存まで固定済みのため依存解決させない
python -m pip check
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
- 起動時に `inventory.db` が自動作成される。API は `http://localhost:8000/api/items`。
- 疎通確認の例: ブラウザまたは `curl http://localhost:8000/api/items` で `{"items": []}`。

**フロントエンド**（別ターミナル）
```powershell
cd 課題2_共通演習\src\frontend
npm install
npm run dev                            # http://localhost:5173
```
- API の向き先を変える場合のみ、`VITE_API_BASE_URL` を設定（既定 `http://127.0.0.1:8000/api`。静的レビュー M-02 により変更）。
- 初期化し直したい場合は、バックエンド停止後に `inventory.db` を削除する。

---

## 9. リスク・未確定事項

### 受講者に判断を求める点

| # | 論点 | 本計画の仮置き |
|---|---|---|
| 1 | CORS と Vite proxy のどちらにするか | **CORS**（API仕様書 1.2 に合わせる）。proxy 化する場合は仕様書 1.2 の更新が必要 |
| 2 | 言語切り替えの方法（定義書 8章で未定義） | **手動の選択 UI（ja/en/zh）**＋localStorage 保存、初期値はブラウザ言語 → `ja` |
| 3 | エラー時（400/409/E099 等）も一覧を再取得するか（pbi.md 未確定事項） | **成功・失敗を問わず再取得**（共通 AC3 の文言どおり）。400 の入力エラーでも再取得される点を許容するか |
| 4 | ルーティング不一致 404 / 405 を共通形式にするか | **対象外（FastAPI 既定のまま）**。共通 AC5 を厳密に解釈するなら共通形式化が必要（新エラーコードの採番を伴う） |
| 5 | 範囲外の整数の扱いで仕様に明記のない部分 | `expected_quantity` が 64bit 範囲外 → **E006**、`id` が 64bit 範囲外 → **E007** と仮置き（DB バインド時の例外で E099 になるのを避けるため） |
| 6 | `msg.list.negative_stock_note`（注記）の表示条件 | **マイナス在庫が 1 件以上あるときのみ**表示（常時表示にもできる） |
| 7 | 増減 UI の形 | 定義書 2.5 のとおり「増減量の入力欄＋更新ボタン」のみ（＋/− クイックボタンは作らない） |
| 8 | `README` を作らず本書 8章を起動手順の正とする方針 | 作らない（必要なら追加） |

### リスク

| # | リスク | 対策 |
|---|---|---|
| 1 | Windows で `localhost` が `::1` に先に解決され、IPv4 へのフォールバックで 200ms 前後の遅延が出て、共通 AC1 を満たせない可能性 | uvicorn は `127.0.0.1` で起動。遅延が出る場合はフロントの `VITE_API_BASE_URL` を `http://127.0.0.1:8000/api` に切り替える（CORS 許可済み）。計測は Step 5 |
| 2 | E099 応答に CORS ヘッダーが付かず、ブラウザで E099 の本文が読めない（Starlette の ServerErrorMiddleware の仕様） | 4.2 のとおり http ミドルウェア内で捕捉し、CORS より内側に配置。静的レビューで登録順を確認 |
| 3 | 数値が JavaScript の安全整数（2^53−1）を超えると、フロントで精度が落ちる | 研修用としては許容（API の範囲検証は 64bit で仕様どおり実装）。必要ならフロント側で上限を設ける |
| 4 | API-4 の E010 で複数人が同時操作した場合の挙動は、実機では 2 画面で確認する必要がある | Step 5 で 2 つのブラウザタブ、または curl で再現 |
| 5 | 中国語メッセージは参考訳（未検証）のため、辞書に誤訳が残りうる | コードコメントと画面上の扱いで「参考訳」と明記（定義書 8章） |
| 6 | 検証を Pydantic でなく自前実装にするため、検証関数の抜け漏れリスクがある | 7.3 の境界値の机上テストと、Step 5 のテストケースで担保 |
| 7 | FastAPI / Vite / React の最新版の仕様差（特に Vite のテンプレートや React 19 の型） | 導入時に `requirements.txt` と `package-lock.json` でバージョンを固定。手書きの最小構成で差異を最小化 |
