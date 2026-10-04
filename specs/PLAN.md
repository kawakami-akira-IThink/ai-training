# 実装計画：顧客マスタ API（CRUD）

仕様の正は [SPEC.md](SPEC.md)。本計画と食い違う場合は SPEC.md を優先する。

## 1. ファイル構成

既存の `doc/`（別演習の成果物）とは混ぜないよう、新しいディレクトリ `customer_api/` にまとめる。

```
customer_api/
├── app/
│   ├── __init__.py
│   ├── main.py         # FastAPI アプリ本体・ルーティング（登録/変更/削除/検索）
│   ├── schemas.py      # 入力モデルとバリデーション（Pydantic）
│   ├── errors.py       # エラーコード定義・例外ハンドラ（{"code","message"} 形式）
│   ├── auth.py         # Bearer 固定値チェック（OAuth 実装済みと仮定したスタブ）
│   ├── db.py           # SQLite 接続・テーブル作成・ロック付きトランザクション
│   ├── repository.py   # 顧客の CRUD SQL
│   └── log_crypto.py   # 顧客情報を Fernet で暗号化してログ出力
├── tools/
│   └── decrypt_log.py  # 暗号化ログの復号ツール（「復号可能」の確認用）
├── tests/
│   ├── conftest.py     # テスト用の一時 DB・環境変数・TestClient
│   ├── test_crud.py    # 正常系
│   ├── test_errors.py  # 異常系（入力・認証・404・重複）
│   └── test_lock.py    # ロック競合
├── requirements.txt    # fastapi, uvicorn, cryptography, pytest, httpx
├── .env.example        # API_TOKEN, LOG_ENCRYPTION_KEY, DB_PATH のサンプル
└── README.md           # 起動方法・テスト方法
```

## 2. 主要処理

### 2.1 API

| 操作 | メソッド・パス | 正常時 |
|------|----------------|--------|
| 登録 | `POST /customers` | 201 `{"id": n}` |
| 変更 | `PUT /customers/{id}` | 204 |
| 削除 | `DELETE /customers/{id}` | 204 |
| 検索 | `GET /customers?name=&age=&gender=&job=` | 200 顧客の配列 |

### 2.2 バリデーション（schemas.py）
- name：1〜256文字、age：0〜1000 の整数、gender：`male` / `female`、job：0〜256文字（省略時は空文字）
- FastAPI 標準の 422 は、例外ハンドラで **400 `VALIDATION_ERROR`** に変換する。

### 2.3 重複チェック
- 登録・変更の前に、4項目すべてが一致する行を検索する。変更時は自分自身（同じ id）を除く。
- 保険として、テーブルに `UNIQUE(name, age, gender, job)` 制約を付ける。同時登録ですり抜けた場合は IntegrityError を `DUPLICATE` に変換する。
  - job を NULL ではなく空文字で保存するのは、NULL だと UNIQUE 制約が効かないため。

### 2.4 ロック（db.py）
- 接続は `sqlite3.connect(DB_PATH, timeout=0, isolation_level=None)` とする。
- 変更・削除は `BEGIN IMMEDIATE` で書き込みロックを取ってから、存在確認 → 重複確認 → 更新/削除 → `COMMIT` の順に行う。
- ロックが取れない場合（`OperationalError: database is locked`）は待たずに **409 `LOCKED`** を返す。
- 例外が起きたら `ROLLBACK` する。

### 2.5 検索
- 指定された条件だけで `WHERE ... AND ...` を組み立てる（値はプレースホルダで渡し、SQL インジェクションを防ぐ）。
- 条件が1つもない場合は DB にアクセスせず、空配列を返す。

### 2.6 認証（auth.py）
- `Authorization: Bearer <token>` を環境変数 `API_TOKEN` と比較する（`hmac.compare_digest` を使う）。
- `API_TOKEN` が未設定のときは全リクエストを拒否する（安全側に倒す）。
- 全エンドポイントに依存関係として付ける。

### 2.7 ログ暗号化（log_crypto.py）
- 顧客情報（name, age, gender, job）を JSON にして Fernet で暗号化し、`customer_enc=<暗号文>` として出力する。
- id、操作名、HTTP ステータス、エラーコードは平文で出力する。
- 鍵は環境変数 `LOG_ENCRYPTION_KEY` から読む。
- `tools/decrypt_log.py` で、ログファイルの暗号文を復号して表示できるようにする。

## 3. テスト観点

| 区分 | 観点 | 対応する受入基準 |
|------|------|------------------|
| 正常系 | 登録 → 全項目一致の検索で見つかる | 登録 |
| 正常系 | 変更 → 検索結果に反映される | 変更 |
| 正常系 | 削除 → 検索で見つからない | 削除 |
| 正常系 | 条件なしの検索 → 0件 | 検索 |
| 正常系 | 一部の条件だけの検索 → AND で絞り込まれる | 検索 |
| 異常系 | 全項目一致で登録 → `DUPLICATE` | 重複 |
| 異常系 | 変更後の値が他の顧客と全項目一致 → `DUPLICATE` | 重複 |
| 異常系 | 何も変わらない変更 → エラーにならない | 重複 |
| 異常系 | 境界値（name 256/257文字、age -1/0/1000/1001、gender が `other`）→ `VALIDATION_ERROR` | 入力 |
| 異常系 | 存在しない id の変更・削除 → `NOT_FOUND` | 404 |
| 異常系 | トークンなし・不正 → `UNAUTHORIZED` | 認証 |
| 異常系 | 別の接続が `BEGIN IMMEDIATE` で保持中に変更・削除 → `LOCKED` | ロック |
| ログ | ログに顧客情報が平文で出ない、かつ復号すると元の値に戻る | セキュリティ |

- ロックのテストは、本当に同時にリクエストを送ると結果が不安定になる。そのため、テスト側で別の接続からロックを握った状態で API を呼ぶ形にして、結果が毎回同じになるようにする。

## 4. 未確定事項（人が判断する）
- **ロック中の登録**：SQLite は DB 全体がロックされるため、ロック中は登録も失敗する。登録も `LOCKED` にするか（案：同じく `LOCKED` を返す）。
- **ロック中の検索**：読み取りは `BEGIN IMMEDIATE` 中でも実行できるので、検索はエラーにしない想定。
- **DB の場所**：環境変数 `DB_PATH` で指定する（既定値は `customer_api/customers.db`）。`*.db` を `.gitignore` に追加する。
- **ログの出力先**：標準出力のみとするか、ファイルにも出すか（案：標準出力のみ）。

## 5. 差分方針（ドラフト作成時）
- 追加するのは `customer_api/` 配下だけ。`doc/` には触れない。
- 既存ファイルの変更は次の2つだけ。
  - `.gitignore`：`*.db` を追加
  - `README.md`：「構成」に `customer_api/` の1行を追加
- 依存パッケージは `customer_api/.venv` に入れる（既存の `.gitignore` で除外済み）。
