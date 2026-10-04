import { useState, type FormEvent } from "react";
import { t } from "../i18n";
import type { Item } from "../types";

interface Props {
  item: Item;
  busy: boolean;
  // 成功なら true（増減量欄をクリア）。deltaText が空なら delta を送らない
  onAdjust: (item: Item, deltaText: string) => Promise<boolean>;
  onDelete: (item: Item) => void;
}

// 1行分の表示。在庫数が負なら赤文字（PBI-1 AC2、PBI-4 AC3）
export default function ItemRow({ item, busy, onAdjust, onDelete }: Props) {
  const [delta, setDelta] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (await onAdjust(item, delta)) setDelta("");
  }

  return (
    <tr>
      <td>{item.name}</td>
      <td className={item.quantity < 0 ? "qty negative" : "qty"}>{item.quantity}</td>
      <td>
        <form className="adjust" onSubmit={handleSubmit} noValidate>
          <input
            type="number"
            step="1"
            aria-label={t("msg.label.delta")}
            value={delta}
            onChange={(e) => setDelta(e.target.value)}
          />
          <button type="submit" disabled={busy}>{t("msg.button.adjust")}</button>
        </form>
      </td>
      <td>
        {/* PBI-3 AC2: 確認ダイアログ経由で削除 */}
        <button type="button" disabled={busy} onClick={() => onDelete(item)}>{t("msg.button.delete")}</button>
      </td>
    </tr>
  );
}
