import { useState, type FormEvent } from "react";
import { t } from "../i18n";

interface Props {
  busy: boolean;
  // 成功なら true（入力欄をクリアする）。quantityText が空なら未指定として扱う
  onAdd: (name: string, quantityText: string) => Promise<boolean>;
}

// PBI-2: 追加フォーム。検証はサーバに一本化（E002〜E004 をトースト表示）
export default function AddItemForm({ busy, onAdd }: Props) {
  const [name, setName] = useState("");
  const [quantity, setQuantity] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    // 成功時のみクリア（失敗時は入力を残して再試行可能）
    if (await onAdd(name, quantity)) {
      setName("");
      setQuantity("");
    }
  }

  return (
    <form className="add" onSubmit={handleSubmit} noValidate>
      <label>
        {t("msg.label.item_name")}
        <input type="text" value={name} onChange={(e) => setName(e.target.value)} />
      </label>
      <label>
        {t("msg.label.initial_quantity")}
        <input type="number" step="1" value={quantity} onChange={(e) => setQuantity(e.target.value)} />
      </label>
      <button type="submit" disabled={busy}>{t("msg.button.add")}</button>
    </form>
  );
}
