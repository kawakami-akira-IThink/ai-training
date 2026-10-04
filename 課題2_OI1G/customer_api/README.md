# 顧客マスタ API（最小ドラフト）

FastAPI + SQLite の顧客マスタ CRUD。仕様は `../specs/SPEC.md`、計画は `../specs/PLAN.md`。

## セットアップ

```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Windows (Git Bash)
```

## 環境変数

| 名前 | 内容 |
|------|------|
| `API_TOKEN` | Bearer トークンの固定値（OAuth 実装済み仮定のスタブ）。未設定だと全リクエスト 401 |
| `LOG_ENCRYPTION_KEY` | ログ暗号化用 Fernet 鍵 |
| `DB_PATH` | SQLite ファイルのパス（省略時は `customer_api/customers.db`） |

鍵の生成：

```
.venv/Scripts/python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 起動

```
API_TOKEN=dummy-token LOG_ENCRYPTION_KEY=<生成した鍵> .venv/Scripts/python -m uvicorn app.main:app
```

## API

| メソッド・パス | 内容 |
|------|------|
| `POST /customers` | 登録（201 `{"id": ...}`） |
| `PUT /customers/{id}` | 変更（204）。`id` は 1〜2^63-1、範囲外は 400 |
| `DELETE /customers/{id}` | 削除（204）。`id` は 1〜2^63-1、範囲外は 400 |
| `POST /customers/search` | 検索（200 で配列）。条件は JSON body。`name` 必須、`age` / `gender` / `job` は任意（AND・完全一致） |

- 検索条件を URL（アクセスログ）に載せないため、検索は GET ではなく POST。`name` を必須にして全件取得を防いでいる。
- `name` / `job` は前後の空白を除去してから検証する。制御文字（改行・タブ含む）は 400。
- `/docs`・`/redoc`・`/openapi.json` は無効（404）。

例：

```
curl -X POST -H "Authorization: Bearer dummy-token" -H "Content-Type: application/json" \
  -d '{"name": "山田", "gender": "male"}' http://127.0.0.1:8000/customers/search
```

## テスト

```
.venv/Scripts/python -m pytest
```

## ログの復号

ログは標準出力のみ。顧客情報は `customer_enc=<暗号文>` で出力される。

```
LOG_ENCRYPTION_KEY=<鍵> .venv/Scripts/python tools/decrypt_log.py ログファイル   # 省略時は標準入力
```
