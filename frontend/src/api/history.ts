import { http, unwrap } from "./client";
import type { HistoryItem, MatchDetailResponse, PaginationResult } from "../types/api";

export async function getMyHistory(page = 1, size = 20): Promise<PaginationResult<HistoryItem>> {
  return unwrap<PaginationResult<HistoryItem>>(
    http.get("/history/me", {
      params: { page, size },
    }),
  );
}

export async function getMatchDetail(matchId: number): Promise<MatchDetailResponse> {
  return unwrap<MatchDetailResponse>(http.get(`/history/matches/${matchId}`));
}
