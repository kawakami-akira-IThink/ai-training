import type { Lang } from "./types";

// 画面文言辞書（error_and_i18n_definition.md 2章）。
// 中国語（zh）は参考訳（未検証）。日本語・英語を正とする。

export const LANGS: Lang[] = ["ja", "en", "zh"];
const STORAGE_KEY = "lang";

type Dict = Record<string, string>;

const MESSAGES: Record<Lang, Dict> = {
  ja: {
    "msg.toast.item_created": "「{name}」を登録しました。",
    "msg.toast.item_deleted": "「{name}」を削除しました。",
    "msg.toast.stock_updated": "在庫を更新しました。",
    "msg.confirm.delete_title": "品目の削除",
    "msg.confirm.delete_body": "「{name}」を削除します。この操作は元に戻せません。よろしいですか？",
    "msg.confirm.delete_ok": "削除する",
    "msg.confirm.delete_cancel": "キャンセル",
    "msg.list.empty": "品目がありません。",
    "msg.list.negative_stock_note": "赤字の在庫数はマイナス在庫です（例外運用）。",
    "msg.list.loading": "読み込み中…",
    "msg.error.network": "サーバに接続できませんでした。通信状況を確認して、もう一度お試しください。",
    "msg.error.unknown": "エラーが発生しました。しばらくしてからもう一度お試しください。",
    "msg.label.item_name": "品目名",
    "msg.label.initial_quantity": "初期在庫数",
    "msg.label.quantity": "在庫数",
    "msg.label.delta": "増減量",
    "msg.button.add": "追加",
    "msg.button.delete": "削除",
    "msg.button.adjust": "更新",
  },
  en: {
    "msg.toast.item_created": "\"{name}\" has been added.",
    "msg.toast.item_deleted": "\"{name}\" has been deleted.",
    "msg.toast.stock_updated": "Stock has been updated.",
    "msg.confirm.delete_title": "Delete item",
    "msg.confirm.delete_body": "\"{name}\" will be deleted. This cannot be undone. Are you sure?",
    "msg.confirm.delete_ok": "Delete",
    "msg.confirm.delete_cancel": "Cancel",
    "msg.list.empty": "No items found.",
    "msg.list.negative_stock_note": "Stock shown in red is negative (exceptional operation).",
    "msg.list.loading": "Loading…",
    "msg.error.network": "Could not connect to the server. Check your connection and try again.",
    "msg.error.unknown": "An error occurred. Please try again later.",
    "msg.label.item_name": "Item name",
    "msg.label.initial_quantity": "Initial stock",
    "msg.label.quantity": "Stock",
    "msg.label.delta": "Adjustment",
    "msg.button.add": "Add",
    "msg.button.delete": "Delete",
    "msg.button.adjust": "Update",
  },
  zh: {
    "msg.toast.item_created": "已添加“{name}”。",
    "msg.toast.item_deleted": "已删除“{name}”。",
    "msg.toast.stock_updated": "库存已更新。",
    "msg.confirm.delete_title": "删除品目",
    "msg.confirm.delete_body": "将删除“{name}”，此操作无法撤销。确定吗？",
    "msg.confirm.delete_ok": "删除",
    "msg.confirm.delete_cancel": "取消",
    "msg.list.empty": "没有品目。",
    "msg.list.negative_stock_note": "红色库存为负库存（例外运营）。",
    "msg.list.loading": "加载中…",
    "msg.error.network": "无法连接到服务器。请检查网络连接后重试。",
    "msg.error.unknown": "发生错误。请稍后重试。",
    "msg.label.item_name": "品目名称",
    "msg.label.initial_quantity": "初始库存",
    "msg.label.quantity": "库存",
    "msg.label.delta": "增减量",
    "msg.button.add": "添加",
    "msg.button.delete": "删除",
    "msg.button.adjust": "更新",
  },
};

// 現在の画面言語（App が変更時に setCurrentLang を呼ぶ）
let currentLang: Lang = "ja";

export function setCurrentLang(lang: Lang): void {
  currentLang = lang;
  document.documentElement.lang = lang;
}

/** 文言取得。{name} 形式のプレースホルダを単純置換する */
export function t(key: string, params?: Record<string, string>): string {
  let text = MESSAGES[currentLang][key] ?? key;
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      text = text.split(`{${k}}`).join(v);
    }
  }
  return text;
}

function isLang(v: unknown): v is Lang {
  return v === "ja" || v === "en" || v === "zh";
}

/** 初期言語: localStorage の保存値 → ブラウザ言語のプライマリ部分 → ja */
export function getInitialLang(): Lang {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (isLang(saved)) return saved;
  } catch {
    // localStorage 使用不可でも動作継続
  }
  const primary = (navigator.language || "").split("-")[0].toLowerCase();
  return isLang(primary) ? primary : "ja";
}

/** 言語の保存（失敗しても無視） */
export function saveLang(lang: Lang): void {
  try {
    localStorage.setItem(STORAGE_KEY, lang);
  } catch {
    // 保存できなくても動作継続
  }
}
