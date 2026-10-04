// 型定義（API仕様書 1.5 / 1.8 に対応）

export type Lang = "ja" | "en" | "zh";

/** 品目オブジェクト（API仕様書 1.8）。quantity はマイナス値を取りうる */
export interface Item {
  id: number;
  name: string;
  quantity: number;
  created_at: string;
  updated_at: string;
}

/** エラーコード（定義書 3章）。未知のコードも来うるため string も許容 */
export type ErrorCode =
  | "E001" | "E002" | "E003" | "E004" | "E005" | "E006"
  | "E007" | "E008" | "E009" | "E010" | "E099";

/**
 * 失敗の正規化結果（定義書 4.3 / 共通 AC5）
 * - api: 共通エラー形式の応答（message はサーバが翻訳済み）
 * - network: 通信失敗 → msg.error.network
 * - unknown: 共通形式でない応答 → msg.error.unknown
 */
export type ApiFailure =
  | { kind: "api"; status: number; code: ErrorCode | string; message: string; details: Record<string, unknown> }
  | { kind: "network" }
  | { kind: "unknown"; status: number };

/** 失敗を例外として投げるためのクラス */
export class ApiError extends Error {
  failure: ApiFailure;
  constructor(failure: ApiFailure) {
    super(failure.kind === "api" ? failure.message : failure.kind);
    this.failure = failure;
  }
}

export type ToastKind = "success" | "error";

export interface Toast {
  id: number;
  kind: ToastKind;
  text: string;
}
