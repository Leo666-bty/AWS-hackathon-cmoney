import { ApiError } from "./client";

export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (typeof error.detail === "string") return error.detail;
    return `服務暫時無法處理（HTTP ${error.status}）`;
  }
  if (error instanceof Error) return error.message;
  return "發生未預期錯誤，請稍後重試。";
}
