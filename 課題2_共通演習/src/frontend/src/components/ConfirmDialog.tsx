import { useEffect, useRef } from "react";
import { t } from "../i18n";
import type { Item } from "../types";

interface Props {
  target: Item | null;
  onConfirm: () => void;
  onCancel: () => void;
}

// PBI-3 AC2: 削除確認ダイアログ（ネイティブ <dialog>）。承諾時のみ onConfirm
export default function ConfirmDialog({ target, onConfirm, onCancel }: Props) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dlg = ref.current;
    if (!dlg) return;
    if (target && !dlg.open) dlg.showModal();
    if (!target && dlg.open) dlg.close();
  }, [target]);

  return (
    <dialog
      ref={ref}
      onCancel={(e) => {
        // Esc キーはキャンセル扱い（状態は App 側で閉じる）
        e.preventDefault();
        onCancel();
      }}
    >
      {target && (
        <>
          <h2>{t("msg.confirm.delete_title")}</h2>
          <p>{t("msg.confirm.delete_body", { name: target.name })}</p>
          <div className="actions">
            <button type="button" onClick={onCancel}>{t("msg.confirm.delete_cancel")}</button>
            <button type="button" onClick={onConfirm}>{t("msg.confirm.delete_ok")}</button>
          </div>
        </>
      )}
    </dialog>
  );
}
