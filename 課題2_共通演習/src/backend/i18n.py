"""多言語メッセージと Accept-Language 判定（定義書 3.2 / 4.1）。"""

SUPPORTED_LANGS = ("ja", "en", "zh")
DEFAULT_LANG = "ja"


def resolve_lang(header: str | None) -> str:
    """Accept-Language の先頭タグのプライマリ部分で言語を決める。未対応・不正は ja。
    例: "en-US,en;q=0.9" -> en / "zh-CN" -> zh / "*" -> ja（q 値の並べ替えはしない）"""
    if not header:
        return DEFAULT_LANG
    first = header.split(",")[0].split(";")[0].strip()
    primary = first.split("-")[0].strip().lower()
    return primary if primary in SUPPORTED_LANGS else DEFAULT_LANG


# エラーメッセージ辞書（定義書 3.2）。zh は参考訳（未検証）。
MESSAGES: dict[str, dict[str, str]] = {
    "ja": {
        "err.invalid_request": "リクエストの形式が正しくありません。",
        "err.item_name_required": "品目名は必須です。",
        "err.item_name_too_long": "品目名は{max_length}文字以内で入力してください。",
        "err.initial_quantity_invalid": "初期在庫数は0以上の整数で指定してください。",
        "err.delta_invalid": "増減量は0以外の整数で指定してください。",
        "err.expected_quantity_invalid": "現在の在庫数（expected_quantity）は整数で指定してください。",
        "err.item_id_invalid": "品目IDの指定が正しくありません。",
        "err.item_not_found": "指定された品目が存在しません。",
        "err.item_name_duplicate": "同じ名称の品目が既に登録されています。",
        "err.stock_conflict": "在庫数が他の操作により更新されています。最新の在庫数を表示しました。",
        "err.internal_server_error": "サーバ内部でエラーが発生しました。しばらくしてからもう一度お試しください。",
    },
    "en": {
        "err.invalid_request": "The request format is invalid.",
        "err.item_name_required": "Item name is required.",
        "err.item_name_too_long": "Item name must be {max_length} characters or fewer.",
        "err.initial_quantity_invalid": "Initial stock must be an integer of 0 or greater.",
        "err.delta_invalid": "Adjustment amount must be a non-zero integer.",
        "err.expected_quantity_invalid": "The current stock quantity (expected_quantity) must be an integer.",
        "err.item_id_invalid": "The item ID is invalid.",
        "err.item_not_found": "The specified item does not exist.",
        "err.item_name_duplicate": "An item with the same name already exists.",
        "err.stock_conflict": "The stock quantity was updated by another operation. The latest quantity is now displayed.",
        "err.internal_server_error": "An internal server error occurred. Please try again later.",
    },
    # 中国語（簡体字）は参考訳（未検証）
    "zh": {
        "err.invalid_request": "请求格式不正确。",
        "err.item_name_required": "品目名称为必填项。",
        "err.item_name_too_long": "品目名称不能超过{max_length}个字符。",
        "err.initial_quantity_invalid": "初始库存必须是大于等于0的整数。",
        "err.delta_invalid": "增减量必须是非0的整数。",
        "err.expected_quantity_invalid": "当前库存数量（expected_quantity）必须是整数。",
        "err.item_id_invalid": "品目ID不正确。",
        "err.item_not_found": "指定的品目不存在。",
        "err.item_name_duplicate": "已存在同名品目。",
        "err.stock_conflict": "库存数量已被其他操作更新，已显示最新库存数量。",
        "err.internal_server_error": "服务器内部发生错误，请稍后重试。",
    },
}


def get_message(lang: str, key: str, params: dict | None = None) -> str:
    """メッセージを取得し、{名前} を params の値で単純置換する。"""
    text = MESSAGES.get(lang, MESSAGES[DEFAULT_LANG])[key]
    for name, value in (params or {}).items():
        text = text.replace("{" + name + "}", str(value))
    return text
