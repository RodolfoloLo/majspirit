import { http, unwrap } from "./client";
import type { HistoryItem, PaginationResult } from "../types/api";

export async function getMyHistory(page = 1, size = 20): Promise<PaginationResult<HistoryItem>> {
  return unwrap<PaginationResult<HistoryItem>>(
    http.get("/history/me", {
      params: { page, size },
    }),
  );
}
