import { useCallback, useEffect, useRef, useState } from "react";
import { adjustItem, createItem, deleteItem, fetchItems, setApiLang } from "./api";
import { getInitialLang, saveLang, setCurrentLang, t } from "./i18n";
import { ApiError, type Item, type Lang, type Toast, type ToastKind } from "./types";
import AddItemForm from "./components/AddItemForm";
import ConfirmDialog from "./components/ConfirmDialog";
import ItemList from "./components/ItemList";
import LanguageSwitcher from "./components/LanguageSwitcher";
import ToastList from "./components/ToastList";

/** 言語を画面文言・API(Accept-Language)・html lang にそろえて反映 */
function applyLang(lang: Lang): void {
  setCurrentLang(lang);
  setApiLang(lang);
}

/** 失敗時のトースト文言（定義書 4.3）。api は error.message をそのまま、他は汎用文言 */
function errorText(e: unknown): string {
  if (e instanceof ApiError) {
    const f = e.failure;
    if (f.kind === "api") return f.message;
    if (f.kind === "network") return t("msg.error.network");
  }
  return t("msg.error.unknown");
}

export default function App() {
  const [lang, setLang] = useState<Lang>(() => {
    // 初回描画前に言語を確定（最初の API 呼び出しにも Accept-Language を付けるため）
    const l = getInitialLang();
    applyLang(l);
    return l;
  });
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true); // 初回取得中のみ true
  const [busy, setBusy] = useState(false); // 操作実行中（二重送信防止）
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [deleteTarget, setDeleteTarget] = useState<Item | null>(null);

  const toastId = useRef(0);
  const refreshSeq = useRef(0);

  const pushToast = useCallback((kind: ToastKind, text: string) => {
    toastId.current += 1;
    const id = toastId.current;
    setToasts((prev) => [...prev, { id, kind, text }]);
  }, []);

  const closeToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((x) => x.id !== id));
  }, []);

  /**
   * 一覧再取得（PBI-1 AC1、共通 AC3/AC4）。
   * 失敗時はトーストのみで直前の一覧を維持（PBI-1 AC5）。古い応答は破棄する。
   */
  const refresh = useCallback(async () => {
    refreshSeq.current += 1;
    const seq = refreshSeq.current;
    try {
      const list = await fetchItems();
      if (seq === refreshSeq.current) setItems(list);
    } catch (e) {
      if (seq === refreshSeq.current) pushToast("error", errorText(e));
    } finally {
      if (seq === refreshSeq.current) setLoading(false);
    }
  }, [pushToast]);

  // 画面表示時に 1 回取得（PBI-1 AC1、共通 AC4）
  useEffect(() => {
    void refresh();
  }, [refresh]);

  /**
   * 追加・削除・増減の共通フロー（共通 AC3）。
   * 成否を問わず最後に再取得する。E008/E010 等も error.message をトースト表示 → 再取得
   * （PBI-3 AC4、PBI-4 AC4/AC7、共通 AC5）。成功なら true を返す。
   */
  async function runOperation(action: () => Promise<string>): Promise<boolean> {
    setBusy(true);
    let ok = false;
    try {
      pushToast("success", await action());
      ok = true;
    } catch (e) {
      pushToast("error", errorText(e));
    }
    await refresh();
    setBusy(false);
    return ok;
  }

  // PBI-2: 追加。数量が空なら quantity を送らない（AC2）。検証はサーバに任せる（AC3〜AC7）
  function handleAdd(name: string, quantityText: string): Promise<boolean> {
    const quantity = quantityText.trim() === "" ? undefined : Number(quantityText);
    return runOperation(async () => {
      const created = await createItem(name, quantity);
      return t("msg.toast.item_created", { name: created.name });
    });
  }

  // PBI-4: 増減。expected_quantity は画面表示中の在庫数（AC1〜AC4）。空欄なら delta を送らない（AC5）
  function handleAdjust(item: Item, deltaText: string): Promise<boolean> {
    const delta = deltaText.trim() === "" ? undefined : Number(deltaText);
    return runOperation(async () => {
      await adjustItem(item.id, item.quantity, delta);
      return t("msg.toast.stock_updated");
    });
  }

  // PBI-3 AC2: 確認ダイアログで承諾された場合のみ削除（AC1/AC3/AC4）
  function handleConfirmDelete() {
    const target = deleteTarget;
    setDeleteTarget(null);
    if (!target) return;
    void runOperation(async () => {
      await deleteItem(target.id);
      return t("msg.toast.item_deleted", { name: target.name });
    });
  }

  // 言語変更: 保存（try/catch 内）→ 反映。一覧の再取得は不要
  function handleLangChange(next: Lang) {
    saveLang(next);
    applyLang(next);
    setLang(next);
  }

  return (
    <main>
      <header className="top">
        <h1>在庫管理 / Inventory</h1>
        <LanguageSwitcher lang={lang} onChange={handleLangChange} />
      </header>

      <AddItemForm busy={busy} onAdd={handleAdd} />

      <ItemList
        items={items}
        loading={loading}
        busy={busy}
        onAdjust={handleAdjust}
        onDelete={setDeleteTarget}
      />

      <ConfirmDialog
        target={deleteTarget}
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeleteTarget(null)}
      />
      <ToastList toasts={toasts} onClose={closeToast} />
    </main>
  );
}
