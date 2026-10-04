import { useEffect } from "react";
import type { Toast } from "../types";

interface Props {
  toasts: Toast[];
  onClose: (id: number) => void;
}

function ToastItem({ toast, onClose }: { toast: Toast; onClose: (id: number) => void }) {
  // 成功 3 秒・エラー 6 秒で自動消去
  useEffect(() => {
    const timer = setTimeout(() => onClose(toast.id), toast.kind === "success" ? 3000 : 6000);
    return () => clearTimeout(timer);
  }, [toast.id, toast.kind, onClose]);

  return (
    <div className={`toast ${toast.kind}`} role={toast.kind === "error" ? "alert" : "status"}>
      <span>{toast.text}</span>
      <button type="button" aria-label="close" onClick={() => onClose(toast.id)}>
        ×
      </button>
    </div>
  );
}

// 共通 AC5: エラーはトーストで統一表示
export default function ToastList({ toasts, onClose }: Props) {
  return (
    <div className="toasts">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onClose={onClose} />
      ))}
    </div>
  );
}
