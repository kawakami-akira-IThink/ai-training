import { t } from "../i18n";
import type { Item } from "../types";
import ItemRow from "./ItemRow";

interface Props {
  items: Item[];
  loading: boolean;
  busy: boolean;
  onAdjust: (item: Item, deltaText: string) => Promise<boolean>;
  onDelete: (item: Item) => void;
}

// PBI-1: 一覧。並べ替えはせず API の順序（ID 昇順）のまま描画（AC4）
export default function ItemList({ items, loading, busy, onAdjust, onDelete }: Props) {
  if (loading) return <p className="state">{t("msg.list.loading")}</p>;
  // PBI-1 AC3: 0 件の空状態
  if (items.length === 0) return <p className="state">{t("msg.list.empty")}</p>;

  // マイナス在庫が 1 件以上あるときだけ注記を表示
  const hasNegative = items.some((i) => i.quantity < 0);

  return (
    <>
      {hasNegative && <p className="note">{t("msg.list.negative_stock_note")}</p>}
      <table>
        <thead>
          <tr>
            <th>{t("msg.label.item_name")}</th>
            <th className="qty">{t("msg.label.quantity")}</th>
            <th>{t("msg.label.delta")}</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <ItemRow key={item.id} item={item} busy={busy} onAdjust={onAdjust} onDelete={onDelete} />
          ))}
        </tbody>
      </table>
    </>
  );
}
