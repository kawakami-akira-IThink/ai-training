import { ApiError, type Item, type Lang } from "./types";

// API のベースURL（未設定時はローカル開発の既定値。Windows の localhost→::1 解決による遅延を避けるため IPv4 を直接指定）
const BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) || "http://127.0.0.1:8000/api";

// 現在の言語。全リクエストの Accept-Language に使う（定義書 4.3-5：画面言語と同じ値）
let apiLang: Lang = "ja";
export function setApiLang(lang: Lang): void {
  apiLang = lang;
}

/** 共通エラー形式 {"error": {"code", "message", "details"}} かを判定 */
function toApiFailure(status: number, body: unknown): ApiError {
  if (typeof body === "object" && body !== null) {
    const err = (body as { error?: unknown }).error;
    if (typeof err === "object" && err !== null) {
      const e = err as { code?: unknown; message?: unknown; details?: unknown };
      if (typeof e.code === "string" && typeof e.message === "string") {
        const details =
          typeof e.details === "object" && e.details !== null ? (e.details as Record<string, unknown>) : {};
        return new ApiError({ kind: "api", status, code: e.code, message: e.message, details });
      }
    }
  }
  return new ApiError({ kind: "unknown", status });
}

/** fetch ラッパ。失敗は ApiError（api / network / unknown）に正規化して throw（共通 AC5） */
async function request(method: string, path: string, body?: unknown): Promise<Response> {
  const headers: Record<string, string> = { "Accept-Language": apiLang };
  if (body !== undefined) headers["Content-Type"] = "application/json";

  let res: Response;
  try {
    res = await fetch(BASE_URL + path, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError({ kind: "network" });
  }

  if (!res.ok) {
    let parsed: unknown = null;
    try {
      parsed = await res.json();
    } catch {
      // JSON でない応答（HTML 等）は unknown 扱い
    }
    throw toApiFailure(res.status, parsed);
  }
  return res;
}

/** 成功応答の JSON を読む。読めなければ unknown 扱い */
async function readJson(res: Response): Promise<unknown> {
  try {
    return await res.json();
  } catch {
    throw new ApiError({ kind: "unknown", status: res.status });
  }
}

/** API-1: 一覧取得（PBI-1 AC1/AC4） */
export async function fetchItems(): Promise<Item[]> {
  const data = (await readJson(await request("GET", "/items"))) as { items?: unknown };
  if (!data || !Array.isArray(data.items)) throw new ApiError({ kind: "unknown", status: 200 });
  return data.items as Item[];
}

/** API-2: 追加（quantity 未指定なら省略＝サーバ側で 0。PBI-2 AC2） */
export async function createItem(name: string, quantity?: number): Promise<Item> {
  const body: { name: string; quantity?: number } = { name };
  if (quantity !== undefined) body.quantity = quantity;
  return (await readJson(await request("POST", "/items", body))) as Item;
}

/** API-3: 削除（204 は Body なし） */
export async function deleteItem(id: number): Promise<void> {
  await request("DELETE", `/items/${id}`);
}

/** API-4: 増減（expected_quantity は画面表示中の在庫数。PBI-4 AC4）。delta 未指定なら送らない */
export async function adjustItem(id: number, expectedQuantity: number, delta?: number): Promise<Item> {
  const body: { delta?: number; expected_quantity: number } = { expected_quantity: expectedQuantity };
  if (delta !== undefined) body.delta = delta;
  return (await readJson(await request("POST", `/items/${id}/adjust`, body))) as Item;
}
